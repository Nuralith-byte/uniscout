from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Все настройки через переменные окружения или backend/.env (см. .env.example)."""

    env: str = "dev"  # dev | prod
    database_url: str = "sqlite:///./dev.db"  # в проде: postgresql+psycopg://... (Supabase)
    cors_origins: str = "http://localhost:5173"
    supabase_jwt_secret: str = ""  # Project Settings -> API -> JWT Secret
    admin_api_key: str = "dev-admin-key"
    sheet_csv_urls: str = ""  # CSV-export URL вкладок Google Sheet через запятую

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
