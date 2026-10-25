"""pumpdata.fun HTTP client.

Every lookup has a free path with no key: ``/free`` in front of it (30 calls every five minutes and 300 a day per IP).
With a key (free at https://pumpdata.fun/keys, 2,000 calls a day) the same call goes to the path itself with an
``x-api-key`` header. A few answers are free for everyone and take neither: the coin check, the wallet leaderboard,
the daily stats.
"""

from typing import Any

from openbb_core.app.model.abstract.error import OpenBBError
from openbb_core.provider.utils.errors import EmptyDataError, UnauthorizedError
from openbb_core.provider.utils.helpers import amake_request

from openbb_pumpdata import __version__

BASE_URL = "https://pumpdata.fun"
KEYS_URL = "https://pumpdata.fun/keys"
USER_AGENT = f"openbb-pumpdata/{__version__} (+https://github.com/pumpdatafun/openbb-pumpdata)"

# answered free for everyone, key or not
OPEN_PATHS = ("/check/", "/wallets/top", "/stats")


def build_url(path: str, api_key: str | None) -> tuple[str, dict[str, str]]:
    """Return the URL and headers for a call: the free path without a key, the keyed path with one."""
    headers = {"accept": "application/json", "user-agent": USER_AGENT}
    if path.startswith(OPEN_PATHS):
        return BASE_URL + path, headers
    if api_key:
        headers["x-api-key"] = api_key
        return BASE_URL + path, headers
    return BASE_URL + "/free" + path, headers


def _why(body: Any, status: int) -> str:
    """The reason pumpdata.fun gave, as text."""
    if isinstance(body, dict):
        for k in ("why", "error", "reason"):
            v = body.get(k)
            if isinstance(v, str) and v:
                return v
            if isinstance(v, dict):
                return "; ".join(f"{a}: {b}" for a, b in v.items())
    return f"HTTP {status}"


async def get_json(
    path: str,
    credentials: dict[str, str] | None,
    method: str = "GET",
    json_body: Any = None,
    **kwargs: Any,
) -> Any:
    """Call pumpdata.fun and return the JSON answer.

    Raises
    ------
    UnauthorizedError
        The key is not known (401).
    EmptyDataError
        Nothing on record for the address or mint asked about (404).
    OpenBBError
        The free allowance is used (402, 429) or another error.
    """
    api_key = (credentials or {}).get("pumpdata_api_key") or None
    url, headers = build_url(path, api_key)
    if json_body is not None:
        headers["content-type"] = "application/json"

    async def callback(response, _session):
        status = response.status
        try:
            body = await response.json(content_type=None)
        except Exception:  # noqa: BLE001
            body = {"raw": (await response.text())[:300]}
        if status == 401:
            raise UnauthorizedError(f"pumpdata.fun: {_why(body, status)}. A free key: {KEYS_URL}")
        if status == 404:
            raise EmptyDataError(f"pumpdata.fun: {_why(body, status)}")
        if status in (402, 429):
            retry = response.headers.get("retry-after")
            more = (
                f" A free key has its own allowance of 2,000 calls a day: {KEYS_URL}"
                if not api_key
                else f" More: {KEYS_URL}"
            )
            raise OpenBBError(
                f"pumpdata.fun: {status}: {_why(body, status)}"
                + (f" (retry in {retry} s)." if retry else ".")
                + more
            )
        if status >= 400:
            raise OpenBBError(f"pumpdata.fun: {status}: {_why(body, status)}")
        return body

    return await amake_request(
        url,
        method=method,  # type: ignore[arg-type]
        timeout=30,
        headers=headers,
        response_callback=callback,
        **({"json": json_body} if json_body is not None else {}),
        **kwargs,
    )
