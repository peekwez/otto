from functools import lru_cache

from dotenv import load_dotenv

from otto.core.models import Settings


@lru_cache
def get_settings(env_file: str = ".env") -> Settings:
    load_dotenv(env_file)
    return Settings()  # type: ignore
