# Sentiment Analysis Pipeline - Setup & Execution Guide

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Train ML Models (2-3 minutes)
```bash
python train_models.py
```

### 3. Start Kafka Infrastructure
```bash
docker-compose up -d
```

### 4. Start Consumer (Terminal A)
```bash
python consumer.py
```

### 5. Start Producer (Terminal B)
```bash
python producer.py
```

### 6. Query Results (Terminal C)
```bash
# Once consumer has processed some messages
python api.py
```

Then access: `http://localhost:8000/api/v1/sentiment/stats`

---

## Detailed Step-by-Step Guide

### Prerequisites Verification

**Check Python version:**
```bash
python --version  # Should be 3.9+
```

**Check Docker installation:**
```bash
docker --version
docker-compose --version
```

**Available disk space:**
```bash
# Windows
fsutil volume diskfree C:

# Linux/Mac
df -h
```

---

## Phase 1: Environment Setup

### Step 1.1: Create Virtual Environment (Recommended)

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 1.2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Verify installation:**
```bash
python -c "import kafka, fastapi, sklearn, sqlalchemy; print('All imports OK')"
```

### Step 1.3: Verify Dataset

```bash
# Check if CSV file exists and has data
python -c "import pandas as pd; df = pd.read_csv('sentiment140_clean.csv', nrows=5); print(f'Rows: {len(df)}, Columns: {df.columns.tolist()}')"
```

**Expected output:**
```
Rows: 5, Columns: ['text', 'sentiment', 'user', ...]
```

---

## Phase 2: Train Machine Learning Models

### Step 2.1: Run Training Script

```bash
python train_models.py
```

**Process:**
1. Loads 10,000 samples from CSV
2. Builds TF-IDF vocabulary
3. Trains Logistic Regression model
4. Evaluates on test set
5. Saves artifacts

**Expected output:**
```
2024-01-15 10:00:00 - __main__ - INFO - ============================================================
2024-01-15 10:00:00 - __main__ - INFO - Starting Model Training Pipeline
2024-01-15 10:00:00 - __main__ - INFO - Loading data from sentiment140_clean.csv
2024-01-15 10:00:02 - __main__ - INFO - Loaded 10000 records
2024-01-15 10:00:02 - __main__ - INFO - Label distribution: {0: 5000, 1: 5000}
2024-01-15 10:00:02 - __main__ - INFO - Train set: 8000 samples, Test set: 2000 samples
2024-01-15 10:00:02 - __main__ - INFO - Training TF-IDF vectorizer...
2024-01-15 10:00:03 - __main__ - INFO - Vectorizer fitted. Vocabulary size: 5000
2024-01-15 10:00:03 - __main__ - INFO - Training Logistic Regression model...
2024-01-15 10:00:05 - __main__ - INFO - Model training completed
2024-01-15 10:00:05 - __main__ - INFO - Evaluating model on test set...
2024-01-15 10:00:06 - __main__ - INFO - Model Performance:
  Accuracy:  0.7850
  Precision: 0.7920
  Recall:    0.7800
  F1-Score:  0.7860
2024-01-15 10:00:06 - __main__ - INFO - Model saved to logistic_model.pkl
2024-01-15 10:00:06 - __main__ - INFO - Vectorizer saved to tfidf_vectorizer.pkl
2024-01-15 10:00:06 - __main__ - INFO - ============================================================
```

### Step 2.2: Verify Model Files

```bash
# Windows
dir logistic_model.pkl tfidf_vectorizer.pkl

# Linux/Mac
ls -lh logistic_model.pkl tfidf_vectorizer.pkl
```

Expected files:
- `logistic_model.pkl` (~1-5 MB)
- `tfidf_vectorizer.pkl` (~500 KB - 2 MB)

---

## Phase 3: Start Kafka Infrastructure

### Step 3.1: Launch Containers

```bash
docker-compose up -d
```

**Output:**
```
Creating network "datamining_sentiment-pipeline" with driver "bridge"
Creating zookeeper ... done
Creating kafka     ... done
```

### Step 3.2: Verify Kafka is Running

```bash
docker-compose ps
```

**Expected:**
```
NAME         STATUS
zookeeper    Up 15 seconds
kafka        Up 10 seconds
```

