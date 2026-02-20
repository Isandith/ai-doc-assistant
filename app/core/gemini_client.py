from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY, GEMINI_API_VERSION

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(api_version=GEMINI_API_VERSION),
)
