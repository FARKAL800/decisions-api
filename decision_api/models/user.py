from pydantic import BaseModel


class User(BaseModel):
    id: int | None = None
    email: str
    scope: str | None = "user"


class UserIn(User):
    password: str
