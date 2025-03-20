from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
import logging
from sentiment_model import SentimentModel

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

# Initialize the sentiment model
sentiment_model = SentimentModel()
sentiment_model.load_latest_model()

@app.route('/analyze', methods=['POST'])
def analyze_tweets():
    try:
        data = request.get_json()
        if not data or 'tweets' not in data:
            return jsonify({'error': 'No tweet provided'}), 400
        
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
        predictions = sentiment_model.predict(tweets)
        
        for tweet, prediction in zip(tweets, predictions):
            logger.info(f"Processing tweet: {tweet}")
            
            # Convert prediction to sentiment score (-1 to 1)
            sentiment_score = (prediction * 2) - 1
            
            # Determine positive/negative based on prediction
            is_positive = prediction > 0.5
            is_negative = prediction < 0.5
            
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