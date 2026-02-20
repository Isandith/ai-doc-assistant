from fastapi import APIRouter
from app.core.gemini_client import client

router = APIRouter(prefix="/models", tags=["models"])

@router.get("")
def list_models(limit: int = 30):
    items = []
    for m in client.models.list():
        items.append({
            "name": getattr(m, "name", None),
            "base_model_id": getattr(m, "base_model_id", None),
            "display_name": getattr(m, "display_name", None),
            "supported_methods": getattr(m, "supported_generation_methods", None),
        })
        if len(items) >= limit:
            break

    return {"count": len(items), "models": items}
