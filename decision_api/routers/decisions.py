from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from decision_api.database import database, decisions_table, es
from decision_api.models.decisions import DecisionCreate, DecisionResponse
from decision_api.models.user import User
from decision_api.security import admin_required, user_required
from decision_api.utils.utility import ChambreEnum

router = APIRouter()


# Créer une nouvelle décision (POST)
@router.post("/decisions", response_model=DecisionResponse, status_code=201)
async def create_decision(
    decision: DecisionCreate, current_user: User = Depends(admin_required)
):
    query = decisions_table.insert().values(**decision.model_dump())
    last_record_id = await database.execute(query)
    return {**decision.model_dump(), "id": last_record_id}


# Obtenir le nombre total de décisions
@router.get("/decisions/count")
async def get_decision_count(current_user: User = Depends(user_required)):
    query = select(func.count(decisions_table.c.id)).select_from(decisions_table)
    count = await database.fetch_val(query)
    return {"total_decisions": count}


# Obtenir des décisions (GET)
@router.get("/decisions", response_model=List[DecisionResponse])
async def get_decisions(
    skip: int = 0, limit: int = 10, current_user: User = Depends(user_required)
):
    query = (
        select(
            decisions_table.c.id,
            decisions_table.c.identifiant,
            decisions_table.c.titre,
            decisions_table.c.chambre,
        )
        .offset(skip)
        .limit(limit)
    )
    decisions = await database.fetch_all(query)
    return decisions


# Rechercher des décisions par chambre
@router.get("/decisions/chambre/", response_model=List[DecisionResponse])
async def get_decisions_by_chambre(
    chambre: Optional[ChambreEnum] = Query(None),
    autre_chambre: Optional[str] = Query(None),
    current_user: User = Depends(user_required),
):
    query = select(
        decisions_table.c.id,
        decisions_table.c.identifiant,
        decisions_table.c.titre,
        decisions_table.c.chambre,
    )

    if chambre is not None:
        query = query.where(decisions_table.c.chambre.like(f"{chambre.value}%"))

    if autre_chambre is not None:
        query = query.where(decisions_table.c.chambre == autre_chambre)

    decisions = await database.fetch_all(query)

    if not decisions:
        raise HTTPException(status_code=404, detail="Aucune décision trouvée")

    return decisions


# Rechercher une décision par identifiant
@router.get("/decisions/{identifiant}", response_model=List[DecisionResponse])
async def get_decision(identifiant: str, current_user: User = Depends(user_required)):
    query = select(
        decisions_table.c.id,
        decisions_table.c.identifiant,
        decisions_table.c.titre,
        decisions_table.c.chambre,
        decisions_table.c.contenu,
    ).where(decisions_table.c.identifiant == identifiant)
    decision = await database.fetch_all(query)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


# Recherche textuel avec elasticsearch
@router.get("/decisions/search/")
async def search_decisions(search: str, current_user: User = Depends(user_required)):
    search_body = {
        "query": {
            "match": {
                "content": search  # Requête de recherche
            }
        }
    }
    results = es.search(index="decisions", body=search_body)  # Exécute la recherche
    return results["hits"]["hits"]
