from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_PATH), env_file_encoding="utf-8")

    ENCRYPTION_KEY: str = Field(..., min_length=1)
    COOKIE_KEY: str = Field(..., min_length=1)

    GEMINI_API_KEY: Optional[str] = None
    IOL_USERNAME: Optional[str] = None
    IOL_PASSWORD: Optional[str] = None
    IOL_API_URL: str = "https://api.invertironline.com"
    ADMIN_PASSWORD: Optional[str] = None


class SettingsError(RuntimeError):
    pass


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        missing = []
        for err in exc.errors():
            if err.get("type") == "missing":
                loc = err.get("loc") or []
                if loc:
                    missing.append(str(loc[0]))
        missing_vars = ", ".join(sorted(set(missing))) if missing else "variables requeridas"
        message = (
            f"Faltan variables de entorno requeridas: {missing_vars}.\n"
            "Genera ENCRYPTION_KEY con:\n"
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"\n"
            "Definí COOKIE_KEY con una cadena segura."
        )
        raise SettingsError(message) from exc
