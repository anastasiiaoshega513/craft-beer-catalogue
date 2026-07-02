from datetime import datetime, timedelta, timezone

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import config
from app.dependencies.users import get_current_user
from app.models.tokens import ActivationToken, PasswordResetToken, RefreshToken
from app.schemas.users import (
    AccessTokenSchema,
    MessageResponseSchema,
    PasswordResetCompleteRequestSchema,
    PasswordResetRequestSchema,
    UserActivationSchema,
    UserLoginSchema,
    UserMeSchema,
    UserRegistrationSchema,
    UserUpdateSchema,
)
from app.security.jwt_token import InvalidTokenError, JWTAuthManager, TokenExpiredError
from app.security.secure_token import hash_token
from app.services.email import send_activation_email, send_password_reset_email
from app.services.users import (
    get_user_by_email,
    internal_server_error,
    invalid_refresh_token_exception,
    invalid_reset_token_exception,
)
from db.dependencies import get_db
from models.users import User

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

jwt_manager = JWTAuthManager(
    secret_key_access=config.JWT_ACCESS_SECRET_KEY,
    secret_key_refresh=config.JWT_REFRESH_SECRET_KEY,
)

REFRESH_TOKEN_COOKIE = "refresh_token"
REFRESH_TOKEN_COOKIE_MAX_AGE = 60 * 60 * 24 * 7


@router.post(
    "/register/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register User",
    description=(
        "Create a new user account and send an activation email. "
        "If an inactive account already exists, a new activation token is sent."
    ),
)
async def register_user(
    user_data: UserRegistrationSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user or resend activation for an inactive account.

    Active accounts cannot be registered again. Inactive accounts receive a new
    activation token after the previous activation token is removed.
    """
    result = await db.execute(
        select(User).options(selectinload(User.activation_token)).where(User.email == user_data.email.lower())
    )
    existing_user = result.scalar_one_or_none()

    if existing_user and existing_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"user_account": "User with this email already exists."},
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
                email=user_data.email.lower(),
                raw_password=user_data.password,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
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
            detail=e.args[0],
        )

    except SQLAlchemyError:
        await db.rollback()
        raise internal_server_error("An error occurred during user creation.")

    activation_link = f"{config.FRONTEND_URL}/beer-catalogue/activate/?token={activation_token.token}"

    background_tasks.add_task(
        send_activation_email,
        user_data.email.lower(),
        activation_link,
    )

    return {"message": "User created. Please check your email."}


@router.post(
    "/activate/",
    response_model=MessageResponseSchema,
    summary="Activate Account",
    description="Activate a user account using an email activation token.",
)
async def activate_user(activation_token: UserActivationSchema, db: AsyncSession = Depends(get_db)):
    """
    Activate a user account using an activation token.

    Expired tokens are deleted. If the account is already active, the token is
    removed and a success message is returned.
    """
    result = await db.execute(
        select(ActivationToken)
        .options(selectinload(ActivationToken.user))
        .where(ActivationToken.token == activation_token.token)
    )

    activation_token_db = result.scalar_one_or_none()

    if activation_token_db is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"activation_token": "Invalid activation token."},
        )

    if activation_token_db.expires_at < datetime.now(timezone.utc):
        await db.delete(activation_token_db)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"activation_token": "Activation token has expired."},
        )

    user = activation_token_db.user

    if user.is_active:
        await db.delete(activation_token_db)
        await db.commit()

        return {
            "message": "User is already activated.",
        }

    user.is_active = True

    await db.delete(activation_token_db)
    await db.commit()

    return {
        "message": "Account activated successfully.",
    }


@router.post(
    "/login/",
    response_model=AccessTokenSchema,
    summary="Log In",
    description=(
        "Authenticate an active user, return an access token, " "and store a refresh token in an HTTP-only cookie."
    ),
)
async def login_user(login_data: UserLoginSchema, response: Response, db: AsyncSession = Depends(get_db)):
    """
    Authenticate an active user and issue access and refresh tokens.

    The access token is returned in the response body. The refresh token is saved
    as a hash in the database and sent to the browser as an HTTP-only cookie.
    """
    user = await get_user_by_email(db, login_data.email)

    if not user or not user.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"user_account": "Invalid email or password."},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"user_account": "User account is not activated."},
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

    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=REFRESH_TOKEN_COOKIE_MAX_AGE,
        httponly=True,
        samesite="none",
        secure=True,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post(
    "/logout/",
    response_model=MessageResponseSchema,
    summary="Log Out",
    description="Delete stored refresh tokens for the authenticated user.",
)
async def logout_user(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Log out the authenticated user.

    Deletes all stored refresh tokens for the user and removes the refresh token
    cookie from the browser.
    """
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == current_user.id))
    await db.commit()

    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        httponly=True,
        samesite="none",
        secure=True,
    )

    return {
        "message": "User logged out successfully.",
    }


