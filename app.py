from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
import random
import logging
from sentiment_model import SentimentAnalyzer

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

def simple_sentiment_score():
    """Returns either -1 or 1 randomly for testing purposes"""
    return random.choice([-1, 1])

# Initialize sentiment analyzer
sentiment_analyzer = SentimentAnalyzer()

@app.route('/analyze', methods=['POST'])
def analyze_tweets():
    try:
        data = request.get_json()
        if not data or 'tweets' not in data:
            return jsonify({'error': 'No tweets provided'}), 400
        
        tweets = data['tweets']
        results = {}
        
        for tweet in tweets:
            logger.info(f"Processing tweet: {tweet}")
            # Use model to predict sentiment
            sentiment_score = sentiment_analyzer.predict_sentiment(tweet)
            results[tweet] = sentiment_score
            
            # Store in database
            new_tweet = Tweet(
                text=tweet,
                positive=sentiment_score > 0,
                negative=sentiment_score < 0
            )
            db.session.add(new_tweet)
            logger.info(f"Added tweet to session with sentiment score: {sentiment_score}")
        
        logger.info("Committing to database...")
        db.session.commit()
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

# Create models directory if it doesn't exist
if not os.path.exists('models'):
    os.makedirs('models')

# Create tables on startup
with app.app_context():
    logger.info("Creating database tables...")
    db.create_all()
    logger.info("Database tables created successfully")
    # Load existing model or train new one if necessary
    if not sentiment_analyzer.load_model():
        logger.info("Training new model...")
        sentiment_analyzer.train_model(db.session, Tweet)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 