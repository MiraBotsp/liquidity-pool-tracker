import pytest

from backend.core.config import load_config
from backend.core.models import SellQuote, TokenSnapshot


@pytest.fixture
def cfg():
    return load_config()


@pytest.fixture
def good_snap():
    return TokenSnapshot(
        mint="GoodMint1111111111111111111111111111111111", symbol="GOOD", price_usd=0.001,
        mcap_usd=500_000, liquidity_usd=80_000, volume_h24=300_000, trades_h24=2000,
        pair_age_min=120, top_wallet_pct=0.03, top10_pct=0.3, decimals=6,
        mint_authority_revoked=True, freeze_authority_null=True,
        sell_quote=SellQuote(ok=True, in_amount=1, out_amount=1, price_impact=0.01),
    )
