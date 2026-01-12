from pgnotify import await_pg_notifications, get_dbapi_connection

from otto.core.logging import get_logger
from otto.core.settings import get_settings

CHANNELS = ["account-data-channel", "payroll-data-channel"]


def pg_listener() -> None:
    settings = get_settings()
    logger = get_logger(__name__)
    _url = settings.postgres.url.get_secret_value()
    _conn = get_dbapi_connection(_url)
    logger.info("Starting Postgres listener...")
    logger.info(f"Listening for Postgres notifications on {CHANNELS}...")
    for notification in await_pg_notifications(_conn, CHANNELS):
        logger.info(notification.channel)
        logger.info(notification.payload)
