from pydantic import AliasPath, BaseModel, ConfigDict, EmailStr, Field, field_validator


class Register(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=8, max_length=100)
    captcha_token: str | None = Field(None, max_length=2048)

    @field_validator("display_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must be at least 2 characters")
        # Shown on pages and in the log viewer: letters, digits and a few separators, nothing that means markup.
        if not all(c.isalnum() or c in " .'_-" for c in value):
            raise ValueError("Use letters, numbers, spaces and . ' _ - only")
        return value


class Login(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=100)
    captcha_token: str | None = Field(None, max_length=2048)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    role: str = Field(validation_alias=AliasPath("role", "name"))


class AuthResponse(BaseModel):
    message: str
    user: UserOut
