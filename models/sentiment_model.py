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
           "le", "la", "les", "aux", "avec", "ce", "ces", "dans", "de", "des", "du",
            "elle", "en", "et", "eux", "il", "je", "la", "le", "leur", "lui", "ma",
            "mais", "me", "même", "mes", "moi", "mon", "ni", "notre", "nous", "on",
            "ou", "par", "pas", "pour", "qu", "que", "qui", "sa", "se", "ses", "son",
            "sur", "ta", "te", "tes", "toi", "ton", "tu", "un", "une", "vos", "votre",
            "vous", "c", "d", "j", "l", "à", "m", "n", "s", "t", "y", "été", "étée",
            "étées", "étés", "étant", "suis", "es", "est", "sommes", "êtes", "sont",
            "serai", "seras", "sera", "serons", "serez", "seront", "serais", "serait",
            "serions", "seriez", "seraient"
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
        
        query = "SELECT text, positive, negative FROM tweets"
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
            
            # Création d'un score de sentiment composite (1 = positif, 0 = neutre, -1 = négatif)
            logger.info("Création du score de sentiment composite...")
            df['sentiment_score'] = df.apply(
                lambda row: 1 if row['positive'] == 1 else (-1 if row['negative'] == 1 else 0), 
                axis=1
            )
            
            # Vectorisation
            logger.info("Vectorisation des textes...")
            X = self.vectorizer.fit_transform(df['text_clean'])
            y = df['sentiment_score']  # Utilise le score composite au lieu de juste 'positive'
            
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
            
            # Prédiction du score de sentiment avec probability
            probas = self.model.predict_proba(vectors)
            
            # Calculer un score continu entre -1 et 1
            results = []
            
            for proba in probas:
                # Si modèle multiclasse (-1, 0, 1)
                if len(proba) == 3:
                    # Calcul pondéré: proba_neg*-1 + proba_neu*0 + proba_pos*1
                    # Classes triées: -1, 0, 1 ou 0, 1, 2 (selon l'ordre des classes)
                    classes = self.model.classes_
                    score = 0
                    
                    for i, class_val in enumerate(classes):
                        if class_val == -1 or class_val == 0:  # classe négative
                            score -= proba[i]
                        elif class_val == 1 or class_val == 2:  # classe positive
                            score += proba[i]
                    
                    results.append(score)
                # Si modèle binaire (0, 1)    
                else:
                    # Transformer la probabilité [0,1] en score [-1,1]
                    score = (proba[1] * 2) - 1
                    results.append(score)
                
            return results
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