### Step 3.3: Create Kafka Topic (Optional - Auto-created)

```bash
docker exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic twitter_stream \
  --partitions 1 \
  --replication-factor 1
```

### Step 3.4: View Kafka Logs

```bash
docker-compose logs kafka | tail -20
```

Look for message: `"Started ConnectorType(INTERNAL)"`

---

## Phase 4: Start Data Processing Pipeline

### Step 4.1: Open Terminal A - Consumer

```bash
python consumer.py
```

**Wait for messages:**
```
2024-01-15 10:30:45 - __main__ - INFO - Kafka consumer initialized...
2024-01-15 10:30:45 - __main__ - INFO - Model loaded from logistic_model.pkl
2024-01-15 10:30:45 - __main__ - INFO - Vectorizer loaded from tfidf_vectorizer.pkl
2024-01-15 10:30:45 - __main__ - INFO - Database initialized: sqlite:///sentiment_db.sqlite
2024-01-15 10:30:45 - __main__ - INFO - Starting to consume messages from Kafka...
```

**Status**: Waiting for messages from producer.

### Step 4.2: Open Terminal B - Producer

```bash
python producer.py
```

**Process starts (may take 1-10 minutes depending on RECORD_LIMIT):**
```
2024-01-15 10:31:00 - __main__ - INFO - Reading CSV file: sentiment140_clean.csv
2024-01-15 10:31:01 - __main__ - INFO - Processing 160000 records (limit: none)
2024-01-15 10:31:02 - __main__ - INFO - Streamed 100 messages so far...
2024-01-15 10:31:03 - __main__ - INFO - Streamed 200 messages so far...
2024-01-15 10:31:13 - __main__ - INFO - Streamed 100 messages so far...
...
2024-01-15 10:45:30 - __main__ - INFO - Stream completed successfully. Messages sent: 160000, Errors: 0
```

**In Terminal A (Consumer)**, you should see:
```
2024-01-15 10:31:02 - __main__ - INFO - Processed 50 messages. Errors: 0
2024-01-15 10:31:04 - __main__ - INFO - Processed 100 messages. Errors: 0
...
```

### Step 4.3: Once Producer Completes

**Terminal A** will show final status:
```
2024-01-15 10:45:30 - __main__ - INFO - Waiting for remaining messages...
```

Keep consumer running to process all messages.

---

## Phase 5: Query Results with API

### Step 5.1: Open Terminal C - API Server

```bash
python api.py
```

**Expected output:**
```
2024-01-15 10:46:00 - __main__ - INFO - Starting Sentiment Analysis API server...
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 5.2: Test Endpoints

#### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "database_connected": true,
  "timestamp": "2024-01-15T10:46:15.123456"
}
```

#### Main Endpoint - Sentiment Stats
```bash
curl http://localhost:8000/api/v1/sentiment/stats
```

**Response:**
```json
{
  "total_processed": 160000,
  "positive_count": 85000,
  "negative_count": 75000,
  "positive_percentage": 53.13,
  "negative_percentage": 46.87,
  "timestamp": "2024-01-15T10:46:15.123456"
}
```

#### Recent Records
```bash
curl http://localhost:8000/api/v1/sentiment/recent?limit=5
```

### Step 5.3: Interactive API Documentation

Open browser: `http://localhost:8000/docs`

This opens Swagger UI where you can:
- View all available endpoints
- Try endpoints with different parameters
- See response schemas

---

## Monitoring Data Flow

### Check Database

```bash
# Install sqlite3 if needed
# Then query the database

sqlite3 sentiment_db.sqlite
```

**Inside sqlite3:**
```sql
-- Count total records
SELECT COUNT(*) as total FROM sentiment_records;

-- Check sentiment distribution
SELECT sentiment_label, COUNT(*) as count 
FROM sentiment_records 
GROUP BY sentiment_label;

-- View recent records
SELECT user, text, sentiment_label, confidence, processed_at 
FROM sentiment_records 
ORDER BY processed_at DESC 
LIMIT 5;

-- Exit
.quit
```

### Monitor Kafka Topic

