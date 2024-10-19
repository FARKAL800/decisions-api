#!/bin/bash

# Attendre qu'Elasticsearch soit prêt
until curl -u "elastic:${ELASTIC_PASSWORD}" -s http://localhost:9200/_cluster/health | grep -q '"status":"green"'; do
  echo "Waiting for Elasticsearch to be ready..."
  sleep 5
done

# Générer une API Key pour Elasticsearch
API_KEY_RESPONSE=$(curl -X POST "http://localhost:9200/_security/api_key" \
-u "elastic:${ELASTIC_PASSWORD}" \
-H "Content-Type: application/json" \
-d '{"name": "render-api-key"}')

# Extraire l'ID et la clé API de la réponse
API_KEY_ID=$(echo $API_KEY_RESPONSE | jq -r '.id')
API_KEY=$(echo $API_KEY_RESPONSE | jq -r '.api_key')

# Afficher l'API Key (ou la stocker dans un fichier/variable d'environnement)
echo "API Key ID: $API_KEY_ID"
echo "API Key: $API_KEY"

# Optionnel : Écrire l'API Key dans un fichier ou envoyer à un autre service
echo $API_KEY > /usr/share/elasticsearch/api_key.txt
