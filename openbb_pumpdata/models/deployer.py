"""pumpdata.fun Deployer Model: a pump.fun deployer's whole launch record."""

from typing import Any

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.abstract.query_params import QueryParams
from pydantic import Field, field_validator

from openbb_pumpdata.utils.client import get_json
from openbb_pumpdata.utils.helpers import check_address, dig


class PumpdataDeployerQueryParams(QueryParams):
    """pumpdata.fun Deployer Query.

    Source: https://pumpdata.fun/pump-fun-api (GET /deployer/{address})
    """

    address: str = Field(description="The deployer's wallet address (the wallet that launched the coins).")

    @field_validator("address", mode="before")
    @classmethod
    def _address(cls, v: str) -> str:
        return check_address(v, "address")


class PumpdataDeployerData(Data):
    """pumpdata.fun Deployer Data: one row, the deployer's record and its next launch's base rate."""

    address: str = Field(description="The deployer's wallet address.")
    launches: int | None = Field(default=None, description="Every pump.fun launch on record.")
    graduations: int | None = Field(default=None, description="Launches that graduated to PumpSwap.")
    graduation_rate: float | None = Field(
        default=None, description="Graduations over launches.", json_schema_extra={"x-unit_measurement": "percent", "x-frontend_multiply": 100}
    )
    best_peak_usd: float | None = Field(default=None, description="The highest first-day peak market cap of its launches, USD.")
    last_launch_gap_s: int | None = Field(default=None, description="Seconds between its last two launches.")
    launches_last_day: int | None = Field(default=None, description="Launches in the last day of the tables' build.")
    last_launch: str | None = Field(default=None, description="Its latest launch, UTC.")
    launches_measured_90d: int | None = Field(default=None, description="Its launches of the last 90 days measured at minute five.")
    doubled_share_90d: float | None = Field(
        default=None, description="Of those, the share that doubled in the 24 hours after minute five.", json_schema_extra={"x-unit_measurement": "percent", "x-frontend_multiply": 100}
    )
    ten_x_share_90d: float | None = Field(
        default=None, description="The share that did ten times.", json_schema_extra={"x-unit_measurement": "percent", "x-frontend_multiply": 100}
    )
    held_2x_share_90d: float | None = Field(
        default=None, description="The share still at double at the end of those 24 hours.", json_schema_extra={"x-unit_measurement": "percent", "x-frontend_multiply": 100}
    )
    dead_share_90d: float | None = Field(
        default=None, description="The share with no priced trade in those 24 hours.", json_schema_extra={"x-unit_measurement": "percent", "x-frontend_multiply": 100}
    )
    next_launch_doubled_share: float | None = Field(
        default=None,
        description="Base rate for its next launch: the share of the last 90 days' launches by deployers with the same record that doubled.",
        json_schema_extra={"x-unit_measurement": "percent", "x-frontend_multiply": 100},
    )
    next_launch_dead_share: float | None = Field(
        default=None, description="The same base rate's share dead the next day.", json_schema_extra={"x-unit_measurement": "percent", "x-frontend_multiply": 100}
    )
    next_launch_n: int | None = Field(default=None, description="Launches behind the base rate.")


class PumpdataDeployerFetcher(Fetcher[PumpdataDeployerQueryParams, list[PumpdataDeployerData]]):
    """Fetch a deployer's record from pumpdata.fun."""

    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> PumpdataDeployerQueryParams:
        """Transform the query."""
        return PumpdataDeployerQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: PumpdataDeployerQueryParams, credentials: dict[str, str] | None, **kwargs: Any
    ) -> dict:
        """Return the raw answer."""
        return await get_json(f"/deployer/{query.address}", credentials, **kwargs)

    @staticmethod
    def transform_data(query: PumpdataDeployerQueryParams, data: dict, **kwargs: Any) -> list[PumpdataDeployerData]:
        """Flatten the record into one row."""
        rec, w, nxt = data.get("record") or {}, data.get("last_90_days") or {}, dig(data, "next_launch", "launches_like_it") or {}
        return [
            PumpdataDeployerData(
                address=data.get("address") or query.address,
                launches=rec.get("launches"),
                graduations=rec.get("graduations"),
                graduation_rate=rec.get("graduation_rate"),
                best_peak_usd=rec.get("best_peak_usd"),
                last_launch_gap_s=rec.get("last_launch_gap_s"),
                launches_last_day=rec.get("launches_last_day"),
                last_launch=rec.get("last_launch"),
                launches_measured_90d=w.get("launches_measured"),
                doubled_share_90d=w.get("doubled_share"),
                ten_x_share_90d=w.get("ten_x_share"),
                held_2x_share_90d=w.get("held_2x_share"),
                dead_share_90d=w.get("dead_share"),
                next_launch_doubled_share=nxt.get("doubled_share"),
                next_launch_dead_share=nxt.get("dead_share"),
                next_launch_n=nxt.get("launches_measured"),
            )
        ]


class PumpdataDeployerLaunchesData(Data):
    """pumpdata.fun Deployer Launches Data: one row per recent launch."""

    mint: str = Field(description="The coin's mint address.")
    created: str | None = Field(default=None, description="When it was launched, UTC.")
    market_cap_usd_at_5m: float | None = Field(default=None, description="Market cap at minute five, USD.")
    buyers_first_10s: int | None = Field(default=None, description="Distinct wallets that bought in the first 10 seconds.")
    peak_mult_24h: float | None = Field(default=None, description="Highest market cap in the 24 hours after minute five, over minute five's.")
    close_mult_24h: float | None = Field(default=None, description="Market cap at the end of those 24 hours, over minute five's.")
    dead_next_day: bool | None = Field(default=None, description="No priced trade in those 24 hours.")
    graduated: bool | None = Field(default=None, description="Graduated to PumpSwap.")


class PumpdataDeployerLaunchesFetcher(Fetcher[PumpdataDeployerQueryParams, list[PumpdataDeployerLaunchesData]]):
    """Fetch a deployer's recent launches from pumpdata.fun."""

    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> PumpdataDeployerQueryParams:
        """Transform the query."""
        return PumpdataDeployerQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: PumpdataDeployerQueryParams, credentials: dict[str, str] | None, **kwargs: Any
    ) -> dict:
        """Return the raw answer."""
        return await get_json(f"/deployer/{query.address}", credentials, **kwargs)

    @staticmethod
    def transform_data(
        query: PumpdataDeployerQueryParams, data: dict, **kwargs: Any
    ) -> list[PumpdataDeployerLaunchesData]:
        """One row per recent launch."""
        return [PumpdataDeployerLaunchesData.model_validate(r) for r in data.get("recent_launches") or []]
