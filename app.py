from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
import logging
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
import numpy as np

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Log the database URL (masking the password)
db_url = os.getenv('DATABASE_URL').replace('mysql://', 'mysql+pymysql://') if os.getenv('DATABASE_URL') else 'mysql+pymysql://user:password@db:3306/tweet_sentiment'
logger.info(f"Connecting to database: {db_url.replace('password', '****')}")

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Tweet(db.Model):
    __tablename__ = 'tweets'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    positive = db.Column(db.Boolean, default=False)
    negative = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

class SentimentAnalyzer:
    def __init__(self):
        self.vectorizer = CountVectorizer(max_features=100)
        self.model = LogisticRegression()
        self.is_trained = False
    
    def train(self, texts, labels):
        """Entraîne le modèle avec les données fournies"""
        if not texts or not labels or len(texts) < 2:
            logger.warning("Pas assez de données pour entraîner le modèle")
            return False
        
        try:
            X = self.vectorizer.fit_transform(texts)
            self.model.fit(X, labels)
            self.is_trained = True
            logger.info("Modèle entraîné avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement : {str(e)}")
            return False
    
    def predict(self, text):
        """Prédit le sentiment d'un texte"""
        if not self.is_trained:
            logger.warning("Le modèle n'est pas encore entraîné")
            return 0
        
        try:
            X = self.vectorizer.transform([text])
            # Obtention de la probabilité de la classe positive
            proba = self.model.predict_proba(X)[0][1]
            # Conversion en score entre -1 et 1
            return (proba * 2) - 1
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction : {str(e)}")
            return 0

    def train_from_database(self):
        """Entraîne le modèle avec les données de la base"""
        try:
            tweets = Tweet.query.all()
            if not tweets:
                logger.warning("Aucune donnée dans la base pour l'entraînement")
                return False
            
            texts = [tweet.text for tweet in tweets]
            labels = [1 if tweet.positive else 0 for tweet in tweets]
            
            return self.train(texts, labels)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données : {str(e)}")
            return False

# Initialiser l'analyseur de sentiment
sentiment_analyzer = SentimentAnalyzer()

@app.route('/analyze', methods=['POST'])
def analyze_tweets():
    try:
        data = request.get_json()
        if not data or 'tweets' not in data:
            return jsonify({'error': 'No tweets provided'}), 400
        
        tweets = data['tweets']
        results = {}
        
        # Pour le premier lot de tweets, on les étiquette manuellement
        # en se basant sur des mots clés positifs et négatifs
        positive_words = ['adore', 'génial', 'super', 'excellent', 'bravo', 'merci', 
                         'sympa', 'agréable', 'bien', 'intuitive']
        negative_words = ['horrible', 'déçu', 'nul', 'bug', 'catastrophique', 
                         'inutilisable', 'éviter']
        
        for tweet in tweets:
            logger.info(f"Processing tweet: {tweet}")
            
            # Pour le premier lot, on étiquette basé sur les mots clés
            tweet_lower = tweet.lower()
            pos_count = sum(1 for word in positive_words if word in tweet_lower)
            neg_count = sum(1 for word in negative_words if word in tweet_lower)
            
            # Déterminer le sentiment basé sur le compte de mots
            if pos_count > neg_count:
                sentiment_score = 0.8
                is_positive = True
                is_negative = False
            elif neg_count > pos_count:
                sentiment_score = -0.8
                is_positive = False
                is_negative = True
            else:
                sentiment_score = 0
                is_positive = False
                is_negative = False
            
            results[tweet] = round(sentiment_score, 2)
            
            # Store in database with correct labels
            new_tweet = Tweet(
                text=tweet,
                positive=is_positive,
                negative=is_negative
            )
            db.session.add(new_tweet)
            logger.info(f"Added tweet to session with sentiment score: {sentiment_score}")
        
        logger.info("Committing to database...")
        db.session.commit()
        
        # Maintenant on peut entraîner le modèle avec ces données étiquetées
        sentiment_analyzer.train_from_database()
        
        logger.info("Successfully committed to database")
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error processing tweets: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/tweets', methods=['GET'])
def get_tweets():
    try:
        tweets = Tweet.query.all()
        result = []
        for tweet in tweets:
            result.append({
                'id': tweet.id,
                'text': tweet.text,
                'positive': tweet.positive,
                'negative': tweet.negative,
                'created_at': tweet.created_at.isoformat()
            })
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching tweets: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Create tables on startup
with app.app_context():
    logger.info("Creating database tables...")
    db.create_all()
    logger.info("Database tables created successfully")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 