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
    type=click.Path(exists=True),
    default=".env",
    help="Path to the .env file",
)
def app(host: str, port: int, env_file: str) -> None:
    """Run the Otto API server."""
    from otto.app.api import run_app
    from otto.core.settings import get_settings

    get_settings(env_file)
    run_app(host, port)


if __name__ == "__main__":
    cli()
