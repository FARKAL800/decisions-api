import json
import os
from enum import Enum

from tqdm import tqdm

from decision_api.database import database, decisions_table


class ChambreEnum(str, Enum):
    CIVILE = "CHAMBRE_CIVILE"
    COMMERCIALE = "CHAMBRE_COMMERCIALE"
    SOCIALE = "CHAMBRE_SOCIALE"
    CRIMINELLE = "CHAMBRE_CRIMINELLE"
    JURI = "ASSEMBLEE_PLENIERE"


# Charger les données à partir des fichiers JSON dans un répertoire (recherche récursive)
async def load_data(directory):
    json_files = []
    absolute_directory = os.path.abspath(directory)
    # Utiliser os.walk pour parcourir tous les sous-répertoires
    for root, _, files in os.walk(absolute_directory):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))

    # Utiliser tqdm pour la barre de progression
    for filename in tqdm(json_files, desc="Loading data", unit="file"):
        with open(
            filename, "r", encoding="utf-8"
        ) as f:  # Ajoutez l'encodage pour éviter les problèmes de lecture
            data = json.load(f)

            # Conversion de la liste des numéros d'affaire en chaîne de caractères
            numeros_affaires = data["TEXTE_JURI_JUDI"]["META"]["META_SPEC"][
                "META_JURI_JUDI"
            ]["NUMEROS_AFFAIRES"].get("NUMERO_AFFAIRE", [])

            if isinstance(numeros_affaires, list):
                numero_affaire = ", ".join(numeros_affaires)
            elif isinstance(numeros_affaires, str):
                numero_affaire = numeros_affaires
            else:
                numero_affaire = ""

            query = decisions_table.insert().values(
                identifiant=data["TEXTE_JURI_JUDI"]["META"]["META_COMMUN"]["ID"],
                titre=data["TEXTE_JURI_JUDI"]["META"]["META_SPEC"]["META_JURI"][
                    "TITRE"
                ],
                date_dec=data["TEXTE_JURI_JUDI"]["META"]["META_SPEC"]["META_JURI"][
                    "DATE_DEC"
                ],
                chambre=data["TEXTE_JURI_JUDI"]["META"]["META_SPEC"]["META_JURI_JUDI"][
                    "FORMATION"
                ],
                contenu=data["TEXTE_JURI_JUDI"]["TEXTE"]["BLOC_TEXTUEL"]["CONTENU"][
                    "#text"
                ],
                numero_affaire=numero_affaire,
                solution=data["TEXTE_JURI_JUDI"]["META"]["META_SPEC"]["META_JURI"][
                    "SOLUTION"
                ],
            ).prefix_with("OR IGNORE")

            await database.execute(query)
