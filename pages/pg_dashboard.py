import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date, datetime
import database as db
import calculators as calc
import utils


# ─────────────────────────────────────────────
# CSS GLOBAL
# ─────────────────────────────────────────────

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Reset e base */
.lp-card {
    background: #0D1F33;
    border: 1px solid rgba(37, 99, 235, 0.18);
    border-radius: 14px;
    padding: 20px 24px;
    text-align: center;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s ease, transform 0.2s ease;
}
.lp-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #2563EB, #10B981);
    opacity: 0.7;
}
.lp-card:hover {
    border-color: rgba(37, 99, 235, 0.45);
    transform: translateY(-2px);
}
.lp-card-label {
    color: #94A3B8;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.lp-card-value {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 5px;
    font-family: 'Inter', monospace;
}
.lp-card-sub {
    color: #64748B;
    font-size: 0.75rem;
    font-weight: 400;
}

/* Tabela de pools */
.pool-table-container {
    background: #0D1F33;
    border: 1px solid rgba(37, 99, 235, 0.15);
    border-radius: 14px;
    overflow: hidden;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}
.pool-table-header {
    display: grid;
    grid-template-columns: 2fr 1fr 1.2fr 1.2fr 1.2fr 1fr 1fr 0.7fr;
    gap: 8px;
    padding: 14px 20px;
    background: rgba(37, 99, 235, 0.08);
    border-bottom: 1px solid rgba(37, 99, 235, 0.15);
    color: #64748B;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
}
.pool-table-row {
    display: grid;
    grid-template-columns: 2fr 1fr 1.2fr 1.2fr 1.2fr 1fr 1fr 0.7fr;
    gap: 8px;
    padding: 14px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    align-items: center;
    transition: background 0.15s;
}
.pool-table-row:hover {
    background: rgba(37, 99, 235, 0.06);
}
.pool-table-row:last-child {
    border-bottom: none;
}
.pool-name {
    color: #F1F5F9;
    font-weight: 600;
    font-size: 0.88rem;
}
.pool-tokens {
    color: #94A3B8;
    font-size: 0.75rem;
    margin-top: 2px;
}
.pool-cell {
    color: #CBD5E1;
    font-size: 0.84rem;
    font-weight: 500;
}
.pool-cell-mono {
    color: #CBD5E1;
    font-size: 0.84rem;
    font-weight: 500;
    font-family: 'Inter', monospace;
}
.status-ativa {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(16, 185, 129, 0.12);
    color: #10B981;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.status-inativa {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(239, 68, 68, 0.12);
    color: #EF4444;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
}

/* Welcome state */
.welcome-container {
    background: linear-gradient(135deg, #0D1F33 0%, #0a1929 100%);
    border: 1px solid rgba(37, 99, 235, 0.25);
    border-radius: 20px;
    padding: 64px 40px;
    text-align: center;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    position: relative;
    overflow: hidden;
}
.welcome-container::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at 50% 50%, rgba(37, 99, 235, 0.05) 0%, transparent 60%);
    pointer-events: none;
}
.welcome-icon {
    font-size: 4rem;
    margin-bottom: 20px;
    display: block;
    filter: drop-shadow(0 0 20px rgba(37, 99, 235, 0.5));
}
.welcome-title {
    color: #F1F5F9;
    font-size: 1.8rem;
    font-weight: 700;
    margin-bottom: 12px;
}
.welcome-sub {
    color: #64748B;
    font-size: 1rem;
    margin-bottom: 28px;
    line-height: 1.6;
}
.welcome-steps {
    display: inline-flex;
    flex-direction: column;
    gap: 10px;
    text-align: left;
    background: rgba(37, 99, 235, 0.06);
    border: 1px solid rgba(37, 99, 235, 0.15);
    border-radius: 12px;
    padding: 20px 28px;
    margin-top: 8px;
}
.welcome-step {
    color: #94A3B8;
    font-size: 0.88rem;
    display: flex;
    align-items: center;
    gap: 10px;
}
.welcome-step-num {
    background: #2563EB;
    color: white;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.72rem;
    font-weight: 700;
    flex-shrink: 0;
}

/* Section headers */
.section-header {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    color: #F1F5F9;
    font-size: 1.05rem;
    font-weight: 600;
    margin: 0 0 16px 0;
    display: flex;
    align-items: center;
    gap: 8px;
    letter-spacing: -0.01em;
}
.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(37, 99, 235, 0.3), transparent);
    margin-left: 8px;
}

