import click


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--host", "-h", default="localhost", help="API host name")
@click.option("--port", "-p", default=8000, help="API port number")
@click.option(
    "--env-file",
    "-e",
    type=click.Path(exists=False),
    default=None,
    help="Path to the .env file",
)
def app(host: str, port: int, env_file: str | None) -> None:
    """Run the Otto API server."""

    from otto.core.settings import get_settings

    get_settings(env_file)

    from otto.app.mcp import run_app

    run_app(host, port)


@cli.command()
@click.option(
    "--env-file",
    "-e",
    type=click.Path(exists=False),
    default=None,
    help="Path to the .env file",
)
def listener(env_file: str | None) -> None:
    """Run the Otto postgres listener app."""

    from otto.core.settings import get_settings

    get_settings(env_file)

    from otto.rt.pg import pg_listener

    pg_listener()


@cli.command("test-client")
def test_client() -> None:
    """Test the MCP OAuth client flow."""
    # from otto.core.settings import get_settings

    # get_settings(env_file)
    import asyncio

    from otto.app.client import connect as connect_client

    asyncio.run(connect_client())


if __name__ == "__main__":
    cli()
