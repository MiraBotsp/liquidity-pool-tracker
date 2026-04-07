import math
from datetime import datetime, date
from typing import List, Dict, Optional


# ─────────────────────────────────────────────
# HELPERS INTERNOS
# ─────────────────────────────────────────────

def _parse_data(d: str) -> date:
    """Converte string 'YYYY-MM-DD' em objeto date."""
    return datetime.strptime(d[:10], "%Y-%m-%d").date()


def _dias_entre(data_inicio: str, data_fim: Optional[str] = None) -> int:
    """Calcula a diferença em dias entre duas datas (strings YYYY-MM-DD).
    Se data_fim for None, usa a data atual.
    """
    inicio = _parse_data(data_inicio)
    fim = _parse_data(data_fim) if data_fim else date.today()
    delta = (fim - inicio).days
    return max(delta, 0)


# ─────────────────────────────────────────────
# PREÇO MÉDIO
# ─────────────────────────────────────────────

def calcular_preco_medio(posicoes: List[Dict], token: str = "a") -> float:
    """
    Preço médio ponderado pela quantidade do token.

    token="a" → usa token_a_amount e token_a_price_usd
    token="b" → usa token_b_amount e token_b_price_usd

    Fórmula: sum(amount_i * price_i) / sum(amount_i)
    Retorna 0.0 se não houver posições ou quantidade total for zero.
    """
    if not posicoes:
        return 0.0

    key_amount = f"token_{token}_amount"
    key_price = f"token_{token}_price_usd"

    total_ponderado = 0.0
    total_amount = 0.0

    for pos in posicoes:
        amount = pos.get(key_amount, 0.0) or 0.0
        price = pos.get(key_price, 0.0) or 0.0
        total_ponderado += amount * price
        total_amount += amount

    if total_amount <= 0:
        return 0.0

    return total_ponderado / total_amount


# ─────────────────────────────────────────────
# CAPITAL
# ─────────────────────────────────────────────

def calcular_capital_total(posicoes: List[Dict]) -> float:
    """Retorna a soma de capital_usd de todas as posições."""
    return sum(float(p.get("capital_usd", 0) or 0) for p in posicoes)


# ─────────────────────────────────────────────
# APR / APY
# ─────────────────────────────────────────────

def calcular_apr(total_fees_usd: float, capital_usd: float, dias: int) -> float:
    """
    APR anualizado baseado nas fees coletadas.

    APR = (fees / capital) * (365 / dias) * 100

    Retorna 0.0 se dias <= 0 ou capital <= 0.
    """
    if dias <= 0 or capital_usd <= 0:
        return 0.0
    return (total_fees_usd / capital_usd) * (365 / dias) * 100


def calcular_apy(apr: float) -> float:
    """
    APY com compounding diário.

    APY = (1 + APR/100/365)^365 - 1

    Retorna o valor em percentual (ex: 12.5 para 12.5%).
    Retorna 0.0 para APR <= 0.
    """
    if apr <= 0:
        return 0.0
    taxa_diaria = apr / 100 / 365
    return ((1 + taxa_diaria) ** 365 - 1) * 100


# ─────────────────────────────────────────────
# IMPERMANENT LOSS
# ─────────────────────────────────────────────

def calcular_il(
    preco_entrada_a: float,
    preco_atual_a: float,
    preco_entrada_b: float,
    preco_atual_b: float,
) -> float:
    """
    Calcula o Impermanent Loss percentual (valor negativo = perda).

    Fórmula:
        r = (preco_atual_a / preco_entrada_a) / (preco_atual_b / preco_entrada_b)
        IL = 2 * sqrt(r) / (1 + r) - 1

    Retorna 0.0 se algum preço de entrada for zero (posição inválida).
    """
    if preco_entrada_a <= 0 or preco_entrada_b <= 0:
        return 0.0
    if preco_atual_a <= 0 or preco_atual_b <= 0:
        return 0.0

    r = (preco_atual_a / preco_entrada_a) / (preco_atual_b / preco_entrada_b)

    if r <= 0:
        return 0.0

    il = (2 * math.sqrt(r) / (1 + r)) - 1
    return il * 100  # retorna em percentual


