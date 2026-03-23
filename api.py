"""
API Module: FastAPI serving layer for sentiment analysis results.

This module provides REST endpoints for querying sentiment statistics
from the SQLite database populated by the consumer.

"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from consumer import SentimentRecord, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sentiment Analysis API",
    description="Real-time sentiment analysis statistics API",
    version="1.0.0"
)

# Database configuration
DATABASE_URL = 'sqlite:///sentiment_db.sqlite'
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# Create tables
Base.metadata.create_all(engine)


# Pydantic models for API responses
class SentimentStatsResponse(BaseModel):
    """Response model for sentiment statistics."""

    total_processed: int
    positive_count: int
    negative_count: int
    positive_percentage: float
    negative_percentage: float
    timestamp: datetime

    class Config:
        from_attributes = True


class SentimentDetailResponse(BaseModel):
    """Response model for recent sentiment records."""

    id: int
    text: str
    user: str
    sentiment_label: int
    confidence: float
    processed_at: datetime

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    """Response model for health check."""

    status: str
    database_connected: bool
    timestamp: datetime


# Utility functions
def get_db_session():
    """Create a database session."""
    return SessionLocal()


def calculate_sentiment_stats(session, hours: Optional[int] = None) -> dict:
    """
    Calculate sentiment statistics from database.

    Args:
        session: Database session
        hours: Filter records from last N hours (None for all)

    Returns:
        dict: Statistics including counts and percentages
    """
    try:
        query = session.query(SentimentRecord)

        # Filter by time if specified
        if hours:
            time_threshold = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(SentimentRecord.processed_at >= time_threshold)

        # Get counts
        total = query.count()
        positive = query.filter(SentimentRecord.sentiment_label == 1).count()
        negative = query.filter(SentimentRecord.sentiment_label == 0).count()

        # Calculate percentages
        positive_pct = (positive / total * 100) if total > 0 else 0.0
        negative_pct = (negative / total * 100) if total > 0 else 0.0

        return {
            'total_processed': total,
            'positive_count': positive,
            'negative_count': negative,
            'positive_percentage': round(positive_pct, 2),
            'negative_percentage': round(negative_pct, 2)
        }

    except Exception as e:
        logger.error(f"Error calculating sentiment stats: {e}")
        raise


# API Endpoints
@app.get("/api/v1/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint.

    Returns:
        HealthCheckResponse with status and database connectivity
    """
    try:
        session = get_db_session()
        try:
            # Try a simple query to verify database connectivity
            session.query(SentimentRecord).limit(1).all()
            db_connected = True
        except Exception as e:
            logger.error(f"Database connectivity check failed: {e}")
            db_connected = False
        finally:
            session.close()

        return HealthCheckResponse(
            status="healthy" if db_connected else "degraded",
            database_connected=db_connected,
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            database_connected=False,
            timestamp=datetime.utcnow()
        )


@app.get("/api/v1/sentiment/stats", response_model=SentimentStatsResponse)
async def get_sentiment_stats(hours: Optional[int] = Query(None)) -> SentimentStatsResponse:
    """
    Get sentiment analysis statistics.

    Query Parameters:
        hours: (Optional) Filter results from last N hours. If not provided,
               returns statistics for all processed data.

    Returns:
        SentimentStatsResponse with sentiment counts and percentages

    Raises:
        HTTPException: If database query fails
    """
    try:
        session = get_db_session()
        try:
            stats = calculate_sentiment_stats(session, hours=hours)

            time_filter_msg = f" (last {hours} hours)" if hours else " (all time)"
            logger.info(
                f"Sentiment stats retrieved: {stats['total_processed']} records"
                f"{time_filter_msg}"
            )

            return SentimentStatsResponse(
                total_processed=stats['total_processed'],
                positive_count=stats['positive_count'],
                negative_count=stats['negative_count'],
                positive_percentage=stats['positive_percentage'],
                negative_percentage=stats['negative_percentage'],
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error fetching sentiment stats: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching sentiment stats: {str(e)}"
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_sentiment_stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@app.get("/api/v1/sentiment/recent", response_model=list[SentimentDetailResponse])
async def get_recent_sentiments(
    limit: int = Query(10, ge=1, le=100),
    hours: Optional[int] = Query(None)
) -> list[SentimentDetailResponse]:
    """
    Get recent sentiment records.

    Query Parameters:
        limit: Maximum number of records to return (1-100, default: 10)
        hours: (Optional) Filter results from last N hours

    Returns:
        List of recent SentimentDetailResponse records

    Raises:
        HTTPException: If database query fails
    """
    try:
        session = get_db_session()
        try:
            query = session.query(SentimentRecord)

            # Filter by time if specified
            if hours:
                from datetime import datetime, timedelta
                time_threshold = datetime.utcnow() - timedelta(hours=hours)
                query = query.filter(SentimentRecord.processed_at >= time_threshold)

            # Get recent records
            records = query.order_by(
                SentimentRecord.processed_at.desc()
            ).limit(limit).all()

            logger.info(f"Retrieved {len(records)} recent sentiment records")

            return [
                SentimentDetailResponse(
                    id=r.id,
                    text=r.text,
                    user=r.user,
                    sentiment_label=r.sentiment_label,
                    confidence=r.confidence,
                    processed_at=r.processed_at
                )
                for r in records
            ]

        except Exception as e:
            logger.error(f"Error fetching recent sentiments: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching recent sentiments: {str(e)}"
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_recent_sentiments: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@app.get("/api/v1/sentiment/stats-by-user")
async def get_stats_by_user(limit: int = Query(10, ge=1, le=50)):
    """
    Get sentiment statistics grouped by user.

    Query Parameters:
        limit: Maximum number of users to return

    Returns:
        List of dictionaries with user and their sentiment statistics
    """
    try:
        session = get_db_session()
        try:
            results = session.query(
                SentimentRecord.user,
                func.count(SentimentRecord.id).label('total'),
                func.sum(
                    (SentimentRecord.sentiment_label == 1).cast(int)
                ).label('positive_count')
            ).group_by(
                SentimentRecord.user
            ).order_by(
                func.count(SentimentRecord.id).desc()
            ).limit(limit).all()

            user_stats = [
                {
                    'user': user,
                    'total_tweets': total,
                    'positive_tweets': positive_count or 0,
                    'negative_tweets': (total - (positive_count or 0)),
                    'positive_percentage': round(
                        ((positive_count or 0) / total * 100) if total > 0 else 0, 2
                    )
                }
                for user, total, positive_count in results
            ]

            logger.info(f"Retrieved sentiment stats for {len(user_stats)} users")
            return user_stats

        except Exception as e:
            logger.error(f"Error fetching stats by user: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching user statistics: {str(e)}"
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_stats_by_user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@app.get("/")
async def root():
    """
    Root endpoint with API information.

    Returns:
        Dictionary with API information and available endpoints
    """
    return {
        "service": "Sentiment Analysis API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/v1/health",
            "sentiment_stats": "/api/v1/sentiment/stats?hours=24",
            "recent_sentiments": "/api/v1/sentiment/recent?limit=10&hours=24",
            "stats_by_user": "/api/v1/sentiment/stats-by-user?limit=10",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }


# Error handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Handle generic exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return HTTPException(
        status_code=500,
        detail="Internal server error"
    )


if __name__ == '__main__':
    import uvicorn

    logger.info("Starting Sentiment Analysis API server...")
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
        log_level='info'
    )