/* Sparkline label */
.sparkline-label {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    color: #94A3B8;
    font-size: 0.78rem;
    font-weight: 500;
    text-align: center;
    margin-bottom: 4px;
}
.sparkline-value {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    color: #F1F5F9;
    font-size: 1.1rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 2px;
}
</style>
"""


# ─────────────────────────────────────────────
# HELPERS INTERNOS
# ─────────────────────────────────────────────

def _dias_desde(data_str: str | None) -> int:
    if not data_str:
        return 0
    try:
        inicio = datetime.strptime(data_str[:10], "%Y-%m-%d").date()
        return max((date.today() - inicio).days, 0)
    except Exception:
        return 0


@st.cache_data(ttl=60)
def _carregar_dados_dashboard() -> tuple[list, list]:
    """Carrega resumo e dados de posicoes/taxas em cache."""
    resumo = db.resumo_pools()
    # Para métricas calculadas, carrega posicoes e taxas de cada pool
    detalhes: list[dict] = []
    for pool in resumo:
        pid = pool["pool_id"]
        posicoes = db.listar_posicoes(pid)
        taxas = db.listar_taxas(pid)
        metricas = calc.calcular_metricas_pool(posicoes, taxas)
        detalhes.append({
            **pool,
            "posicoes": posicoes,
            "taxas": taxas,
            "metricas": metricas,
        })
    return resumo, detalhes


def _calcular_metricas_globais(detalhes: list[dict]) -> dict:
    """Agrega métricas de todas as pools em números globais."""
    capital_total = 0.0
    fees_total = 0.0
    capital_ativo = 0.0
    apr_ponderado_num = 0.0
    pools_ativas = 0
    pools_inativas = 0

    for d in detalhes:
        m = d["metricas"]
        cap = float(d.get("capital_total") or 0)
        fees = float(d.get("total_taxas") or 0)
        capital_total += cap
        fees_total += fees

        if d.get("ativa"):
            pools_ativas += 1
            capital_ativo += cap
            apr_ponderado_num += m["apr"] * cap
        else:
            pools_inativas += 1

    apr_medio = (apr_ponderado_num / capital_ativo) if capital_ativo > 0 else 0.0

    return {
        "capital_total": capital_total,
        "fees_total": fees_total,
        "apr_medio": apr_medio,
        "pools_ativas": pools_ativas,
        "pools_inativas": pools_inativas,
        "pools_total": pools_ativas + pools_inativas,
    }


# ─────────────────────────────────────────────
# COMPONENTES DE UI
# ─────────────────────────────────────────────

def _render_header_metricas(globais: dict, detalhes: list = None) -> None:
    import streamlit.components.v1 as components

    apr = globais["apr_medio"]
    apy = calc.calcular_apy(apr)
    cor_apr = "#10B981" if apr >= 15 else ("#F59E0B" if apr >= 5 else "#EF4444")
    pct_fees = (globais["fees_total"] / globais["capital_total"] * 100) if globais["capital_total"] > 0 else 0.0
    cor_fees = "#10B981" if globais["fees_total"] > 0 else "#94A3B8"
    n_pools = globais["pools_total"]
    pools_label = f"em {n_pools} pool{'s' if n_pools != 1 else ''}"
    sub_pools = (f"{globais['pools_inativas']} inativa{'s' if globais['pools_inativas'] != 1 else ''}"
                 if globais["pools_inativas"] > 0 else "todas ativas")

    # Net Yield Médio ponderado
    _ny_num = 0.0
    _ny_den = 0.0
    _ny_algum = False
    if detalhes:
        for _d in detalhes:
            _m = _d.get("metricas", {})
            _cap = float(_d.get("capital_total") or 0)
            _apr_d = _m.get("apr", 0)
            _il_d  = _m.get("il_pct")
            if _il_d is not None and _cap > 0:
                _ny_val_d = calc.calcular_net_yield(_apr_d, _il_d)
                if _ny_val_d is not None:
                    _ny_num += _ny_val_d * _cap
                    _ny_den += _cap
                    _ny_algum = True

    if _ny_algum and _ny_den > 0:
        _net_yield_medio = _ny_num / _ny_den
        _ny_val_str = utils.fmt_pct(_net_yield_medio)
        _ny_cor = "#10B981" if _net_yield_medio >= 0 else "#EF4444"
        _ny_sub = "APR médio - IL médio"
    else:
        _ny_val_str = "—"
        _ny_cor = "#475569"
        _ny_sub = "Insira preços na Análise"

    cards = [
        ("Capital Investido",    utils.fmt_usd(globais["capital_total"], 0), pools_label,                        "#F1F5F9"),
        ("Fees Coletadas",       utils.fmt_usd(globais["fees_total"], 2),    f"{utils.fmt_pct(pct_fees)} do capital", cor_fees),
        ("APR Médio Ponderado",  utils.fmt_pct(apr),                         f"APY {utils.fmt_pct(apy)}",        cor_apr),
        ("Pools Ativas",         str(globais["pools_ativas"]),                sub_pools,                          "#2563EB"),
        ("Net Yield Médio",      _ny_val_str,                                 _ny_sub,                            _ny_cor),
    ]

    cards_html = ""
    for label, valor, sub, cor in cards:
        cards_html += f"""
        <div class="card">
            <div class="card-top"></div>
            <div class="label">{label}</div>
            <div class="value" style="color:{cor}">{valor}</div>
            <div class="sub">{sub}</div>
        </div>"""

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{background:transparent;font-family:'Segoe UI',Inter,sans-serif}}
    .row{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;padding:2px}}
    .card{{background:#0D1F33;border:1px solid rgba(37,99,235,0.18);border-radius:14px;
           padding:16px 16px;position:relative;overflow:hidden;
           transition:border-color .25s,transform .2s}}
    .card:hover{{border-color:rgba(37,99,235,0.45);transform:translateY(-2px)}}
    .card-top{{position:absolute;top:0;left:0;right:0;height:2px;
               background:linear-gradient(90deg,#2563EB,#10B981);opacity:.7}}
    .label{{color:#64748B;font-size:0.68rem;font-weight:600;letter-spacing:.08em;
            text-transform:uppercase;margin-bottom:8px}}
    .value{{font-size:1.5rem;font-weight:800;line-height:1.1;margin-bottom:6px;
            font-variant-numeric:tabular-nums}}
    .sub{{color:#475569;font-size:0.72rem}}
    </style></head><body>
    <div class="row">{cards_html}</div>
    </body></html>"""

    components.html(html, height=115, scrolling=False)