# ─────────────────────────────────────────────
# RETORNO LÍQUIDO
# ─────────────────────────────────────────────

def calcular_retorno_liquido(apr: float, il_pct: float) -> float:
    """
    Retorno líquido estimado.

    retorno_liquido = APR + IL_pct
    (IL já é negativo quando há perda, ex: -3.5)
    """
    return apr + il_pct


# ─────────────────────────────────────────────
# VALOR HOLD
# ─────────────────────────────────────────────

def calcular_valor_hold(
    posicoes: List[Dict],
    preco_atual_a: float,
    preco_atual_b: float,
) -> float:
    """
    Calcula o valor total caso o usuário tivesse simplesmente segurado
    os tokens sem fornecer liquidez (estratégia HODL).

    valor_hold = sum(token_a_amount_i * preco_atual_a + token_b_amount_i * preco_atual_b)
    """
    if not posicoes:
        return 0.0

    total = 0.0
    for pos in posicoes:
        amt_a = float(pos.get("token_a_amount", 0) or 0)
        amt_b = float(pos.get("token_b_amount", 0) or 0)
        total += amt_a * preco_atual_a + amt_b * preco_atual_b

    return total


# ─────────────────────────────────────────────
# MÉTRICAS COMPLETAS
# ─────────────────────────────────────────────

def calcular_metricas_pool(
    posicoes: List[Dict],
    taxas: List[Dict],
    preco_atual_a: Optional[float] = None,
    preco_atual_b: Optional[float] = None,
) -> Dict:
    """
    Calcula e retorna um dicionário completo com todas as métricas da pool.

    Parâmetros:
        posicoes      — lista de dicts retornados por listar_posicoes()
        taxas         — lista de dicts retornados por listar_taxas()
        preco_atual_a — preço atual em USD do token A (opcional)
        preco_atual_b — preço atual em USD do token B (opcional)

    Retorno:
        {
            capital_total       float   — soma dos aportes em USD
            total_fees          float   — soma das fees coletadas em USD
            dias_na_pool        int     — dias desde o primeiro aporte
            apr                 float   — APR anualizado (%)
            apy                 float   — APY com compounding diário (%)
            il_pct              float   — Impermanent Loss (%) ou None
            retorno_liquido     float   — APR + IL ou None
            preco_medio_a       float   — preço médio ponderado do token A
            preco_medio_b       float   — preço médio ponderado do token B
            valor_hold          float   — valor se tivesse segurado (ou None)
            ganho_vs_hold       float   — capital_total + fees - valor_hold (ou None)
        }
    """
    capital_total = calcular_capital_total(posicoes)
    total_fees = sum(float(t.get("valor_usd", 0) or 0) for t in taxas)
    preco_medio_a = calcular_preco_medio(posicoes, token="a")
    preco_medio_b = calcular_preco_medio(posicoes, token="b")

    # Dias na pool: da primeira posição até hoje
    dias_na_pool = 0
    if posicoes:
        datas = [p["data"] for p in posicoes if p.get("data")]
        if datas:
            data_inicio = min(datas)
            dias_na_pool = _dias_entre(data_inicio)

    apr = calcular_apr(total_fees, capital_total, dias_na_pool)
    apy = calcular_apy(apr)

    # IL — calculado apenas se os preços atuais forem fornecidos
    il_pct: Optional[float] = None
    retorno_liquido: Optional[float] = None

    if preco_atual_a is not None and preco_atual_b is not None:
        if preco_medio_a > 0 and preco_medio_b > 0:
            il_pct = calcular_il(
                preco_entrada_a=preco_medio_a,
                preco_atual_a=preco_atual_a,
                preco_entrada_b=preco_medio_b,
                preco_atual_b=preco_atual_b,
            )
            retorno_liquido = calcular_retorno_liquido(apr, il_pct)

    # Valor HODL e ganho vs hold
    valor_hold: Optional[float] = None
    ganho_vs_hold: Optional[float] = None

    if preco_atual_a is not None and preco_atual_b is not None:
        valor_hold = calcular_valor_hold(posicoes, preco_atual_a, preco_atual_b)
        # Ganho vs hold: (capital_total + fees) - valor_hold
        # Positivo = LP foi melhor que segurar
        ganho_vs_hold = (capital_total + total_fees) - valor_hold

    return {
        "capital_total": capital_total,
        "total_fees": total_fees,
        "dias_na_pool": dias_na_pool,
        "apr": apr,
        "apy": apy,
        "il_pct": il_pct,
        "retorno_liquido": retorno_liquido,
        "preco_medio_a": preco_medio_a,
        "preco_medio_b": preco_medio_b,
        "valor_hold": valor_hold,
        "ganho_vs_hold": ganho_vs_hold,
    }


