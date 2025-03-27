# API d'Analyse de Sentiment pour Tweets

Cette API Flask analyse le sentiment des tweets et stocke les résultats dans une base de données MySQL. L'application utilise un modèle de machine learning pour déterminer si un tweet est positif ou négatif.

## Fonctionnalités

- Analyse de sentiment de tweets via une API REST
- Stockage des résultats dans une base de données MySQL
- Visualisation des tweets analysés
- Réentraînement périodique du modèle via un planificateur de tâches

## Prérequis

- Docker et Docker Compose
- Git

## Installation et déploiement

### Démarrage rapide avec Docker Compose

```bash
# Cloner le dépôt
git clone https://github.com/Mehdii-tech/ml-sentiment-flask-api.git
cd ml-sentiment-flask-api

# Démarrer l'application
docker-compose up -d
```

L'application sera accessible à l'adresse: http://localhost:5001

## Structure de la base de données

La table `tweets` contient les champs suivants:

- `id`: Identifiant unique
- `text`: Contenu du tweet
- `positive`: 1 si le tweet est jugé positif, 0 sinon
- `negative`: 1 si le tweet est jugé négatif, 0 sinon
- `created_at`: Date de création de l'enregistrement

## Endpoints API

### Analyser des tweets

```
POST /analyze
Content-Type: application/json
```

Corps de la requête:

```json
{
  "tweets": ["Premier tweet à analyser", "Deuxième tweet à analyser"]
}
```

Réponse:

```json
{
  "Premier tweet à analyser": 0.75,
  "Deuxième tweet à analyser": -0.32
}
```

### Lister tous les tweets analysés

```
GET /tweets
```

Réponse:

```json
[
  {
    "id": 1,
    "text": "Premier tweet à analyser",
    "positive": true,
    "negative": false,
    "created_at": "2023-04-01T12:34:56"
  },
  {
    "id": 2,
    "text": "Deuxième tweet à analyser",
    "positive": false,
    "negative": true,
    "created_at": "2023-04-01T12:35:00"
  }
]
```

## Architecture du projet

- `app.py`: Application Flask principale
- `scheduler.py`: Script de réentraînement périodique du modèle
- `models/sentiment_model.py`: Classe pour la gestion du modèle de sentiment
- `docker-compose.yml`: Configuration des services Docker
- `Dockerfile`: Instructions de build pour l'image Docker
- `entrypoint.sh`: Script d'initialisation du conteneur
- `init.sql`: Script SQL pour initialiser la base de données
- `init.sh`: Script de démarrage pour faciliter le lancement
- `crontab`: Cronjob config file

## Développement

Pour démarrer l'application en mode développement:

```bash
docker-compose up
```

Pour reconstruire les conteneurs après des modifications:

```bash
docker-compose up --build
```

## Maintenance

Le modèle est automatiquement réentraînés selon le planning défini dans le fichier crontab (Tout les Samedis Miniuit). Seules les 3 versions les plus récentes des modèles sont conservées pour économiser de l'espace disque.
