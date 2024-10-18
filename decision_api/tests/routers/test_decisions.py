from unittest.mock import patch

import pytest
from httpx import AsyncClient

fake_decision = {
    "identifiant": "DEC2024-001",
    "titre": "Décision de la Cour d'appel sur le recours n° 1234",
    "date_dec": "2024-10-15",
    "chambre": "Chambre civile",
    "contenu": "La cour a décidé d'annuler la décision rendue en première instance et de renvoyer l'affaire devant la cour de première instance.",
    "numero_affaire": "1234",
    "solution": "Annulation de la décision",
}

fake_decision_response = {
    "identifiant": "DEC2024-001",
    "titre": "Décision de la Cour d'appel sur le recours n° 1234",
    "chambre": "Chambre civile",
}


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
async def test_create_decision_without_previlege(
    async_client: AsyncClient, logged_in_token: str
):
    response = await async_client.post(
        "/decisions",
        json=fake_decision,
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 403


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
async def test_get_decisions(async_client: AsyncClient, created_decision: dict):
    response = await async_client.get("/decisions?skip=0&limit=10")
    assert response.status_code == 200
    assert response.json() == [created_decision]


@patch(
    "elasticsearch.Elasticsearch.search"
)  # On remplace la méthode `search` d'Elasticsearch
@pytest.mark.anyio
async def test_search(mock_search, async_client: AsyncClient):
    # Simule la réponse d'Elasticsearch
    mock_search.return_value = {
        "hits": {
            "total": 1,
            "hits": [{"_source": {"id": 1, "content": "Simulated decision content"}}],
        }
    }

    # Appel de la route avec un client de test
    response = await async_client.get("/decisions/search/?search=decision")
    assert response.status_code == 200

    # On extrait la partie intéressante de la réponse Elasticsearch
    response_hits = response.json()["hits"]

    # Simule la réponse attendue
    expected_result = [{"_source": {"id": 1, "content": "Simulated decision content"}}]

    # On compare les résultats
    assert response_hits["hits"] == expected_result
