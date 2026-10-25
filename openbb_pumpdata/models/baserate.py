"""pumpdata.fun Base Rate Model: of the coins that crossed a market-cap band, the share that went on to 2x, 5x, 10x, 20x."""

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.abstract.query_params import QueryParams
from pydantic import Field

from openbb_pumpdata.utils.client import get_json

PCT = {"x-unit_measurement": "percent", "x-frontend_multiply": 100}
BANDS = ("5k-10k", "10k-15k", "15k-20k", "15k-28k", "20k-28k", "28k-40k", "40k-60k", "60k-100k", "100k-250k", "250k-1000k")


class PumpdataBaseRateQueryParams(QueryParams):
    """pumpdata.fun Base Rate Query.

    Source: https://pumpdata.fun/pump-fun-api (GET /baserate)
    """

    band: str = Field(default="15k-28k", description=f"The market-cap band in USD, one of: {', '.join(BANDS)}.")
    start_date: datetime | None = Field(
        default=None, description="Start of the window (UTC). Default: four days before the end."
    )
    end_date: datetime | None = Field(
        default=None, description="End of the window (UTC). Default: three hours ago (a crossing's peak is read over the three hours after it)."
    )
    venue: Literal["any", "curve", "pool"] = Field(default="any", description="Crossings on the bonding curve, in PumpSwap pools, or either.")


class PumpdataBaseRateData(Data):
    """pumpdata.fun Base Rate Data: one row."""

    band: str = Field(description="The market-cap band in USD.")
    start_date: str | None = Field(default=None, description="Start of the window, UTC.")
    end_date: str | None = Field(default=None, description="End of the window, UTC.")
    venue: str | None = Field(default=None, description="The venue counted.")
    crossed: int | None = Field(default=None, description="Coins whose first trade inside the band fell in the window.")
    reached_2x: float | None = Field(default=None, description="The share whose peak in the next three hours reached 2x the band's crossing value.", json_schema_extra=PCT)
    reached_5x: float | None = Field(default=None, description="The share that reached 5x.", json_schema_extra=PCT)
    reached_10x: float | None = Field(default=None, description="The share that reached 10x.", json_schema_extra=PCT)
    reached_20x: float | None = Field(default=None, description="The share that reached 20x.", json_schema_extra=PCT)
    median_peak: float | None = Field(default=None, description="The median peak, as a multiple of the crossing value.")


def _iso(d: datetime) -> str:
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class PumpdataBaseRateFetcher(Fetcher[PumpdataBaseRateQueryParams, list[PumpdataBaseRateData]]):
    """Fetch a market-cap band's base rate from pumpdata.fun."""

    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> PumpdataBaseRateQueryParams:
        """Transform the query: a window ending three hours ago, four days long, unless given."""
        q = PumpdataBaseRateQueryParams(**params)
        if q.end_date is None:
            q.end_date = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(hours=3)
        if q.start_date is None:
            q.start_date = q.end_date - timedelta(days=4)
        return q

    @staticmethod
    async def aextract_data(query: PumpdataBaseRateQueryParams, credentials: dict[str, str] | None, **kwargs: Any) -> dict:
        """Return the raw answer."""
        path = f"/baserate?band={query.band}&from={_iso(query.start_date)}&to={_iso(query.end_date)}&venue={query.venue}"  # type: ignore[arg-type]
        return await get_json(path, credentials, **kwargs)

    @staticmethod
    def transform_data(query: PumpdataBaseRateQueryParams, data: dict, **kwargs: Any) -> list[PumpdataBaseRateData]:
        """One row."""
        r = data.get("reached") or {}
        return [
            PumpdataBaseRateData(
                band=data.get("band") or query.band,
                start_date=data.get("from"),
                end_date=data.get("to"),
                venue=data.get("venue"),
                crossed=data.get("crossed"),
                reached_2x=r.get("2x"),
                reached_5x=r.get("5x"),
                reached_10x=r.get("10x"),
                reached_20x=r.get("20x"),
                median_peak=data.get("median_peak"),
            )
        ]
