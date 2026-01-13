import json
import sys

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
        channel = notification.channel
        payload = json.loads(notification.payload)
        num_columns = len(payload.keys())
        data_size = sys.getsizeof(notification.payload)
        logger.info(
            f"Received Postgres notification from channel: "
            f"{channel}, columns: {num_columns}, size: {data_size} bytes"
        )
        logger.info(f"Payload data: {payload}")