def _gauge_fig(valor: float, cor: str) -> go.Figure:
    """Retorna figura do gauge para um valor específico (usado na animação)."""
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=valor,
            number={
                "suffix": "%",
                "font": {"size": 36, "color": cor, "family": "Inter, monospace"},
                "valueformat": ".1f",
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 1,
                    "tickcolor": "#1E3A5F",
                    "tickfont": {"size": 9, "color": "#475569"},
                    "tickvals": [0, 15, 30, 50, 75, 100],
                    "ticktext": ["0%", "15%", "30%", "50%", "75%", "100%"],
                },
                "bar": {"color": cor, "thickness": 0.20},
                "bgcolor": "#060B14",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 5],    "color": "rgba(239,68,68,0.10)"},
                    {"range": [5, 15],   "color": "rgba(245,158,11,0.10)"},
                    {"range": [15, 50],  "color": "rgba(16,185,129,0.12)"},
                    {"range": [50, 100], "color": "rgba(37,99,235,0.10)"},
                ],
                "threshold": {
                    "line": {"color": cor, "width": 2},
                    "thickness": 0.55,
                    "value": valor,
                },
            },
        ),
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#F1F5F9", family="Inter, Segoe UI, sans-serif"),
            margin=dict(l=10, r=10, t=20, b=10),
            height=190,
        ),
    )


