"""The fetchers on real pumpdata.fun answers (tests/fixtures, saved Oct 25 2026), the paths, and the errors."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from openbb_core.app.model.abstract.error import OpenBBError
from openbb_core.provider.utils.errors import EmptyDataError, UnauthorizedError

from openbb_pumpdata import pumpdata_provider
from openbb_pumpdata.models.baserate import PumpdataBaseRateFetcher
from openbb_pumpdata.models.deployer import PumpdataDeployerFetcher, PumpdataDeployerLaunchesFetcher
from openbb_pumpdata.models.launch import PumpdataCheckFetcher, PumpdataLaunchFetcher
from openbb_pumpdata.models.similar import PumpdataSimilarFetcher
from openbb_pumpdata.models.stats import PumpdataStatsFetcher
from openbb_pumpdata.models.wallets import PumpdataTopWalletsFetcher, PumpdataWalletsFetcher
from openbb_pumpdata.utils import client

FX = Path(__file__).parent / "fixtures"
MINT = "CSocnzcRpgSCr1naKcNTieWZUxb6rABe45j844m7pump"
DEPLOYER = "7ufmve7ZSFCzuNcKRunYrGtyb2Ka1MXzkWwf7jZhVsmL"


def fx(name: str) -> dict:
    return json.loads((FX / f"{name}.json").read_text())


def test_provider_lists_every_command():
    assert pumpdata_provider.name == "pumpdata"
    assert pumpdata_provider.credentials == ["pumpdata_api_key"]
    assert set(pumpdata_provider.fetcher_dict) == {
        "PumpdataCheck", "PumpdataLaunch", "PumpdataSimilar", "PumpdataDeployer", "PumpdataDeployerLaunches",
        "PumpdataWallets", "PumpdataTopWallets", "PumpdataBaseRate", "PumpdataStats",
    }


def test_paths_free_without_a_key_keyed_with_one_open_ones_neither():
    url, h = client.build_url(f"/deployer/{DEPLOYER}", None)
    assert url == f"https://pumpdata.fun/free/deployer/{DEPLOYER}" and "x-api-key" not in h
    url, h = client.build_url(f"/deployer/{DEPLOYER}", "pdk_" + "k" * 32)
    assert url == f"https://pumpdata.fun/deployer/{DEPLOYER}" and h["x-api-key"] == "pdk_" + "k" * 32
    for open_path in (f"/check/{MINT}.json", "/wallets/top?followable=1&limit=5", "/stats.json"):
        url, h = client.build_url(open_path, "pdk_" + "k" * 32)
        assert url == "https://pumpdata.fun" + open_path and "x-api-key" not in h
    assert h["user-agent"].startswith("openbb-pumpdata/"), "never pumpdata-*: that prefix is how pumpdata.fun counts its own tools"


def test_addresses_are_checked():
    with pytest.raises(ValueError):
        PumpdataDeployerFetcher.transform_query({"address": "not-an-address"})
    q = PumpdataWalletsFetcher.transform_query({"addresses": f" {DEPLOYER} ,{DEPLOYER}"})
    assert q.addresses == DEPLOYER, "trimmed and deduped"
    with pytest.raises(ValueError):
        b58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        PumpdataWalletsFetcher.transform_query({"addresses": ",".join(c + "1" * 31 for c in b58[:51])})


def test_deployer_row_and_its_launches():
    q = PumpdataDeployerFetcher.transform_query({"address": DEPLOYER})
    [row] = PumpdataDeployerFetcher.transform_data(q, fx("deployer"))
    assert row.address == DEPLOYER and row.launches == 610 and row.graduations == 170
    assert row.launches_measured_90d == 296 and row.doubled_share_90d == 0.25
    assert row.next_launch_n == 861654 and row.next_launch_dead_share == 0.6211
    launches = PumpdataDeployerLaunchesFetcher.transform_data(q, fx("deployer"))
    assert len(launches) == 10 and launches[0].mint.endswith("pump") and launches[0].buyers_first_10s == 36


def test_launch_and_check():
    q = PumpdataLaunchFetcher.transform_query({"mint": MINT})
    [row] = PumpdataLaunchFetcher.transform_data(q, fx("launch"))
    assert row.deployer == "EFSr396A6Jh7bNCSujGRLMkyXspbWitEvjNVatGD56oF" and row.deployer_launches == 333
    assert row.curve_bought_at_launch is True and row.bundle_supply_share == 0.7931 and row.matches_n == 143
    [c] = PumpdataCheckFetcher.transform_data(q, fx("check"))
    assert c.rules_say == "skip" and "serial_launcher" in c.flags and c.deployer_launches == 333
    assert c.answer.startswith(MINT + " was launched")


def test_similar_wallets_top():
    q = PumpdataSimilarFetcher.transform_query({"mint": MINT, "limit": 3})
    rows = PumpdataSimilarFetcher.transform_data(q, fx("similar"))
    assert len(rows) == 3 and rows[0].same_deployer is True and rows[0].peak_mult_24h == 1.058
    q = PumpdataWalletsFetcher.transform_query({"addresses": DEPLOYER})
    [w] = PumpdataWalletsFetcher.transform_data(q, fx("wallets"))
    assert w.wallet_class == "bot" and w.coins == 594 and w.snipe_share == 0.986
    q = PumpdataTopWalletsFetcher.transform_query({"limit": 2})
    top = PumpdataTopWalletsFetcher.transform_data(q, fx("top"))
    assert len(top) == 2 and top[0].wallet_class == "winner" and top[0].followable is True and top[0].rank == 9


def test_baserate_window_and_row():
    q = PumpdataBaseRateFetcher.transform_query({"band": "15k-28k"})
    assert (datetime.now(timezone.utc) - q.end_date).total_seconds() >= 3 * 3600 - 5, "the window ends three hours back"
    assert (q.end_date - q.start_date).days == 4
    [row] = PumpdataBaseRateFetcher.transform_data(q, fx("baserate"))
    assert row.crossed == 2203 and row.reached_2x == 0.361 and row.reached_20x == 0.02 and row.median_peak == 1.499


def test_stats_row():
    q = PumpdataStatsFetcher.transform_query({})
    [row] = PumpdataStatsFetcher.transform_data(q, fx("stats"))
    assert row.day == "2026-10-24" and row.launched == 42009 and row.graduated == 933
    assert row.headline.startswith("42,009 launched")


class FakeResponse:
    def __init__(self, status: int, body: dict, headers: dict | None = None):
        self.status, self._body, self.headers = status, body, headers or {}

    async def json(self, content_type=None):
        return self._body

    async def text(self):
        return json.dumps(self._body)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "body", "headers", "error", "match"),
    [
        (401, {"error": "unknown_key"}, {}, UnauthorizedError, "unknown_key"),
        (404, {"error": "unknown_mint"}, {}, EmptyDataError, "unknown_mint"),
        (429, {"error": "too many"}, {"retry-after": "60"}, OpenBBError, r"retry in 60 s.*free key"),
        (402, {"why": "the free 300 lookups a day are used"}, {}, OpenBBError, "300 lookups"),
    ],
)
async def test_errors_say_why(monkeypatch, status, body, headers, error, match):
    async def fake_request(url, method="GET", timeout=10, response_callback=None, **kwargs):
        return await response_callback(FakeResponse(status, body, headers), None)

    monkeypatch.setattr(client, "amake_request", fake_request)
    with pytest.raises(error, match=match):
        await client.get_json(f"/launch/{MINT}", None)
