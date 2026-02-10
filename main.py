from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors
import os
import traceback

# -------------------------------------------------
# Load environment variables from .env
# -------------------------------------------------
load_dotenv()

APP_NAME = os.getenv("APP_NAME", "AI Document Assistant")
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = os.getenv("APP_PORT", "8000")

# Prefer GEMINI_API_KEY, but support old LLM_API_KEY too
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY (or LLM_API_KEY) in .env")

# Model + API version
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")
# Gemini SDK uses v1beta by default; you can switch to stable v1 if you want
GEMINI_API_VERSION = os.getenv("GEMINI_API_VERSION", "v1beta")

# -------------------------------------------------
# Gemini client (google-genai)
# -------------------------------------------------
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(api_version=GEMINI_API_VERSION),
)

# -------------------------------------------------
# FastAPI app
# -------------------------------------------------
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

# -------------------------------------------------
# Global exception handler
# -------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"error": str(exc)})

# -------------------------------------------------
# Health check
# -------------------------------------------------
@app.get("/")
def health_check():
    return {
        "status": "ok",
        "env": os.getenv("APP_ENV", "unknown"),
        "api_version": GEMINI_API_VERSION,
        "model": DEFAULT_MODEL,
    }

# -------------------------------------------------
# List first N available models for your key
# -------------------------------------------------
@app.get("/models")
def list_models(limit: int = 30):
    items = []
    try:
        for m in client.models.list():
            items.append({
                "name": getattr(m, "name", None),  # often looks like "models/...."
                "base_model_id": getattr(m, "base_model_id", None),
                "display_name": getattr(m, "display_name", None),
                "supported_methods": getattr(m, "supported_generation_methods", None),
            })
            if len(items) >= limit:
                break
    except Exception as e:
        return {"error": str(e)}

    return {"count": len(items), "models": items}

# -------------------------------------------------
# Request DTO
# -------------------------------------------------
class AskRequest(BaseModel):
    input: str

# -------------------------------------------------
# LLM test endpoint
# -------------------------------------------------
@app.post("/ask")
def ask(request: AskRequest):
    try:
        resp = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=request.input,
            config=types.GenerateContentConfig(
                max_output_tokens=300,
                temperature=0.2,
                # Keep retries low while you're debugging quota problems
                http_options=types.HttpOptions(
                    retry_options=types.HttpRetryOptions(attempts=1)
                ),
            ),
        )
        return {"model": DEFAULT_MODEL, "answer": resp.text}

    except errors.ClientError as e:
        # Return the real status code (404/429/etc.) instead of always 500
        status_code = getattr(e, "code", 500) or 500

        headers = {}
        if status_code == 429:
            # Optional hint to clients
            headers["Retry-After"] = "60"

        return JSONResponse(
            status_code=status_code,
            content={"error": str(e), "model": DEFAULT_MODEL},
            headers=headers,
        )
    

    
