from typing import Literal

from pydantic import AnyHttpUrl, AnyUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from otto.core.logging import get_logger


class PostgresConnectionError(Exception):
    """Custom exception for Postgres connection errors."""


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="POSTGRES__",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    url: SecretStr
    schema_name: str

    def test_connection(self) -> None:
        """Test the Postgres connection."""
        import psycopg2
        from psycopg2 import sql

        logger = get_logger(__name__)
        logger.info("Testing Postgres connection...")
        try:
            conn = psycopg2.connect(self.url.get_secret_value())
            cursor = conn.cursor()
            cursor.execute(sql.SQL("SELECT * FROM information_schema.tables"))
            rows = cursor.fetchall()
            logger.info(f"Connected to Postgres. Found {len(rows)} tables...")
            conn.close()
            logger.info("Postgres connection successful...")
        except Exception as e:
            logger.error(f"Postgres connection failed: {e}")
            raise PostgresConnectionError(f"Failed to connect to Postgres: {e}") from e


class GoogleOAuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GOOGLE_OAUTH__",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore",
    )
    client_id: str  # Type: MCP_CLIENT_ID env var
    client_secret: SecretStr  # Type: MCP_CLIENT_SECRET env var
    callback_path: str = "/cfo/auth/callback"
    enable_auth: bool = True  # Set to False to disable authentication

    # Google OAuth URLs
    auth_url: str = "https://accounts.google.com/o/oauth2/auth"
    token_url: str = "https://oauth2.googleapis.com/token"

    scopes: str = (
        "https://www.googleapis.com/auth/userinfo.email,"
        "https://www.googleapis.com/auth/userinfo.profile,"
        "openid"
    )


class NgrokSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NGROK__",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore",
    )
    auth_token: SecretStr
    enable_tunnel: bool = True


class KeysSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ENCRYPTION_KEYS__",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore",
    )
    storage_encryption_key: SecretStr
    jwt_signing_key: SecretStr


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="REDIS__",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore",
    )
    host: AnyUrl = AnyUrl("redis://localhost")
    port: int = 6379


class SendGridSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SENDGRID__",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore",
    )
    api_key: SecretStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )
    stage: Literal["dev", "stage", "prod"] = "prod"
    server_url: AnyHttpUrl = AnyHttpUrl("http://localhost:8000")

    google_oauth: GoogleOAuthSettings
    postgres: PostgresSettings
    ngrok: NgrokSettings
    keys: KeysSettings
    sendgrid: SendGridSettings
    redis: RedisSettings = RedisSettings()
