from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:latest"
    short_term_window: int = 50
    risk_anomaly_threshold: int = 65
    auto_act_threshold: int = 50
    human_approval_threshold: int = 80
    db_path: str = "db/logistics.sqlite"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
