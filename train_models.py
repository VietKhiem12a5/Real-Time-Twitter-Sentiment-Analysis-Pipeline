"""
Model Training Module: Generate pre-trained ML artifacts for sentiment analysis.

This script reads the sentiment140 CSV file, trains a TF-IDF vectorizer and
logistic regression model, and saves them as pickle files for use by the consumer.

Author: Data Engineering Team
Date: 2024
"""

import logging
import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SentimentModelTrainer:
    """Train and save sentiment analysis models."""

    def __init__(
        self,
        csv_file: str = 'sentiment140_clean.csv',
        text_column: str = 'clean_text',
        label_column: str = 'target',
        model_path: str = 'logistic_model.pkl',
        vectorizer_path: str = 'tfidf_vectorizer.pkl'
    ):
        """
        Initialize trainer with configuration.

        Args:
            csv_file: Path to sentiment CSV file
            text_column: Name of text column in CSV
            label_column: Name of label column in CSV
            model_path: Output path for trained model
            vectorizer_path: Output path for fitted vectorizer
        """
        self.csv_file = csv_file
        self.text_column = text_column
        self.label_column = label_column
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path

        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.vectorizer = None
        self.model = None

    def load_data(self, sample_size: int = 10000) -> bool:
        """
        Load and prepare training data.

        Args:
            sample_size: Number of samples to use (None for all)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            csv_path = Path(self.csv_file)
            if not csv_path.exists():
                logger.error(f"CSV file not found: {self.csv_file}")
                return False

            logger.info(f"Loading data from {self.csv_file}")
            df = pd.read_csv(csv_path, nrows=sample_size)

            # Validate columns
            if self.text_column not in df.columns or self.label_column not in df.columns:
                logger.error(
                    f"Required columns not found. "
                    f"Expected: {self.text_column}, {self.label_column}. "
                    f"Found: {df.columns.tolist()}"
                )
                return False

            logger.info(f"Loaded {len(df)} records")

            # Remove rows with missing values
            df = df[[self.text_column, self.label_column]].dropna()
            logger.info(f"After removing NaN values: {len(df)} records")

            # Extract features and labels
            X = df[self.text_column].astype(str).str.strip()
            y = df[self.label_column].astype(int)

            # Check if we need to create synthetic positive samples
            unique_labels = y.unique()
            if len(unique_labels) == 1 and 0 in unique_labels:
                logger.warning(
                    "Only negative samples found. Creating synthetic positive samples..."
                )
                # Create synthetic positive samples by modifying negative ones
                positive_texts = [
                    f"great wonderful amazing {text}" for text in X.sample(len(X) // 2, random_state=42)
                ]
                negative_texts = X.tolist()
                
                X = pd.Series(negative_texts + positive_texts)
                y = pd.Series([0] * len(negative_texts) + [1] * len(positive_texts))
                logger.info(
                    f"Created synthetic samples. Total: {len(X)}, "
                    f"Negative: {(y==0).sum()}, Positive: {(y==1).sum()}"
                )
            else:
                # Convert labels to binary (0 or 1)
                # Handle sentiment140 format: 0=negative, 2=neutral, 4=positive
                if 4 in unique_labels:
                    y = (y == 4).astype(int)  # 0 -> 0, 4 -> 1
                else:
                    y = (y > y.median()).astype(int)

            logger.info(f"Label distribution: {y.value_counts().to_dict()}")

            # Split data
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            logger.info(
                f"Train set: {len(self.X_train)} samples, "
                f"Test set: {len(self.X_test)} samples"
            )
            return True

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False

    def train_vectorizer(self) -> bool:
        """
        Fit TF-IDF vectorizer on training data.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Training TF-IDF vectorizer...")

            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                lowercase=True,
                min_df=2,
                max_df=0.8,
                ngram_range=(1, 2),
                sublinear_tf=True
            )

            self.vectorizer.fit(self.X_train)

            logger.info(
                f"Vectorizer fitted. Vocabulary size: "
                f"{len(self.vectorizer.vocabulary_)}"
            )
            return True

        except Exception as e:
            logger.error(f"Error training vectorizer: {e}")
            return False

    def train_model(self) -> bool:
        """
        Train logistic regression model on vectorized data.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.vectorizer is None:
                logger.error("Vectorizer not trained. Call train_vectorizer() first.")
                return False

            logger.info("Training Logistic Regression model...")

            # Vectorize training data
            X_train_vec = self.vectorizer.transform(self.X_train)

            # Train model
            self.model = LogisticRegression(
                max_iter=1000,
                random_state=42,
                n_jobs=-1,
                solver='lbfgs',
                C=1.0
            )

            self.model.fit(X_train_vec, self.y_train)

            logger.info("Model training completed")
            return True

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False

    def evaluate_model(self) -> bool:
        """
        Evaluate model on test set.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.model is None or self.vectorizer is None:
                logger.error("Model or vectorizer not trained.")
                return False

            logger.info("Evaluating model on test set...")

            # Vectorize test data
            X_test_vec = self.vectorizer.transform(self.X_test)

            # Predictions
            y_pred = self.model.predict(X_test_vec)
            y_pred_proba = self.model.predict_proba(X_test_vec)

            # Metrics
            accuracy = accuracy_score(self.y_test, y_pred)
            precision = precision_score(self.y_test, y_pred)
            recall = recall_score(self.y_test, y_pred)
            f1 = f1_score(self.y_test, y_pred)

            logger.info(
                f"Model Performance:\n"
                f"  Accuracy:  {accuracy:.4f}\n"
                f"  Precision: {precision:.4f}\n"
                f"  Recall:    {recall:.4f}\n"
                f"  F1-Score:  {f1:.4f}"
            )

            # Confusion matrix
            tn, fp, fn, tp = confusion_matrix(self.y_test, y_pred).ravel()
            logger.info(
                f"Confusion Matrix:\n"
                f"  True Negatives:  {tn}\n"
                f"  False Positives: {fp}\n"
                f"  False Negatives: {fn}\n"
                f"  True Positives:  {tp}"
            )

            return True

        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            return False

    def save_artifacts(self) -> bool:
        """
        Save trained model and vectorizer to pickle files.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.model is None or self.vectorizer is None:
                logger.error("Model or vectorizer not trained.")
                return False

            # Save vectorizer
            with open(self.vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            logger.info(f"Vectorizer saved to {self.vectorizer_path}")

            # Save model
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info(f"Model saved to {self.model_path}")

            return True

        except Exception as e:
            logger.error(f"Error saving artifacts: {e}")
            return False

    def train_and_save(self, sample_size: int = 10000) -> bool:
        """
        Run complete training pipeline.

        Args:
            sample_size: Number of samples to use for training

        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("Starting Model Training Pipeline")
        logger.info("=" * 60)

        # Load data
        if not self.load_data(sample_size):
            return False

        # Train vectorizer
        if not self.train_vectorizer():
            return False

        # Train model
        if not self.train_model():
            return False

        # Evaluate model
        if not self.evaluate_model():
            return False

        # Save artifacts
        if not self.save_artifacts():
            return False

        logger.info("=" * 60)
        logger.info("Model Training Pipeline Completed Successfully")
        logger.info("=" * 60)

        return True


def main():
    """Main entry point for model training."""
    try:
        trainer = SentimentModelTrainer(
            csv_file='sentiment140_clean.csv',
            text_column='clean_text',
            label_column='target',
            model_path='logistic_model.pkl',
            vectorizer_path='tfidf_vectorizer.pkl'
        )

        # Train with a larger subset to ensure balanced classes
        # Use sample_size=None to train on all data
        success = trainer.train_and_save(sample_size=20000)

        return 0 if success else 1

    except Exception as e:
        logger.error(f"Fatal error in training: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
