from pathlib import Path
from pydantic_settings import BaseSettings

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    groq_api_key: str
    qdrant_url: str = "http://localhost:6333"

    class Config:
        env_file = str(ENV_PATH) if ENV_PATH.exists() else ".env"


settings = Settings()