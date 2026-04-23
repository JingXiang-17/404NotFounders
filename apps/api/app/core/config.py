from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    MODEL_API_KEY: str
    MODEL_BASE_URL: str
    MODEL_NAME: str
    
    SQLITE_PATH: str = "sqlite:///./lintasniaga.db"
    
    # Directories
    UPLOAD_DIR: Path = Path("data/uploads")
    DATA_DIR: Path = Path("data")
    SNAPSHOT_DIR: Path = Path("data/snapshots")
    RAW_ARTIFACT_DIR: Path = Path("data/raw")
    REFERENCE_DIR: Path = Path("data/reference")
    
    # Langfuse
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = ""
    
    # External APIs
    OPENWEATHER_API_KEY: str = ""
    
    # Resilience
    USE_LAST_VALID_SNAPSHOT_ON_FAILURE: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
