# Real-Time Twitter Sentiment Analysis Pipeline

A production-grade, scalable streaming data pipeline for real-time sentiment analysis using Apache Kafka, machine learning, and FastAPI.

## Architecture Overview

```
┌─────────────────┐
│  sentiment140   │
│   CSV Dataset   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐       ┌────────────────┐
│   Producer      │──────▶│  Kafka Topic   │
│  (CSV Stream)   │       │ twitter_stream │
└─────────────────┘       └────────┬───────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  Consumer       │
                         │  (ML Processor) │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  SQLite Database │
                         │ sentiment_db.db  │
                         └──────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  FastAPI Server  │
                         │  (REST API)      │
                         └──────────────────┘
```

## Technology Stack

- **Messaging**: Apache Kafka (Confluent images)
- **Web Framework**: FastAPI + Uvicorn
- **ML/NLP**: Scikit-learn (TF-IDF, Logistic Regression)
- **Database**: SQLite with SQLAlchemy ORM
- **Container**: Docker & Docker Compose
- **Language**: Python 3.9+

## Project Structure

```
datamining/
├── docker-compose.yml          # Kafka & Zookeeper setup
├── requirements.txt            # Python dependencies
├── train_models.py             # ML model training script
├── producer.py                 # Kafka data producer
├── consumer.py                 # Kafka data consumer + ML inference
├── api.py                      # FastAPI serving layer
├── sentiment140_clean.csv      # Sample dataset
└── README.md                   # This file
```

## Setup & Installation

### Prerequisites

- Python 3.9 or higher
- Docker Desktop (with Docker Compose)
- 4GB+ RAM available
- ~2GB disk space for dataset and models

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or use a virtual environment (recommended):

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Then install dependencies
pip install -r requirements.txt
```

### Step 2: Train ML Models

Before running the consumer, train the sentiment classification models:

```bash
python train_models.py
```

**Output:**
- `logistic_model.pkl` - Pre-trained logistic regression model
- `tfidf_vectorizer.pkl` - Fitted TF-IDF vectorizer

**Note**: This uses 10,000 samples by default. To use all data, edit `train_models.py` and change:
```python
success = trainer.train_and_save(sample_size=None)  # Use all data
```

### Step 3: Start Kafka & Zookeeper

```bash
docker-compose up -d
```

Verify containers are running:

```bash
docker-compose ps
```

Expected output:
```
NAME            STATUS
zookeeper       Up 2s
kafka           Up 2s
```

To view logs:
```bash
docker-compose logs -f kafka
```

## Running the Pipeline

### Terminal 1: Start the Consumer

```bash
python consumer.py
```

**Expected output:**
```
2024-01-15 10:30:45 - __main__ - INFO - Kafka consumer initialized...
2024-01-15 10:30:45 - __main__ - INFO - Model loaded from logistic_model.pkl
2024-01-15 10:30:45 - __main__ - INFO - Vectorizer loaded from tfidf_vectorizer.pkl
2024-01-15 10:30:45 - __main__ - INFO - Database initialized...
2024-01-15 10:30:45 - __main__ - INFO - Starting to consume messages from Kafka...
```

### Terminal 2: Start the Producer

In a new terminal, start streaming data:

```bash
python producer.py
```

**Expected output:**
```
2024-01-15 10:31:00 - __main__ - INFO - Reading CSV file: sentiment140_clean.csv
2024-01-15 10:31:00 - __main__ - INFO - Processing 160000 records...
2024-01-15 10:31:10 - __main__ - INFO - Streamed 100 messages so far...
```

**Note**: The producer will stream data with a 0.1-second delay between messages to simulate real-time scenarios. The consumer will simultaneously process these messages and save results to the database.

### Terminal 3: Start the API Server

In another terminal, launch the FastAPI server:

```bash
python api.py
```

Or use uvicorn directly:

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
2024-01-15 10:32:00 - __main__ - INFO - Starting Sentiment Analysis API server...
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## API Endpoints

### 1. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "database_connected": true,
  "timestamp": "2024-01-15T10:32:15.123456"
}
```

### 2. Sentiment Statistics (Main Endpoint)

Get overall sentiment statistics for all processed tweets:

```bash
curl http://localhost:8000/api/v1/sentiment/stats
```

**Response:**
```json
{
  "total_processed": 5000,
  "positive_count": 3200,
  "negative_count": 1800,
  "positive_percentage": 64.0,
  "negative_percentage": 36.0,
  "timestamp": "2024-01-15T10:32:15.123456"
}
```

**Optional Query Parameter** - Filter by hours:

```bash
# Get stats from last 24 hours
curl http://localhost:8000/api/v1/sentiment/stats?hours=24

# Get stats from last 1 hour
curl http://localhost:8000/api/v1/sentiment/stats?hours=1
```

### 3. Recent Sentiment Records

Get recently processed tweets with their sentiment predictions:

```bash
curl http://localhost:8000/api/v1/sentiment/recent?limit=10
```

**Response:**
```json
[
  {
    "id": 5000,
    "text": "This product is amazing! Highly recommend!",
    "user": "@user123",
    "sentiment_label": 1,
    "confidence": 0.92,
    "processed_at": "2024-01-15T10:32:10.123456"
  },
  {
    "id": 4999,
    "text": "Worst experience ever. Total waste of time.",
    "user": "@user456",
    "sentiment_label": 0,
    "confidence": 0.88,
    "processed_at": "2024-01-15T10:32:09.123456"
  }
]
```

**Query Parameters:**
- `limit`: Number of records (1-100, default: 10)
- `hours`: Filter from last N hours (optional)

### 4. Statistics by User

Get sentiment breakdown per user:

