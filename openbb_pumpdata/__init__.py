"""pumpdata.fun provider extension for OpenBB: pump.fun's whole on-chain history."""

__version__ = "0.1.0"

from openbb_core.provider.abstract.provider import Provider  # noqa: E402

from openbb_pumpdata.models.baserate import PumpdataBaseRateFetcher  # noqa: E402
from openbb_pumpdata.models.deployer import (  # noqa: E402
    PumpdataDeployerFetcher,
    PumpdataDeployerLaunchesFetcher,
)
from openbb_pumpdata.models.launch import PumpdataCheckFetcher, PumpdataLaunchFetcher  # noqa: E402
from openbb_pumpdata.models.similar import PumpdataSimilarFetcher  # noqa: E402
from openbb_pumpdata.models.stats import PumpdataStatsFetcher  # noqa: E402
from openbb_pumpdata.models.wallets import PumpdataTopWalletsFetcher, PumpdataWalletsFetcher  # noqa: E402

pumpdata_provider = Provider(
    name="pumpdata",
    website="https://pumpdata.fun",
    description="""pumpdata.fun: every pump.fun trade, ever, read from the Solana chain (bonding curve and PumpSwap,
since pump.fun's first day). A deployer's whole launch record, a coin's bundle and insiders and how launches like it
went, what any wallet did on pump.fun, the base rate of a market-cap band, and each day's totals.
Free to start: no key, 300 lookups a day per IP. A free key (https://pumpdata.fun/keys) gives 2,000 a day.""",
    credentials=["api_key"],
    fetcher_dict={
        "PumpdataCheck": PumpdataCheckFetcher,
        "PumpdataLaunch": PumpdataLaunchFetcher,
        "PumpdataSimilar": PumpdataSimilarFetcher,
        "PumpdataDeployer": PumpdataDeployerFetcher,
        "PumpdataDeployerLaunches": PumpdataDeployerLaunchesFetcher,
        "PumpdataWallets": PumpdataWalletsFetcher,
        "PumpdataTopWallets": PumpdataTopWalletsFetcher,
        "PumpdataBaseRate": PumpdataBaseRateFetcher,
        "PumpdataStats": PumpdataStatsFetcher,
    },
    repr_name="pumpdata.fun",
    instructions="No key needed: each call uses the free path. A free key from https://pumpdata.fun/keys raises the "
    "allowance to 2,000 calls a day; set it as `pumpdata_api_key`.",
)
