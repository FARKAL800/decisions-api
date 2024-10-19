import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

os.environ["ENV_STATE"] = "test"  # noqa

from decision_api.database import database, user_table
from decision_api.main import app
from decision_api.security import admin_required, create_access_token

fake_decision = {
    "identifiant": "DEC2024-001",
    "titre": "Décision de la Cour d'appel sur le recours n° 1234",
    "date_dec": "2024-10-15",
    "chambre": "CHAMBRE_CIVILE_1",
    "contenu": "La cour a décidé d'annuler la décision rendue en première instance et de renvoyer l'affaire devant la cour de première instance.",
    "numero_affaire": "1234",
    "solution": "Annulation de la décision",
}

fake_decision_response = {
    "id": 1,
    "identifiant": "DEC2024-001",
    "titre": "Décision de la Cour d'appel sur le recours n° 1234",
    "chambre": "CHAMBRE_CIVILE_1",
}


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


async def fake_user_required():
    # Simule un utilisateur admin sans vérifier les rôles
    return {}


@pytest.fixture()
async def override_admin_required():
    app.dependency_overrides[admin_required] = fake_user_required
    yield
    app.dependency_overrides = {}


@pytest.fixture()
async def registered_user_admin(
    async_client: AsyncClient, override_admin_required
) -> dict:
    user_details = {
        "email": "test_admin@example.com",
        "password": "1234",
        "scope": "admin",
    }

    await async_client.post("/register", json=user_details)

    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)
    user_details["id"] = user.id
    return user_details


@pytest.fixture()
async def registered_user(async_client: AsyncClient, override_admin_required) -> dict:
    user_details = {
        "email": "test_user@example.com",
        "password": "1234",
        "scope": "user",
    }

    await async_client.post("/register", json=user_details)

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