def _render_gauge_apr(apr_medio: float, apy: float, placeholder) -> None:
    """Anima o gauge de 0 → apr_medio via Python loop no st.empty placeholder."""
    import time

    if apr_medio >= 15:
        cor = "#10B981"
        zona = "Excelente"
    elif apr_medio >= 5:
        cor = "#F59E0B"
        zona = "Moderado"
    else:
        cor = "#EF4444"
        zona = "Baixo"

    key = f"gauge_played_{round(apr_medio, 2)}"
    ja_animou = st.session_state.get(key, False)

    if not ja_animou:
        steps = 30
        for i in range(steps + 1):
            val = apr_medio * i / steps
            placeholder.plotly_chart(
                _gauge_fig(val, cor),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            time.sleep(0.025)
        st.session_state[key] = True
    else:
        placeholder.plotly_chart(
            _gauge_fig(apr_medio, cor),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    # Labels abaixo do gauge — bem espaçados
    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-around;gap:8px;
             background:#0D1F33;border:1px solid rgba(37,99,235,0.15);
             border-radius:10px;padding:10px 6px;margin-top:6px">
            <div style="text-align:center">
                <div style="color:#475569;font-size:0.65rem;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:4px">APR</div>
                <div style="color:{cor};font-size:1.1rem;font-weight:800;font-family:monospace">{utils.fmt_pct(apr_medio)}</div>
            </div>
            <div style="width:1px;background:rgba(255,255,255,0.06)"></div>
            <div style="text-align:center">
                <div style="color:#475569;font-size:0.65rem;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:4px">APY</div>
                <div style="color:{cor};font-size:1.1rem;font-weight:800;font-family:monospace">{utils.fmt_pct(apy)}</div>
            </div>
            <div style="width:1px;background:rgba(255,255,255,0.06)"></div>
            <div style="text-align:center">
                <div style="color:#475569;font-size:0.65rem;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:4px">Zona</div>
                <div style="color:{cor};font-size:1.1rem;font-weight:700">{zona}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_tabela_pools(detalhes: list[dict]) -> None:
    """Tabela de pools usando st.components.v1.html para garantir renderização."""
    import streamlit.components.v1 as components

    rows_html = ""
    for d in detalhes:
        m = d["metricas"]
        apr = m["apr"]
        cor_apr = utils.cor_valor(apr)
        dias = _dias_desde(d.get("data_primeira_posicao"))
        nome = d.get("nome", "—")
        tokens = f"{d.get('token_a','?')}/{d.get('token_b','?')}"
        fee_tier = d.get("fee_tier", "")
        fee_str = f" · {fee_tier}" if fee_tier else ""
        chain_badge = utils.badge_chain(d.get("chain", "—"))
        proto_badge = utils.badge_protocolo(d.get("protocolo", "—"))
        status_html = (
            '<span class="pill green">● Ativa</span>'
            if d.get("ativa")
            else '<span class="pill red">● Inativa</span>'
        )
        capital_str = utils.fmt_usd(float(d.get("capital_total") or 0))
        fees_str    = utils.fmt_usd(float(d.get("total_taxas") or 0))
        apr_str     = utils.fmt_pct(apr)
        dias_str    = utils.fmt_dias(dias) if dias > 0 else "—"

        # Range badge
        _pmin = d.get("preco_min")
        _pmax = d.get("preco_max")
        if _pmin and _pmax:
            # Try to determine in/out range using preco_atual if available
            _preco_atual_pool = d.get("preco_atual_a") or d.get("preco_a")
            if _preco_atual_pool is not None:
                try:
                    _rng = calc.status_range(float(_preco_atual_pool), float(_pmin), float(_pmax))
                    if _rng.get("in_range"):
                        range_html = '<span class="pill green">IN</span>'
                    else:
                        range_html = '<span class="pill red">OUT</span>'
                except Exception:
                    range_html = '<span style="color:#94A3B8;font-size:0.75rem">—</span>'
            else:
                range_html = '<span style="color:#64748B;font-size:0.72rem">conf.</span>'
        else:
            range_html = '<span style="color:#334155;font-size:0.75rem">—</span>'

        rows_html += f"""
        <div class="row">
            <div class="cell">
                <div class="name">{nome}</div>
                <div class="sub">{tokens}{fee_str}</div>
            </div>
            <div class="cell">{chain_badge}</div>
            <div class="cell">{proto_badge}</div>
            <div class="cell mono">{capital_str}</div>
            <div class="cell mono" style="color:#10B981">{fees_str}</div>
            <div class="cell mono" style="color:{cor_apr};font-weight:700">{apr_str}</div>
            <div class="cell" style="color:#94A3B8;font-size:0.78rem">{dias_str}</div>
            <div class="cell">{range_html}</div>
            <div class="cell">{status_html}</div>
        </div>"""

    n_rows = len(detalhes)
    altura = max(120, n_rows * 58 + 52)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; font-family: 'Segoe UI', Inter, sans-serif; }}
  .table {{ width: 100%; border-radius: 12px; overflow: hidden;
            border: 1px solid rgba(37,99,235,0.18); background: #0D1F33; }}
  .header, .row {{
    display: grid;
    grid-template-columns: 2fr 0.9fr 1.1fr 1.1fr 1fr 0.9fr 0.9fr 0.7fr 0.7fr;
    align-items: center;
    gap: 6px;
    padding: 10px 16px;
  }}
  .header {{
    background: rgba(37,99,235,0.10);
    border-bottom: 1px solid rgba(37,99,235,0.18);
    color: #475569;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
  }}
  .row {{
    border-bottom: 1px solid rgba(255,255,255,0.04);
    transition: background 0.15s;
  }}
  .row:last-child {{ border-bottom: none; }}
  .row:hover {{ background: rgba(37,99,235,0.06); }}
  .cell {{ color: #CBD5E1; font-size: 0.82rem; }}
  .mono {{ font-variant-numeric: tabular-nums; }}
  .name {{ color: #F1F5F9; font-weight: 600; font-size: 0.85rem; }}
  .sub  {{ color: #64748B; font-size: 0.72rem; margin-top: 2px; }}
  .pill {{ display: inline-block; padding: 2px 10px; border-radius: 20px;
           font-size: 0.70rem; font-weight: 600; }}
  .pill.green {{ background: rgba(16,185,129,0.15); color: #10B981; }}
  .pill.red   {{ background: rgba(239,68,68,0.15);  color: #EF4444; }}
</style>
</head>
<body>
<div class="table">
  <div class="header">
    <div>POOL</div><div>CHAIN</div><div>PROTOCOLO</div>
    <div>CAPITAL</div><div>FEES</div><div>APR</div>
    <div>TEMPO</div><div>RANGE</div><div>STATUS</div>
  </div>
  {rows_html}
</div>
</body>
</html>"""

    components.html(html, height=altura, scrolling=False)


def _render_donut_capital(detalhes: list[dict]) -> go.Figure:
    """Donut chart de distribuição do capital por pool."""

    labels = []
    values = []
    cores = []
    textos_hover = []

    total = sum(float(d.get("capital_total") or 0) for d in detalhes)

    for d in detalhes:
        cap = float(d.get("capital_total") or 0)
        if cap <= 0:
            continue
        chain = d.get("chain", "")
        cor = utils.CHAIN_CORES.get(chain, "#64748B")
        labels.append(d.get("nome", "—"))
        values.append(cap)
        cores.append(cor)
        pct = (cap / total * 100) if total > 0 else 0
        textos_hover.append(
            f"<b>{d.get('nome','—')}</b><br>"
            f"Capital: {utils.fmt_usd(cap)}<br>"
            f"Participação: {pct:.1f}%<br>"
            f"Chain: {chain}<br>"
            f"Protocolo: {d.get('protocolo','—')}"
        )

    if not values:
        values = [1]
        labels = ["Sem dados"]
        cores = ["#334155"]
        textos_hover = ["Nenhuma pool com capital"]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.62,
            marker=dict(
                colors=cores,
                line=dict(color="#060B14", width=2),
            ),
            customdata=textos_hover,
            hovertemplate="%{customdata}<extra></extra>",
            textinfo="percent",
            textposition="outside",
            textfont=dict(size=11, color="#CBD5E1", family="Inter, Segoe UI, sans-serif"),
            insidetextorientation="radial",
            pull=[0.03] * len(values),
            sort=True,
            direction="clockwise",
        )
    )

    total_fmt = utils.fmt_usd(total, 0)
    fig.add_annotation(
        text=f"<b style='font-size:1.1em'>{total_fmt}</b><br><span style='color:#64748B;font-size:0.8em'>Total</span>",
        x=0.5, y=0.5,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=16, color="#F1F5F9", family="Inter, Segoe UI, sans-serif"),
        align="center",
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F1F5F9", family="Inter, Segoe UI, sans-serif"),
        margin=dict(l=10, r=10, t=20, b=10),
        height=230,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color="#94A3B8", family="Inter, Segoe UI, sans-serif"),
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
        ),
        transition=dict(duration=500, easing="cubic-in-out"),
    )

    return fig


def _render_barras_fees(detalhes: list[dict]) -> go.Figure:
    """Gráfico de barras horizontal com fees por pool, ordenado descendente."""

    data_sorted = sorted(
        [d for d in detalhes if float(d.get("total_taxas") or 0) > 0],
        key=lambda x: float(x.get("total_taxas") or 0),
        reverse=False,  # ascending para barras horizontais (maior fica no topo)
    )

    if not data_sorted:
        fig = go.Figure()
        fig.add_annotation(
            text="Nenhuma fee registrada ainda",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=14, color="#64748B", family="Inter, Segoe UI, sans-serif"),
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,31,51,0.5)",
            font=dict(color="#F1F5F9", family="Inter, Segoe UI, sans-serif"),
            margin=dict(l=20, r=20, t=40, b=20),
            height=130,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    nomes = [d.get("nome", "—") for d in data_sorted]
    fees = [float(d.get("total_taxas") or 0) for d in data_sorted]
    capitais = [float(d.get("capital_total") or 0) for d in data_sorted]

    # Cores com gradiente baseado na proporção fee/capital
    cores_barras = []
    for f, c in zip(fees, capitais):
        ratio = (f / c) if c > 0 else 0
        if ratio >= 0.10:
            cores_barras.append("#10B981")
        elif ratio >= 0.04:
            cores_barras.append("#34D399")
        else:
            cores_barras.append("#6EE7B7")

    hover_texts = [
        f"<b>{n}</b><br>Fees: {utils.fmt_usd(f)}<br>Capital: {utils.fmt_usd(c)}<br>Yield: {utils.fmt_pct(f/c*100 if c > 0 else 0)}"
        for n, f, c in zip(nomes, fees, capitais)
    ]

    # Animação: frames de 0 → valor real
    n_frames = 25
    frames = [
        go.Frame(data=[go.Bar(
            y=nomes,
            x=[f * i / n_frames for f in fees],
            orientation="h",
            marker=dict(color=cores_barras, opacity=0.9),
        )])
        for i in range(1, n_frames + 1)
    ]

    fig = go.Figure(
        data=[go.Bar(
            y=nomes,
            x=[0] * len(fees),
            orientation="h",
            marker=dict(color=cores_barras, line=dict(color="rgba(0,0,0,0)", width=0), opacity=0.9),
            text=[utils.fmt_usd(f) for f in fees],
            textposition="outside",
            textfont=dict(size=10, color="#94A3B8", family="Inter, Segoe UI, sans-serif"),
            hovertext=hover_texts,
            hoverinfo="text",
        )],
        frames=frames,
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,31,51,0.3)",
            font=dict(color="#F1F5F9", family="Inter, Segoe UI, sans-serif"),
            margin=dict(l=10, r=70, t=10, b=40),
            height=max(140, 44 * len(data_sorted) + 50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, tickfont=dict(size=10, color="#94A3B8"), automargin=True),
            bargap=0.3,
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                x=0.5, y=-0.22,
                xanchor="center",
                buttons=[dict(
                    label="▶  Animar",
                    method="animate",
                    args=[None, dict(frame=dict(duration=30, redraw=True), fromcurrent=True)],
                )],
                font=dict(size=10, color="#94A3B8"),
                bgcolor="#0D1F33",
                bordercolor="#1E3A5F",
            )],
        ),
    )

    return fig


def _render_sparkline(pool: dict, posicoes: list[dict], cor: str) -> go.Figure:
    """Mini sparkline da evolução de capital de uma pool."""

    fig = go.Figure()

    if posicoes:
        datas = [p.get("data", "")[:10] for p in posicoes]
        # Capital acumulado ao longo do tempo
        capitais_acum = []
        acum = 0.0
        for p in posicoes:
            acum += float(p.get("capital_usd") or 0)
            capitais_acum.append(acum)

        fig.add_trace(
            go.Scatter(
                x=datas,
                y=capitais_acum,
                mode="lines",
                fill="tozeroy",
                fillcolor=f"rgba{tuple(int(cor.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.12,)}",
                line=dict(color=cor, width=2),
                hovertemplate="<b>%{x}</b><br>Capital: $ %{y:,.0f}<extra></extra>",
                showlegend=False,
            )
        )

        # Marcador no último ponto
        if datas:
            fig.add_trace(
                go.Scatter(
                    x=[datas[-1]],
                    y=[capitais_acum[-1]],
                    mode="markers",
                    marker=dict(color=cor, size=7, line=dict(color="#060B14", width=2)),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
    else:
        fig.add_annotation(
            text="Sem posições",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=11, color="#475569", family="Inter, Segoe UI, sans-serif"),
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,31,51,0.4)",
        font=dict(color="#F1F5F9", family="Inter, Segoe UI, sans-serif"),
        margin=dict(l=4, r=4, t=4, b=4),
        height=80,
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.04)",
            showticklabels=False,
            zeroline=False,
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#0D1F33",
            bordercolor=cor,
            font=dict(color="#F1F5F9", size=11),
        ),
    )

    return fig


def _render_capital_linhas(detalhes: list[dict]) -> None:
    """Gráfico de linhas com evolução do capital acumulado por pool."""
    cores_fallback = ["#2563EB", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444", "#F97316"]

    fig = go.Figure()
    tem_dados = False

    for idx, d in enumerate(detalhes):
        posicoes = d.get("posicoes", [])
        if not posicoes:
            continue

        cor = utils.CHAIN_CORES.get(d.get("chain", ""), cores_fallback[idx % len(cores_fallback)])
        nome = d.get("nome", "—")

        # Ordena por data e acumula capital
        posicoes_ord = sorted(posicoes, key=lambda p: p.get("data", ""))
        datas, capitais_acum = [], []
        acum = 0.0
        for p in posicoes_ord:
            acum += float(p.get("capital_usd") or 0)
            datas.append(p.get("data", "")[:10])
            capitais_acum.append(acum)

        if not datas:
            continue

        tem_dados = True

        # Linha principal
        fig.add_trace(go.Scatter(
            x=datas,
            y=capitais_acum,
            mode="lines+markers",
            name=nome,
            line=dict(color=cor, width=2.5, shape="spline", smoothing=0.8),
            marker=dict(color=cor, size=5, line=dict(color="#060B14", width=1.5)),
            fill="tozeroy",
            fillcolor=f"rgba({int(cor[1:3],16)},{int(cor[3:5],16)},{int(cor[5:7],16)},0.06)",
            hovertemplate=f"<b>{nome}</b><br>%{{x}}<br>Capital: $%{{y:,.2f}}<extra></extra>",
        ))

        # Marcador no último ponto com valor
        fig.add_trace(go.Scatter(
            x=[datas[-1]],
            y=[capitais_acum[-1]],
            mode="markers+text",
            marker=dict(color=cor, size=9, line=dict(color="#060B14", width=2)),
            text=[f"  {utils.fmt_usd(capitais_acum[-1], 0)}"],
            textposition="middle right",
            textfont=dict(color=cor, size=10, family="Inter, monospace"),
            showlegend=False,
            hoverinfo="skip",
        ))

    if not tem_dados:
        fig.add_annotation(
            text="Registre aportes para ver a evolução do capital",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=13, color="#475569"),
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,31,51,0.4)",
        font=dict(color="#F1F5F9", family="Inter, Segoe UI, sans-serif"),
        margin=dict(l=10, r=80, t=10, b=30),
        height=220,
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            font=dict(size=10, color="#94A3B8"),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            showgrid=False, zeroline=False,
            tickfont=dict(size=9, color="#475569"),
        ),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=False,
            tickfont=dict(size=9, color="#475569"),
            tickformat="$,.0f",
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#0D1F33", bordercolor="#2563EB",
                        font=dict(color="#F1F5F9", size=11)),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False},
                    key="capital_linhas")


def _render_welcome() -> None:
    """Tela de boas-vindas quando não há pools cadastradas."""
    st.markdown(
        """
        <div class="welcome-container">
            <span class="welcome-icon">💧</span>
            <div class="welcome-title">Bem-vindo ao Liquidity Pool Tracker</div>
            <div class="welcome-sub">
                Ainda não há pools cadastradas.<br>
                Comece adicionando sua primeira posição de liquidez.
            </div>
            <div class="welcome-steps">
                <div class="welcome-step">
                    <span class="welcome-step-num">1</span>
                    Acesse <strong style="color:#F1F5F9">Gerenciar Pools</strong> no menu lateral
                </div>
                <div class="welcome-step">
                    <span class="welcome-step-num">2</span>
                    Crie uma nova pool com protocolo, chain e par de tokens
                </div>
                <div class="welcome-step">
                    <span class="welcome-step-num">3</span>
                    Registre suas posições de entrada e fees coletadas
                </div>
                <div class="welcome-step">
                    <span class="welcome-step-num">4</span>
                    Acompanhe APR, APY e performance em tempo real
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# RENDER PRINCIPAL
# ─────────────────────────────────────────────

def render() -> None:
    """Página principal do dashboard de pools de liquidez."""

    # Injeta CSS global
    st.markdown(_CSS, unsafe_allow_html=True)

    # Título da página
    st.markdown(
        """
        <div style="margin-bottom:28px">
            <h1 style="
                font-family: Inter, 'Segoe UI', sans-serif;
                font-size: 1.75rem;
                font-weight: 800;
                color: #F1F5F9;
                margin: 0 0 4px 0;
                letter-spacing: -0.02em;
            ">
                Dashboard
                <span style="
                    background: linear-gradient(135deg, #2563EB, #10B981);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                ">Liquidity Pools</span>
            </h1>
            <div style="color:#475569;font-size:0.85rem;font-family:Inter,'Segoe UI',sans-serif">
                Visão geral consolidada das suas posições de liquidez DeFi
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Carrega dados ──────────────────────────────────────────────────────────
    try:
        resumo, detalhes = _carregar_dados_dashboard()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    # ── Estado vazio ───────────────────────────────────────────────────────────
    if not detalhes:
        _render_welcome()
        return

    # ── Métricas globais ───────────────────────────────────────────────────────
    globais = _calcular_metricas_globais(detalhes)

    # ── SEÇÃO 1 — Metric Cards ─────────────────────────────────────────────────
    _render_header_metricas(globais, detalhes=detalhes)

    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)

    # ── SEÇÃO 2 — Gauge APR + Donut Capital ───────────────────────────────────
    col_gauge, col_donut = st.columns([1, 1.4], gap="large")

    with col_gauge:
        st.markdown(
            '<div class="section-header">⚡ Performance APR</div>',
            unsafe_allow_html=True,
        )
        apy_medio = calc.calcular_apy(globais["apr_medio"])
        gauge_placeholder = st.empty()
        _render_gauge_apr(globais["apr_medio"], apy_medio, gauge_placeholder)

    with col_donut:
        st.markdown(
            '<div class="section-header">🥧 Distribuição do Capital</div>',
            unsafe_allow_html=True,
        )
        fig_donut = _render_donut_capital(detalhes)
        st.plotly_chart(
            fig_donut,
            use_container_width=True,
            config={"displayModeBar": False},
            key="donut_capital",
        )

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

    # ── SEÇÃO 3 — Tabela de Pools ──────────────────────────────────────────────
    st.markdown(
        '<div class="section-header">📊 Pools de Liquidez</div>',
        unsafe_allow_html=True,
    )
    _render_tabela_pools(detalhes)

    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)

    # ── SEÇÃO 4 — Barras de Fees ───────────────────────────────────────────────
    pools_com_fees = [d for d in detalhes if float(d.get("total_taxas") or 0) > 0]

    col_fees, col_spark_title = st.columns([1.2, 1], gap="large")

    with col_fees:
        st.markdown(
            '<div class="section-header">💰 Fees Coletadas por Pool</div>',
            unsafe_allow_html=True,
        )
        fig_fees = _render_barras_fees(detalhes)
        st.plotly_chart(
            fig_fees,
            use_container_width=True,
            config={"displayModeBar": False},
            key="bar_fees",
        )

    with col_spark_title:
        st.markdown(
            '<div class="section-header">📈 Evolução do Capital</div>',
            unsafe_allow_html=True,
        )
        _render_capital_linhas(detalhes)

    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)

    # ── SEÇÃO 5 — APR por Pool (mini barras horizontais) ──────────────────────
    pools_com_capital = [d for d in detalhes if float(d.get("capital_total") or 0) > 0]

    if len(pools_com_capital) > 1:
        st.markdown(
            '<div class="section-header">🎯 APR por Pool</div>',
            unsafe_allow_html=True,
        )

        sorted_apr = sorted(
            pools_com_capital,
            key=lambda d: d["metricas"]["apr"],
            reverse=True,
        )

        nomes_apr = [d.get("nome", "—") for d in sorted_apr]
        valores_apr = [d["metricas"]["apr"] for d in sorted_apr]
        cores_apr = [
            "#10B981" if a >= 15 else ("#F59E0B" if a >= 5 else "#EF4444")
            for a in valores_apr
        ]
        hover_apr = [
            f"<b>{n}</b><br>APR: {utils.fmt_pct(a)}<br>APY: {utils.fmt_pct(calc.calcular_apy(a))}<br>Capital: {utils.fmt_usd(float(d.get('capital_total') or 0))}"
            for n, a, d in zip(nomes_apr, valores_apr, sorted_apr)
        ]

        fig_apr = go.Figure(
            go.Bar(
                y=nomes_apr,
                x=valores_apr,
                orientation="h",
                marker=dict(
                    color=cores_apr,
                    opacity=0.85,
                    line=dict(color="rgba(0,0,0,0)", width=0),
                ),
                text=[utils.fmt_pct(a) for a in valores_apr],
                textposition="outside",
                textfont=dict(size=11, color="#94A3B8", family="Inter, Segoe UI, sans-serif"),
                hovertext=hover_apr,
                hoverinfo="text",
            )
        )

        fig_apr.add_vline(
            x=15,
            line=dict(color="rgba(16,185,129,0.35)", width=1.5, dash="dot"),
            annotation=dict(
                text="15% target",
                font=dict(size=10, color="#10B981", family="Inter, Segoe UI, sans-serif"),
                xanchor="left",
            ),
        )

        fig_apr.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,31,51,0.3)",
            font=dict(color="#F1F5F9", family="Inter, Segoe UI, sans-serif"),
            margin=dict(l=10, r=70, t=10, b=10),
            height=max(120, 40 * len(sorted_apr) + 40),
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.04)",
                zeroline=False,
                ticksuffix="%",
                tickfont=dict(size=10, color="#475569"),
            ),
            yaxis=dict(
                showgrid=False,
                tickfont=dict(size=11, color="#94A3B8", family="Inter, Segoe UI, sans-serif"),
                automargin=True,
            ),
            bargap=0.4,
            hoverlabel=dict(
                bgcolor="#0D1F33",
                bordercolor="#2563EB",
                font=dict(color="#F1F5F9", size=12),
            ),
        )

        st.plotly_chart(
            fig_apr,
            use_container_width=True,
            config={"displayModeBar": False},
            key="bar_apr_pools",
        )

    # ── Rodapé de atualização ──────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="
            text-align:right;
            color:#334155;
            font-size:0.72rem;
            font-family:Inter,'Segoe UI',sans-serif;
            margin-top:24px;
            padding-top:12px;
            border-top:1px solid rgba(255,255,255,0.04)
        ">
            Dados atualizados a cada 60 segundos · {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
        """,
        unsafe_allow_html=True,
    )
