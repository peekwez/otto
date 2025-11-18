"""Logging configuration and utilities for the Otto application."""

from __future__ import annotations

import logging
import sys
import threading

import loguru
from loguru import logger

_loggers: dict[str, loguru.Logger] = {}
_handlers_configured = False
_loggers_lock = threading.RLock()


def get_logger(name: str, level: str = "info") -> loguru.Logger:
    """
    Get a logger instance with the specified settings.

    Args:
        name: The name of the logger.
        level: The logging level (default: "info").

    Returns:
        A logger instance configured with the provided settings.
    """
    global _loggers, _handlers_configured
    if name in _loggers:
        return _loggers[name]

    with _loggers_lock:
        if not _handlers_configured:
            logger.remove()  # Remove default logger
            logger.add(
                sys.stdout,
                level=level.upper(),
                format=(
                    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                    "<level>{level: <8}</level> | "
                    "{extra[source]}:{function}:{line} - "
                    "<level>{message}</level>"
                ),
                colorize=True,
                catch=True,
            )
            _handlers_configured = True

        bound_logger = logger.bind(name=name, source=name)
        _loggers[name] = bound_logger
        return bound_logger


def patch_server_logging(logger: loguru.Logger) -> None:
    """
    Patch standard library logging to use loguru for server components.

    This intercepts logs from uvicorn, fastapi, celery, and other server
    frameworks and redirects them through loguru for consistent formatting.

    Args:
        logger: The loguru logger instance to use for intercepted logs.
    """
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            # Get corresponding Loguru level
            level: str | int | None = None
            if (
                record.name.startswith(
                    (
                        "azure.core",
                        "azure.monitor",
                        "azure.identity",
                        "azure.eventhub",
                        "applicationinsights",
                    )
                )
                and record.levelname.lower() == "info"
            ):
                return

            try:
                level = logger.level(record.levelname).name
            except (ValueError, AttributeError):
                level = record.levelno

            source = f"{record.name}"

            logger.opt(depth=0, exception=record.exc_info).bind(
                name=record.name,
                source=source,
                function=record.funcName,
                line=record.lineno,
                module=record.module,
            ).log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)
    loggers = (
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "asyncio",
        "starlette",
        "celery",
        "celery.task",
        "celery.worker",
        "celery.app",
        "celery.app.trace",
    )

    for logger_name in loggers:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = []
        logging_logger.propagate = True
