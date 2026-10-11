"""Configuração validada. Segredos vêm do ambiente (.env); limiares do config.yaml."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, SecretStr

ROOT = Path(__file__).resolve().parents[2]

Fraction = Field(ge=0, le=1)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CrawlCfg(_Strict):
    interval_s: int = Field(60, ge=5)
    max_tokens_per_cycle: int = Field(30, ge=1, le=200)
    chain_id: str = "solana"
    quote_mint: str


class RateLimitsCfg(_Strict):
    dexscreener_profiles_rpm: int = Field(ge=1, le=60)
    dexscreener_pairs_rpm: int = Field(ge=1, le=300)
    jupiter_rpm: int = Field(ge=1)
    solana_rpc_rpm: int = Field(ge=1)


class HttpCfg(_Strict):
    timeout_s: float = Field(10, gt=0)
    retries: int = Field(3, ge=0, le=10)
    backoff_base_s: float = Field(0.5, ge=0)


class GateCfg(_Strict):
    min_age_minutes: float = Field(ge=0)
    min_liquidity_usd: float = Field(ge=0)
    min_volume_h24: float = Field(ge=0)
    min_mcap_usd: float = Field(ge=0)
    min_trades_h24: int = Field(ge=0)
    max_top_wallet: float = Fraction
    max_top_10: float = Fraction
    require_mint_authority_revoked: bool = True
    require_freeze_authority_null: bool = True
    require_sell_route: bool = True
    max_sell_price_impact: float = Fraction
    blocklist_file: str = "blocklist.txt"
    excluded_owners: list[str] = []


class JevCfg(_Strict):
    model: str = "~typesafe/jev-latest"
    base_url: str = "https://openrouter.ai/api/alpha"
    timeout_s: float = 20


class ScanCfg(_Strict):
    min_real: float = Fraction


class SoftCfg(_Strict):
    momentum_already_spent_max: float = Fraction
    dev_wallet_clean_min: float = Fraction
    rug_probability_max: float = Fraction
    concentration_is_exit_risk_max: float = Fraction
    liquidity_fits_ticket_min: float = Fraction
    social_farm_suspected: bool = False
    min_sentiment: float = Field(ge=-1, le=1)


class ChiefCfg(_Strict):
    max_per_cycle: int = Field(3, ge=0, le=10)
    model: str = "claude-opus-5-5"


class ModelCfg(_Strict):
    model: str = "claude-sonnet-5-5"


class JournalCfg(ModelCfg):
    dir: str = "journal"


class PaperCfg(_Strict):
    bankroll_usd: float = Field(gt=0)
    auto_approve: bool = False


class RiskCfg(_Strict):
    per_trade_pct: float = Field(gt=0, le=0.05)
    max_ticket_pct_bankroll: float = Field(gt=0, le=0.10)
    max_ticket_pct_liquidity: float = Field(gt=0, le=0.05)
    max_open_positions: int = Field(ge=1, le=5)
    daily_loss_limit_pct: float = Field(gt=0, le=0.5)
    max_consecutive_losses: int = Field(3, ge=1)
    cooldown_minutes: int = Field(ge=0)
    poll_seconds: int = Field(ge=1)


class SizeCfg(_Strict):
    kelly_min_samples: int = Field(100, ge=30)


class CardCfg(_Strict):
    ttl_seconds: int = Field(ge=10)
    max_drift_pct: float = Fraction


class BudgetCfg(_Strict):
    daily_usd: float = Field(ge=0)


class Secrets(BaseModel):
    """Nunca serializado em log, evento, banco ou prompt (SecretStr mascara o valor)."""
    openrouter_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    solana_rpc_url: SecretStr | None = None   # ex.: Helius com ?api-key=...
    live_trading: bool = False


class DeskConfig(_Strict):
    mode: Literal["paper", "live"] = "paper"
    data_source: Literal["auto", "real", "mock"] = "auto"
    db_path: str = "spider_desk.db"
    crawl: CrawlCfg
    rate_limits: RateLimitsCfg
    http: HttpCfg
    gate: GateCfg
    jev: JevCfg
    scan: ScanCfg
    soft: SoftCfg
    chief: ChiefCfg
    social: ModelCfg
    journal: JournalCfg
    paper: PaperCfg
    risk: RiskCfg
    size: SizeCfg
    card: CardCfg
    budget: BudgetCfg

    @property
    def max_ticket_usd(self) -> float:
        return self.paper.bankroll_usd * self.risk.max_ticket_pct_bankroll

    def resolve(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else ROOT / p


def load_secrets(env_file: Path | None = None) -> Secrets:
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file or ROOT / ".env", override=False)
    except ImportError:  # pragma: no cover
        pass
    return Secrets(
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY") or None,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
        solana_rpc_url=os.getenv("SOLANA_RPC_URL") or None,
        live_trading=os.getenv("LIVE_TRADING", "false").strip().lower() == "true",
    )


def load_config(path: Path | str | None = None) -> DeskConfig:
    path = Path(path) if path else ROOT / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg = DeskConfig.model_validate(data)
    if cfg.mode == "live":
        # Fase 7 ainda não existe: recusar em vez de rodar algo pela metade.
        raise ValueError("mode=live ainda não está implementado (Fase 7). Use mode: paper.")
    return cfg


def load_blocklist(cfg: DeskConfig) -> set[str]:
    p = cfg.resolve(cfg.gate.blocklist_file)
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.add(line)
    return out
