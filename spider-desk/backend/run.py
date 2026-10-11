"""CLI da mesa.

    python -m backend.run cycle [--mock] [--cycles N]   # roda ciclos CRAWLER→GATE
    python -m backend.run jev-check                      # 1 chamada real ao Jev (valida a chave)
"""
from __future__ import annotations

import argparse
import asyncio
import logging

import httpx
import structlog

from .adapters.jev import ChoiceQ, JevClient, JevError, NoulQ
from .adapters.market import RealMarket
from .adapters.mocks.market_mock import MockMarket
from .agents.crawler import Crawler
from .agents.gate import Gate
from .core.bus import EventBus
from .core.config import load_blocklist, load_config, load_secrets
from .core.db import Database
from .pipeline import Desk


async def build_source(cfg, secrets, force_mock: bool):
    if force_mock or cfg.data_source == "mock":
        return MockMarket(max_ticket_usd=cfg.max_ticket_usd)
    real = RealMarket(cfg, secrets)
    if cfg.data_source == "real" or await real.probe():
        return real
    await real.aclose()
    print("⚠  APIs de mercado inacessíveis — usando MOCK (dados falsos).")
    return MockMarket(max_ticket_usd=cfg.max_ticket_usd)


async def cmd_cycle(args) -> None:
    cfg, secrets = load_config(args.config), load_secrets()
    db = Database(cfg.resolve(cfg.db_path))
    bus = EventBus()
    bus.subscribe(db.save_event)
    source = await build_source(cfg, secrets, args.mock)
    desk = Desk(Crawler(source, cfg.crawl.max_tokens_per_cycle),
                Gate(cfg.gate, load_blocklist(cfg)), bus, db)
    print(f"Spider Desk — modo PAPEL — dados: {source.name.upper()}")
    try:
        for i in range(args.cycles):
            results = await desk.run_cycle()
            ok = [s for s, r in results if r.passed]
            print(f"\nCiclo {i + 1}: {len(results)} tokens, {len(ok)} passaram no GATE")
            for s, r in results:
                mark = "✓" if r.passed else "✗"
                why = "" if r.passed else f"  ← {r.reason}"
                liq = f"{s.liquidity_usd:>10,.0f}" if s.liquidity_usd else f"{'—':>10}"
                print(f"  {mark} {s.symbol:<10} liq ${liq}{why}")
            if i + 1 < args.cycles:
                await asyncio.sleep(cfg.crawl.interval_s)
    finally:
        await source.aclose()
        db.close()


async def cmd_jev_check(args) -> None:
    cfg, secrets = load_config(args.config), load_secrets()
    if not secrets.openrouter_api_key:
        raise SystemExit("OPENROUTER_API_KEY não definida (coloque no .env).")
    async with httpx.AsyncClient(timeout=cfg.jev.timeout_s) as c:
        jev = JevClient(c, secrets.openrouter_api_key.get_secret_value(),
                        model=cfg.jev.model, base_url=cfg.jev.base_url)
        qs = {
            "movement": ChoiceQ(instructions="Is this trading activity organic or wash trading?",
                                criteria={"real": "Many distinct wallets, organic flow",
                                          "wash": "Few wallets cycling volume",
                                          "unclear": "Not enough signal"}),
            "momentum_already_spent": NoulQ(instructions="Has most of the move already happened?",
                                            criteria={"true": "Price already pumped and fading",
                                                      "false": "Move still early"}),
        }
        state = {"price_change_h1": 0.12, "price_change_h6": 0.4, "volume_to_liquidity": 3.1,
                 "unique_buyers_h1": 410, "unique_sellers_h1": 380, "top5_wallets_share_of_volume": 0.09}
        try:
            ans = await jev.decide(state, qs)
        except JevError as e:
            raise SystemExit(f"Jev falhou: {e}")
        for k, a in ans.items():
            print(k, a.model_dump())


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING))
    p = argparse.ArgumentParser(prog="spider-desk")
    p.add_argument("--config", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cycle")
    c.add_argument("--mock", action="store_true")
    c.add_argument("--cycles", type=int, default=1)
    sub.add_parser("jev-check")
    args = p.parse_args()
    asyncio.run({"cycle": cmd_cycle, "jev-check": cmd_jev_check}[args.cmd](args))


if __name__ == "__main__":
    main()
