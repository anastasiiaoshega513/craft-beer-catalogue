from pydantic import BaseModel, EmailStr, field_validator, ConfigDict

from app.validators import users as validators


class BaseEmailPasswordSchema(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        validators.validate_password_strength(value)
        return value


class UserRegistrationSchema(BaseEmailPasswordSchema):
    first_name: str | None = None
    last_name: str | None = None


class UserActivationSchema(BaseModel):
    token: str


class UserLoginSchema(BaseEmailPasswordSchema):
    pass


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserUpdateSchema(BaseEmailPasswordSchema):
    pass


class MessageResponseSchema(BaseModel):
    message: str


class UserMeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class AccessTokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
