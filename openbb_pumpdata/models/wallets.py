"""pumpdata.fun Wallets Models: what wallets did on pump.fun (a class with its reason, and PnL), and the leaderboard."""

from typing import Any

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.abstract.query_params import QueryParams
from pydantic import Field, field_validator

from openbb_pumpdata.utils.client import get_json
from openbb_pumpdata.utils.helpers import check_address, dig

PCT = {"x-unit_measurement": "percent", "x-frontend_multiply": 100}


class PumpdataWalletsQueryParams(QueryParams):
    """pumpdata.fun Wallets Query.

    Source: https://pumpdata.fun/pump-fun-api (POST /wallets)
    """

    __json_schema_extra__ = {"addresses": {"multiple_items_allowed": True}}

    addresses: str = Field(description="One or more wallet addresses, comma-separated (up to 50).")
    mint: str | None = Field(
        default=None, description="A coin's mint: a wallet whose record starts after this coin's launch is classed `new`."
    )

    @field_validator("addresses", mode="before")
    @classmethod
    def _addresses(cls, v: str | list[str]) -> str:
        items = v if isinstance(v, list) else str(v).split(",")
        out = list(dict.fromkeys(check_address(a, "addresses") for a in items if str(a).strip()))
        if not out:
            raise ValueError("addresses: at least one wallet address")
        if len(out) > 50:
            raise ValueError("addresses: at most 50 in one call")
        return ",".join(out)

    @field_validator("mint", mode="before")
    @classmethod
    def _mint(cls, v: str | None) -> str | None:
        return check_address(v, "mint") if v else None


class PumpdataWalletData(Data):
    """pumpdata.fun Wallet Data: one row per wallet."""

    address: str = Field(description="The wallet address.")
    wallet_class: str | None = Field(
        default=None, description="winner, net_loser, bot, supply_seller, new or none: a rule over its whole pump.fun record."
    )
    why: str | None = Field(default=None, description="The rule that placed it in its class.")
    pnl_sol: float | None = Field(default=None, description="SOL taken out minus SOL put in, over its whole record.")
    put_in: float | None = Field(default=None, description="SOL paid on buys.")
    took_out: float | None = Field(default=None, description="SOL received on sells.")
    coins: int | None = Field(default=None, description="Coins it traded.")
    first_seen: str | None = Field(default=None, description="Its first pump.fun trade, UTC.")
    trades_per_day: float | None = Field(default=None, description="Its pace over the tables' last 20 days.")
    median_hold_s: float | None = Field(default=None, description="Median seconds from a coin's first buy to its first sell.")
    snipe_share: float | None = Field(default=None, description="The share of its new coins bought in their create block or the next.", json_schema_extra=PCT)


def _wallet_row(address: str, w: dict) -> dict:
    return {
        "address": address,
        "wallet_class": w.get("class"),
        "why": w.get("why"),
        "pnl_sol": w.get("pnl_sol"),
        "put_in": w.get("put_in"),
        "took_out": w.get("took_out"),
        "coins": w.get("coins"),
        "first_seen": w.get("first_seen"),
        "trades_per_day": dig(w, "recent", "trades_per_day"),
        "median_hold_s": dig(w, "recent", "median_hold_s"),
        "snipe_share": dig(w, "recent", "snipe_share"),
    }


class PumpdataWalletsFetcher(Fetcher[PumpdataWalletsQueryParams, list[PumpdataWalletData]]):
    """Fetch wallet records from pumpdata.fun."""

    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> PumpdataWalletsQueryParams:
        """Transform the query."""
        return PumpdataWalletsQueryParams(**params)

    @staticmethod
    async def aextract_data(query: PumpdataWalletsQueryParams, credentials: dict[str, str] | None, **kwargs: Any) -> dict:
        """Return the raw answer."""
        body: dict[str, Any] = {"addresses": query.addresses.split(",")}
        if query.mint:
            body["mint"] = query.mint
        return await get_json("/wallets", credentials, method="POST", json_body=body, **kwargs)

    @staticmethod
    def transform_data(query: PumpdataWalletsQueryParams, data: dict, **kwargs: Any) -> list[PumpdataWalletData]:
        """One row per wallet asked about, in the order asked."""
        return [
            PumpdataWalletData.model_validate(_wallet_row(a, data[a]))
            for a in query.addresses.split(",")
            if isinstance(data.get(a), dict)
        ]


class PumpdataTopWalletsQueryParams(QueryParams):
    """pumpdata.fun Top Wallets Query.

    Source: https://pumpdata.fun/pump-fun-copy-trading (GET /wallets/top)
    """

    followable: bool = Field(
        default=True, description="Only winners that still trade, at a pace a copier can keep (not bots, not supply sellers)."
    )
    limit: int = Field(default=25, ge=1, le=100, description="How many wallets.")


class PumpdataTopWalletData(PumpdataWalletData):
    """pumpdata.fun Top Wallet Data: one row per wallet on the leaderboard."""

    rank: int | None = Field(default=None, description="Its rank by PnL over its whole record.")
    followable: bool | None = Field(default=None, description="Still trades, at a pace a copier can keep.")


class PumpdataTopWalletsFetcher(Fetcher[PumpdataTopWalletsQueryParams, list[PumpdataTopWalletData]]):
    """Fetch the pump.fun wallet leaderboard from pumpdata.fun (free for everyone)."""

    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> PumpdataTopWalletsQueryParams:
        """Transform the query."""
        return PumpdataTopWalletsQueryParams(**params)

    @staticmethod
    async def aextract_data(query: PumpdataTopWalletsQueryParams, credentials: dict[str, str] | None, **kwargs: Any) -> dict:
        """Return the raw answer."""
        return await get_json(f"/wallets/top?followable={1 if query.followable else 0}&limit={query.limit}", credentials, **kwargs)

    @staticmethod
    def transform_data(query: PumpdataTopWalletsQueryParams, data: dict, **kwargs: Any) -> list[PumpdataTopWalletData]:
        """One row per wallet."""
        return [
            PumpdataTopWalletData.model_validate(_wallet_row(w.get("address"), w) | {"rank": w.get("rank"), "followable": w.get("followable")})
            for w in (data.get("wallets") or [])[: query.limit]
        ]
