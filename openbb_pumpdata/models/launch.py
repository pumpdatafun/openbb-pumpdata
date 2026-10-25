"""pumpdata.fun Launch and Check Models: one pump.fun coin's launch, its deployer, its bundle, and how coins like it went."""

from typing import Any, Literal

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.abstract.query_params import QueryParams
from pydantic import Field, field_validator

from openbb_pumpdata.utils.client import get_json
from openbb_pumpdata.utils.helpers import check_address, dig

PCT = {"x-unit_measurement": "percent", "x-frontend_multiply": 100}


class PumpdataLaunchQueryParams(QueryParams):
    """pumpdata.fun Launch Query.

    Source: https://pumpdata.fun/pump-fun-api (GET /launch/{mint})
    """

    mint: str = Field(description="The coin's mint address.")

    @field_validator("mint", mode="before")
    @classmethod
    def _mint(cls, v: str) -> str:
        return check_address(v, "mint")


class PumpdataLaunchData(Data):
    """pumpdata.fun Launch Data: one row per coin."""

    mint: str = Field(description="The coin's mint address.")
    created: str | None = Field(default=None, description="When it was launched, UTC.")
    deployer: str | None = Field(default=None, description="The wallet that launched it.")
    deployer_launches: int | None = Field(default=None, description="The deployer's launches on record, counted as of this launch.")
    deployer_graduations: int | None = Field(default=None, description="The deployer's graduations before this launch.")
    deployer_best_peak_usd: float | None = Field(default=None, description="The best first-day peak of its earlier launches, USD.")
    deployer_launches_last_day: int | None = Field(default=None, description="The deployer's launches in the day before this one.")
    buyers_first_10s: int | None = Field(default=None, description="Distinct wallets that bought in the first 10 seconds (the bundle).")
    bundle_supply_share: float | None = Field(default=None, description="The share of supply those wallets held at 10 seconds.", json_schema_extra=PCT)
    insider_supply_share: float | None = Field(default=None, description="The deployer's and the bundle's share of supply now.", json_schema_extra=PCT)
    curve_bought_at_launch: bool | None = Field(default=None, description="One or two wallets took the whole bonding curve as it launched.")
    curve_progress: float | None = Field(default=None, description="How far along its bonding curve it is (1 = graduated).", json_schema_extra=PCT)
    migrated_at: str | None = Field(default=None, description="When it graduated to PumpSwap, UTC.")
    market_cap_usd_now: float | None = Field(default=None, description="Market cap at its last trade, USD.")
    matches_n: int | None = Field(default=None, description="Past launches that looked the same at the same age.")
    matches_graduated_share: float | None = Field(default=None, description="The share of those that graduated.", json_schema_extra=PCT)
    matches_peak_day1_p50: float | None = Field(default=None, description="Their median first-day peak, as a multiple of the market cap at the matched age.")
    matches_peak_day1_p90: float | None = Field(default=None, description="Their 90th-percentile first-day peak multiple.")
    matches_dead: int | None = Field(default=None, description="How many of them were dead the next day.")
    summary: str | None = Field(default=None, description="The answer in a sentence or two.")


def flatten_launch(j: dict, mint: str) -> dict:
    """One row from a /launch answer (also the `launch` inside a /check answer)."""
    dep = j.get("deployer") or {}
    return {
        "mint": j.get("mint") or mint,
        "created": j.get("created"),
        "deployer": dep.get("address") if isinstance(dep, dict) else dep,
        "deployer_launches": dig(j, "deployer", "launches"),
        "deployer_graduations": dig(j, "deployer", "graduations"),
        "deployer_best_peak_usd": dig(j, "deployer", "best_peak"),
        "deployer_launches_last_day": dig(j, "deployer", "launches_last_day"),
        "buyers_first_10s": dig(j, "bundle_at_creation", "buyers_first_10s"),
        "bundle_supply_share": dig(j, "bundle_at_creation", "supply_share"),
        "insider_supply_share": j.get("insider_supply_share"),
        "curve_bought_at_launch": dig(j, "curve_bought_at_launch", "yes"),
        "curve_progress": j.get("curve_progress"),
        "migrated_at": j.get("migrated_at"),
        "market_cap_usd_now": j.get("market_cap_usd_now"),
        "matches_n": dig(j, "matches", "n"),
        "matches_graduated_share": dig(j, "matches", "graduated_share"),
        "matches_peak_day1_p50": dig(j, "matches", "peak_day1", "p50"),
        "matches_peak_day1_p90": dig(j, "matches", "peak_day1", "p90"),
        "matches_dead": dig(j, "matches", "peak_day1", "dead"),
        "summary": j.get("summary"),
    }


class PumpdataLaunchFetcher(Fetcher[PumpdataLaunchQueryParams, list[PumpdataLaunchData]]):
    """Fetch one coin's launch record from pumpdata.fun."""

    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> PumpdataLaunchQueryParams:
        """Transform the query."""
        return PumpdataLaunchQueryParams(**params)

    @staticmethod
    async def aextract_data(query: PumpdataLaunchQueryParams, credentials: dict[str, str] | None, **kwargs: Any) -> dict:
        """Return the raw answer."""
        return await get_json(f"/launch/{query.mint}", credentials, **kwargs)

    @staticmethod
    def transform_data(query: PumpdataLaunchQueryParams, data: dict, **kwargs: Any) -> list[PumpdataLaunchData]:
        """One row."""
        return [PumpdataLaunchData.model_validate(flatten_launch(data, query.mint))]


class PumpdataCheckData(PumpdataLaunchData):
    """pumpdata.fun Check Data: the launch row plus what the rules say and why."""

    rules_say: Literal["skip", "caution", "no_flags"] | str | None = Field(
        default=None, description="What the check's rules say: skip, caution, or no flags. A rule over the record, not advice."
    )
    flags: str | None = Field(default=None, description="The flags raised, comma-separated (serial_launcher, curve_bought_at_launch, ...).")
    checked_at: str | None = Field(default=None, description="When the check was made, UTC.")
    data_as_of: str | None = Field(default=None, description="The deep tables' build the check reads, UTC.")
    answer: str | None = Field(default=None, description="The check in plain sentences.")


class PumpdataCheckFetcher(Fetcher[PumpdataLaunchQueryParams, list[PumpdataCheckData]]):
    """Fetch the free one-call pre-buy check from pumpdata.fun."""

    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> PumpdataLaunchQueryParams:
        """Transform the query."""
        return PumpdataLaunchQueryParams(**params)

    @staticmethod
    async def aextract_data(query: PumpdataLaunchQueryParams, credentials: dict[str, str] | None, **kwargs: Any) -> dict:
        """Return the raw answer."""
        return await get_json(f"/check/{query.mint}.json", credentials, **kwargs)

    @staticmethod
    def transform_data(query: PumpdataLaunchQueryParams, data: dict, **kwargs: Any) -> list[PumpdataCheckData]:
        """One row: the launch flattened, the rules' verdict and flags."""
        row = flatten_launch(data.get("launch") or {}, data.get("mint") or query.mint)
        flags = [f.get("flag") for f in data.get("flags") or [] if isinstance(f, dict) and f.get("flag")]
        answer = data.get("answer")
        row.update(
            rules_say=data.get("rules_say"),
            flags=", ".join(flags) or None,
            checked_at=data.get("checked_at"),
            data_as_of=data.get("data_as_of"),
            answer=" ".join(answer) if isinstance(answer, list) else answer,
        )
        return [PumpdataCheckData.model_validate(row)]
