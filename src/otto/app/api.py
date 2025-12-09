import contextlib
from collections.abc import AsyncGenerator

import arrow
from fastapi import FastAPI

from otto.app.mcp import create_server, load_datasets
from otto.core.logging import get_logger

# from otto.core.settings import get_settings

logger = get_logger(__name__)
mcp = create_server()
start_time: arrow.Arrow = arrow.utcnow()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with contextlib.AsyncExitStack() as stack:
        load_datasets()
        await stack.enter_async_context(mcp.http_app().lifespan(app))
        logger.info("MCP application startup complete.")
        logger.info("Application startup complete.")
        yield


app = FastAPI(name="demo_mcp", lifespan=lifespan)


@app.get("/")
async def read_root() -> dict[str, str]:
    return {
        "name": "CFO Financial Planning MCP",
        "status": "running",
        "uptime": start_time.humanize(),
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.mount("/mcp", mcp.http_app())


def run_app(host: str, port: int) -> None:
    import uvicorn

    from otto.app.tunnel import start_ngrok, stop_ngrok
    from otto.core.logging import patch_server_logging

    _logger = get_logger(__name__)

    patch_server_logging(_logger)

    try:
        url = start_ngrok(f"{port}")
        _logger.info(f"ngrok tunnel started at {url}")
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            log_config=None,
        )
    except Exception as e:
        _logger.error(f"Error running FastAPI server: {e}")
    finally:
        _logger.info("Shutting down ngrok tunnel...")
        stop_ngrok()
