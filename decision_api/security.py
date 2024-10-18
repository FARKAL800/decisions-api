import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from decision_api.config import config
from decision_api.database import database, user_table
from decision_api.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token", scopes={"admin": "Admin access", "user": "User access"}
)
pwd_context = CryptContext(schemes=["bcrypt"])

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def access_token_expire_minutes() -> int:
    return 30


def create_access_token(email: str, scope: str):
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "scope": scope}
    encoded_jwt = jwt.encode(
        jwt_data, key=config.SECRET_KEY, algorithm=config.ALGORITHM
    )
    return encoded_jwt


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def get_user(email: str):
    query = user_table.select().where(user_table.c.email == email)
    result = await database.fetch_one(query)
    if result:
        return result


async def authenticate_user(email: str, password: str):
    user = await get_user(email)
    if not user:
        raise credentials_exception
    if not verify_password(password, user.password):
        raise credentials_exception
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(
            token, key=config.SECRET_KEY, algorithms=[config.ALGORITHM]
        )
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except JWTError as e:
        raise credentials_exception from e
    user = await get_user(email=email)
    if user is None:
        raise credentials_exception
    return user


# Dépendance pour vérifier le rôle "admin"
async def admin_required(current_user: User = Depends(get_current_user)):
    if "admin" not in current_user.scope:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions, admin access required",
        )
    return current_user


# Dépendance pour vérifier le rôle "user"
async def user_required(current_user: User = Depends(get_current_user)):
    if "user" not in current_user.scopes and "admin" not in current_user.scope:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions, user access required",
        )
    return current_user
