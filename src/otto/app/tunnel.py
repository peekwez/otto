from pyngrok import conf, ngrok  # type: ignore

from otto.core.settings import get_settings

_public_url: str | None = None


def start_ngrok(address: str = "8000") -> str | None:
    global _public_url
    settings = get_settings()
    conf.get_default().auth_token = settings.ngrok.auth_token.get_secret_value()
    url = ngrok.connect(
        address, bind_tls=True, domain=settings.server_url.host
    ).public_url
    _public_url = url
    return url


def stop_ngrok() -> None:
    """Stop the ngrok tunnel."""
    global _public_url
    if _public_url:
        ngrok.disconnect(_public_url)  # type: ignore
        _public_url = None
    ngrok.kill()
