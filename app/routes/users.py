from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app import config
from db.dependencies import get_db
from app.models.users import User
from app.schemas.users import MessageResponseSchema, UserRegistrationSchema
from app.models.tokens import ActivationToken
from app.services.email import send_activation_email

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
        new_user = User.create(email=user.email, raw_password=user.password)
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