@router.get(
    "/me/",
    response_model=UserMeSchema,
    summary="Get My Profile",
    description="Return the authenticated user's profile.",
)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return current_user


@router.patch(
    "/me/",
    response_model=UserMeSchema,
    summary="Update My Profile",
    description="Update editable profile fields for the authenticated user.",
)
async def update_me(
    data: UserUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the authenticated user's editable profile fields.

    Only fields provided in the request body are updated.
    """
    update_data = data.model_dump(exclude_unset=True)

    try:
        for field, value in update_data.items():
            setattr(current_user, field, value)

        await db.commit()
        await db.refresh(current_user)

    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=e.args[0])

    except SQLAlchemyError:
        await db.rollback()
        raise internal_server_error("An error occurred while updating user.")

    return current_user


@router.post(
    "/refresh/",
    response_model=AccessTokenSchema,
    summary="Refresh Access Token",
    description="Create a new access token from a valid refresh token cookie.",
)
async def refresh_access_token(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Issue a new access token from a refresh token cookie.

    The raw refresh token is decoded, hashed, and matched against the database
    before a new access token is created.
    """
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE)

    if not refresh_token:
        raise invalid_refresh_token_exception()

    try:
        payload = jwt_manager.decode_refresh_token(refresh_token)
        user_id = int(payload["sub"])

    except (TokenExpiredError, InvalidTokenError, KeyError, ValueError):
        raise invalid_refresh_token_exception()

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(refresh_token),
            RefreshToken.user_id == user_id,
        )
    )
    db_refresh_token = result.scalar_one_or_none()

    if db_refresh_token is None:
        raise invalid_refresh_token_exception()

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise invalid_refresh_token_exception()

    access_token = jwt_manager.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/password-reset-request/",
    response_model=MessageResponseSchema,
    summary="Request Password Reset",
    description="Send password reset instructions if the email belongs to a user account.",
)
async def password_reset_request(
    user_email: PasswordResetRequestSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a password reset token and send reset instructions if the user exists.

    The endpoint returns the same message for registered and unregistered emails, so
    the API does not reveal which emails belong to user accounts.
    """
    user = await get_user_by_email(db, user_email.email)

    if not user:
        return {
            "message": "You will receive an email with instructions to reset your password.",
        }

    old_token_result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
    old_token = old_token_result.scalar_one_or_none()

    if old_token:
        await db.delete(old_token)
        await db.flush()

    password_reset_token = PasswordResetToken(user_id=user.id)
    db.add(password_reset_token)
    await db.commit()
    await db.refresh(password_reset_token)

    password_reset_link = (
        f"{config.FRONTEND_URL}/beer-catalogue/password-reset-complete/?token={password_reset_token.token}"
    )

    background_tasks.add_task(
        send_password_reset_email,
        user.email,
        password_reset_link,
    )

    return {
        "message": "You will receive an email with instructions to reset your password.",
    }


@router.post(
    "/password-reset-complete/",
    response_model=MessageResponseSchema,
    summary="Complete Password Reset",
    description="Reset a user's password using a valid password reset token.",
)
async def password_reset_complete(data: PasswordResetCompleteRequestSchema, db: AsyncSession = Depends(get_db)):
    """
    Reset a user's password using a valid password reset token.

    The related user is loaded together with the token because the password is
    updated after token validation. Invalid, expired, or unusable tokens are deleted.
    """
    result = await db.execute(
        select(PasswordResetToken)
        .options(selectinload(PasswordResetToken.user))
        .where(PasswordResetToken.token == data.token)
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise invalid_reset_token_exception()

    if db_token.expires_at < datetime.now(timezone.utc):
        await db.delete(db_token)
        await db.commit()

        raise invalid_reset_token_exception()

    user = db_token.user

    if not user or not user.is_active:
        await db.delete(db_token)
        await db.commit()

        raise invalid_reset_token_exception()

    if user.verify_password(data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"password": "New password must be different from the current password."},
        )

    try:
        user.password = data.password
        await db.delete(db_token)
        await db.commit()

    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=e.args[0],
        )

    except SQLAlchemyError:
        await db.rollback()
        raise internal_server_error("An error occurred during password resetting.")

    return {"message": "You have successfully reset your password."}
