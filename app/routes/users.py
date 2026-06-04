from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import config
from db.dependencies import get_db
from app.models.users import User
from app.services.email import send_activation_email
from app.models.tokens import ActivationToken, RefreshToken
from app.schemas.users import (
    UserActivationSchema,
    UserLoginSchema,
    MessageResponseSchema,
    UserRegistrationSchema,
    TokenResponseSchema,
    UserMeSchema,
    AccessTokenSchema,
    RefreshTokenSchema,
)
from app.security.jwt_token import JWTAuthManager, TokenExpiredError, InvalidTokenError
from app.dependencies.users import get_current_user
from app.security.secure_token import hash_token

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
    result = await db.execute(select(User).where(User.email == user.email.lower()))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists.",
        )

    try:
        new_user = User.create(
            email=user.email,
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

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during user creation.",
        )

    else:
        activation_link = (
            f"{config.FRONTEND_URL}/activate/?token={activation_token.token}"
        )
        background_tasks.add_task(
            send_activation_email,
            user.email,
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
    return {
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
    }


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
