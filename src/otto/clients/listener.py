import json
import sys

from pgnotify import await_pg_notifications, get_dbapi_connection

from otto.clients.mail import send_mail
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
        # logger.info(f"Payload data: {payload}")

        # TODO: Process the notification payload as needed
        # do something with an agent. analyze breakeven or forecast
        # TODO: Send notification to other services or trigger workflows
        if channel == "payroll-data-channel" and payload["monthly"] >= 10000.00:
            data = json.dumps(payload, indent=2)
            send_mail(
                subject=f"High Payroll Alert: ${payload['monthly']}",
                content=(
                    f"<p>Received high payroll notification with payload"
                    f":</p><pre>{data}</pre>"
                ),
            )
