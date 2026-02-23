import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "AI Document Assistant")
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = os.getenv("APP_PORT", "8000")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY (or LLM_API_KEY) in .env")

DEFAULT_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")
GEMINI_API_VERSION = os.getenv("GEMINI_API_VERSION", "v1beta")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/ai_doc_assistant")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ai_doc_assistant")
DB_USER = os.getenv("DB_USER", "username")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-key.json")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "your-firebase-project")

# Development Mode - Skip authentication
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
