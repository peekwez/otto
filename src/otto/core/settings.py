import threading

from dotenv import load_dotenv

from otto.core.logging import get_logger
from otto.core.models import Settings

_settings: Settings | None = None
_lock = threading.RLock()


def get_settings(env_file: str = ".env") -> Settings:
    global _settings
    if _settings is not None:
        return _settings

    with _lock:
        logger = get_logger(__name__)

        load_dotenv(env_file)
        logger.info("Loading env file..")

        _settings = Settings()  # type: ignore
        logger.info("Settings loaded...")

        _settings.postgres.test_connection()
    return _settings