def calcular_il_real(posicoes: List[Dict], taxas: List[Dict]) -> Optional[float]:
    """
    Calcula o IL real usando o último snapshot registrado nas taxas.

    Quando o usuário registra uma retirada de taxa com valor_pool_usd +
    preços dos tokens, temos dados reais para o cálculo.

    Fórmula:
        IL real = (valor_pool_atual / valor_hold_com_precos_atuais) - 1

    Onde valor_hold = quanto valeria se tivesse só segurado os tokens.

    Retorna None se não houver snapshots com dados suficientes.
    """
    # Busca a taxa mais recente que tenha snapshot completo
    snapshots = [
        t for t in taxas
        if t.get("valor_pool_usd") and t.get("token_a_price_usd") and t.get("token_b_price_usd")
    ]
    if not snapshots or not posicoes:
        return None

    ultimo = max(snapshots, key=lambda t: t.get("data", ""))
    valor_pool = float(ultimo["valor_pool_usd"])
    pa_atual = float(ultimo["token_a_price_usd"])
    pb_atual = float(ultimo["token_b_price_usd"])

    valor_hold = calcular_valor_hold(posicoes, pa_atual, pb_atual)
    if valor_hold <= 0:
        return None

    # IL = valor_pool / valor_hold - 1  (negativo = perda vs hold)
    return (valor_pool / valor_hold - 1) * 100


def historico_il(posicoes: List[Dict], taxas: List[Dict]) -> List[Dict]:
    """
    Retorna histórico de IL calculado a cada snapshot registrado.

    Cada item: { "data": str, "il_pct": float, "valor_pool": float, "valor_hold": float }
    """
    snapshots = [
        t for t in taxas
        if t.get("valor_pool_usd") and t.get("token_a_price_usd") and t.get("token_b_price_usd")
    ]
    if not snapshots or not posicoes:
        return []

    resultado = []
    for s in sorted(snapshots, key=lambda t: t.get("data", "")):
        pa = float(s["token_a_price_usd"])
        pb = float(s["token_b_price_usd"])
        valor_pool = float(s["valor_pool_usd"])
        valor_hold = calcular_valor_hold(posicoes, pa, pb)
        if valor_hold > 0:
            il = (valor_pool / valor_hold - 1) * 100
            resultado.append({
                "data": s["data"],
                "il_pct": il,
                "valor_pool": valor_pool,
                "valor_hold": valor_hold,
            })

    return resultado


# ─────────────────────────────────────────────
# NET YIELD REAL
# ─────────────────────────────────────────────

def calcular_net_yield(apr: float, il_pct: Optional[float]) -> Optional[float]:
    """
    Net Yield Real = APR - |IL|
    Retorna None se IL não disponível.
    O resultado positivo = LP está ganhando vs HODL.
    """
    if il_pct is None:
        return None
    return apr + il_pct  # il_pct já é negativo quando há perda


