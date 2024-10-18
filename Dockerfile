# Utilise une image de base Python
FROM python:3.12-slim

# Définir le répertoire de travail à la racine
WORKDIR /

# Copier le fichier .env à la racine
COPY .env .

# Copier les fichiers de votre application FastAPI et le script.py
COPY ./decision_api /decision_api
COPY case_scraper.py .

# Copier les dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le script de démarrage
COPY start_fastapi_container.sh /start_fastapi_container.sh
RUN chmod +x /start_fastapi_container.sh

# Expose le port 8000 pour FastAPI
EXPOSE 8000

# Utiliser le script de démarrage pour lancer le processus
CMD ["/start_fastapi_container.sh"]