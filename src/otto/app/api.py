import contextlib
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from otto.app.mcp import initialize_datasets, mcp
from otto.core.logging import get_logger, patch_server_logging

_logger = get_logger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup code here
    async with contextlib.AsyncExitStack() as stack:
        initialize_datasets()
        await stack.enter_async_context(mcp.session_manager.run())

        yield
    # Shutdown code here


app = FastAPI(
    name="demo_mcp",
    lifespan=lifespan,
)


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"Hello": "World"}


app.mount("/cfo", mcp.streamable_http_app())


def run_app(host: str, port: int) -> None:
    import uvicorn

    patch_server_logging(_logger)

    uvicorn.run(
        "otto.app.api:app",
        # workers=4,
        host=host,
        port=port,
        log_config=None,
        log_level="info",
        reload=True,
        # loop="auto",
        # http="auto",
        # server_header=False,
    )
