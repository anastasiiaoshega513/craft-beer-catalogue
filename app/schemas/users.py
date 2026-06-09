from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.validators import users as validators


class MessageResponseSchema(BaseModel):
    message: str


class EmailSchema(BaseModel):
    email: EmailStr


class PasswordSchema(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value:
            raise ValueError("Password is required.")

        return value


class UserLoginSchema(EmailSchema):
    password: str


class UserRegistrationSchema(EmailSchema, PasswordSchema):
    first_name: str | None = None
    last_name: str | None = None


class UserActivationSchema(BaseModel):
    token: str


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class AccessTokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserMeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr


class UserUpdateSchema(BaseModel):
    first_name: str | None = None
    last_name: str | None = None


class PasswordResetRequestSchema(EmailSchema):
    pass


class PasswordResetCompleteRequestSchema(PasswordSchema):
    token: str
