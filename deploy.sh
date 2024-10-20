#!/bin/bash

# Vérifier si Docker et Docker Compose sont installés
if ! command -v docker &> /dev/null; then
    echo "Docker n'est pas installé. Veuillez l'installer."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose n'est pas installé. Veuillez l'installer."
    exit 1
fi

# Lancer Elasticsearch
echo "Lancement d'Elasticsearch..."
docker-compose build --no-cache elasticsearch
docker-compose up -d elasticsearch

# Vérifier la santé d'Elasticsearch
echo "Attente d'Elasticsearch pour être opérationnel..."
until curl -s -u "elastic:your_password" -X GET "http://localhost:9200/_cluster/health?wait_for_status=yellow&timeout=50s" > /dev/null; do
    echo "Elasticsearch est en cours de démarrage..."
    sleep 5
done

# Créer l'API Key pour Elasticsearch
echo "Création de l'API Key pour Elasticsearch..."
API_KEY_RESPONSE=$(
    curl -X POST "localhost:9200/_security/api_key" -u "elastic:your_password" -H "Content-Type: application/json" -d '{"name": "my-api-key"}'
)

# Extraire la clé API de la réponse
API_KEY=$(echo "$API_KEY_RESPONSE" | jq -r '.encoded')

# Vérifier si la clé API a été générée avec succès
if [ -z "$API_KEY" ] || [ "$API_KEY" == "null" ]; then
    echo "Erreur lors de la génération de l'API Key. Réponse de l'API: $API_KEY_RESPONSE"
    exit 1
fi

# Remplace la ligne existante API_KEY si elle est déjà dans .env
if grep -q "DEV_ELASTICSEARCH_API_KEY=" .env; then
    sed -i "s/^DEV_ELASTICSEARCH_API_KEY=.*/DEV_ELASTICSEARCH_API_KEY=${API_KEY}/" .env
else
    echo "DEV_ELASTICSEARCH_API_KEY=${API_KEY}" >> .env
fi

# Remplace la ligne existante API_KEY si elle est déjà dans .env
if grep -q "ELASTICSEARCH_API_KEY=" .env; then
    sed -i "s/^ELASTICSEARCH_API_KEY=.*/ELASTICSEARCH_API_KEY=${API_KEY}/" .env
else
    echo "ELASTICSEARCH_API_KEY=${API_KEY}" >> .env
fi

# Fermez l'exposition du port
#docker update --publish-rm 9200 juripredis-elasticsearch-1

# Démarrer FastAPI
echo "Lancement de FastAPI..."
docker-compose build --no-cache fastapi
docker-compose up -d fastapi

echo "Déploiement terminé. Accédez à l'API à l'adresse http://localhost:8000"