```bash
curl http://localhost:8000/api/v1/sentiment/stats-by-user?limit=10
```

**Response:**
```json
[
  {
    "user": "@user123",
    "total_tweets": 150,
    "positive_tweets": 120,
    "negative_tweets": 30,
    "positive_percentage": 80.0
  }
]
```

### 5. API Documentation

Interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Database Schema

The SQLite database contains a single table: `sentiment_records`

```sql
CREATE TABLE sentiment_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text VARCHAR(500) NOT NULL,
    user VARCHAR(100),
    sentiment_label INTEGER NOT NULL,      -- 0=Negative, 1=Positive
    confidence FLOAT,                       -- Prediction probability (0.0-1.0)
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    kafka_timestamp INTEGER
);
```

## Configuration

### Producer Configuration (producer.py)

```python
BOOTSTRAP_SERVERS = 'localhost:9092'      # Kafka broker
KAFKA_TOPIC = 'twitter_stream'             # Kafka topic
CSV_FILE = 'sentiment140_clean.csv'        # Data source
MESSAGE_DELAY = 0.1                        # Seconds between messages
RECORD_LIMIT = None                        # Process all records
```

### Consumer Configuration (consumer.py)

```python
BOOTSTRAP_SERVERS = 'localhost:9092'       # Kafka broker
KAFKA_TOPIC = 'twitter_stream'             # Topic to consume
CONSUMER_GROUP = 'sentiment-analysis-group' # Consumer group ID
DB_PATH = 'sqlite:///sentiment_db.sqlite'  # SQLite database URL
MODEL_PATH = 'logistic_model.pkl'          # ML model
VECTORIZER_PATH = 'tfidf_vectorizer.pkl'   # TF-IDF vectorizer
```

### API Configuration (api.py)

```python
DATABASE_URL = 'sqlite:///sentiment_db.sqlite'  # Database URL
HOST = '0.0.0.0'                               # API host
PORT = 8000                                     # API port
```

## Monitoring & Logging

All components include comprehensive logging:

- **Log Level**: INFO (set in respective modules)
- **Format**: `timestamp - module - level - message`
- **Files**: Logs are printed to console

To increase verbosity, modify logging level in source files:

```python
logging.basicConfig(level=logging.DEBUG)  # Change INFO to DEBUG
```

## Error Handling

The pipeline includes production-grade error handling:

- **Producer**: Delivery report callbacks with retry logic
- **Consumer**: Message parsing and database transaction error handling
- **API**: HTTP exception handling with appropriate status codes
- **Database**: Transaction rollback on errors

## Stopping the Pipeline

### Stop Consumer/Producer

Press `Ctrl+C` in the respective terminal.

### Stop API Server

Press `Ctrl+C` in the API terminal.

### Stop Kafka & Zookeeper

```bash
docker-compose down

# To also remove volumes (WARNING: deletes data)
docker-compose down -v
```

## Troubleshooting

### Issue: Kafka connection refused

```
Error: Connection refused (localhost:9092)
```

**Solution:**
```bash
docker-compose ps  # Verify containers are running
docker-compose logs kafka  # Check Kafka logs
docker-compose restart kafka  # Restart Kafka
```

### Issue: Model files not found

```
FileNotFoundError: Model file not found: logistic_model.pkl
```

**Solution**: Run the training script first:
```bash
python train_models.py
```

### Issue: Database locked

**Solution**: Delete the old database and restart:
```bash
rm sentiment_db.sqlite
python consumer.py  # Recreates database
```

### Issue: Port already in use

Change the port in the respective configuration:

```bash
# API on different port
uvicorn api:app --port 8001
```

## Performance Tuning

### Kafka Producer Throughput

Modify in `producer.py`:
```python
MESSAGE_DELAY = 0.01  # Faster streaming (10ms between messages)
```

### ML Model Batch Processing

For higher throughput, consider implementing batch inference in the consumer by collecting multiple messages before prediction.

### Database Indexing

Add indexes for faster queries:

```python
# In consumer.py, after Base.metadata.create_all():
engine.execute(
    "CREATE INDEX IF NOT EXISTS idx_user ON sentiment_records(user)"
)
engine.execute(
    "CREATE INDEX IF NOT EXISTS idx_timestamp ON sentiment_records(processed_at)"
)
```

## Deployment Considerations

For production deployment:

1. **Use managed Kafka** (AWS MSK, Confluent Cloud)
2. **Switch to production database** (PostgreSQL, MySQL)
3. **Add authentication** (SSL/TLS for Kafka, Bearer tokens for API)
4. **Implement horizontal scaling** (multiple consumer instances)
5. **Use a reverse proxy** (Nginx, AWS ALB)
6. **Add monitoring** (Prometheus, Grafana)
7. **Implement CI/CD** (GitHub Actions, Jenkins)

## Testing

Run unit tests (to be implemented):

```bash
pytest tests/
```

## File Descriptions

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Container orchestration for Kafka & Zookeeper |
| `requirements.txt` | Python package dependencies |
| `train_models.py` | Train and save ML models to pickle files |
| `producer.py` | Read CSV and stream messages to Kafka |
| `consumer.py` | Consume Kafka messages, apply ML model, save to DB |
| `api.py` | FastAPI server with sentiment statistics endpoints |

## License

MIT License - See LICENSE file for details

## Support & Issues

For issues or questions:
1. Check the Troubleshooting section
2. Review logs from respective components
3. Verify Kafka connectivity with: `docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092`

## Contributing

Contributions welcome! Please ensure:
- Code follows PEP 8 style guide
- All functions have docstrings
- Error handling is implemented
- Logging is comprehensive

---

**Last Updated**: January 2024  
**Version**: 1.0.0
