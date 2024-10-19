from unittest.mock import patch

import pytest
from httpx import AsyncClient

from decision_api.main import app
from decision_api.tests.conftest import fake_decision, fake_decision_response


async def create_decision(
    body: dict, async_client: AsyncClient, logged_in_token_admin: str
) -> dict:
    response = await async_client.post(
        "/decisions",
        json=body,
        headers={"Authorization": f"Bearer {logged_in_token_admin}"},
    )
    return response.json()


@pytest.fixture()
async def created_decision(async_client: AsyncClient, logged_in_token_admin: str):
    return await create_decision(fake_decision, async_client, logged_in_token_admin)


@pytest.mark.anyio
async def test_create_decision(async_client: AsyncClient, logged_in_token_admin: str):
    response = await async_client.post(
        "/decisions",
        json=fake_decision,
        headers={"Authorization": f"Bearer {logged_in_token_admin}"},
    )

    assert response.status_code == 201
    assert fake_decision_response.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_decision_without_body(
    async_client: AsyncClient, logged_in_token_admin: str
):
    response = await async_client.post(
        "/decisions",
        json={},
        headers={"Authorization": f"Bearer {logged_in_token_admin}"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_decision_without_previlege(
    async_client: AsyncClient, logged_in_token: str
):
    app.dependency_overrides = {}
    response = await async_client.post(
        "/decisions",
        json=fake_decision,
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_get_decisions(
    async_client: AsyncClient, created_decision: dict, logged_in_token: str
):
    response = await async_client.get(
        "/decisions?skip=0&limit=10",
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 200
    assert fake_decision_response.items() <= response.json()[0].items()


@pytest.mark.anyio
async def test_get_decisions_by_chambre(
    async_client: AsyncClient, created_decision: dict, logged_in_token: str
):
    response = await async_client.get(
        "/decisions/chambre/?chambre=CHAMBRE_CIVILE",
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 200
    assert fake_decision_response.items() <= response.json()[0].items()


@pytest.mark.anyio
async def test_get_decisions_by_identifiant(
    async_client: AsyncClient, created_decision: dict, logged_in_token: str
):
    response = await async_client.get(
        "/decisions/DEC2024-001",
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 200
    assert fake_decision_response.items() <= response.json()[0].items()


@pytest.mark.anyio
async def test_get_total_number_of_decision(
    async_client: AsyncClient, created_decision: dict, logged_in_token: str
):
    response = await async_client.get(
        "decisions/count",
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"total_decisions": 1}


@patch(
    "elasticsearch.Elasticsearch.search"
)  # On remplace la méthode `search` d'Elasticsearch
@pytest.mark.anyio
async def test_search(mock_search, async_client: AsyncClient, logged_in_token: str):
    # Simule la réponse d'Elasticsearch
    mock_search.return_value = {
        "hits": {
            "total": 1,
            "hits": [{"_source": {"id": 1, "content": "Simulated decision content"}}],
        }
    }

    # Appel de la route avec un client de test
    response = await async_client.get(
        "/decisions/search/?search=decision",
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 200

    # On extrait la partie intéressante de la réponse Elasticsearch
    response_hits = response.json()

    # Simule la réponse attendue
    expected_result = [{"_source": {"id": 1, "content": "Simulated decision content"}}]

    # On compare les résultats
    assert response_hits == expected_result
