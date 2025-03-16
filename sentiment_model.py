import pandas as pd
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import logging
from datetime import datetime

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.vectorizer = None
        self.model = None
        self.french_stopwords = [
            "le", "la", "les", "un", "une", "des", "du", "de", "dans", "et", "en", "au",
            "aux", "avec", "ce", "ces", "pour", "par", "sur", "pas", "plus", "où", "mais",
            "ou", "donc", "ni", "car", "ne", "que", "qui", "quoi", "quand", "à", "son",
            "sa", "ses", "ils", "elles", "nous", "vous", "est", "sont", "cette", "cet",
            "aussi", "être", "avoir", "faire", "comme", "tout", "bien", "mal", "on", "lui"
        ]

    def clean_text(self, text):
        """Cleans the input text"""
        text = str(text).lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def load_data_from_db(self, db_session, Tweet):
        """Loads data from the database"""
        tweets = db_session.query(Tweet).all()
        texts = [tweet.text for tweet in tweets]
        labels = [1 if tweet.positive else 0 for tweet in tweets]
        return pd.DataFrame({'text': texts, 'label': labels})

    def train_model(self, db_session, Tweet):
        """Trains the model with database data"""
        logger.info("Starting model training...")
        
        # Loading data
        df = self.load_data_from_db(db_session, Tweet)
        if len(df) == 0:
            logger.warning("No data available for training")
            return False

        # Cleaning texts
        df['text_clean'] = df['text'].apply(self.clean_text)

        # Vectorization
        self.vectorizer = CountVectorizer(stop_words=self.french_stopwords, max_features=100)
        X = self.vectorizer.fit_transform(df['text_clean'])
        y = df['label']

        # Data splitting
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

        # Training
        self.model = LogisticRegression()
        self.model.fit(X_train, y_train)

        # Evaluation
        y_pred = self.model.predict(X_test)
        logger.info("\nClassification Report:\n" + classification_report(y_test, y_pred))
        logger.info("\nConfusion Matrix:\n" + str(confusion_matrix(y_test, y_pred)))

        # Save model
        self.save_model()
        
        return True

    def predict_sentiment(self, text):
        """Predicts sentiment of a text"""
        if self.model is None or self.vectorizer is None:
            self.load_model()
            if self.model is None:
                return 0

        cleaned_text = self.clean_text(text)
        vectorized_text = self.vectorizer.transform([cleaned_text])
        prediction = self.model.predict_proba(vectorized_text)[0]
        
        # Converts prediction to score between -1 and 1
        sentiment_score = (prediction[1] - 0.5) * 2
        return sentiment_score

    def save_model(self):
        """Saves the model and vectorizer"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        joblib.dump(self.model, f'models/sentiment_model_{timestamp}.joblib')
        joblib.dump(self.vectorizer, f'models/vectorizer_{timestamp}.joblib')
        logger.info("Model saved successfully")

    def load_model(self):
        """Loads the latest saved model"""
        try:
            import glob
            model_files = glob.glob('models/sentiment_model_*.joblib')
            vectorizer_files = glob.glob('models/vectorizer_*.joblib')
            
            if not model_files or not vectorizer_files:
                logger.warning("No model found")
                return False

            latest_model = max(model_files)
            latest_vectorizer = max(vectorizer_files)
            
            self.model = joblib.load(latest_model)
            self.vectorizer = joblib.load(latest_vectorizer)
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False 