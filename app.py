from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
import logging
import time
import pymysql
from models.sentiment_model import SentimentModel
from sklearn.metrics import classification_report

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create models directory if it doesn't exist
os.makedirs('models', exist_ok=True)
logger.info("Ensuring models directory exists")

app = Flask(__name__)

# Disable Flask's reloader in debug mode
app.config['USE_RELOADER'] = False

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

def check_db_connection():
    """Check if database is ready using direct PyMySQL connection"""
    try:
        conn = pymysql.connect(
            host="db",
            user="user",
            password="password",
            database="tweet_sentiment"
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tweets")
            count = cursor.fetchone()[0]
            conn.close()
            return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return False

def test_model_with_seed_data():
    """Test the model with seed data and log performance metrics"""
    try:
        logger.info("Testing model with seed data...")
        # Get all tweets from database
        tweets = Tweet.query.all()
        
        if not tweets:
            logger.warning("No seed data found in database for testing")
            return
        
        texts = [tweet.text for tweet in tweets]
        labels = [1 if tweet.positive else 0 for tweet in tweets]
        
        # Get predictions
        sentiment_scores = sentiment_model.predict(texts)
        
        # Convert scores to binary labels for performance metrics
        predictions_binary = [1 if score > 0 else 0 for score in sentiment_scores]
        
        # Log performance metrics
        logger.info("\nModel Performance on Seed Data:")
        logger.info(classification_report(labels, predictions_binary))
        
        # Log some example predictions
        logger.info("\nExample Predictions:")
        for text, true_label, pred, score in zip(texts[:3], labels[:3], predictions_binary[:3], sentiment_scores[:3]):
            sentiment_str = f"Positif ({score:.2f})" if score > 0 else f"Négatif ({score:.2f})"
            logger.info(f"\nText: {text}")
            logger.info(f"True Label: {'Positive' if true_label == 1 else 'Negative'}")
            logger.info(f"Predicted: {sentiment_str}")
            
    except Exception as e:
        logger.error(f"Error testing model: {str(e)}")

def initialize_model():
    """Initialize and train the model if needed"""
    try:
        # First try to load the latest model
        logger.info("Attempting to load latest model...")
        if sentiment_model.load_latest_model():
            logger.info("Successfully loaded existing model")
            return True
            
        # If no model exists, train a new one with seed data (first launch only)
        logger.info("No existing model found. Training new model with seed data...")
        if sentiment_model.train_model():
            logger.info("Model trained successfully with seed data")
            test_model_with_seed_data()  # Only test after initial training
            return True
        else:
            logger.error("Failed to train model with seed data")
            return False
        
    except Exception as e:
        logger.error(f"Error during model initialization: {str(e)}")
        return False

# Initialize the sentiment model
sentiment_model = SentimentModel()

# Create tables and initialize model on startup
with app.app_context():
    logger.info("Starting application initialization...")
    
    # Check database connection
    if not check_db_connection():
        logger.error("Failed to connect to database. Exiting...")
        exit(1)
    
    logger.info("Database connection successful!")
    logger.info("Creating database tables...")
    db.create_all()
    logger.info("Database tables created successfully")
    
    # Initialize and test model
    if not initialize_model():
        logger.error("Failed to initialize model. Exiting...")
        exit(1)
    
    logger.info("Application initialization completed successfully")

@app.route('/analyze', methods=['POST'])
def analyze_tweets():
    try:
        data = request.get_json()
        if not data or 'tweets' not in data:
            return jsonify({'error': 'No tweet provided'}), 400
        
        # Ensure we have a model loaded
        if not sentiment_model.is_model_loaded():
            logger.info("Loading latest model for prediction...")
            if not sentiment_model.load_latest_model():
                return jsonify({'error': 'No trained model available'}), 500
        
        tweets = data['tweets']
        
        # Check if tweets is a list
        if not isinstance(tweets, list):
            return jsonify({'error': 'Incorrect format. A list is expected'}), 400
            
        # Check if tweets list is empty
        if len(tweets) == 0:
            return jsonify({'error': 'Tweet list is empty'}), 400
            
        # Check if each tweet is a string
        for tweet in tweets:
            if not isinstance(tweet, str):
                return jsonify({'error': 'Incorrect Format. Each tweet need to be a string '}), 400
            if len(tweet.strip()) == 0:
                return jsonify({'error': 'The tweets can\'t be empty'}), 400
        
        results = {}
        
        # Get predictions from the model
        logger.info(f"Making predictions for {len(tweets)} tweets...")
        sentiment_scores = sentiment_model.predict(tweets)
        
        # Process predictions and store in database
        for tweet, score in zip(tweets, sentiment_scores):
            # Le score est déjà entre -1 et 1
            sentiment_score = float(score)
            
            # Store score in results (arrondi à 2 décimales)
            results[tweet] = round(sentiment_score, 2)
            
            # Store in database (on définit positif/négatif basé sur le score)
            new_tweet = Tweet(
                text=tweet,
                positive=sentiment_score > 0,
                negative=sentiment_score < 0
            )
            db.session.add(new_tweet)
        
        # Commit to database
        db.session.commit()
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False) 