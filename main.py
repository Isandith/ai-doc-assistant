from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import traceback

from app.core.config import APP_NAME, APP_HOST, APP_PORT, GEMINI_API_VERSION, DEFAULT_MODEL
from app.core.database import create_db_and_tables
from app.routers.health import router as health_router
from app.routers.models import router as models_router
from app.routers.ask import router as ask_router
from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router
from app.routers.chat import router as chat_router

app = FastAPI(title=APP_NAME)

# Create database tables on startup
@app.on_event("startup")
def startup_event():
    create_db_and_tables()

# Add CORS middleware to allow Swagger UI to load
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def print_swagger_urls():
    base_url = f"http://{APP_HOST}:{APP_PORT}"
    print("\n" + "=" * 50)
    print(f"{APP_NAME} is running")
    print(f"Swagger UI: {base_url}/docs")
    print(f"ReDoc UI : {base_url}/redoc")
    print(f"Gemini API version: {GEMINI_API_VERSION}")
    print(f"Default model: {DEFAULT_MODEL}")
    print("=" * 50 + "\n")

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"error": str(exc)})

# plug in endpoints from other files
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(models_router)
app.include_router(ask_router)
app.include_router(documents_router)
app.include_router(chat_router)
