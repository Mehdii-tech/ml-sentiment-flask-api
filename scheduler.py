from models.sentiment_model import SentimentModel
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def cleanup_old_models():
    """Clean up old model files keeping only the last 3 versions"""
    try:
        # Clean up model files
        model_files = sorted([f for f in os.listdir('models') if f.startswith('sentiment_model_')])
        if len(model_files) > 3:
            for old_file in model_files[:-3]:
                try:
                    os.remove(os.path.join('models', old_file))
                    logger.info(f"Removed old model file: {old_file}")
                except Exception as e:
                    logger.error(f"Error removing old model file {old_file}: {str(e)}")

        # Clean up vectorizer files
        vectorizer_files = sorted([f for f in os.listdir('models') if f.startswith('vectorizer_')])
        if len(vectorizer_files) > 3:
            for old_file in vectorizer_files[:-3]:
                try:
                    os.remove(os.path.join('models', old_file))
                    logger.info(f"Removed old vectorizer file: {old_file}")
                except Exception as e:
                    logger.error(f"Error removing old vectorizer file {old_file}: {str(e)}")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

def retrain_model():
    """Retrain the model with latest data"""
    try:
        logger.info("Starting model retraining...")
        
        # Initialize model
        sentiment_model = SentimentModel()
        
        # Train model with latest data
        if sentiment_model.train_model():
            logger.info("Model retrained successfully")
            cleanup_old_models()
            return True
        else:
            logger.error("Failed to retrain model")
            return False
            
    except Exception as e:
        logger.error(f"Error during model retraining: {str(e)}")
        return False

if __name__ == "__main__":
    retrain_model()
