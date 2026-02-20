from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from google.genai import types, errors

from app.core.gemini_client import client
from app.core.config import DEFAULT_MODEL

router = APIRouter(prefix="/ask", tags=["ask"])

class AskRequest(BaseModel):
    input: str

@router.post("")
def ask(request: AskRequest):
    try:
        resp = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=request.input,
            config=types.GenerateContentConfig(
                max_output_tokens=300,
                temperature=0.2,
                http_options=types.HttpOptions(
                    retry_options=types.HttpRetryOptions(attempts=1)
                ),
            ),
        )
        return {"model": DEFAULT_MODEL, "answer": resp.text}

    except errors.ClientError as e:
        status_code = getattr(e, "code", 500) or 500
        headers = {"Retry-After": "60"} if status_code == 429 else {}
        return JSONResponse(
            status_code=status_code,
            content={"error": str(e), "model": DEFAULT_MODEL},
            headers=headers,
        )
