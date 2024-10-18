import databases
import sqlalchemy
from elasticsearch import Elasticsearch

from decision_api.config import config

# Configuration de la base de données
database = databases.Database(
    config.DATABASE_URL, force_rollback=config.DB_FORCE_ROLL_BACK
)
metadata = sqlalchemy.MetaData()

# Définition de la table sans ORM
decisions_table = sqlalchemy.Table(
    "decisions",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("identifiant", sqlalchemy.String, index=True, unique=True),
    sqlalchemy.Column("titre", sqlalchemy.String),
    sqlalchemy.Column("date_dec", sqlalchemy.String),
    sqlalchemy.Column("chambre", sqlalchemy.String),
    sqlalchemy.Column("contenu", sqlalchemy.Text),  # Texte complet
    sqlalchemy.Column("numero_affaire", sqlalchemy.String),
    sqlalchemy.Column("solution", sqlalchemy.String),
)

user_table = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String, unique=True),
    sqlalchemy.Column("password", sqlalchemy.String),
    sqlalchemy.Column("scope", sqlalchemy.String),
)

# Créer la base de données et les tables si elles n'existent pas
engine = sqlalchemy.create_engine(config.DATABASE_URL)
metadata.create_all(engine)

# Fonction qui vérifie si la data base a été peuplé
async def is_database_populated() -> bool:
    """Vérifie si la table decisions_table existe et contient des données."""
    query = sqlalchemy.select(sqlalchemy.func.count(decisions_table.c.id)).select_from(decisions_table)
    count = await database.fetch_val(query)
    return count != 0

# Fonction pour insérer un utilisateur
def insert_user(email: str, password: str, scope: str):
    with engine.connect() as conn:
        query = sqlalchemy.insert(user_table).values(
            email=email, password=password, scope=scope
        )
        conn.execute(query)
        conn.commit()


es = Elasticsearch(
    config.ELASTICSEARCH_URL, api_key=config.ELASTICSEARCH_API_KEY
)  # Connexion à Elasticsearch

from tqdm import tqdm

async def index_sqlite_data():
    query = decisions_table.select()
    decisions = await database.fetch_all(query)
    es.indices.create(index="decisions", ignore=400)

    # Utilisez tqdm pour afficher la progression
    with tqdm(total=len(decisions), desc="Indexing decisions") as bar:
        for decision in decisions:
            doc = {"content": decision.contenu, "identification": decision.identifiant}
            
            try:
                # Essaye d'indexer chaque décision
                response = es.index(index="decisions", id=decision.id, body=doc)
                bar.set_postfix({"ID": response["_id"]})  # Met à jour le postfix avec l'ID du document indexé
                bar.update(1)  # Incrémente la barre de progression
            except Exception as e:
                # Capture toute exception et affiche le message d'erreur
                print(f"Erreur lors de l'indexation du document avec ID {decision.id}: {e}")
