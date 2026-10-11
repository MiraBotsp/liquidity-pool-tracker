"""RPC Solana (JSON-RPC padrão; funciona com Helius/QuickNode/público).

Métodos: getAccountInfo (jsonParsed) → autoridades/decimais/supply do mint;
getTokenLargestAccounts → 20 maiores contas; getMultipleAccounts → dono de cada conta.
`holders` exige indexador (ex.: Helius DAS) e fica None por ora.
"""
from __future__ import annotations

import httpx

from ..core.http import ApiError, RateLimiter, request_json

PUBLIC_RPC = "https://api.mainnet-beta.solana.com"


class SolanaRpc:
    def __init__(self, client: httpx.AsyncClient, url: str | None, *, rpm: int,
                 retries: int = 3, backoff: float = 0.5) -> None:
        self.c = client
        self.url = url or PUBLIC_RPC
        self.lim = RateLimiter(rpm)
        self.retries, self.backoff = retries, backoff
        self._id = 0

    async def call(self, method: str, params: list):
        self._id += 1
        body = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}
        data = await request_json(self.c, "POST", self.url, json=body, limiter=self.lim,
                                  retries=self.retries, backoff=self.backoff)
        if "error" in data:
            raise ApiError(f"rpc {method}: {data['error'].get('message')}")
        return data["result"]

    async def mint_info(self, mint: str) -> dict:
        res = await self.call("getAccountInfo", [mint, {"encoding": "jsonParsed"}])
        info = (((res or {}).get("value") or {}).get("data") or {}).get("parsed", {}).get("info")
        if not info:
            raise ApiError(f"mint {mint} não é um token SPL válido")
        return {
            "decimals": int(info["decimals"]),
            "supply": int(info["supply"]),
            "mint_authority_revoked": info.get("mintAuthority") is None,
            "freeze_authority_null": info.get("freezeAuthority") is None,
        }

    async def concentration(self, mint: str, supply: int, excluded: set[str]) -> tuple[float, float]:
        """(maior carteira, top 10) como fração do supply, ignorando donos em `excluded`.

        As maiores contas são *contas de token*; agregamos por dono para não subestimar
        uma carteira que espalhou saldo em várias contas.
        """
        if supply <= 0:
            raise ApiError("supply zero")
        res = await self.call("getTokenLargestAccounts", [mint])
        accounts = [(a["address"], int(a["amount"])) for a in res.get("value", [])]
        if not accounts:
            raise ApiError("sem contas")
        infos = await self.call("getMultipleAccounts",
                                [[a for a, _ in accounts], {"encoding": "jsonParsed"}])
        by_owner: dict[str, int] = {}
        for (addr, amount), acc in zip(accounts, infos.get("value", [])):
            owner = ((((acc or {}).get("data") or {}).get("parsed") or {}).get("info") or {}).get("owner")
            owner = owner or addr
            if owner in excluded or addr in excluded:
                continue
            by_owner[owner] = by_owner.get(owner, 0) + amount
        top = sorted(by_owner.values(), reverse=True)
        return (top[0] / supply if top else 0.0, sum(top[:10]) / supply)
