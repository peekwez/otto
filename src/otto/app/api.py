import contextlib
from collections.abc import AsyncGenerator

from fastapi import FastAPI

# from otto.app.auth import app as auth_router
from otto.app.mcp import load_datasets, mcp_app
from otto.core.logging import get_logger

logger = get_logger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with contextlib.AsyncExitStack() as stack:
        load_datasets()
        await stack.enter_async_context(mcp_app.lifespan(app))
        logger.info("MCP application startup complete.")
        logger.info("Application startup complete.")
        yield


app = FastAPI(name="demo_mcp", lifespan=lifespan)


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"Hello": "World"}


app.mount("/cfo", mcp_app)
# app.include_router(auth_router, prefix="/auth", tags=["auth"])


def run_app(host: str, port: int) -> None:
    import uvicorn

    from otto.core.logging import patch_server_logging

    _logger = get_logger(__name__)

    patch_server_logging(_logger)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        log_config=None,
    )
