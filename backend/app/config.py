from functools import lru_cache
from typing import Literal
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    app_env: Literal['local', 'test', 'demo', 'production'] = 'local'
    database_url: str = 'postgresql+psycopg://voluntia:voluntia_local@127.0.0.1:55432/voluntia'
    migration_database_url: str = ''
    jwt_secret: str = ''
    public_base_url: str = 'http://localhost:4200'
    public_signup_enabled: bool = True
    email_mode: Literal['smtp', 'disabled'] = 'smtp'
    smtp_host: str = '127.0.0.1'
    smtp_port: int = 1025
    smtp_user: str = ''
    smtp_password: str = ''
    smtp_from: str = 'no-reply@voluntia.test'
    smtp_tls: bool = False
    storage_backend: Literal['local', 'supabase'] = 'local'
    storage_path: str = '.local/storage'
    supabase_url: str = ''
    supabase_service_role_key: str = ''
    supabase_bucket: str = 'voluntia-demo-private'

    @model_validator(mode='after')
    def validate_environment(self):
        if len(self.jwt_secret) < 32:
            raise ValueError('Configurar JWT_SECRET aleatorio de al menos 32 caracteres')
        if self.public_signup_enabled and self.email_mode != 'smtp':
            raise ValueError('Registro abierto requiere SMTP operativo')
        if self.app_env in ('demo', 'production'):
            if not self.public_base_url.startswith('https://'):
                raise ValueError('Entorno remoto requiere HTTPS')
            if self.storage_backend != 'supabase':
                raise ValueError('Entorno remoto requiere Supabase Storage')
            if self.email_mode == 'smtp' and not self.smtp_tls:
                raise ValueError('SMTP remoto requiere TLS')
        if self.app_env == 'production' and self.email_mode != 'smtp':
            raise ValueError('Producción requiere correo configurado')
        if self.storage_backend == 'supabase' and not (self.supabase_url.startswith('https://') and self.supabase_service_role_key):
            raise ValueError('Configurar Supabase Storage en servidor')
        return self


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
