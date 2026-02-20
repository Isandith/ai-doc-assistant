from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import traceback

from app.core.config import APP_NAME, APP_HOST, APP_PORT, GEMINI_API_VERSION, DEFAULT_MODEL
from app.routers.health import router as health_router
from app.routers.models import router as models_router
from app.routers.ask import router as ask_router

app = FastAPI(title=APP_NAME)

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
app.include_router(health_router)
app.include_router(models_router)
app.include_router(ask_router)
