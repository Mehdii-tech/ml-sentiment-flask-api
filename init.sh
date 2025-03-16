#!/bin/bash

echo "Démarrage de l'environnement MySQL pour le stockage des tweets..."

# Lancer docker-compose
docker-compose up -d

# Attendre que MySQL soit prêt
echo "Attente du démarrage de MySQL..."
sleep 10

echo "Base de données prête!"
echo "La table 'tweets' a été créée avec la structure suivante:"
echo "- id : Identifiant unique"
echo "- text : Contenu du tweet"
echo "- positive : 1 si le tweet est jugé positif, 0 sinon"
echo "- negative : 1 si le tweet est jugé négatif, 0 sinon"
echo "- created_at : Date de création de l'enregistrement"

echo ""
echo "Connexion à la base de données: mysql -u user -ppassword -h 127.0.0.1 tweet_sentiment"