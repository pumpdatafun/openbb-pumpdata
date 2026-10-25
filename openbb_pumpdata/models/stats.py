"""pumpdata.fun Stats Model: one UTC day on pump.fun (launches, graduations, volume), free for everyone."""

from datetime import date as dateType
from typing import Any

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.abstract.query_params import QueryParams
from pydantic import Field

from openbb_pumpdata.utils.client import get_json

PCT = {"x-unit_measurement": "percent", "x-frontend_multiply": 100}


class PumpdataStatsQueryParams(QueryParams):
    """pumpdata.fun Stats Query.

    Source: https://pumpdata.fun/stats (GET /stats.json, /stats/{day}.json)
    """

    day: dateType | None = Field(default=None, description="The UTC day. Default: yesterday, the newest whole day.")


class PumpdataStatsData(Data):
    """pumpdata.fun Stats Data: one row per day."""

    day: str = Field(description="The UTC day.")
    launched: int | None = Field(default=None, description="Coins launched on pump.fun.")
    graduated: int | None = Field(default=None, description="Coins that graduated to PumpSwap.")
    graduation_rate: float | None = Field(default=None, description="Graduated over launched.", json_schema_extra=PCT)
    volume_sol: float | None = Field(default=None, description="SOL traded, bonding curve and PumpSwap pools.")
    volume_usd: float | None = Field(default=None, description="The same in USD at each hour's SOL price.")
    volume_curve_sol: float | None = Field(default=None, description="SOL traded on bonding curves.")
    volume_pool_sol: float | None = Field(default=None, description="SOL traded in PumpSwap pools.")
    trades: int | None = Field(default=None, description="Trades counted.")
    traders_up: int | None = Field(default=None, description="Wallets that ended the day up.")
    traders_down: int | None = Field(default=None, description="Wallets that ended the day down.")
    sol_usd: float | None = Field(default=None, description="The day's SOL price used, USD.")
    headline: str | None = Field(default=None, description="The day in one line.")
    summary: str | None = Field(default=None, description="The day in a paragraph.")


class PumpdataStatsFetcher(Fetcher[PumpdataStatsQueryParams, list[PumpdataStatsData]]):
    """Fetch a day of pump.fun stats from pumpdata.fun."""

    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> PumpdataStatsQueryParams:
        """Transform the query."""
        return PumpdataStatsQueryParams(**params)

    @staticmethod
    async def aextract_data(query: PumpdataStatsQueryParams, credentials: dict[str, str] | None, **kwargs: Any) -> dict:
        """Return the raw answer."""
        return await get_json(f"/stats/{query.day.isoformat()}.json" if query.day else "/stats.json", credentials, **kwargs)

    @staticmethod
    def transform_data(query: PumpdataStatsQueryParams, data: dict, **kwargs: Any) -> list[PumpdataStatsData]:
        """One row."""
        t, m = data.get("totals") or {}, data.get("money") or {}
        return [
            PumpdataStatsData(
                day=data.get("day") or (query.day.isoformat() if query.day else ""),
                launched=t.get("launched"),
                graduated=t.get("graduated"),
                graduation_rate=t.get("graduation_rate"),
                volume_sol=t.get("volume_sol"),
                volume_usd=t.get("volume_usd"),
                volume_curve_sol=t.get("volume_curve_sol"),
                volume_pool_sol=t.get("volume_pool_sol"),
                trades=t.get("trades"),
                traders_up=m.get("traders_up"),
                traders_down=m.get("traders_down"),
                sol_usd=m.get("sol_usd"),
                headline=data.get("headline"),
                summary=data.get("summary"),
            )
        ]
