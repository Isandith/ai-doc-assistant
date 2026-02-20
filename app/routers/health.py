from fastapi import APIRouter
from app.core.config import GEMINI_API_VERSION, DEFAULT_MODEL, DATABASE_URL
from sqlmodel import text
import os

router = APIRouter(tags=["health"])

@router.get("/")
def health_check():
    return {
        "status": "ok",
        "env": os.getenv("APP_ENV", "unknown"),
        "api_version": GEMINI_API_VERSION,
        "model": DEFAULT_MODEL,
    }

@router.get("/db-test")
def test_database_connection():
    """Test database connection and return status"""
    try:
        from app.core.database import engine
        
        # Try to connect and execute a simple query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            
            # Get database name
            db_result = conn.execute(text("SELECT current_database();"))
            db_name = db_result.fetchone()[0]
        
        return {
            "status": "connected",
            "message": "Database connection successful",
            "database": db_name,
            "postgresql_version": version,
            "database_url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "N/A"  # Hide password
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": "Database connection failed",
            "error": str(e),
            "database_url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "N/A"
        }
