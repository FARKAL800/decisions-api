from contextlib import asynccontextmanager

from fastapi import FastAPI

from decision_api.config import config
from decision_api.database import (
    database,
    index_sqlite_data,
    insert_user,
    is_database_populated,
    user_table,
)
from decision_api.routers.decisions import router as decision_router
from decision_api.routers.user import router as user_router
from decision_api.security import get_password_hash
from decision_api.utils.utility import load_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connexion à la base de données
    await database.connect()

    # Vérifier si la base de données est vide ou incomplète
    if not await is_database_populated():
        await load_data("/Cases")  # Charger les données si nécessaire

    # Vérifier si les utilisateurs existent déjà pour éviter la duplication
    query = user_table.select().where(user_table.c.email == "admin@example.com")
    result = await database.fetch_one(query)

    if result is None:  # Si l'utilisateur n'existe pas, on les insère
        insert_user(
            email="admin@example.com",
            password=get_password_hash(config.ADMIN_PASSWORD),
            scope="admin",
        )
        insert_user(
            email="user@example.com",
            password=get_password_hash(config.USER_PASSWORD),
            scope="user",
        )

    # On remplit l'index à partir de la base
    await index_sqlite_data()

    # Maintenant que tout est configuré, on lance l'application
    yield

    # Déconnexion de la base de données
    await database.disconnect()


# Initialiser FastAPI
app = FastAPI(lifespan=lifespan)

app.include_router(decision_router)
app.include_router(user_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
