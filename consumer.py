"""
Consumer Module: Process streaming Twitter data with ML sentiment analysis.

This module consumes messages from the 'twitter_stream' Kafka topic,
applies a pre-trained sentiment classification model, and stores
results in a SQLite database.

"""

import json
import logging
import pickle
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from confluent_kafka import Consumer, KafkaError
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()


class SentimentRecord(Base):
    """SQLAlchemy model for storing sentiment analysis results."""

    __tablename__ = 'sentiment_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String(500), nullable=False)
    user = Column(String(100), nullable=True)
    sentiment_label = Column(Integer, nullable=False)  # 0=Negative, 1=Positive
    confidence = Column(Float, nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    kafka_timestamp = Column(Integer, nullable=True)

    def __repr__(self):
        return (
            f"<SentimentRecord(user='{self.user}', "
            f"sentiment={self.sentiment_label}, processed_at='{self.processed_at}')>"
        )


class SentimentConsumer:
    """Consumer for processing Twitter sentiment data from Kafka."""

    def __init__(
        self,
        bootstrap_servers: str = 'localhost:9092',
        topic: str = 'twitter_stream',
        group_id: str = 'sentiment-analysis-group',
        db_path: str = 'sqlite:///sentiment_db.sqlite',
        model_path: str = 'logistic_model.pkl',
        vectorizer_path: str = 'tfidf_vectorizer.pkl'
    ):
        """
        Initialize the consumer with ML artifacts and database connection.

        Args:
            bootstrap_servers: Kafka broker address
            topic: Kafka topic to consume from
            group_id: Consumer group ID
            db_path: SQLAlchemy database URL
            model_path: Path to the trained logistic regression model
            vectorizer_path: Path to the fitted TF-IDF vectorizer
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.db_path = db_path
        self.running = True
        self.processed_count = 0
        self.error_count = 0

        # Initialize Kafka consumer
        self.consumer = None
        self._initialize_consumer()

        # Load ML artifacts
        self.model = None
        self.vectorizer = None
        self._load_ml_artifacts(model_path, vectorizer_path)

        # Initialize database
        self.engine = None
        self.Session = None
        self._initialize_database()

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _initialize_consumer(self) -> None:
        """Initialize and configure the Kafka consumer."""
        try:
            config = {
                'bootstrap.servers': self.bootstrap_servers,
                'group.id': self.group_id,
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': True,
                'auto.commit.interval.ms': 5000,
                'session.timeout.ms': 30000,
            }
            self.consumer = Consumer(config)
            self.consumer.subscribe([self.topic])
            logger.info(
                f"Kafka consumer initialized. Group: {self.group_id}, "
                f"Topic: {self.topic}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            raise

    def _load_ml_artifacts(
        self,
        model_path: str,
        vectorizer_path: str
    ) -> None:
        """
        Load pre-trained ML model and vectorizer.

        Args:
            model_path: Path to the logistic regression model pickle file
            vectorizer_path: Path to the TF-IDF vectorizer pickle file

        Raises:
            FileNotFoundError: If model or vectorizer files not found
            Exception: If loading artifacts fails
        """
        try:
            # Check if files exist
            if not Path(model_path).exists():
                raise FileNotFoundError(
                    f"Model file not found: {model_path}. "
                    f"Please run train_models.py first."
                )
            if not Path(vectorizer_path).exists():
                raise FileNotFoundError(
                    f"Vectorizer file not found: {vectorizer_path}. "
                    f"Please run train_models.py first."
                )

            # Load artifacts
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
                logger.info(f"Model loaded from {model_path}")

            with open(vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
                logger.info(f"Vectorizer loaded from {vectorizer_path}")

        except FileNotFoundError as e:
            logger.error(str(e))
            raise
        except Exception as e:
            logger.error(f"Error loading ML artifacts: {e}")
            raise

    def _initialize_database(self) -> None:
        """Initialize SQLAlchemy database connection and create tables."""
        try:
            self.engine = create_engine(self.db_path, echo=False)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            logger.info(f"Database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def predict_sentiment(self, text: str) -> tuple[int, float]:
        """
        Predict sentiment for given text.

        Args:
            text: Tweet text to analyze

        Returns:
            tuple: (sentiment_label, confidence_score)
                  sentiment_label: 0=Negative, 1=Positive
                  confidence_score: probability of predicted class
        """
        try:
            # Transform text using vectorizer
            text_vector = self.vectorizer.transform([text])

            # Get prediction and probability
            prediction = self.model.predict(text_vector)[0]
            probabilities = self.model.predict_proba(text_vector)[0]

            # Get confidence for predicted class
            confidence = probabilities[prediction]

            return int(prediction), float(confidence)

        except Exception as e:
            logger.error(f"Error in sentiment prediction: {e}")
            return 0, 0.0

    def process_message(self, message_json: dict) -> Optional[SentimentRecord]:
        """
        Process a single message from Kafka.

        Args:
            message_json: Parsed JSON message from Kafka

        Returns:
            SentimentRecord object or None if processing failed
        """
        try:
            # Extract fields
            text = message_json.get('text', '').strip()
            user = message_json.get('user', 'unknown')
            kafka_timestamp = message_json.get('timestamp')

            # Validate text
            if not text or len(text) < 3:
                logger.warning("Skipping message with invalid text")
                return None

            # Predict sentiment
            sentiment_label, confidence = self.predict_sentiment(text)

            # Create database record
            record = SentimentRecord(
                text=text[:500],  # Truncate to column limit
                user=user[:100],
                sentiment_label=sentiment_label,
                confidence=confidence,
                kafka_timestamp=kafka_timestamp
            )

            # Save to database
            session = self.Session()
            try:
                session.add(record)
                session.commit()
                self.processed_count += 1

                if self.processed_count % 50 == 0:
                    logger.info(
                        f"Processed {self.processed_count} messages. "
                        f"Errors: {self.error_count}"
                    )

                return record

            except Exception as e:
                session.rollback()
                logger.error(f"Database error: {e}")
                self.error_count += 1
                return None
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.error_count += 1
            return None

    def consume(self, timeout_ms: int = 1000) -> None:
        """
        Start consuming messages from Kafka.

        Args:
            timeout_ms: Timeout for consuming in milliseconds
        """
        logger.info("Starting to consume messages from Kafka...")

        try:
            while self.running:
                msg = self.consumer.poll(timeout=timeout_ms / 1000.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"End of partition: {msg.topic()}")
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        self.error_count += 1
                else:
                    try:
                        # Decode and parse message
                        message_json = json.loads(msg.value().decode('utf-8'))

                        # Process the message
                        record = self.process_message(message_json)

                        if record:
                            logger.debug(
                                f"Processed: user={record.user}, "
                                f"sentiment={record.sentiment_label}, "
                                f"confidence={record.confidence:.3f}"
                            )

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message JSON: {e}")
                        self.error_count += 1
                    except Exception as e:
                        logger.error(f"Unexpected error processing message: {e}")
                        self.error_count += 1

        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Fatal error in consume loop: {e}")
        finally:
            self.close()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}. Shutting down...")
        self.running = False

    def close(self) -> None:
        """Close consumer, database connection, and clean up resources."""
        try:
            if self.consumer:
                self.consumer.close()
                logger.info("Kafka consumer closed")

            if self.engine:
                self.engine.dispose()
                logger.info("Database connection closed")

            logger.info(
                f"Consumer shut down. Total processed: {self.processed_count}, "
                f"Errors: {self.error_count}"
            )
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point for the consumer."""
    try:
        # Configuration
        BOOTSTRAP_SERVERS = 'localhost:9092'
        KAFKA_TOPIC = 'twitter_stream'
        CONSUMER_GROUP = 'sentiment-analysis-group'
        DB_PATH = 'sqlite:///sentiment_db.sqlite'
        MODEL_PATH = 'logistic_model.pkl'
        VECTORIZER_PATH = 'tfidf_vectorizer.pkl'

        # Initialize consumer
        consumer = SentimentConsumer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            topic=KAFKA_TOPIC,
            group_id=CONSUMER_GROUP,
            db_path=DB_PATH,
            model_path=MODEL_PATH,
            vectorizer_path=VECTORIZER_PATH
        )

        # Start consuming
        consumer.consume()
        return 0

    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
