from pydantic import BaseModel, EmailStr, validator, constr

from soc_network.config import get_settings


class RegistrationForm(BaseModel):
    username: constr(to_lower=True)
    password: str
    email: EmailStr | None

    @validator("password")
    def hash_password(cls, password):
        settings = get_settings()
        password = settings.PWD_CONTEXT.hash(password)
        return password


class RegistrationSuccess(BaseModel):
    message: str
