from functools import lru_cache
from typing import Literal
from pydantic import model_validator, Field
from urllib.parse import urlsplit
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", hide_input_in_errors=True
    )
    app_env: Literal["local", "test", "demo", "production"] = "local"
    database_url: str = Field(
        default="postgresql+psycopg://voluntia:voluntia_local@127.0.0.1:55432/voluntia",
        repr=False,
    )
    migration_database_url: str = Field(default="", repr=False)
    jwt_secret: str = Field(default="", repr=False)
    public_base_url: str = "http://localhost:4200"
    public_signup_enabled: bool = True
    email_mode: Literal["smtp", "disabled"] = "smtp"
    smtp_host: str = "127.0.0.1"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = Field(default="", repr=False)
    smtp_from: str = "no-reply@voluntia.test"
    smtp_tls: bool = False
    storage_backend: Literal["local", "supabase"] = "local"
    storage_path: str = ".local/storage"
    supabase_url: str = ""
    supabase_service_role_key: str = Field(default="", repr=False)
    supabase_bucket: str = "voluntia-demo-private"

    @model_validator(mode="after")
    def validate_environment(self):
        for value in (self.database_url, self.migration_database_url):
            if not value:
                continue
            try:
                target = make_url(value)
            except Exception:
                raise ValueError(
                    "URL PostgreSQL inválida; revisar configuración privada"
                ) from None
            if target.drivername != "postgresql+psycopg":
                raise ValueError("Usar el driver postgresql+psycopg")
            local = target.host in ("localhost", "127.0.0.1", "::1", "db", "postgres")
            if not local and target.query.get("sslmode") not in (
                "require",
                "verify-ca",
                "verify-full",
            ):
                raise ValueError("Toda conexión PostgreSQL remota requiere TLS")
            if (
                target.host
                and target.host.endswith(".pooler.supabase.com")
                and target.port != 5432
            ):
                raise ValueError(
                    "Voluntia requiere Session pooler de Supabase en puerto 5432"
                )
        origin = urlsplit(self.public_base_url)
        if (
            origin.scheme not in ("http", "https")
            or not origin.hostname
            or origin.username
            or origin.password
            or origin.path not in ("", "/")
            or origin.query
            or origin.fragment
        ):
            raise ValueError(
                "PUBLIC_BASE_URL debe ser un origen HTTP(S) sin ruta, credenciales ni query"
            )
        if self.storage_backend == "supabase":
            storage = urlsplit(self.supabase_url)
            if (
                storage.scheme != "https"
                or not storage.hostname
                or storage.username
                or storage.password
                or storage.path not in ("", "/")
                or storage.query
                or storage.fragment
            ):
                raise ValueError("SUPABASE_URL debe ser el origen HTTPS del proyecto")
        if len(self.jwt_secret) < 32:
            raise ValueError(
                "Configurar JWT_SECRET aleatorio de al menos 32 caracteres"
            )
        if self.public_signup_enabled and self.email_mode != "smtp":
            raise ValueError("Registro abierto requiere SMTP operativo")
        if self.app_env in ("demo", "production"):
            target = make_url(self.database_url)
            if (
                target.host in ("localhost", "127.0.0.1", "::1", "db", "postgres", None)
                or not target.username
                or not target.password
            ):
                raise ValueError(
                    "Entorno remoto requiere conexión dedicada con credenciales de ejecución"
                )
            if target.query.get("sslmode") not in (
                "require",
                "verify-ca",
                "verify-full",
            ):
                raise ValueError("Entorno remoto requiere TLS PostgreSQL")
            if self.migration_database_url == self.database_url:
                raise ValueError("Separar credenciales de migración y ejecución")
            if not self.public_base_url.startswith("https://"):
                raise ValueError("Entorno remoto requiere HTTPS")
            if self.storage_backend != "supabase":
                raise ValueError("Entorno remoto requiere Supabase Storage")
            if self.email_mode == "smtp" and not self.smtp_tls:
                raise ValueError("SMTP remoto requiere TLS")
        if self.app_env == "production" and self.email_mode != "smtp":
            raise ValueError("Producción requiere correo configurado")
        if self.storage_backend == "supabase" and not (
            self.supabase_url.startswith("https://") and self.supabase_service_role_key
        ):
            raise ValueError("Configurar Supabase Storage en servidor")
        if (
            self.storage_backend == "supabase"
            and self.supabase_service_role_key.startswith("sb_publishable_")
        ):
            raise ValueError("Storage requiere una clave secreta de servidor")
        self.public_base_url = self.public_base_url.rstrip("/")
        self.supabase_url = self.supabase_url.rstrip("/")
        return self


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
