# openbb-pumpdata

pump.fun's whole on-chain history in [OpenBB](https://github.com/openbq-org/OpenBB), from [pumpdata.fun](https://pumpdata.fun):
every pump.fun trade, ever, read from the Solana chain (bonding curve and PumpSwap, since pump.fun's first day).

Ask who launched a coin and what their other launches did, whether the first buyers took the whole curve, how launches
that looked the same went, what a wallet did on pump.fun, and how often coins crossing a market cap went on to 2x or
10x. Facts over the chain's record, not predictions or advice.

## Install

```bash
pip install openbb-pumpdata      # or: pip install git+https://github.com/pumpdatafun/openbb-pumpdata
python -c "import openbb; openbb.build()"
```

No key is needed: each call uses pumpdata.fun's free path (300 lookups a day per IP). A free key from
[pumpdata.fun/keys](https://pumpdata.fun/keys) gives 2,000 a day:

```python
from openbb import obb
obb.user.credentials.pumpdata_api_key = "pdk_..."
```

## Commands

| Command | What it answers |
|---|---|
| `obb.pumpdata.check(mint)` | The pre-buy check: who launched the coin, its bundle and insiders, how coins like it went, the flags and what the rules say (free for everyone) |
| `obb.pumpdata.launch(mint)` | One coin's launch: the deployer's record as of the launch, the bundle in the first 10 seconds, the insiders' share now, the look-alikes |
| `obb.pumpdata.similar(mint, limit)` | The past launches most like it, and what each did in the 24 hours after minute five |
| `obb.pumpdata.deployer(address)` | A deployer's whole record: launches, graduations, its last 90 days, the base rate for its next launch |
| `obb.pumpdata.deployer_launches(address)` | Its most recent launches, each with its first-day outcome |
| `obb.pumpdata.wallets(addresses)` | Up to 50 wallets: winner, net loser, bot, supply seller, new or none, with the reason and PnL in SOL |
| `obb.pumpdata.top_wallets(followable, limit)` | The wallet leaderboard: winners over their whole record that still trade at a pace a copier can keep (free for everyone) |
| `obb.pumpdata.baserate(band, start_date, end_date, venue)` | Of the coins that crossed a market-cap band, the share that reached 2x, 5x, 10x, 20x in the next three hours |
| `obb.pumpdata.stats(day)` | One UTC day on pump.fun: launches, graduations, volume, traders up and down (free for everyone) |

```python
from openbb import obb

obb.pumpdata.check(mint="CSocnzcRpgSCr1naKcNTieWZUxb6rABe45j844m7pump").to_dataframe()
obb.pumpdata.deployer(address="7ufmve7ZSFCzuNcKRunYrGtyb2Ka1MXzkWwf7jZhVsmL").to_dataframe()
obb.pumpdata.baserate(band="15k-28k").to_dataframe()
```

Every command is also served by OpenBB's API and MCP server once installed (`openbb-api`, `openbb-mcp`).

## Data

Where each field comes from, how fresh each layer is (deep tables rebuilt daily, an hourly fill, live for coins minutes
old), and the point-in-time guarantee (a launch's deployer record and look-alikes count only what was knowable at that
moment, so a backtest on them has no lookahead): [pumpdata.fun/methodology](https://pumpdata.fun/methodology).
Live freshness: [pumpdata.fun/status](https://pumpdata.fun/status). The same calls without OpenBB:
[the API](https://pumpdata.fun/pump-fun-api), [MCP](https://pumpdata.fun/mcp), and
[pumpdata-skills](https://github.com/pumpdatafun/pumpdata-skills) for coding agents.

pumpdata.fun is independent and not affiliated with pump.fun.

## Development

```bash
pip install -e . pytest pytest-asyncio
pytest
```

The tests run each command's transform on real answers saved in `tests/fixtures`.
