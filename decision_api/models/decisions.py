from pydantic import BaseModel
from typing import Optional

# Modèles Pydantic
class DecisionCreate(BaseModel):
    identifiant: str
    titre: str
    date_dec: str
    chambre: str
    contenu: str
    numero_affaire: str
    solution: str


class DecisionResponse(BaseModel):
    id: int
    identifiant: str
    titre: str
    chambre: str
    contenu: Optional[str] = None 

    class Config:
        from_attributes = True
