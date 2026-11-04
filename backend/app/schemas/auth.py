from pydantic import AliasPath, BaseModel, ConfigDict, EmailStr, Field, field_validator


class Register(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=8, max_length=100)

    @field_validator("display_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must be at least 2 characters")
        return value


class Login(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=100)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    role: str = Field(validation_alias=AliasPath("role", "name"))


class AuthResponse(BaseModel):
    message: str
    user: UserOut
