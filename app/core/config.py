from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "SoundVerse"
    database_url: str = ""
    force_sqlite_local: bool = False
    auto_sqlite_fallback: bool = True

    api_key: str

    @model_validator(mode="after")
    def resolve_database_url(self) -> "Settings":
        if self.force_sqlite_local:
            self.database_url = "sqlite:///./soundverse.db"
        elif not (self.database_url or "").strip():
            raise ValueError(
                "DATABASE_URL is required unless FORCE_SQLITE_LOCAL=1 "
                "(offline / DNS issues — uses ./soundverse.db)."
            )
        return self


settings = Settings()
