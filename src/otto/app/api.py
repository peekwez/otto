import contextlib

from fastapi import FastAPI

from otto.app.mcp import mcp


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code here
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())

        yield
    # Shutdown code here


app = FastAPI(
    name="demo_api",
    lifespan=lifespan,
)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


app.mount("/demo", mcp.streamable_http_app())


def run_app(host: str, port: int) -> None:
    import uvicorn

    uvicorn.run("otto.app.api:app", host=host, port=port, reload=True)
