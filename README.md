# Real-Time Twitter Sentiment Analysis Pipeline

A production-grade, scalable streaming data pipeline for real-time sentiment analysis using Apache Kafka, machine learning, and FastAPI.

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
### Terminal 2: Start the Producer

In a new terminal, start streaming data:

```bash
python producer.py
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
## API Endpoints
Interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

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


