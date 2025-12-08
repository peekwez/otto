from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from otto.core.logging import get_logger


class PostgresConnectionError(Exception):
    """Custom exception for Postgres connection errors."""


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="POSTGRES__", case_sensitive=False, env_file_encoding="utf-8"
    )

    url: str
    schema_name: str

    def test_connection(self) -> None:
        """Test the Postgres connection."""
        import psycopg2
        from psycopg2 import sql

        logger = get_logger(__name__)
        logger.info("Testing Postgres connection...")
        try:
            conn = psycopg2.connect(self.url)
            cursor = conn.cursor()
            cursor.execute(sql.SQL("SELECT * FROM information_schema.tables"))
            rows = cursor.fetchall()
            logger.info(f"Connected to Postgres. Found {len(rows)}")
            conn.close()
            logger.info("Postgres connection successful.")
        except Exception as e:
            logger.error(f"Postgres connection failed: {e}")
            raise PostgresConnectionError(f"Failed to connect to Postgres: {e}") from e


class GoogleOAuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GOOGLE_OAUTH__", case_sensitive=False, env_file_encoding="utf-8"
    )
    client_id: str  # Type: MCP_CLIENT_ID env var
    client_secret: str  # Type: MCP_CLIENT_SECRET env var
    callback_path: str = "http://localhost:8000/cfo/callback"

    # Google OAuth URLs
    auth_url: str = "https://accounts.google.com/o/oauth2/auth"
    token_url: str = "https://oauth2.googleapis.com/token"

    scope: str = (
        "https://www.googleapis.com/auth/userinfo.email "
        "https://www.googleapis.com/auth/userinfo.profile openid"
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )
    host: str = "localhost"
    port: int = 8000
    server_url: AnyHttpUrl = AnyHttpUrl("http://localhost:8000")

    google_oauth: GoogleOAuthSettings
    postgres: PostgresSettings
