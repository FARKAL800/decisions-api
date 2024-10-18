from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from decision_api.database import database, user_table
from decision_api.models.user import UserIn
from decision_api.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user,
)

router = APIRouter()


@router.post("/register", status_code=201)
async def register(user: UserIn):
    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists",
        )
    hashed_password = get_password_hash(user.password)
    query = user_table.insert().values(
        email=user.email, password=hashed_password, scope=user.scope
    )

    await database.execute(query)
    return {"detail": "User created."}


@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(form_data.username, form_data.password)
    access_token = create_access_token(user.email, user.scope)
    return {"access_token": access_token, "token_type": "bearer"}