# ─────────────────────────────────────────────
# BREAK-EVEN
# ─────────────────────────────────────────────

def calcular_breakeven_dias(il_usd: float, taxas: List[Dict]) -> Optional[int]:
    """
    Quantos dias de fees para cobrir o IL atual.
    Usa a média diária dos últimos 30 dias de taxas.
    Retorna None se não há histórico suficiente.
    """
    if not taxas or il_usd <= 0:
        return None
    taxas_ord = sorted(taxas, key=lambda t: t.get("data", ""))
    if len(taxas_ord) < 2:
        return None
    data_ini = _parse_data(taxas_ord[0]["data"])
    data_fim = _parse_data(taxas_ord[-1]["data"])
    dias = max((data_fim - data_ini).days, 1)
    total = sum(float(t.get("valor_usd", 0) or 0) for t in taxas_ord)
    fee_diaria = total / dias
    if fee_diaria <= 0:
        return None
    return math.ceil(il_usd / fee_diaria)


# ─────────────────────────────────────────────
# FEE RUN RATE
# ─────────────────────────────────────────────

def calcular_fee_run_rate(taxas: List[Dict], janela_dias: int = 7) -> float:
    """
    Taxa média de fees por dia nos últimos N dias.
    Indica o ritmo atual da pool, não a média histórica acumulada.
    """
    if not taxas:
        return 0.0
    hoje = date.today()
    recentes = [
        t for t in taxas
        if _dias_entre(t.get("data", ""), str(hoje)) <= janela_dias
    ]
    if not recentes:
        return 0.0
    total = sum(float(t.get("valor_usd", 0) or 0) for t in recentes)
    return total / janela_dias


# ─────────────────────────────────────────────
# RANGE DE PREÇO
# ─────────────────────────────────────────────

def status_range(preco_atual: Optional[float],
                 preco_min: Optional[float],
                 preco_max: Optional[float]) -> dict:
    """
    Verifica se a pool está dentro do range de preço configurado.
    Retorna:
        {
            "in_range": bool | None,
            "pct_posicao": float | None,   # 0-100%: onde está dentro do range
            "distancia_min": float | None,  # % de distância do limite inferior
            "distancia_max": float | None,  # % de distância do limite superior
        }
    """
    if preco_atual is None or preco_min is None or preco_max is None:
        return {"in_range": None, "pct_posicao": None, "distancia_min": None, "distancia_max": None}
    if preco_min <= 0 or preco_max <= preco_min:
        return {"in_range": None, "pct_posicao": None, "distancia_min": None, "distancia_max": None}

    in_range = preco_min <= preco_atual <= preco_max
    span = preco_max - preco_min
    pct_posicao = ((preco_atual - preco_min) / span * 100) if span > 0 else None
    distancia_min = ((preco_atual - preco_min) / preco_min * 100)
    distancia_max = ((preco_max - preco_atual) / preco_max * 100)

    return {
        "in_range": in_range,
        "pct_posicao": pct_posicao,
        "distancia_min": distancia_min,
        "distancia_max": distancia_max,
    }


# ─────────────────────────────────────────────
# RISK SCORE
# ─────────────────────────────────────────────

