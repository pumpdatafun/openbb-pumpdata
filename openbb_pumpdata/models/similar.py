"""pumpdata.fun Similar Model: the past launches most like a coin, and what each did next."""

from typing import Any

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.abstract.query_params import QueryParams
from pydantic import Field, field_validator

from openbb_pumpdata.utils.client import get_json
from openbb_pumpdata.utils.helpers import check_address, dig


class PumpdataSimilarQueryParams(QueryParams):
    """pumpdata.fun Similar Query.

    Source: https://pumpdata.fun/pump-fun-api (GET /similar/{mint})
    """

    mint: str = Field(description="The coin's mint address.")
    limit: int = Field(default=10, ge=1, le=50, description="How many comparable launches to return.")

    @field_validator("mint", mode="before")
    @classmethod
    def _mint(cls, v: str) -> str:
        return check_address(v, "mint")


class PumpdataSimilarData(Data):
    """pumpdata.fun Similar Data: one row per comparable launch."""

    mint: str = Field(description="The comparable launch's mint address.")
    created: str | None = Field(default=None, description="When it was launched, UTC.")
    deployer: str | None = Field(default=None, description="The wallet that launched it.")
    same_deployer: bool | None = Field(default=None, description="Launched by the same wallet as the coin asked about.")
    market_cap_usd_at_5m: float | None = Field(default=None, description="Its market cap at minute five, USD.")
    buyers_first_10s: int | None = Field(default=None, description="Distinct wallets that bought in its first 10 seconds.")
    graduated_by_5m: bool | None = Field(default=None, description="Graduated by minute five.")
    peak_mult_24h: float | None = Field(default=None, description="Highest market cap in the 24 hours after minute five, over minute five's.")
    close_mult_24h: float | None = Field(default=None, description="Market cap at the end of those 24 hours, over minute five's.")
    dead_next_day: bool | None = Field(default=None, description="No priced trade in those 24 hours.")
    similar_because: str | None = Field(default=None, description="Why it was matched.")


class PumpdataSimilarFetcher(Fetcher[PumpdataSimilarQueryParams, list[PumpdataSimilarData]]):
    """Fetch the comparable launches for a coin from pumpdata.fun."""

    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> PumpdataSimilarQueryParams:
        """Transform the query."""
        return PumpdataSimilarQueryParams(**params)

    @staticmethod
    async def aextract_data(query: PumpdataSimilarQueryParams, credentials: dict[str, str] | None, **kwargs: Any) -> dict:
        """Return the raw answer."""
        return await get_json(f"/similar/{query.mint}?limit={query.limit}", credentials, **kwargs)

    @staticmethod
    def transform_data(query: PumpdataSimilarQueryParams, data: dict, **kwargs: Any) -> list[PumpdataSimilarData]:
        """One row per comparable."""
        return [
            PumpdataSimilarData(
                mint=c.get("mint"),
                created=c.get("created"),
                deployer=c.get("deployer"),
                same_deployer=c.get("same_deployer"),
                market_cap_usd_at_5m=dig(c, "at_5m", "market_cap_usd"),
                buyers_first_10s=dig(c, "at_5m", "buyers_first_10s"),
                graduated_by_5m=dig(c, "at_5m", "graduated"),
                peak_mult_24h=dig(c, "next_24h", "peak_mult"),
                close_mult_24h=dig(c, "next_24h", "close_mult"),
                dead_next_day=dig(c, "next_24h", "dead"),
                similar_because=c.get("similar_because"),
            )
            for c in (data.get("comparables") or [])[: query.limit]
        ]
