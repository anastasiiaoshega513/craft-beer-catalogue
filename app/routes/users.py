from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import config
from app.dependencies.users import get_current_user
from app.models.tokens import ActivationToken, PasswordResetToken, RefreshToken
from app.models.users import User
from app.schemas.users import (
    AccessTokenSchema,
    MessageResponseSchema,
    PasswordResetCompleteRequestSchema,
    PasswordResetRequestSchema,
    RefreshTokenSchema,
    TokenResponseSchema,
    UserActivationSchema,
    UserLoginSchema,
    UserMeSchema,
    UserRegistrationSchema,
    UserUpdateSchema,
)
from app.security.jwt_token import InvalidTokenError, JWTAuthManager, TokenExpiredError
from app.security.secure_token import hash_token
from app.services.email import send_activation_email, send_password_reset_email
from db.dependencies import get_db

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/register/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user: UserRegistrationSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User)
                              .options(selectinload(User.activation_token))
                              .where(User.email == user.email.lower()))
    existing_user = result.scalar_one_or_none()

    if existing_user and existing_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists.",
        )

    try:
        if existing_user:
            if existing_user.activation_token:
                await db.delete(existing_user.activation_token)
                await db.flush()

            activation_token = ActivationToken(user_id=existing_user.id)
            db.add(activation_token)

        else:
            new_user = User.create(
                email=user.email.lower(),
                raw_password=user.password,
                first_name=user.first_name,
                last_name=user.last_name,
            )

            db.add(new_user)
            await db.flush()

            activation_token = ActivationToken(user_id=new_user.id)
            db.add(activation_token)

        await db.commit()
        await db.refresh(activation_token)

    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        )

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during user creation.",
        )

    activation_link = (
        f"{config.FRONTEND_URL}/activate/?token={activation_token.token}"
    )

    background_tasks.add_task(
        send_activation_email,
        user.email.lower(),
        activation_link,
    )

    return {"message": "User created. Please check your email."}


@router.post("/activate/", response_model=MessageResponseSchema)
async def activate_user(
    activation_token: UserActivationSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ActivationToken)
        .options(selectinload(ActivationToken.user))
        .where(ActivationToken.token == activation_token.token)
    )

    activation_token = result.scalar_one_or_none()

    if activation_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid activation token.",
        )

    if activation_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        await db.delete(activation_token)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation token has expired.",
        )

    user = activation_token.user

    if user.is_active:
        await db.delete(activation_token)
        await db.commit()

        return {
            "message": "User is already activated.",
        }

    user.is_active = True

    await db.delete(activation_token)
    await db.commit()

    return {
        "message": "Account activated successfully.",
    }


jwt_manager = JWTAuthManager(
    secret_key_access=config.JWT_ACCESS_SECRET_KEY,
    secret_key_refresh=config.JWT_REFRESH_SECRET_KEY,
)


@router.post("/login/", response_model=TokenResponseSchema)
async def login_user(login_data: UserLoginSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == login_data.email.lower())
    )
    user = result.scalar_one_or_none()

    if not user or not user.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not activated.",
        )

    token_data = {
        "sub": str(user.id),
        "email": user.email,
    }

    access_token = jwt_manager.create_access_token(token_data)
    refresh_token = jwt_manager.create_refresh_token(token_data)

    db_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    db.add(db_refresh_token)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout/", response_model=MessageResponseSchema)
async def logout_user(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    await db.execute(
        delete(RefreshToken).where(RefreshToken.user_id == current_user.id)
    )
    await db.commit()

    return {
        "message": "User logged out successfully.",
    }


@router.get("/me/", response_model=UserMeSchema)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me/", response_model=UserMeSchema)
async def update_me(
    data: UserUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_data = data.model_dump(exclude_unset=True)

    try:
        for field, value in update_data.items():
            setattr(current_user, field, value)

        await db.commit()
        await db.refresh(current_user)

    except ValueError as error:
        await db.rollback()

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    except SQLAlchemyError:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating user.",
        )

    return current_user


@router.post("/refresh/", response_model=AccessTokenSchema)
async def refresh_access_token(
    refresh_token: RefreshTokenSchema, db: AsyncSession = Depends(get_db)
):

    try:
        payload = jwt_manager.decode_refresh_token(refresh_token.refresh_token)
        user_id = int(payload["sub"])

    except (TokenExpiredError, InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(refresh_token.refresh_token),
            RefreshToken.user_id == user_id,
        )
    )
    db_refresh_token = result.scalar_one_or_none()

    if db_refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is not active.",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    access_token = jwt_manager.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/password-reset-request/", response_model=MessageResponseSchema)
async def password_reset_request(
    user_email: PasswordResetRequestSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == user_email.email.lower())
    )
    user = result.scalar_one_or_none()

    if not user:
        return {
            "message": "You will receive an email with instructions to reset your password.",
        }

    old_token_result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    )
    old_token = old_token_result.scalar_one_or_none()

    if old_token:
        await db.delete(old_token)
        await db.flush()

    password_reset_token = PasswordResetToken(user_id=user.id)
    db.add(password_reset_token)
    await db.commit()
    await db.refresh(password_reset_token)

    password_reset_link = f"{config.FRONTEND_URL}/password-reset-complete/?token={password_reset_token.token}"

    background_tasks.add_task(
        send_password_reset_email,
        user.email,
        password_reset_link,
    )

    return {
        "message": "You will receive an email with instructions to reset your password.",
    }


@router.post("/password-reset-complete/", response_model=MessageResponseSchema)
async def password_reset_complete(
    data: PasswordResetCompleteRequestSchema, db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(PasswordResetToken)
        .options(selectinload(PasswordResetToken.user))
        .where(PasswordResetToken.token == data.token)
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or token."
        )

    if db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        await db.delete(db_token)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or token.",
        )

    user = db_token.user

    if not user or not user.is_active:
        await db.delete(db_token)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or token.",
        )

    try:
        user.password = data.password
        await db.delete(db_token)
        await db.commit()

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during password resetting.",
        )

    return {"message": "You have successfully reset your password."}