def calcular_risk_score(pool: dict, posicoes: List[Dict], taxas: List[Dict]) -> dict:
    """
    Score de risco simplificado (0 = sem risco, 100 = máximo risco).
    Baseado em vetores mensuráveis com dados disponíveis.
    Retorna: { "score": int, "nivel": str, "fatores": list[dict] }
    """
    fatores = []
    score = 0

    # 1. Concentração no protocolo (sem diversificação = risco)
    # Proxy: capital nesta pool vs. sem info de outras → neutro
    cap = sum(float(p.get("capital_usd", 0) or 0) for p in posicoes)
    fatores.append({"nome": "Capital em risco", "valor": cap, "peso": 0})

    # 2. IL atual elevado
    il_real = calcular_il_real(posicoes, taxas)
    if il_real is not None:
        il_abs = abs(il_real)
        il_score = min(il_abs * 3, 35)  # 0-35 pontos
        score += il_score
        fatores.append({"nome": "Impermanent Loss", "valor": f"{il_real:.1f}%", "peso": round(il_score)})
    else:
        fatores.append({"nome": "Impermanent Loss", "valor": "Sem dados", "peso": 0})

    # 3. APR negativo (net yield ruim)
    total_fees = sum(float(t.get("valor_usd", 0) or 0) for t in taxas)
    dias = 1
    if posicoes:
        datas = [p["data"] for p in posicoes if p.get("data")]
        if datas:
            dias = max(_dias_entre(min(datas)), 1)
    apr = calcular_apr(total_fees, cap, dias)
    net = calcular_net_yield(apr, il_real)
    if net is not None and net < 0:
        apr_score = min(abs(net) * 2, 30)
        score += apr_score
        fatores.append({"nome": "Net Yield negativo", "valor": f"{net:.1f}%", "peso": round(apr_score)})
    else:
        fatores.append({"nome": "Net Yield", "valor": f"{net:.1f}%" if net is not None else "—", "peso": 0})

    # 4. Fee run rate caindo (pool esfriando)
    run_rate = calcular_fee_run_rate(taxas, 7)
    run_rate_30 = calcular_fee_run_rate(taxas, 30)
    if run_rate_30 > 0 and run_rate < run_rate_30 * 0.5:
        score += 20
        fatores.append({"nome": "Atividade caindo", "valor": f"Run rate 7d: ${run_rate:.2f}/dia", "peso": 20})
    else:
        fatores.append({"nome": "Atividade da pool", "valor": f"${run_rate:.2f}/dia", "peso": 0})

    # 5. Sem range configurado (concentrated liquidity sem monitoramento)
    if pool.get("preco_min") and pool.get("preco_max"):
        fatores.append({"nome": "Range configurado", "valor": "Sim", "peso": 0})
    else:
        score += 15
        fatores.append({"nome": "Range não configurado", "valor": "Sem monitoramento", "peso": 15})

    score = min(score, 100)
    nivel = "BAIXO" if score < 30 else ("MÉDIO" if score < 60 else "ALTO")

    return {"score": score, "nivel": nivel, "fatores": fatores}


# ─────────────────────────────────────────────
# TIMELINE IL VS FEES
# ─────────────────────────────────────────────

def timeline_il_vs_fees(posicoes: List[Dict], taxas: List[Dict]) -> List[Dict]:
    """
    Retorna série temporal com fees acumuladas e IL acumulado (via snapshots).
    Cada ponto: { "data", "fees_acum", "il_usd", "net_usd" }
    """
    if not taxas:
        return []

    taxas_ord = sorted(taxas, key=lambda t: t.get("data", ""))
    capital = calcular_capital_total(posicoes)

    resultado = []
    fees_acum = 0.0

    for t in taxas_ord:
        fees_acum += float(t.get("valor_usd", 0) or 0)

        # IL em USD neste ponto (se tiver snapshot)
        il_usd = None
        vp = t.get("valor_pool_usd")
        pa = t.get("token_a_price_usd")
        pb = t.get("token_b_price_usd")
        if vp and pa and pb:
            valor_hold = calcular_valor_hold(posicoes, float(pa), float(pb))
            if valor_hold > 0:
                il_usd = float(vp) - valor_hold  # negativo = perda

        resultado.append({
            "data": t["data"][:10],
            "fees_acum": fees_acum,
            "il_usd": il_usd,
            "net_usd": (fees_acum + il_usd) if il_usd is not None else None,
        })

    return resultado
