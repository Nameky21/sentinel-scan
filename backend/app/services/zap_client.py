from zapv2 import ZAPv2

from app.config import settings


class ZapUnavailableError(RuntimeError):
    """Raised when the ZAP daemon cannot be reached."""


def get_zap() -> ZAPv2:
    proxy = settings.zap_base_url
    return ZAPv2(apikey=settings.zap_api_key, proxies={"http": proxy, "https": proxy})


def get_version(zap: ZAPv2) -> str:
    try:
        return zap.core.version
    except Exception as exc:
        raise ZapUnavailableError(f"Could not reach ZAP at {settings.zap_base_url}: {exc}") from exc
