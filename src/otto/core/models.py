from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="POSTGRES__", case_sensitive=False, env_file_encoding="utf-8"
    )

    url: str
    schema_name: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )
    postgres: PostgresSettings
