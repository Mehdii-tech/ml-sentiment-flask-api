#!/bin/bash

echo "Démarrage de l'environnement complet (MySQL + API Flask)..."

# Lancer docker-compose
docker-compose up -d

# Attendre que MySQL soit prêt
echo "Attente du démarrage des services..."
sleep 15

echo "Services prêts!"
echo "La table 'tweets' a été créée avec la structure suivante:"
echo "- id : Identifiant unique"
echo "- text : Contenu du tweet"
echo "- positive : 1 si le tweet est jugé positif, 0 sinon"
echo "- negative : 1 si le tweet est jugé négatif, 0 sinon"
echo "- created_at : Date de création de l'enregistrement"

echo ""
echo "API Flask disponible sur: http://localhost:5000"
echo "Endpoints disponibles:"
echo "- POST /analyze : Analyser des tweets"
echo "- GET /tweets : Lister tous les tweets"
echo ""
echo "Exemple d'utilisation:"
echo "curl -X POST http://localhost:5000/analyze -H \"Content-Type: application/json\" -d '{\"tweets\": [\"Premier tweet\", \"Deuxième tweet\"]}'"
echo "curl http://localhost:5000/tweets"