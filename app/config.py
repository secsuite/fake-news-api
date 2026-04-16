"""Application settings loaded from environment variables and .env."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration object."""

    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    DEBUG: bool = False
    PRELOAD_MODELS_ON_STARTUP: bool = False

    MODEL_DIR: str = str(Path(__file__).resolve().parent / "ml" / "models" / "fake_news")
    MODEL_ONNX_FILE: str = "model.onnx"

    INFERENCE_MAX_LENGTH: int = 512
    INFERENCE_THRESHOLD: float = 0.5

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }

    def ensure_directories(self) -> None:
        Path(self.MODEL_DIR).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
