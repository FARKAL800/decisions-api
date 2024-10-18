import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

os.environ["ENV_STATE"] = "test"  # noqa

from decision_api.database import database, user_table
from decision_api.main import app
from decision_api.security import create_access_token


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    await database.connect()
    yield
    await database.disconnect()


@pytest.fixture()
async def async_client(client) -> AsyncGenerator:
    async with AsyncClient(app=app, base_url=client.base_url) as ac:
        yield ac


@pytest.fixture()
async def registered_user_admin(async_client: AsyncClient) -> dict:
    user_details = {
        "email": "test_admin@example.com",
        "password": "1234",
        "scope": "admin",
    }
    await async_client.post("register", json=user_details)
    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)
    user_details["id"] = user.id
    return user_details


@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    user_details = {
        "email": "test_user@example.com",
        "password": "1234",
        "scope": "user",
    }
    await async_client.post("register", json=user_details)
    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)
    user_details["id"] = user.id
    return user_details


@pytest.fixture()
async def logged_in_token(registered_user: dict) -> str:
    return create_access_token(registered_user["email"], registered_user["scope"])


@pytest.fixture()
async def logged_in_token_admin(registered_user_admin: dict) -> str:
    return create_access_token(
        registered_user_admin["email"], registered_user_admin["scope"]
    )