```bash
# List messages in topic (last 5)
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic twitter_stream \
  --from-beginning \
  --max-messages 5

# Check topic information
docker exec kafka kafka-topics \
  --describe \
  --bootstrap-server localhost:9092 \
  --topic twitter_stream
```

### View Real-Time Logs

```bash
# Consumer logs
# (In consumer terminal, watch for "Processed X messages")

# Kafka logs
docker-compose logs -f kafka

# API logs
# (In API terminal)
```

---

## Performance Monitoring

### Messages Per Second

Note the timestamps in producer output:
```
2024-01-15 10:31:02 - Streamed 100 messages
2024-01-15 10:31:12 - Streamed 200 messages
```

With 0.1s delay between messages, effective throughput is ~10 messages/second.

### Database Size

```bash
# Windows
dir sentiment_db.sqlite

# Linux/Mac
ls -lh sentiment_db.sqlite
```

Each record typically adds ~250-500 bytes.

### Consumer Lag

Monitor consumer progress vs producer completion time.

---

## Troubleshooting

### Issue 1: "Connection refused: localhost:9092"

**Symptoms:**
```
Producer: Error: Connection refused
```

**Solutions:**
```bash
# Check if containers are running
docker-compose ps

# Restart Kafka
docker-compose restart kafka

# Check Kafka logs
docker-compose logs kafka

# Ensure port 9092 isn't in use
lsof -i :9092  # macOS/Linux
netstat -ano | findstr :9092  # Windows
```

### Issue 2: "Model file not found"

**Symptoms:**
```
Consumer: FileNotFoundError: Model file not found: logistic_model.pkl
```

**Solution:**
```bash
# Run training script
python train_models.py

# Verify files exist
ls -la logistic_model.pkl tfidf_vectorizer.pkl
```

### Issue 3: Database Locked

**Symptoms:**
```
Consumer: sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Kill any lingering processes
pkill -f "python consumer.py"

# Delete and recreate database
rm sentiment_db.sqlite

# Restart consumer
python consumer.py
```

### Issue 4: CSV File Not Found

**Symptoms:**
```
Producer: csv file not found: sentiment140_clean.csv
```

**Solution:**
```bash
# Verify file exists
ls -la sentiment140_clean.csv

# Or check in Python
import os
print(os.getcwd())  # Check current directory
```

### Issue 5: Port 8000 Already in Use

**Symptoms:**
```
API: Address already in use: ('0.0.0.0', 8000)
```

**Solution:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows (find PID first, then taskkill)

# Or use different port
uvicorn api:app --port 8001
```

---

## Graceful Shutdown

### Stop Everything

**Terminal A (Consumer):** Press `Ctrl+C`
```
^CConsumer interrupted by user
Consumer shut down. Total processed: 160000, Errors: 0
```

**Terminal B (Producer):** Already finished

**Terminal C (API):** Press `Ctrl+C`
```
^C
Shutdown complete.
```

**Stop Kafka:**
```bash
docker-compose down
```

### Verify Shutdown

```bash
docker-compose ps  # Should show no containers

ps aux | grep python  # Should show no python processes
```

---

## Next Steps

1. **Explore API**: Visit http://localhost:8000/docs
2. **Review Results**: Query database with provided SQL examples
3. **Customize**: 
   - Adjust `MESSAGE_DELAY` in producer for faster/slower processing
   - Modify ML model hyperparameters in `train_models.py`
   - Add custom endpoints in `api.py`

4. **Scale Up**:
   - Increase `RECORD_LIMIT` in producer
   - Add multiple consumer instances (requires consumer group coordination)
   - Use PostgreSQL instead of SQLite for production

---

## Performance Recommendations

| Setting | Value | Effect |
|---------|-------|--------|
| `MESSAGE_DELAY` | 0.01 | Faster streaming (10x) |
| Sample size | None | Train on all data |
| Kafka partitions | 3+ | Parallel consumption |
| API workers | 4 | Higher concurrency |

---

## Need Help?

1. Check logs in each terminal
2. Review Kafka connectivity: `docker-compose logs kafka`
3. Verify database: `sqlite3 sentiment_db.sqlite ".tables"`
4. Test API manually: `curl http://localhost:8000/api/v1/health`

---

**Last Updated**: January 2024
