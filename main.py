from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

APP_NAME = os.getenv("APP_NAME", "AI Document Assistant")
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = os.getenv("APP_PORT", "8000")

app = FastAPI(title=APP_NAME)


@app.on_event("startup")
def print_swagger_urls():
    base_url = f"http://{APP_HOST}:{APP_PORT}"
    print("\n" + "=" * 50)
    print(f"🚀 {APP_NAME} is running")
    print(f"📄 Swagger UI: {base_url}/docs")
    print(f"📘 ReDoc UI : {base_url}/redoc")
    print("=" * 50 + "\n")


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "env": os.getenv("APP_ENV", "unknown")
    }
