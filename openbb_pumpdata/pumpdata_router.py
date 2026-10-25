"""pumpdata.fun Router: obb.pumpdata.*"""

from openbb_core.app.model.command_context import CommandContext
from openbb_core.app.model.example import APIEx
from openbb_core.app.model.obbject import OBBject
from openbb_core.app.provider_interface import ExtraParams, ProviderChoices, StandardParams
from openbb_core.app.query import Query as OBBQuery
from openbb_core.app.router import Router

router = Router(prefix="", description="pump.fun's whole on-chain history, from pumpdata.fun.")

MINT = "CSocnzcRpgSCr1naKcNTieWZUxb6rABe45j844m7pump"
DEPLOYER = "7ufmve7ZSFCzuNcKRunYrGtyb2Ka1MXzkWwf7jZhVsmL"


def _ex(description: str, **parameters) -> APIEx:
    return APIEx(description=description, parameters={**parameters, "provider": "pumpdata"})


@router.command(
    model="PumpdataCheck",
    examples=[_ex("The pre-buy check for one coin.", mint=MINT)],
)
async def check(
    cc: CommandContext, provider_choices: ProviderChoices, standard_params: StandardParams, extra_params: ExtraParams
) -> OBBject:
    """Check a pump.fun coin before buying: who launched it, its bundle and insiders, how coins like it went, and the flags."""
    return await OBBject.from_query(OBBQuery(**locals()))


@router.command(
    model="PumpdataLaunch",
    examples=[_ex("One coin's launch record.", mint=MINT)],
)
async def launch(
    cc: CommandContext, provider_choices: ProviderChoices, standard_params: StandardParams, extra_params: ExtraParams
) -> OBBject:
    """Get a pump.fun coin's launch: its deployer's record as of the launch, the bundle, the insiders, and the look-alikes."""
    return await OBBject.from_query(OBBQuery(**locals()))


@router.command(
    model="PumpdataSimilar",
    examples=[_ex("The five launches most like a coin, and what each did next.", mint=MINT, limit=5)],
)
async def similar(
    cc: CommandContext, provider_choices: ProviderChoices, standard_params: StandardParams, extra_params: ExtraParams
) -> OBBject:
    """Get the past pump.fun launches most like a coin, and what each did in the 24 hours after minute five."""
    return await OBBject.from_query(OBBQuery(**locals()))


@router.command(
    model="PumpdataDeployer",
    examples=[_ex("A deployer's whole launch record.", address=DEPLOYER)],
)
async def deployer(
    cc: CommandContext, provider_choices: ProviderChoices, standard_params: StandardParams, extra_params: ExtraParams
) -> OBBject:
    """Get a pump.fun deployer's record: launches, graduations, how its last 90 days went, the base rate for its next launch."""
    return await OBBject.from_query(OBBQuery(**locals()))


@router.command(
    model="PumpdataDeployerLaunches",
    examples=[_ex("A deployer's recent launches.", address=DEPLOYER)],
)
async def deployer_launches(
    cc: CommandContext, provider_choices: ProviderChoices, standard_params: StandardParams, extra_params: ExtraParams
) -> OBBject:
    """Get a pump.fun deployer's most recent launches, each with its first-day outcome."""
    return await OBBject.from_query(OBBQuery(**locals()))


@router.command(
    model="PumpdataWallets",
    examples=[_ex("What one wallet did on pump.fun.", addresses=DEPLOYER)],
)
async def wallets(
    cc: CommandContext, provider_choices: ProviderChoices, standard_params: StandardParams, extra_params: ExtraParams
) -> OBBject:
    """Get what up to 50 wallets did on pump.fun: winner, net loser, bot, supply seller, new or none, with the reason and PnL."""
    return await OBBject.from_query(OBBQuery(**locals()))


@router.command(
    model="PumpdataTopWallets",
    examples=[_ex("The ten followable winners.", followable=True, limit=10)],
)
async def top_wallets(
    cc: CommandContext, provider_choices: ProviderChoices, standard_params: StandardParams, extra_params: ExtraParams
) -> OBBject:
    """Get the pump.fun wallet leaderboard: winners over their whole record, followable ones (still trading, human pace) first."""
    return await OBBject.from_query(OBBQuery(**locals()))


@router.command(
    model="PumpdataBaseRate",
    examples=[_ex("The $15k-28k band over the default window.", band="15k-28k")],
)
async def baserate(
    cc: CommandContext, provider_choices: ProviderChoices, standard_params: StandardParams, extra_params: ExtraParams
) -> OBBject:
    """Get a market-cap band's base rate: of the coins that crossed it, the share that went on to 2x, 5x, 10x, 20x in three hours."""
    return await OBBject.from_query(OBBQuery(**locals()))


@router.command(
    model="PumpdataStats",
    examples=[_ex("Yesterday on pump.fun."), _ex("One day.", day="2026-10-24")],
)
async def stats(
    cc: CommandContext, provider_choices: ProviderChoices, standard_params: StandardParams, extra_params: ExtraParams
) -> OBBject:
    """Get one UTC day on pump.fun: launches, graduations, volume, traders up and down."""
    return await OBBject.from_query(OBBQuery(**locals()))
