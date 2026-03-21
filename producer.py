"""
Producer Module: Stream Twitter data from CSV to Kafka topic.

This module reads a sentiment dataset from a CSV file and streams
each record as a JSON message to the 'twitter_stream' Kafka topic.
Includes delivery report callbacks for monitoring message delivery status.

Author: Data Engineering Team
Date: 2024
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional, Callable

import pandas as pd
from confluent_kafka import Producer
from confluent_kafka.error import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TwitterProducer:
    """Producer for streaming Twitter sentiment data to Kafka."""

    def __init__(
        self,
        bootstrap_servers: str = 'localhost:9092',
        topic: str = 'twitter_stream',
        message_delay: float = 0.1
    ):
        """
        Initialize the Kafka producer.

        Args:
            bootstrap_servers: Kafka broker address in format host:port
            topic: Kafka topic name to produce messages to
            message_delay: Delay in seconds between message productions
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.message_delay = message_delay
        self.producer = None
        self.message_count = 0
        self.error_count = 0

        self._initialize_producer()

    def _initialize_producer(self) -> None:
        """Initialize and configure the Kafka producer."""
        try:
            config = {
                'bootstrap.servers': self.bootstrap_servers,
                'client.id': 'twitter-sentiment-producer',
                'acks': 'all',
                'retries': 3,
                'retry.backoff.ms': 100,
            }
            self.producer = Producer(config)
            logger.info(
                f"Kafka producer initialized with broker: {self.bootstrap_servers}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise

    def delivery_report(self, err: Optional[KafkaError], msg) -> None:
        """
        Callback for delivery reports from Kafka.

        Args:
            err: Error encountered during delivery (None if successful)
            msg: The delivered message
        """
        if err is not None:
            logger.error(
                f"Message delivery failed: {err} (Topic: {msg.topic()}, "
                f"Partition: {msg.partition()})"
            )
            self.error_count += 1
        else:
            logger.debug(
                f"Message delivered to {msg.topic()} "
                f"[{msg.partition()}] at offset {msg.offset()}"
            )
            self.message_count += 1

    def produce_from_csv(
        self,
        csv_file: str,
        text_column: str = 'text',
        user_column: str = None,
        limit: Optional[int] = None
    ) -> bool:
        """
        Read CSV file and stream records to Kafka.

        Args:
            csv_file: Path to the CSV file
            text_column: Name of the column containing tweet text
            user_column: Name of the column containing user information (optional)
            limit: Maximum number of records to process (None for all)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Verify file exists
            csv_path = Path(csv_file)
            if not csv_path.exists():
                logger.error(f"CSV file not found: {csv_file}")
                return False

            logger.info(f"Reading CSV file: {csv_file}")
            df = pd.read_csv(csv_file, nrows=limit)

            # Validate required columns
            if text_column not in df.columns:
                logger.error(
                    f"Required text column not found. Expected: {text_column}. "
                    f"Found: {df.columns.tolist()}"
                )
                return False
            
            # If user column doesn't exist, create synthetic users
            if user_column is None or user_column not in df.columns:
                df['__user__'] = [f'user_{i}' for i in range(len(df))]
                user_column = '__user__'
                logger.info(f"User column not found. Creating synthetic users.")

            logger.info(
                f"Processing {len(df)} records from CSV "
                f"(limit: {limit if limit else 'none'})"
            )

            for idx, row in df.iterrows():
                try:
                    # Prepare message payload
                    message = {
                        'text': str(row[text_column]).strip(),
                        'user': str(row[user_column]).strip(),
                        'timestamp': int(time.time() * 1000),  # ms since epoch
                        'source': 'csv_stream'
                    }

                    # Produce to Kafka with delivery report
                    self.producer.produce(
                        topic=self.topic,
                        key=str(row[user_column]).encode('utf-8'),
                        value=json.dumps(message).encode('utf-8'),
                        callback=self.delivery_report
                    )

                    # Log progress every 100 messages
                    if (idx + 1) % 100 == 0:
                        logger.info(f"Streamed {idx + 1} messages so far...")

                    # Introduce delay to simulate real-time streaming
                    time.sleep(self.message_delay)

                except Exception as e:
                    logger.error(
                        f"Error processing row {idx}: {e}"
                    )
                    self.error_count += 1
                    continue

            # Flush any remaining messages
            logger.info("Flushing remaining messages...")
            self.producer.flush(timeout=30)

            logger.info(
                f"Stream completed successfully. "
                f"Messages sent: {self.message_count}, Errors: {self.error_count}"
            )
            return True

        except Exception as e:
            logger.error(f"Error in produce_from_csv: {e}")
            return False

    def close(self) -> None:
        """Close the producer and clean up resources."""
        if self.producer:
            self.producer.flush()
            logger.info("Producer closed successfully")


def main():
    """Main entry point for the producer."""
    try:
        # Configuration
        BOOTSTRAP_SERVERS = 'localhost:9092'
        KAFKA_TOPIC = 'twitter_stream'
        CSV_FILE = 'sentiment140_clean.csv'
        MESSAGE_DELAY = 0.1  # seconds
        RECORD_LIMIT = 5000  # Limit to 5000 records to avoid memory issues

        # Initialize producer
        producer = TwitterProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            topic=KAFKA_TOPIC,
            message_delay=MESSAGE_DELAY
        )

        # Stream data from CSV
        success = producer.produce_from_csv(
            csv_file=CSV_FILE,
            text_column='clean_text',
            user_column=None,
            limit=RECORD_LIMIT
        )

        if not success:
            logger.error("Producer failed to complete streaming")
            return 1

        producer.close()
        return 0

    except KeyboardInterrupt:
        logger.info("Producer interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Fatal error in producer: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
