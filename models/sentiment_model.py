import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
import re
import logging
from datetime import datetime
from sqlalchemy import create_engine
import joblib
import os
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentModel:
    def __init__(self):
        self.vectorizer = CountVectorizer(max_features=100)
        self.model = LogisticRegression()
        self._is_loaded = False
        self.french_stopwords = [
            "le", "la", "les", "un", "une", "des", "du", "de", "dans", "et", "en", "au",
            "aux", "avec", "ce", "ces", "pour", "par", "sur", "pas", "plus", "où", "mais",
            "ou", "donc", "ni", "car", "ne", "que", "qui", "quoi", "quand", "à", "son",
            "sa", "ses", "ils", "elles", "nous", "vous", "est", "sont", "cette", "cet",
            "aussi", "être", "avoir", "faire", "comme", "tout", "bien", "mal", "on", "lui"
        ]
        
    def clean_text(self, text):
        """Nettoie le texte en entrée"""
        text = str(text).lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def load_data_from_db(self):
        """Charge les données depuis la base de données"""
        load_dotenv()
        db_url = os.getenv('DATABASE_URL').replace('mysql://', 'mysql+pymysql://')
        engine = create_engine(db_url)
        
        query = "SELECT text, positive FROM tweets"
        df = pd.read_sql(query, engine)
        return df

    def train_model(self):
        """Entraîne le modèle sur les données de la base"""
        try:
            # Chargement des données
            logger.info("Chargement des données depuis la base...")
            df = self.load_data_from_db()
            
            if df.empty:
                logger.error("Aucune donnée trouvée dans la base")
                return False
            
            # Nettoyage des textes
            logger.info("Nettoyage des textes...")
            df['text_clean'] = df['text'].apply(self.clean_text)
            
            # Vectorisation
            logger.info("Vectorisation des textes...")
            X = self.vectorizer.fit_transform(df['text_clean'])
            y = df['positive']
            
            # Division des données
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.25, random_state=42
            )
            
            # Entraînement
            logger.info("Entraînement du modèle...")
            self.model.fit(X_train, y_train)
            
            # Évaluation
            y_pred = self.model.predict(X_test)
            logger.info("\nRapport de classification :")
            logger.info(classification_report(y_test, y_pred))
            logger.info("\nMatrice de confusion :")
            logger.info(confusion_matrix(y_test, y_pred))
            
            # Sauvegarde du modèle
            self.save_model()
            self._is_loaded = True
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement : {str(e)}")
            return False

    def predict(self, texts):
        """Prédit le sentiment pour une liste de textes"""
        try:
            if not self._is_loaded:
                logger.warning("Model not loaded. Attempting to load latest model...")
                if not self.load_latest_model():
                    raise Exception("No model available for prediction")
                
            cleaned_texts = [self.clean_text(text) for text in texts]
            vectors = self.vectorizer.transform(cleaned_texts)
            predictions = self.model.predict_proba(vectors)
            # Retourne la probabilité de la classe positive (score entre 0 et 1)
            return predictions[:, 1]
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction : {str(e)}")
            return None

    def save_model(self):
        """Sauvegarde le modèle et le vectorizer"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = f'models/sentiment_model_{timestamp}.joblib'
        vectorizer_path = f'models/vectorizer_{timestamp}.joblib'
        
        os.makedirs('models', exist_ok=True)
        
        joblib.dump(self.model, model_path)
        joblib.dump(self.vectorizer, vectorizer_path)
        logger.info(f"Modèle sauvegardé : {model_path}")
        logger.info(f"Vectorizer sauvegardé : {vectorizer_path}")

    def load_latest_model(self):
        """Charge le dernier modèle sauvegardé"""
        try:
            # Check if models directory exists
            if not os.path.exists('models'):
                logger.info("Models directory does not exist")
                return False

            model_files = sorted([f for f in os.listdir('models') if f.startswith('sentiment_model_')])
            vectorizer_files = sorted([f for f in os.listdir('models') if f.startswith('vectorizer_')])
            
            if not (model_files and vectorizer_files):
                logger.info("No existing model files found")
                return False

            latest_model = os.path.join('models', model_files[-1])
            latest_vectorizer = os.path.join('models', vectorizer_files[-1])
            
            logger.info(f"Loading model from: {latest_model}")
            logger.info(f"Loading vectorizer from: {latest_vectorizer}")
            
            self.model = joblib.load(latest_model)
            self.vectorizer = joblib.load(latest_vectorizer)
            self._is_loaded = True
            logger.info("Model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self._is_loaded = False
            return False

    def is_model_loaded(self):
        """Check if the model is loaded and ready for predictions"""
        return self._is_loaded

if __name__ == "__main__":
    # Test du modèle
    sentiment_model = SentimentModel()
    sentiment_model.train_model()