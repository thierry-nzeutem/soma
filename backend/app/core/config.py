from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "SOMA"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://soma_user:soma_password@localhost:5432/soma"
    DATABASE_URL_SYNC: str = "postgresql://soma_user:soma_password@localhost:5432/soma"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    SECRET_KEY: str = "changeme-in-production-use-a-long-random-string-at-least-32-chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # AI / Claude Vision
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    # Mode mock : True = réponse simulée sans API (défaut développement)
    CLAUDE_VISION_MOCK_MODE: bool = True
    # Modèle à utiliser pour l'analyse photo repas
    CLAUDE_VISION_MODEL: str = "claude-opus-4-5"
    # Timeout en secondes pour les appels Claude Vision
    CLAUDE_VISION_TIMEOUT_S: int = 30

    # AI / Claude Coach (LOT 9)
    CLAUDE_COACH_MOCK_MODE: bool = True        # True = réponse simulée sans API
    CLAUDE_COACH_MODEL: str = "claude-sonnet-4-5"
    CLAUDE_COACH_MAX_TOKENS: int = 1024
    CLAUDE_COACH_TIMEOUT_S: int = 45
    CLAUDE_COACH_TEMPERATURE: float = 0.3

    # Storage
    STORAGE_PATH: str = "./data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    # Taille maximale des photos de repas (Mo)
    MAX_FOOD_PHOTO_SIZE_MB: int = 10
    # Types MIME acceptés pour les photos
    ALLOWED_PHOTO_MIME_TYPES: str = "image/jpeg,image/png,image/webp,image/heic"

    # Tests
    # URL PostgreSQL pour les tests d'intégration (si absente, les tests intégration sont skippés)
    TEST_DATABASE_URL: Optional[str] = None


settings = Settings()
