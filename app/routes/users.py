from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import config
from db.dependencies import get_db
from app.models.users import User
from app.schemas.users import MessageResponseSchema, UserRegistrationSchema
from app.services.email import send_activation_email
from app.models.tokens import ActivationToken
from app.schemas.users import UserActivationSchema

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post("/register/", response_model=MessageResponseSchema)
async def register_user(
        user: UserRegistrationSchema,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == user.email.lower()))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
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
        activation_link = f"{config.FRONTEND_URL}/activate/?token={activation_token.token}"
        background_tasks.add_task(
            send_activation_email,
            user.email,
            activation_link,
        )

        return {
            "message": "User created. Please check your email."
        }


@router.post("/activate/", response_model=MessageResponseSchema)
async def activate_user(activation_token: UserActivationSchema, db: AsyncSession = Depends(get_db)):
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

