from typing import Optional

# ─────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────

CHAIN_CORES: dict[str, str] = {
    "Ethereum":  "#627EEA",
    "Arbitrum":  "#28A0F0",
    "Base":      "#0052FF",
    "BSC":       "#F0B90B",
    "Polygon":   "#8247E5",
    "Avalanche": "#E84142",
    "Solana":    "#9945FF",
    "Optimism":  "#FF0420",
}

PROTOCOLO_ICONES: dict[str, str] = {
    "Uniswap v3":  "🦄",
    "Uniswap v2":  "🦄",
    "PancakeSwap": "🥞",
    "Curve":       "🌊",
    "Balancer":    "⚖️",
    "SushiSwap":   "🍣",
    "Raydium":     "☀️",
    "Orca":        "🐋",
}

# Cor padrão para chains/protocolos desconhecidos
_COR_PADRAO_CHAIN = "#64748B"
_COR_PADRAO_PROTOCOLO = "#475569"


# ─────────────────────────────────────────────
# FORMATAÇÃO NUMÉRICA
# ─────────────────────────────────────────────

def fmt_usd(valor: float, decimais: int = 2) -> str:
    """
    Formata um valor float como dólares americanos.

    Exemplos:
        fmt_usd(1234.5)      → '$ 1,234.50'
        fmt_usd(-500.1, 0)   → '$ -500'
        fmt_usd(0)           → '$ 0.00'
    """
    if valor is None:
        return "$ —"
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return "$ —"

    if valor < 0:
        return f"-$ {abs(valor):,.{decimais}f}"
    return f"$ {valor:,.{decimais}f}"


def fmt_pct(valor: float, decimais: int = 2) -> str:
    """
    Formata um valor float como percentual com sinal explícito.

    Exemplos:
        fmt_pct(12.345)   → '+12.35%'
        fmt_pct(-5.67)    → '-5.67%'
        fmt_pct(0)        → '0.00%'
    """
    if valor is None:
        return "—%"
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return "—%"

    if valor > 0:
        return f"+{valor:.{decimais}f}%"
    return f"{valor:.{decimais}f}%"


def fmt_token(valor: float, decimais: int = 6) -> str:
    """
    Formata a quantidade de um token cripto com casas decimais configuráveis.

    Exemplos:
        fmt_token(1.23456789)    → '1.234568'
        fmt_token(0.0001, 8)     → '0.00010000'
        fmt_token(1000, 2)       → '1,000.00'
    """
    if valor is None:
        return "—"
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return "—"

    return f"{valor:,.{decimais}f}"


# ─────────────────────────────────────────────
# CORES
# ─────────────────────────────────────────────

def cor_valor(valor: float) -> str:
    """
    Retorna uma cor hexadecimal baseada no sinal do valor:
        positivo → '#10B981' (verde)
        negativo → '#EF4444' (vermelho)
        zero     → '#94A3B8' (cinza)
    """
    if valor is None:
        return "#94A3B8"
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return "#94A3B8"

    if valor > 0:
        return "#10B981"
    if valor < 0:
        return "#EF4444"
    return "#94A3B8"


# ─────────────────────────────────────────────
# BADGES HTML
# ─────────────────────────────────────────────

def _badge_html(
    texto: str,
    cor_bg: str,
    cor_texto: str = "#FFFFFF",
    negrito: bool = True,
) -> str:
    """Gera HTML de um badge inline com estilo consistente."""
    peso = "600" if negrito else "400"
    return (
        f'<span style="'
        f"background-color:{cor_bg};"
        f"color:{cor_texto};"
        f"padding:2px 10px;"
        f"border-radius:12px;"
        f"font-size:0.78rem;"
        f"font-weight:{peso};"
        f'white-space:nowrap;">'
        f"{texto}"
        f"</span>"
    )


def badge_chain(chain: str) -> str:
    """
    Retorna HTML de um badge colorido para a chain informada.

    Chains suportadas: Ethereum, Arbitrum, Base, BSC, Polygon, Avalanche,
                       Solana, Optimism.
    Chains desconhecidas recebem cor cinza neutra.

    Exemplo de uso no Streamlit:
        st.markdown(badge_chain("Arbitrum"), unsafe_allow_html=True)
    """
    chain = chain.strip() if chain else "—"
    cor = CHAIN_CORES.get(chain, _COR_PADRAO_CHAIN)

    # BSC usa texto escuro pois o fundo é amarelo
    cor_texto = "#1A1A1A" if chain == "BSC" else "#FFFFFF"

    return _badge_html(chain, cor, cor_texto)


def badge_protocolo(protocolo: str) -> str:
    """
    Retorna HTML de um badge para o protocolo informado.
    Inclui o ícone quando disponível.

    Exemplo de uso no Streamlit:
        st.markdown(badge_protocolo("Uniswap v3"), unsafe_allow_html=True)
    """
    protocolo = protocolo.strip() if protocolo else "—"
    icone = PROTOCOLO_ICONES.get(protocolo, "")
    label = f"{icone} {protocolo}".strip() if icone else protocolo

    return _badge_html(label, _COR_PADRAO_PROTOCOLO, "#FFFFFF")


# ─────────────────────────────────────────────
# HELPERS EXTRAS
# ─────────────────────────────────────────────

def fmt_dias(dias: int) -> str:
    """
    Formata número de dias de forma legível.

    Exemplos:
        fmt_dias(1)    → '1 dia'
        fmt_dias(45)   → '45 dias'
        fmt_dias(365)  → '1 ano'
        fmt_dias(400)  → '1 ano e 35 dias'
    """
    if dias is None or dias < 0:
        return "—"
    if dias == 0:
        return "0 dias"

    anos = dias // 365
    resto = dias % 365

    partes = []
    if anos:
        partes.append(f"{anos} {'ano' if anos == 1 else 'anos'}")
    if resto:
        partes.append(f"{resto} {'dia' if resto == 1 else 'dias'}")

    return " e ".join(partes)


def fmt_numero_compacto(valor: float) -> str:
    """
    Formata grandes números de forma compacta.

    Exemplos:
        fmt_numero_compacto(1_500_000) → '$ 1.50M'
        fmt_numero_compacto(25_000)    → '$ 25.00K'
        fmt_numero_compacto(999)       → '$ 999.00'
    """
    if valor is None:
        return "$ —"
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return "$ —"

    abs_val = abs(valor)
    sinal = "-" if valor < 0 else ""

    if abs_val >= 1_000_000:
        return f"{sinal}$ {abs_val / 1_000_000:.2f}M"
    if abs_val >= 1_000:
        return f"{sinal}$ {abs_val / 1_000:.2f}K"
    return f"{sinal}$ {abs_val:.2f}"


def delta_color_streamlit(valor: float) -> str:
    """
    Retorna a string de cor para o parâmetro delta_color do st.metric().

    Positivo → 'normal'   (verde nativo do Streamlit)
    Negativo → 'inverse'  (vermelho nativo do Streamlit)
    Zero     → 'off'
    """
    if valor is None:
        return "off"
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return "off"

    if valor > 0:
        return "normal"
    if valor < 0:
        return "inverse"
    return "off"
