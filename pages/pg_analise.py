import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
import database as db
import calculators as calc
import utils


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _layout_base(title: str = "") -> dict:
    """Retorna o layout padrão para todos os gráficos Plotly."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,31,51,0.8)",
        font=dict(color="#F1F5F9", family="Inter, Segoe UI, sans-serif", size=12),
        margin=dict(l=20, r=20, t=50 if title else 30, b=20),
        title=dict(
            text=title,
            font=dict(size=14, color="#94A3B8", family="Inter, Segoe UI, sans-serif"),
            x=0.01,
        ) if title else None,
        xaxis=dict(
            gridcolor="#0F1F35",
            zerolinecolor="#1E3A5F",
            tickfont=dict(color="#64748B", size=11),
            linecolor="#0F1F35",
        ),
        yaxis=dict(
            gridcolor="#0F1F35",
            zerolinecolor="#1E3A5F",
            tickfont=dict(color="#64748B", size=11),
            linecolor="#0F1F35",
        ),
        legend=dict(
            bgcolor="rgba(13,31,51,0.9)",
            bordercolor="#1E3A5F",
            borderwidth=1,
            font=dict(color="#94A3B8", size=11),
        ),
        hoverlabel=dict(
            bgcolor="#0D1F33",
            bordercolor="#2563EB",
            font=dict(color="#F1F5F9", size=12),
        ),
    )


def _section_header(titulo: str, subtitulo: str = "", icone: str = "") -> None:
    """Renderiza um cabeçalho de seção estilizado."""
    st.markdown(f"""
    <div style="
        display:flex; align-items:center; gap:0.75rem;
        margin: 2rem 0 1.25rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #0F1F35;
    ">
        {'<div style="font-size:1.25rem;line-height:1">' + icone + '</div>' if icone else ''}
        <div>
            <div style="font-size:0.68rem;font-weight:700;color:#2563EB;
                        letter-spacing:0.12em;text-transform:uppercase;
                        margin-bottom:0.15rem">{titulo}</div>
            {'<div style="font-size:0.8rem;color:#475569;font-weight:400">' + subtitulo + '</div>' if subtitulo else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _metric_card(label: str, valor: str, cor: str, subtitulo: str = "",
                 extra_html: str = "") -> str:
    """Gera HTML de um card de métrica principal."""
    return f"""
    <div class="lp-card-highlight" style="text-align:center;padding:1.75rem 1rem">
        <div style="color:#94A3B8;font-size:0.68rem;letter-spacing:1.5px;
                    text-transform:uppercase;font-weight:600;margin-bottom:0.5rem">
            {label}
        </div>
        <div style="color:{cor};font-size:2.2rem;font-weight:800;
                    margin:8px 0;letter-spacing:-0.03em;line-height:1.1">
            {valor}
        </div>
        <div style="color:#64748B;font-size:0.75rem;min-height:1rem">{subtitulo}</div>
        {extra_html}
    </div>
    """


def _gauge_bar(valor_pct: float, max_val: float = 100) -> str:
    """Gera barra de progresso HTML para APR/APY."""
    pct_clamped = min(max(valor_pct, 0), max_val)
    fill = (pct_clamped / max_val) * 100
    cor = "#10B981" if fill > 50 else "#F59E0B" if fill > 20 else "#EF4444"
    return f"""
    <div style="margin-top:0.5rem">
        <div style="
            height:4px;background:#1E3A5F;border-radius:999px;
            overflow:hidden;width:100%
        ">
            <div style="
                height:100%;width:{fill:.1f}%;
                background:linear-gradient(90deg,{cor}88,{cor});
                border-radius:999px;
                transition:width 1s ease;
            "></div>
        </div>
        <div style="font-size:0.68rem;color:#475569;margin-top:0.3rem;text-align:right">
            vs {max_val:.0f}% ref
        </div>
    </div>
    """


def _scoreboard_html(lp_valor: float, hodl_valor: float, capital: float) -> str:
    """Gera HTML do placar LP vs HODL."""
    lp_pct   = ((lp_valor   - capital) / capital * 100) if capital > 0 else 0
    hodl_pct = ((hodl_valor - capital) / capital * 100) if capital > 0 else 0
    vantagem = lp_valor - hodl_valor
    vant_pct = ((abs(vantagem)) / abs(hodl_valor) * 100) if hodl_valor != 0 else 0

    lp_cor     = utils.cor_valor(lp_pct)
    hodl_cor   = utils.cor_valor(hodl_pct)
    vant_cor   = utils.cor_valor(vantagem)
    vant_sinal = "+" if vantagem >= 0 else ""
    winner     = "LP" if vantagem >= 0 else "HODL"
    winner_cor = "#10B981" if vantagem >= 0 else "#8B5CF6"

    return f"""
    <div style="background:#0D1F33;border:1px solid rgba(37,99,235,0.25);
                border-radius:14px;padding:16px 20px;margin-top:4px">
        <div style="display:flex;justify-content:space-between;align-items:center;
                    flex-wrap:wrap;gap:1rem">
            <div style="flex:1;min-width:140px">
                <div style="font-size:0.68rem;color:#475569;text-transform:uppercase;
                            letter-spacing:0.1em;font-weight:600;margin-bottom:4px">
                    💧 LP Strategy
                </div>
                <div style="font-size:1.4rem;font-weight:700;color:#F1F5F9">
                    {utils.fmt_usd(lp_valor)}
                </div>
                <div style="font-size:0.78rem;font-weight:600;color:{lp_cor}">
                    {utils.fmt_pct(lp_pct)} vs entrada
                </div>
            </div>
            <div style="flex:1;min-width:140px">
                <div style="font-size:0.68rem;color:#475569;text-transform:uppercase;
                            letter-spacing:0.1em;font-weight:600;margin-bottom:4px">
                    💎 HODL Strategy
                </div>
                <div style="font-size:1.4rem;font-weight:700;color:#F1F5F9">
                    {utils.fmt_usd(hodl_valor)}
                </div>
                <div style="font-size:0.78rem;font-weight:600;color:{hodl_cor}">
                    {utils.fmt_pct(hodl_pct)} vs entrada
                </div>
            </div>
            <div style="flex:1;min-width:140px;text-align:right">
                <div style="font-size:0.68rem;color:#475569;text-transform:uppercase;
                            letter-spacing:0.1em;font-weight:600;margin-bottom:4px">
                    Vantagem {winner}
                </div>
                <div style="font-size:1.4rem;font-weight:700;color:{vant_cor}">
                    {vant_sinal}{utils.fmt_usd(abs(vantagem))}
                </div>
                <div style="font-size:0.78rem;font-weight:600;color:{vant_cor}">
                    {vant_sinal}{vant_pct:.1f}% a favor
                </div>
            </div>
            <div style="padding:5px 16px;border-radius:999px;
                        background:{winner_cor}22;border:1px solid {winner_cor}55;
                        color:{winner_cor};font-size:0.78rem;font-weight:700;
                        letter-spacing:0.05em;align-self:center;">
                {winner} WIN
            </div>
        </div>
    </div>
    """


# ─────────────────────────────────────────────
# GRÁFICOS
# ─────────────────────────────────────────────

def _grafico_waterfall(metricas: dict) -> go.Figure:
    capital   = metricas["capital_total"]
    fees      = metricas["total_fees"]
    il_pct    = metricas.get("il_pct") or 0.0
    il_valor  = capital * (il_pct / 100)
    ret_liq   = capital + fees + il_valor

    valores = [capital, fees, il_valor, ret_liq]
    labels  = ["Capital<br>Investido", "Fees<br>Coletadas", "Impermanent<br>Loss", "Retorno<br>Líquido"]
    cores   = ["#2563EB", "#10B981", "#EF4444", "#F59E0B"]
    medidas = ["absolute", "relative", "relative", "total"]

    textos = [
        utils.fmt_usd(capital),
        f"+{utils.fmt_usd(fees)}",
        utils.fmt_usd(il_valor),
        utils.fmt_usd(ret_liq),
    ]

    # Cor da barra "absolute" (capital) precisa ir via marker direto no Waterfall
    cor_il = "#EF4444" if il_valor < 0 else "#10B981"

    fig = go.Figure(go.Waterfall(
        name="Decomposição",
        orientation="v",
        measure=medidas,
        x=labels,
        y=valores,
        text=textos,
        textposition="outside",
        textfont=dict(color="#F1F5F9", size=12, family="Inter, Segoe UI, sans-serif"),
        connector=dict(line=dict(color="#1E3A5F", width=1.5, dash="dot")),
        # increasing/decreasing/totals controlam barras relativas e total
        increasing=dict(marker=dict(color="#10B981")),
        decreasing=dict(marker=dict(color=cor_il)),
        totals=dict(marker=dict(color="#F59E0B")),
    ))

    layout = _layout_base("Decomposição do Retorno")
    layout.update(dict(
        showlegend=False,
        yaxis=dict(
            gridcolor="#0F1F35",
            zerolinecolor="rgba(37,99,235,0.27)",
            zerolinewidth=1,
            tickfont=dict(color="#64748B", size=11),
            tickformat="$,.0f",
        ),
        xaxis=dict(
            tickfont=dict(color="#94A3B8", size=12, family="Inter, Segoe UI, sans-serif"),
            gridcolor="rgba(0,0,0,0)",
        ),
    ))
    fig.update_layout(**layout)
    return fig


def _grafico_lp_vs_hodl(metricas: dict, token_a: str, token_b: str) -> go.Figure:
    capital    = metricas["capital_total"]
    fees       = metricas["total_fees"]
    valor_hold = metricas.get("valor_hold") or capital
    lp_total   = capital + fees

    fig = go.Figure()

    # LP bars
    fig.add_trace(go.Bar(
        name="Capital LP",
        x=["Estratégia LP"],
        y=[capital],
        marker_color="#1E3A5F",
        marker_line=dict(color="rgba(37,99,235,0.27)", width=1),
        text=[utils.fmt_usd(capital)],
        textposition="inside",
        textfont=dict(color="#94A3B8", size=11),
        hovertemplate="<b>Capital</b><br>%{y:$,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Fees LP",
        x=["Estratégia LP"],
        y=[fees],
        marker_color="#10B981",
        marker_line=dict(color="rgba(16,185,129,0.27)", width=1),
        text=[f"+{utils.fmt_usd(fees)}"],
        textposition="inside",
        textfont=dict(color="#052e16", size=11, family="Inter, Segoe UI, sans-serif"),
        hovertemplate="<b>Fees</b><br>%{y:$,.2f}<extra></extra>",
    ))

    # HODL bar
    hodl_cor = "#8B5CF6" if valor_hold >= lp_total else "#8B5CF6"
    fig.add_trace(go.Bar(
        name="HODL",
        x=["Estratégia HODL"],
        y=[valor_hold],
        marker_color="#8B5CF6",
        marker_line=dict(color="rgba(139,92,246,0.27)", width=1),
        text=[utils.fmt_usd(valor_hold)],
        textposition="inside",
        textfont=dict(color="#F3E8FF", size=11),
        hovertemplate="<b>Valor HODL</b><br>%{y:$,.2f}<extra></extra>",
    ))

    # Linha de capital inicial
    fig.add_hline(
        y=capital,
        line_dash="dot",
        line_color="rgba(245,158,11,0.33)",
        line_width=1.5,
        annotation_text="Capital inicial",
        annotation_font=dict(color="#F59E0B", size=10),
        annotation_position="top right",
    )

    layout = _layout_base(f"LP vs HODL — {token_a}/{token_b}")
    layout.update(dict(
        barmode="stack",
        showlegend=True,
        legend=dict(
            bgcolor="rgba(13,31,51,0.9)",
            bordercolor="#1E3A5F",
            borderwidth=1,
            x=0.01, y=0.99,
            font=dict(color="#94A3B8", size=11),
        ),
        yaxis=dict(
            gridcolor="#0F1F35",
            tickformat="$,.0f",
            tickfont=dict(color="#64748B", size=11),
        ),
        xaxis=dict(
            tickfont=dict(color="#94A3B8", size=13, family="Inter, Segoe UI, sans-serif"),
            gridcolor="rgba(0,0,0,0)",
        ),
    ))
    fig.update_layout(**layout)
    return fig


def _grafico_curva_il(preco_medio_a: float, preco_atual_a: float | None) -> go.Figure:
    preco_ratios = np.linspace(0.05, 10, 300)
    il_values    = [calc.calcular_il(1.0, float(r), 1.0, 1.0) for r in preco_ratios]

    fig = go.Figure()

    # Área preenchida
    fig.add_trace(go.Scatter(
        x=preco_ratios,
        y=il_values,
        fill="tozeroy",
        fillcolor="rgba(239,68,68,0.08)",
        line=dict(color="#EF4444", width=2.5),
        name="Curva IL",
        hovertemplate=(
            "<b>Variação:</b> %{x:.2f}x<br>"
            "<b>IL:</b> %{y:.2f}%<extra></extra>"
        ),
        mode="lines",
    ))

    # Ponto de referência (sem IL)
    fig.add_vline(
        x=1.0,
        line_dash="dash",
        line_color="rgba(16,185,129,0.4)",
        line_width=1.5,
        annotation_text="Sem IL",
        annotation_font=dict(color="#10B981", size=10),
        annotation_position="top",
    )

    # Posição atual
    if preco_atual_a is not None and preco_medio_a > 0:
        ratio_atual = preco_atual_a / preco_medio_a
        il_atual    = calc.calcular_il(1.0, ratio_atual, 1.0, 1.0)

        fig.add_vline(
            x=ratio_atual,
            line_dash="dot",
            line_color="rgba(245,158,11,0.53)",
            line_width=2,
        )
        fig.add_trace(go.Scatter(
            x=[ratio_atual],
            y=[il_atual],
            mode="markers+text",
            marker=dict(
                color="#F59E0B",
                size=12,
                symbol="diamond",
                line=dict(color="rgba(245,158,11,0.53)", width=2),
            ),
            text=[f"  Posição atual<br>  IL: {il_atual:.2f}%"],
            textposition="middle right",
            textfont=dict(color="#F59E0B", size=11),
            name="Posição Atual",
            hovertemplate=(
                f"<b>Posição Atual</b><br>"
                f"Ratio: {ratio_atual:.2f}x<br>"
                f"IL: {il_atual:.2f}%<extra></extra>"
            ),
        ))

    layout = _layout_base("Curva de Impermanent Loss")
    layout.update(dict(
        showlegend=True,
        xaxis=dict(
            title=dict(
                text="Variação do Preço (x vezes o preço de entrada)",
                font=dict(color="#64748B", size=11),
            ),
            gridcolor="#0F1F35",
            tickformat=".1f",
            ticksuffix="x",
            tickfont=dict(color="#64748B", size=11),
        ),
        yaxis=dict(
            title=dict(
                text="Impermanent Loss (%)",
                font=dict(color="#64748B", size=11),
            ),
            gridcolor="#0F1F35",
            tickformat=".1f",
            ticksuffix="%",
            tickfont=dict(color="#64748B", size=11),
        ),
    ))
    fig.update_layout(**layout)
    return fig


def _grafico_heatmap_mensal(taxas: list, posicoes: list) -> go.Figure | None:
    if not taxas or not posicoes:
        return None

    capital_total = sum(float(p.get("capital_usd", 0) or 0) for p in posicoes)
    if capital_total <= 0:
        return None

    df = pd.DataFrame(taxas)
    df["data"] = pd.to_datetime(df["data"])
    df["ano"]  = df["data"].dt.year
    df["mes"]  = df["data"].dt.month

    mensal = (
        df.groupby(["ano", "mes"])["valor_usd"]
        .sum()
        .reset_index()
        .rename(columns={"valor_usd": "fees_mes"})
    )
    # APR mensal: (fees/capital) * (365/30) * 100
    mensal["apr_mensal"] = (mensal["fees_mes"] / capital_total) * (365 / 30) * 100

    anos  = sorted(mensal["ano"].unique())
    meses = list(range(1, 13))
    nomes_meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    z     = []
    texts = []
    for ano in anos:
        row_z    = []
        row_text = []
        for mes in meses:
            sub = mensal[(mensal["ano"] == ano) & (mensal["mes"] == mes)]
            if not sub.empty:
                apr_val = float(sub["apr_mensal"].iloc[0])
                row_z.append(apr_val)
                row_text.append(f"{apr_val:.1f}%")
            else:
                row_z.append(None)
                row_text.append("")
        z.append(row_z)
        texts.append(row_text)

    fig = go.Figure(go.Heatmap(
        z=z,
        x=nomes_meses,
        y=[str(a) for a in anos],
        text=texts,
        texttemplate="%{text}",
        textfont=dict(size=11, color="#F1F5F9"),
        colorscale=[
            [0.0,  "#450A0A"],
            [0.25, "#7F1D1D"],
            [0.5,  "#854D0E"],
            [0.75, "#14532D"],
            [1.0,  "#052E16"],
        ],
        colorbar=dict(
            title=dict(text="APR %", font=dict(color="#94A3B8", size=11)),
            tickfont=dict(color="#64748B", size=10),
            bgcolor="#0D1F33",
            bordercolor="#1E3A5F",
            borderwidth=1,
            len=0.8,
        ),
        hoverongaps=False,
        hovertemplate=(
            "<b>%{y} — %{x}</b><br>"
            "APR: %{z:.1f}%<extra></extra>"
        ),
        xgap=3,
        ygap=3,
    ))

    layout = _layout_base("Heatmap de Performance Mensal (APR Implícito)")
    layout.update(dict(
        xaxis=dict(
            tickfont=dict(color="#94A3B8", size=11),
            gridcolor="rgba(0,0,0,0)",
        ),
        yaxis=dict(
            tickfont=dict(color="#94A3B8", size=11),
            gridcolor="rgba(0,0,0,0)",
        ),
    ))
    fig.update_layout(**layout)
    return fig


def _grafico_simulador(
    capital: float,
    fees_acumuladas: float,
    dias_passados: int,
    preco_atual_a: float,
    preco_medio_a: float,
    variacao_a_pct: float,
    dias_futuro: int,
    fee_rate_dia: float,
) -> go.Figure:
    dias_total = dias_passados + dias_futuro
    eixo_dias  = list(range(0, dias_total + 1))

    preco_futuro_a = preco_atual_a * (1 + variacao_a_pct / 100)

    retornos    = []
    il_projs    = []
    fees_projs  = []

    for d in eixo_dias:
        fees_d = fees_acumuladas + (capital * fee_rate_dia / 100) * max(0, d - dias_passados)
        il_d   = 0.0
        if preco_medio_a > 0:
            if d <= dias_passados:
                il_d = calc.calcular_il(preco_medio_a, preco_atual_a, 1.0, 1.0)
            else:
                frac = (d - dias_passados) / dias_futuro if dias_futuro > 0 else 1
                p_interp = preco_atual_a + (preco_futuro_a - preco_atual_a) * frac
                il_d = calc.calcular_il(preco_medio_a, p_interp, 1.0, 1.0)
        il_valor = capital * (il_d / 100)
        ret_d    = capital + fees_d + il_valor
        retornos.append(ret_d)
        il_projs.append(il_d)
        fees_projs.append(fees_d)

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.65, 0.35],
        vertical_spacing=0.06,
        subplot_titles=["Valor Total Projetado (USD)", "IL Projetado (%)"],
    )

    # Separar passado vs futuro
    idx_fut = dias_passados

    # Linha passado
    fig.add_trace(go.Scatter(
        x=eixo_dias[:idx_fut + 1],
        y=retornos[:idx_fut + 1],
        mode="lines",
        line=dict(color="#2563EB", width=2.5),
        name="Histórico",
        hovertemplate="Dia %{x}<br>Valor: %{y:$,.2f}<extra></extra>",
    ), row=1, col=1)

    # Linha futuro
    fig.add_trace(go.Scatter(
        x=eixo_dias[idx_fut:],
        y=retornos[idx_fut:],
        mode="lines",
        line=dict(color="#F59E0B", width=2.5, dash="dash"),
        fill="tonexty" if False else None,
        name="Projeção",
        hovertemplate="Dia %{x}<br>Projeção: %{y:$,.2f}<extra></extra>",
    ), row=1, col=1)

    # Área de projeção sombreada
    fig.add_trace(go.Scatter(
        x=eixo_dias[idx_fut:],
        y=retornos[idx_fut:],
        mode="none",
        fill="tozeroy",
        fillcolor="rgba(245,158,11,0.04)",
        showlegend=False,
        hoverinfo="skip",
    ), row=1, col=1)

    # Capital inicial (linha referência)
    fig.add_hline(
        y=capital,
        line_dash="dot",
        line_color="#1E3A5F",
        line_width=1,
        row=1, col=1,
    )

    # IL projetado
    fig.add_trace(go.Scatter(
        x=eixo_dias,
        y=il_projs,
        mode="lines",
        line=dict(color="#EF4444", width=2),
        fill="tozeroy",
        fillcolor="rgba(239,68,68,0.06)",
        name="IL %",
        hovertemplate="Dia %{x}<br>IL: %{y:.2f}%<extra></extra>",
    ), row=2, col=1)

    # Linha divisória passado/futuro
    if dias_passados > 0:
        fig.add_vline(
            x=dias_passados,
            line_dash="dot",
            line_color="#475569",
            line_width=1,
            annotation_text="Hoje",
            annotation_font=dict(color="#64748B", size=10),
        )

    layout = _layout_base()
    layout.update(dict(
        showlegend=True,
        legend=dict(
            orientation="h", x=0.01, y=1.02,
            bgcolor="rgba(13,31,51,0.9)",
            bordercolor="#1E3A5F", borderwidth=1,
            font=dict(color="#94A3B8", size=11),
        ),
        xaxis2=dict(
            title=dict(text="Dias", font=dict(color="#64748B", size=11)),
            gridcolor="#0F1F35",
            tickfont=dict(color="#64748B", size=11),
        ),
        yaxis=dict(
            gridcolor="#0F1F35",
            tickformat="$,.0f",
            tickfont=dict(color="#64748B", size=11),
        ),
        yaxis2=dict(
            gridcolor="#0F1F35",
            tickformat=".1f",
            ticksuffix="%",
            tickfont=dict(color="#64748B", size=11),
        ),
        annotations=[
            dict(
                text="Valor Total Projetado (USD)",
                x=0, xref="paper", y=1.02, yref="paper",
                showarrow=False, font=dict(size=12, color="#94A3B8"),
            ),
            dict(
                text="IL Projetado (%)",
                x=0, xref="paper", y=0.32, yref="paper",
                showarrow=False, font=dict(size=12, color="#94A3B8"),
            ),
        ],
        margin=dict(l=20, r=20, t=40, b=30),
    ))
    fig.update_layout(**layout)
    return fig


# ─────────────────────────────────────────────
# RENDER PRINCIPAL
# ─────────────────────────────────────────────

def render() -> None:
    # ── Título ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="animation:fadeInUp 0.4s ease both">
        <div style="
            font-size:0.7rem;font-weight:700;color:#2563EB;
            letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.3rem
        ">Painel de Inteligência</div>
        <h1 style="margin:0;font-size:1.8rem;font-weight:800;
                   background:linear-gradient(135deg,#F1F5F9,#60A5FA);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   background-clip:text;letter-spacing:-0.03em">
            Análise Avançada de Pools
        </h1>
        <p style="color:#475569;font-size:0.85rem;margin-top:0.35rem;font-weight:400">
            Decomposição de retorno · IL · APR/APY · Simulação prospectiva
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:1.5rem'></div>", unsafe_allow_html=True)

    # ── Carregar pools ───────────────────────────────────────────────────────────
    pools = db.listar_pools(apenas_ativas=False)
    if not pools:
        st.info("Nenhuma pool cadastrada. Adicione pools e posições primeiro.")
        return

    # ═══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 1 — Seletor de Pool e Preços Atuais
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header("Seleção de Pool", "Escolha a pool e insira os preços atuais", "🎯")

    opcoes = {f"{p['nome']} ({p['protocolo']} · {p['chain']})": p for p in pools}
    pool_label = st.selectbox(
        "Pool para análise",
        list(opcoes.keys()),
        key="analise_pool_select",
        label_visibility="collapsed",
    )
    pool = opcoes[pool_label]
    pool_id   = pool["id"]
    token_a   = pool["token_a"]
    token_b   = pool["token_b"]
    fee_tier  = pool.get("fee_tier", "")

    # Info da pool
    _fee_part = f"  ·  {fee_tier}" if fee_tier else ""
    _ativa_part = "  ·  🟢 Ativa" if pool.get("ativa") else "  ·  🔴 Inativa"
    st.info(
        f"**{token_a} / {token_b}**  ·  {pool['protocolo']}  ·  {pool['chain']}"
        f"{_fee_part}{_ativa_part}"
    )

    # Carregar dados
    posicoes = db.listar_posicoes(pool_id)
    taxas    = db.listar_taxas(pool_id)

    if not posicoes:
        st.info(
            f"Nenhuma posição registrada para **{pool['nome']}**. "
            "Adicione posições na aba Posições."
        )
        return

    # Preços default: última posição
    pos_recente      = sorted(posicoes, key=lambda x: x["data"])[-1]
    default_preco_a  = float(pos_recente.get("token_a_price_usd") or 0)
    default_preco_b  = float(pos_recente.get("token_b_price_usd") or 0)

    st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
    col_pa, col_pb, col_btn = st.columns([2, 2, 1])

    with col_pa:
        preco_a_input = st.number_input(
            f"Preço atual de {token_a} (USD)",
            min_value=0.0,
            value=default_preco_a,
            step=0.01,
            format="%.4f",
            key="analise_preco_a",
        )
    with col_pb:
        preco_b_input = st.number_input(
            f"Preço atual de {token_b} (USD)",
            min_value=0.0,
            value=default_preco_b,
            step=0.01,
            format="%.4f",
            key="analise_preco_b",
        )
    with col_btn:
        st.markdown("<div style='padding-top:1.68rem'></div>", unsafe_allow_html=True)
        calcular = st.button(
            "⚡ Calcular Análise",
            key="analise_btn_calcular",
            type="primary",
            use_container_width=True,
        )

    # Guardar preços no session_state ao clicar
    if calcular:
        st.session_state["analise_preco_a_val"] = preco_a_input
        st.session_state["analise_preco_b_val"] = preco_b_input
        st.session_state["analise_pool_id"]     = pool_id

    preco_a = st.session_state.get("analise_preco_a_val", preco_a_input)
    preco_b = st.session_state.get("analise_preco_b_val", preco_b_input)

    # Se a pool mudou, resetar preços salvos
    if st.session_state.get("analise_pool_id") != pool_id:
        preco_a = preco_a_input
        preco_b = preco_b_input

    use_precos = preco_a > 0 and preco_b > 0

    # Calcular métricas
    metricas = calc.calcular_metricas_pool(
        posicoes, taxas,
        preco_atual_a=preco_a if use_precos else None,
        preco_atual_b=preco_b if use_precos else None,
    )

    capital    = metricas["capital_total"]
    fees       = metricas["total_fees"]
    apr        = metricas["apr"]
    apy        = metricas["apy"]
    il_pct     = metricas.get("il_pct")
    ret_liq    = metricas.get("retorno_liquido")
    valor_hold = metricas.get("valor_hold")
    dias       = metricas["dias_na_pool"]
    pm_a       = metricas["preco_medio_a"]
    pm_b       = metricas["preco_medio_b"]

    st.markdown("<hr>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 2 — Cards de Métricas Principais
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header("Métricas Principais", f"Período: {utils.fmt_dias(dias)}", "📊")

    # ── Build card data ──────────────────────────────────────────────────────────
    # Card 1: Capital Investido
    _c1_sub = utils.fmt_dias(dias) + " na pool"
    _c1_extra = ""
    if valor_hold is not None:
        _diff = capital + fees - valor_hold
        _cor_d = utils.cor_valor(_diff)
        _sinal = "+" if _diff >= 0 else ""
        _c1_extra = (
            f'<div style="margin-top:4px;font-size:0.73rem;font-weight:600;color:{_cor_d}">'
            f'{_sinal}{utils.fmt_usd(_diff)} vs HODL</div>'
        )

    # Card 2: Fees Coletadas
    _fees_pct = (fees / capital * 100) if capital > 0 else 0
    _c2_sub = f"{_fees_pct:.2f}% do capital"

    # Card 3: APR
    _apr_cor = "#F59E0B" if apr > 0 else "#EF4444"
    _apr_pct_clamped = min(apr, 200)
    _apr_fill = (_apr_pct_clamped / 200) * 100
    _gauge_cor = "#10B981" if _apr_fill > 50 else "#F59E0B" if _apr_fill > 20 else "#EF4444"
    _c3_extra = (
        f'<div style="margin-top:6px">'
        f'<div style="height:4px;background:#1E3A5F;border-radius:999px;overflow:hidden">'
        f'<div style="height:100%;width:{_apr_fill:.1f}%;'
        f'background:linear-gradient(90deg,{_gauge_cor}88,{_gauge_cor});border-radius:999px"></div>'
        f'</div>'
        f'<div style="font-size:0.67rem;color:#475569;margin-top:3px;text-align:right">vs 200% ref</div>'
        f'</div>'
    )

    # Card 4: IL
    if il_pct is not None:
        _il_cor = utils.cor_valor(il_pct)
        _il_val = utils.fmt_pct(il_pct)
        _il_sub = "IL positivo (raro)" if il_pct > 0 else "Perda por divergência"
        _c4_extra = ""
        if ret_liq is not None:
            _cor_ret = utils.cor_valor(ret_liq)
            _c4_extra = (
                f'<div style="margin-top:4px;font-size:0.73rem;font-weight:600;color:{_cor_ret}">'
                f'Retorno líquido: {utils.fmt_pct(ret_liq)}</div>'
            )
    else:
        _il_cor = "#475569"
        _il_val = "—"
        _il_sub = "Insira preços atuais"
        _c4_extra = ""

        # Card 5: Net Yield
    _net_yield = calc.calcular_net_yield(apr, il_pct) if il_pct is not None else None
    if _net_yield is not None:
        _ny_cor = utils.cor_valor(_net_yield)
        _ny_val = utils.fmt_pct(_net_yield)
        _ny_sub = "APR - IL = retorno vs HODL"
    else:
        _ny_cor = "#475569"
        _ny_val = "—"
        _ny_sub = "Insira preços atuais"

    _cards_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;font-family:'Segoe UI',Inter,sans-serif}}
.row{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;padding:2px}}
.card{{background:#0D1F33;border:1px solid rgba(37,99,235,0.35);border-radius:14px;
      padding:16px 12px;position:relative;overflow:hidden;text-align:center;
      box-shadow:0 0 20px rgba(37,99,235,0.13)}}
.card-top{{position:absolute;top:0;left:0;right:0;height:2px;
          background:linear-gradient(90deg,#2563EB,#10B981);opacity:.7}}
.label{{color:#94A3B8;font-size:0.65rem;font-weight:600;letter-spacing:.09em;
       text-transform:uppercase;margin-bottom:8px}}
.value{{font-size:1.7rem;font-weight:800;line-height:1.1;margin-bottom:5px;
       font-variant-numeric:tabular-nums;letter-spacing:-0.03em}}
.sub{{color:#64748B;font-size:0.72rem;min-height:1rem}}
</style></head><body>
<div class="row">
  <div class="card"><div class="card-top"></div>
    <div class="label">Capital Investido</div>
    <div class="value" style="color:#60A5FA">{utils.fmt_usd(capital)}</div>
    <div class="sub">{_c1_sub}</div>
    {_c1_extra}
  </div>
  <div class="card"><div class="card-top"></div>
    <div class="label">Fees Coletadas</div>
    <div class="value" style="color:#10B981">{utils.fmt_usd(fees)}</div>
    <div class="sub">{_c2_sub}</div>
  </div>
  <div class="card"><div class="card-top"></div>
    <div class="label">APR (Anualizado)</div>
    <div class="value" style="color:{_apr_cor}">{utils.fmt_pct(apr)}</div>
    <div class="sub">APY: {utils.fmt_pct(apy)}</div>
    {_c3_extra}
  </div>
  <div class="card"><div class="card-top"></div>
    <div class="label">Impermanent Loss</div>
    <div class="value" style="color:{_il_cor}">{_il_val}</div>
    <div class="sub">{_il_sub}</div>
    {_c4_extra}
  </div>
  <div class="card"><div class="card-top"></div>
    <div class="label">Net Yield Real</div>
    <div class="value" style="color:{_ny_cor}">{_ny_val}</div>
    <div class="sub">{_ny_sub}</div>
  </div>
</div></body></html>"""
    components.html(_cards_html, height=130, scrolling=False)

    st.markdown("<div style='margin-bottom:1rem'></div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 2b — Range de Preço (Concentrated Liquidity)
    # ═══════════════════════════════════════════════════════════════════════════
    pool_data = db.get_pool(pool_id)
    _preco_min = pool_data.get("preco_min") if pool_data else None
    _preco_max = pool_data.get("preco_max") if pool_data else None

    if _preco_min and _preco_max:
        _section_header("Range de Preço", f"Liquidez concentrada · {token_a} min/max configurado", "🎯")
        _preco_atual_range = preco_a if use_precos else None
        rng = calc.status_range(_preco_atual_range, _preco_min, _preco_max)

        _in_range = rng.get("in_range")
        _pct_pos  = rng.get("pct_posicao")
        _dist_min = rng.get("distancia_min")
        _dist_max = rng.get("distancia_max")

        if _preco_atual_range is not None and _in_range is not None:
            _badge_cor  = "#10B981" if _in_range else "#EF4444"
            _badge_bg   = "rgba(16,185,129,0.15)" if _in_range else "rgba(239,68,68,0.15)"
            _badge_txt  = "IN RANGE" if _in_range else "OUT OF RANGE"
            _badge_icon = "🟢" if _in_range else "🔴"
            _fill_pct   = max(0.0, min(100.0, float(_pct_pos or 0) * 100))

            _min_fmt    = utils.fmt_usd(_preco_min)
            _max_fmt    = utils.fmt_usd(_preco_max)
            _cur_fmt    = utils.fmt_usd(_preco_atual_range)
            _dmin_fmt   = f"{abs(_dist_min or 0):.1f}%" if _dist_min is not None else "—"
            _dmax_fmt   = f"{abs(_dist_max or 0):.1f}%" if _dist_max is not None else "—"

            _range_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;font-family:'Segoe UI',Inter,sans-serif;padding:4px 0}}
.wrap{{background:#0D1F33;border:1px solid {_badge_cor}44;border-radius:14px;padding:18px 20px}}
.badge{{display:inline-flex;align-items:center;gap:6px;background:{_badge_bg};
       color:{_badge_cor};border:1px solid {_badge_cor}55;border-radius:999px;
       padding:6px 18px;font-size:1rem;font-weight:700;letter-spacing:0.05em;margin-bottom:16px}}
.bar-wrap{{background:#1E3A5F;border-radius:999px;height:10px;width:100%;overflow:hidden;margin:10px 0}}
.bar-fill{{height:100%;width:{_fill_pct:.1f}%;background:linear-gradient(90deg,{_badge_cor}88,{_badge_cor});
          border-radius:999px;transition:width 1s ease}}
.labels{{display:flex;justify-content:space-between;font-size:0.72rem;color:#64748B;margin-top:4px}}
.dists{{display:flex;gap:24px;margin-top:12px;flex-wrap:wrap}}
.dist-item{{font-size:0.78rem;color:#94A3B8}}
.dist-val{{font-weight:700;color:{_badge_cor}}}
</style></head><body>
<div class="wrap">
  <div class="badge">{_badge_icon} {_badge_txt}</div>
  <div class="bar-wrap"><div class="bar-fill"></div></div>
  <div class="labels">
    <span>MIN {_min_fmt}</span>
    <span style="color:#F1F5F9;font-weight:600">ATUAL {_cur_fmt}</span>
    <span>MAX {_max_fmt}</span>
  </div>
  <div class="dists">
    <div class="dist-item">Distância do mínimo: <span class="dist-val">{_dmin_fmt}</span></div>
    <div class="dist-item">Distância do máximo: <span class="dist-val">{_dmax_fmt}</span></div>
  </div>
</div>
</body></html>"""
            components.html(_range_html, height=150, scrolling=False)
        else:
            st.info(
                f"Range configurado: [{utils.fmt_usd(_preco_min)} – {utils.fmt_usd(_preco_max)}]. "
                "Insira o preço atual para ver o status do range."
            )

        st.markdown("<hr>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 3 — Waterfall Chart
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header("Decomposição do Retorno", "Waterfall: Capital → Fees → IL → Resultado", "📉")

    if capital > 0:
        fig_wf = _grafico_waterfall(metricas)
        st.plotly_chart(fig_wf, use_container_width=True, config={"displayModeBar": False}, key="analise_waterfall")
    else:
        st.info("Dados insuficientes para o waterfall chart.")

    # ─── Break-even & Run Rate (após waterfall) ──────────────────────────────
    _section_header("Break-even & Run Rate", "Quanto tempo até cobrir o IL com fees", "⏱️")
    col_be, col_rr = st.columns(2)
    with col_be:
        if il_pct is not None and capital > 0:
            _il_usd_be = capital * abs(il_pct) / 100
            _dias_be = calc.calcular_breakeven_dias(_il_usd_be, taxas)
            if _dias_be is not None:
                _be_cor = "#10B981" if _dias_be <= 30 else ("#F59E0B" if _dias_be <= 90 else "#EF4444")
                components.html(f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;font-family:'Segoe UI',Inter,sans-serif}}
.card{{background:#0D1F33;border:1px solid rgba(37,99,235,0.2);border-radius:12px;padding:16px 18px}}
.lbl{{color:#64748B;font-size:0.68rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px}}
.val{{font-size:1.65rem;font-weight:800;color:{_be_cor};letter-spacing:-0.03em}}
.sub{{color:#475569;font-size:0.74rem;margin-top:4px}}
</style></head><body>
<div class="card">
  <div class="lbl">Break-even</div>
  <div class="val">{_dias_be} dias</div>
  <div class="sub">de fees cobre IL atual de {utils.fmt_usd(_il_usd_be)}</div>
</div></body></html>""", height=100, scrolling=False)
            else:
                st.info("Dados insuficientes para calcular break-even.")
        else:
            st.info("Insira preços atuais para calcular o break-even.")

    with col_rr:
        _rr7  = calc.calcular_fee_run_rate(taxas, 7)
        _rr30 = calc.calcular_fee_run_rate(taxas, 30)
        _delta_rr = _rr7 - _rr30
        _delta_cor = utils.cor_valor(_delta_rr)
        _delta_sym = "+" if _delta_rr >= 0 else ""
        components.html(f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;font-family:'Segoe UI',Inter,sans-serif}}
.card{{background:#0D1F33;border:1px solid rgba(37,99,235,0.2);border-radius:12px;padding:16px 18px}}
.lbl{{color:#64748B;font-size:0.68rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px}}
.row2{{display:flex;gap:20px;align-items:flex-end}}
.val{{font-size:1.65rem;font-weight:800;color:#10B981;letter-spacing:-0.03em}}
.sub{{color:#475569;font-size:0.74rem;margin-top:4px}}
.delta{{font-size:0.82rem;font-weight:700;color:{_delta_cor};margin-left:4px}}
</style></head><body>
<div class="card">
  <div class="lbl">Fee Run Rate</div>
  <div class="row2">
    <div>
      <div class="val">{utils.fmt_usd(_rr7)}/dia</div>
      <div class="sub">últimos 7 dias <span class="delta">{_delta_sym}{utils.fmt_usd(abs(_delta_rr))}/dia vs 30d</span></div>
    </div>
    <div style="text-align:right">
      <div style="color:#64748B;font-size:0.68rem;text-transform:uppercase;letter-spacing:.08em">30d avg</div>
      <div style="font-size:1.1rem;font-weight:700;color:#94A3B8">{utils.fmt_usd(_rr30)}/dia</div>
    </div>
  </div>
</div></body></html>""", height=100, scrolling=False)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 3b — IL vs Fees Timeline
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header("IL vs Fees Timeline", "Evolução temporal: fees acumuladas vs impermanent loss", "📊")

    _hist = calc.timeline_il_vs_fees(posicoes, taxas)
    if _hist:
        _df_hist = pd.DataFrame(_hist)
        _fig_tl = go.Figure()

        # Fees acumuladas (verde)
        _fig_tl.add_trace(go.Scatter(
            x=_df_hist["data"],
            y=_df_hist["fees_acum"],
            name="Fees Acumuladas",
            mode="lines",
            line=dict(color="#10B981", width=2),
            fill="tozeroy",
            fillcolor="rgba(16,185,129,0.07)",
            hovertemplate="<b>%{x}</b><br>Fees: $%{y:,.2f}<extra></extra>",
        ))

        # IL em USD (vermelho) — apenas onde não None
        _il_series = _df_hist["il_usd"].where(_df_hist["il_usd"].notna())
        _fig_tl.add_trace(go.Scatter(
            x=_df_hist["data"],
            y=_il_series,
            name="IL (USD)",
            mode="lines",
            line=dict(color="#EF4444", width=2),
            hovertemplate="<b>%{x}</b><br>IL: $%{y:,.2f}<extra></extra>",
        ))

        # Net (amarelo)
        _net_series = _df_hist["net_usd"].where(_df_hist["net_usd"].notna())
        _fig_tl.add_trace(go.Scatter(
            x=_df_hist["data"],
            y=_net_series,
            name="Net (Fees + IL)",
            mode="lines",
            line=dict(color="#F59E0B", width=2, dash="dot"),
            hovertemplate="<b>%{x}</b><br>Net: $%{y:,.2f}<extra></extra>",
        ))

        # Linha zero
        _fig_tl.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.15)", line_width=1)

        _layout_tl = _layout_base()
        _layout_tl.update(dict(
            height=200,
            showlegend=True,
            legend=dict(orientation="h", x=0.01, y=1.12, bgcolor="rgba(0,0,0,0)",
                        font=dict(size=10, color="#94A3B8")),
            margin=dict(l=20, r=20, t=30, b=20),
            yaxis=dict(gridcolor="#0F1F35", tickformat="$,.0f",
                       tickfont=dict(color="#64748B", size=10)),
            xaxis=dict(gridcolor="#0F1F35", tickfont=dict(color="#64748B", size=10)),
        ))
        _fig_tl.update_layout(**_layout_tl)
        st.plotly_chart(_fig_tl, use_container_width=True, config={"displayModeBar": False}, key="analise_timeline")
    else:
        st.info("Dados insuficientes para a timeline IL vs Fees.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 4 — LP vs HODL
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header("LP vs HODL", "Comparativo de estratégias com os preços atuais", "⚔️")

    if use_precos and valor_hold is not None:
        fig_hodl = _grafico_lp_vs_hodl(metricas, token_a, token_b)
        st.plotly_chart(fig_hodl, use_container_width=True, config={"displayModeBar": False}, key="analise_hodl_com_precos")
        lp_total = capital + fees
        _sb_html = _scoreboard_html(lp_total, valor_hold, capital)
        components.html(
            f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;font-family:'Segoe UI',Inter,sans-serif;padding:2px}}
.card{{background:#0D1F33;border:1px solid rgba(37,99,235,0.25);border-radius:14px;
      padding:16px 20px;margin-top:4px}}
.inner{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem}}
.col{{flex:1;min-width:130px}}
.col-right{{flex:1;min-width:130px;text-align:right}}
.lbl{{font-size:0.67rem;color:#475569;text-transform:uppercase;
     letter-spacing:0.1em;font-weight:600;margin-bottom:4px}}
.val{{font-size:1.4rem;font-weight:700;color:#F1F5F9}}
.sub{{font-size:0.78rem;font-weight:600}}
.badge{{padding:5px 16px;border-radius:999px;font-size:0.78rem;
       font-weight:700;letter-spacing:0.05em;align-self:center;white-space:nowrap}}
</style></head><body>{_sb_html}</body></html>""",
            height=100,
            scrolling=False,
        )
    else:
        # Gráfico simplificado sem HODL
        fig_hodl = _grafico_lp_vs_hodl(metricas, token_a, token_b)
        st.plotly_chart(fig_hodl, use_container_width=True, config={"displayModeBar": False}, key="analise_hodl_sem_precos")
        st.info("Insira os preços atuais para ver o comparativo LP vs HODL completo.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 5 — Curva de IL
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(
        "Curva de Impermanent Loss",
        f"Sensibilidade do IL à variação do preço de {token_a}",
        "📈",
    )

    if pm_a > 0:
        fig_il = _grafico_curva_il(
            preco_medio_a=pm_a,
            preco_atual_a=preco_a if use_precos else None,
        )
        st.plotly_chart(fig_il, use_container_width=True, config={"displayModeBar": False}, key="analise_curva_il")

        # Legenda de referência
        st.markdown("""
        <div style="display:flex;gap:1.5rem;flex-wrap:wrap;margin-top:0.5rem;
                    padding:0.75rem 1rem;background:#0A1628;border-radius:8px;
                    border:1px solid #0F1F35">
            <div style="font-size:0.75rem;color:#64748B">
                <span style="color:#10B981;font-weight:700">1.0x</span> — Sem IL
            </div>
            <div style="font-size:0.75rem;color:#64748B">
                <span style="color:#F59E0B;font-weight:700">2.0x</span> — IL ≈ -5.7%
            </div>
            <div style="font-size:0.75rem;color:#64748B">
                <span style="color:#EF4444;font-weight:700">4.0x</span> — IL ≈ -20.0%
            </div>
            <div style="font-size:0.75rem;color:#64748B">
                <span style="color:#EF4444;font-weight:700">9.0x</span> — IL ≈ -25.0%
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Preço médio de entrada não disponível para calcular a curva de IL.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 6 — Heatmap de Performance Mensal
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(
        "Performance Mensal",
        "APR implícito por mês — verde = bom, vermelho = ruim",
        "🗓️",
    )

    if taxas:
        fig_heat = _grafico_heatmap_mensal(taxas, posicoes)
        if fig_heat:
            st.plotly_chart(fig_heat, use_container_width=True,
                            config={"displayModeBar": False}, key="analise_heatmap")
        else:
            st.info("Dados insuficientes para o heatmap mensal.")
    else:
        st.info("Nenhuma taxa registrada para este pool. Adicione fees coletadas na aba Taxas.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 7 — Tabela de Preço Médio vs Preço Atual
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(
        "Preço Médio vs Preço Atual",
        "Resumo por token com variação percentual",
        "💱",
    )

    total_a = sum(float(p.get("token_a_amount", 0) or 0) for p in posicoes)
    total_b = sum(float(p.get("token_b_amount", 0) or 0) for p in posicoes)

    var_a = ((preco_a - pm_a) / pm_a * 100) if (use_precos and pm_a > 0) else None
    var_b = ((preco_b - pm_b) / pm_b * 100) if (use_precos and pm_b > 0) else None

    rows = []
    for token_nome, pm, p_atual, total_qty, var_pct in [
        (token_a, pm_a, preco_a if use_precos else None, total_a, var_a),
        (token_b, pm_b, preco_b if use_precos else None, total_b, var_b),
    ]:
        val_entrada = total_qty * pm if pm > 0 else 0
        val_atual   = total_qty * p_atual if p_atual else None
        rows.append({
            "Token": token_nome,
            "Preço Médio Entrada": pm,
            "Preço Atual": p_atual if p_atual else float("nan"),
            "Variação %": var_pct if var_pct is not None else float("nan"),
            "Qty Total": total_qty,
            "Valor Entrada (USD)": val_entrada,
            "Valor Atual (USD)": val_atual if val_atual else float("nan"),
        })

    df_preco = pd.DataFrame(rows)

    def _highlight_var(val):
        if pd.isna(val):
            return "color: #475569"
        return f"color: {'#10B981' if val >= 0 else '#EF4444'}; font-weight:600"

    def _fmt_usd_nan(v):
        return utils.fmt_usd(v) if not pd.isna(v) else "—"

    def _fmt_pct_nan(v):
        return utils.fmt_pct(v) if not pd.isna(v) else "—"

    try:
        styled = (
            df_preco.style
            .format({
                "Preço Médio Entrada": lambda v: utils.fmt_usd(v) if v > 0 else "—",
                "Preço Atual":         _fmt_usd_nan,
                "Variação %":          _fmt_pct_nan,
                "Qty Total":           lambda v: utils.fmt_token(v),
                "Valor Entrada (USD)": _fmt_usd_nan,
                "Valor Atual (USD)":   _fmt_usd_nan,
            })
            .applymap(_highlight_var, subset=["Variação %"])
            .set_properties(**{
                "background-color": "#0A1628",
                "color": "#CBD5E1",
                "border": "1px solid #0F1F35",
                "font-size": "0.875rem",
            })
            .set_table_styles([
                {"selector": "thead th", "props": [
                    ("background-color", "#0D1F33"),
                    ("color", "#60A5FA"),
                    ("font-weight", "600"),
                    ("font-size", "0.78rem"),
                    ("text-transform", "uppercase"),
                    ("letter-spacing", "0.05em"),
                    ("border-bottom", "1px solid #1E3A5F"),
                ]},
                {"selector": "tbody tr:hover td", "props": [
                    ("background-color", "#0F1F35 !important"),
                ]},
            ])
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)
    except Exception:
        st.dataframe(df_preco, use_container_width=True, hide_index=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 8 — Simulador "E se?"
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(
        "Simulador E se?",
        "Projete cenários futuros ajustando preços, tempo e taxas",
        "🔮",
    )

    with st.container():
        scol1, scol2, scol3 = st.columns(3)

        with scol1:
            var_preco_pct = st.slider(
                f"Variação futura do {token_a} (%)",
                min_value=-90,
                max_value=900,
                value=0,
                step=5,
                key="sim_var_preco",
                help="Variação percentual esperada do preço do token A a partir do preço atual",
            )
        with scol2:
            dias_futuro = st.slider(
                "Tempo adicional na pool (dias)",
                min_value=1,
                max_value=730,
                value=90,
                step=1,
                key="sim_dias_futuro",
                help="Quantos dias a mais você pretende ficar na pool",
            )
        with scol3:
            fee_rate_dia = st.number_input(
                "Fee rate diária esperada (%/dia)",
                min_value=0.0,
                max_value=5.0,
                value=round((apr / 365) if apr > 0 else 0.05, 4),
                step=0.001,
                format="%.4f",
                key="sim_fee_rate",
                help="Taxa de fee diária esperada como % do capital",
            )

    # Projeções calculadas
    p_atual_a_sim = preco_a if use_precos and preco_a > 0 else (pm_a if pm_a > 0 else 1.0)
    preco_fut_a   = p_atual_a_sim * (1 + var_preco_pct / 100)
    fees_proj     = fees + capital * fee_rate_dia / 100 * dias_futuro
    il_proj       = calc.calcular_il(pm_a, preco_fut_a, 1.0, 1.0) if pm_a > 0 else 0.0
    il_proj_val   = capital * (il_proj / 100)
    ret_proj      = capital + fees_proj + il_proj_val
    apr_proj      = calc.calcular_apr(fees_proj, capital, dias + dias_futuro)

    # Scoreboard de projeção
    cor_ret_proj = utils.cor_valor(ret_proj - capital)
    cor_il_proj  = utils.cor_valor(il_proj)
    cor_apr_proj = utils.cor_valor(apr_proj)

    fees_proj_liquido = fees_proj + il_proj_val
    cor_liq = utils.cor_valor(fees_proj_liquido)
    _ret_pct_proj = (ret_proj - capital) / capital * 100 if capital > 0 else 0

    _sim_cards_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;font-family:'Segoe UI',Inter,sans-serif}}
.row{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;padding:2px}}
.card{{background:#0D1F33;border:1px solid rgba(37,99,235,0.25);border-radius:14px;
      padding:16px 12px;text-align:center;position:relative;overflow:hidden}}
.card-top{{position:absolute;top:0;left:0;right:0;height:2px;
          background:linear-gradient(90deg,#2563EB,#10B981);opacity:.5}}
.label{{color:#475569;font-size:0.65rem;font-weight:600;letter-spacing:1px;
       text-transform:uppercase;margin-bottom:6px}}
.value{{font-size:1.55rem;font-weight:800;line-height:1.1;
       letter-spacing:-0.02em;font-variant-numeric:tabular-nums}}
.sub{{color:#475569;font-size:0.71rem;margin-top:3px}}
</style></head><body>
<div class="row">
  <div class="card"><div class="card-top"></div>
    <div class="label">Valor Projetado</div>
    <div class="value" style="color:{cor_ret_proj}">{utils.fmt_usd(ret_proj)}</div>
    <div class="sub">{utils.fmt_pct(_ret_pct_proj)} vs entrada</div>
  </div>
  <div class="card"><div class="card-top"></div>
    <div class="label">APR Projetado</div>
    <div class="value" style="color:{cor_apr_proj}">{utils.fmt_pct(apr_proj)}</div>
    <div class="sub">{utils.fmt_dias(dias + dias_futuro)} total</div>
  </div>
  <div class="card"><div class="card-top"></div>
    <div class="label">IL Projetado</div>
    <div class="value" style="color:{cor_il_proj}">{utils.fmt_pct(il_proj)}</div>
    <div class="sub">{token_a} → {utils.fmt_usd(preco_fut_a)}</div>
  </div>
  <div class="card"><div class="card-top"></div>
    <div class="label">Fees Líquidas (Fees - IL)</div>
    <div class="value" style="color:{cor_liq}">{utils.fmt_usd(fees_proj_liquido)}</div>
    <div class="sub">{utils.fmt_usd(fees_proj)} fees · IL: {utils.fmt_pct(il_proj)}</div>
  </div>
</div></body></html>"""
    components.html(_sim_cards_html, height=115, scrolling=False)

    st.markdown("<div style='margin-top:1.25rem'></div>", unsafe_allow_html=True)

    # Gráfico de projeção temporal
    fig_sim = _grafico_simulador(
        capital=capital,
        fees_acumuladas=fees,
        dias_passados=dias,
        preco_atual_a=p_atual_a_sim,
        preco_medio_a=pm_a if pm_a > 0 else p_atual_a_sim,
        variacao_a_pct=var_preco_pct,
        dias_futuro=dias_futuro,
        fee_rate_dia=fee_rate_dia,
    )
    st.plotly_chart(fig_sim, use_container_width=True, config={"displayModeBar": False}, key="analise_simulacao")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 9 — Risk Score
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header("Risk Score", "Avaliação de risco consolidada da posição", "🛡️")

    try:
        _risk = calc.calcular_risk_score(pool_data or {}, posicoes, taxas)
        _score     = _risk.get("score", 0)
        _nivel     = _risk.get("nivel", "—")
        _fatores   = _risk.get("fatores", [])

        _score_cor = "#10B981" if _score < 30 else ("#F59E0B" if _score <= 60 else "#EF4444")
        _fill_risk = min(100.0, float(_score))

        _fatores_html = ""
        for _f in _fatores:
            _f_nome  = _f.get("nome", "—") if isinstance(_f, dict) else str(_f)
            _f_val   = _f.get("valor", "") if isinstance(_f, dict) else ""
            _f_peso  = _f.get("peso", "") if isinstance(_f, dict) else ""
            _f_cor   = _f.get("cor", "#94A3B8") if isinstance(_f, dict) else "#94A3B8"
            _f_peso_str = f" · peso {_f_peso}" if _f_peso else ""
            _fatores_html += f"""
            <div style="display:flex;align-items:center;gap:10px;padding:6px 0;
                        border-bottom:1px solid rgba(255,255,255,0.04)">
              <div style="width:8px;height:8px;border-radius:50%;background:{_f_cor};flex-shrink:0"></div>
              <div style="flex:1;font-size:0.8rem;color:#CBD5E1">{_f_nome}</div>
              <div style="font-size:0.78rem;font-weight:600;color:{_f_cor}">{_f_val}{_f_peso_str}</div>
            </div>"""

        _risk_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;font-family:'Segoe UI',Inter,sans-serif}}
.wrap{{display:flex;gap:20px;flex-wrap:wrap}}
.score-box{{background:#0D1F33;border:1px solid {_score_cor}44;border-radius:14px;
           padding:20px 24px;flex:0 0 180px;text-align:center}}
.score-lbl{{color:#64748B;font-size:0.68rem;font-weight:600;letter-spacing:.08em;
           text-transform:uppercase;margin-bottom:8px}}
.score-val{{font-size:2.8rem;font-weight:900;color:{_score_cor};letter-spacing:-0.04em;line-height:1}}
.score-nivel{{font-size:0.85rem;font-weight:700;color:{_score_cor};margin-top:4px}}
.bar-wrap{{background:#1E3A5F;border-radius:999px;height:8px;width:100%;overflow:hidden;margin:10px 0}}
.bar-fill{{height:100%;width:{_fill_risk:.1f}%;background:linear-gradient(90deg,{_score_cor}88,{_score_cor});border-radius:999px}}
.fatores-box{{background:#0D1F33;border:1px solid rgba(37,99,235,0.18);border-radius:14px;
             padding:16px 20px;flex:1;min-width:240px}}
.f-title{{color:#64748B;font-size:0.68rem;font-weight:700;letter-spacing:.08em;
         text-transform:uppercase;margin-bottom:8px}}
</style></head><body>
<div class="wrap">
  <div class="score-box">
    <div class="score-lbl">Risk Score</div>
    <div class="score-val">{_score}</div>
    <div class="score-nivel">{_nivel}</div>
    <div class="bar-wrap"><div class="bar-fill"></div></div>
    <div style="display:flex;justify-content:space-between;font-size:0.65rem;color:#334155">
      <span>0 Baixo</span><span>100 Alto</span>
    </div>
  </div>
  <div class="fatores-box">
    <div class="f-title">Fatores de Risco</div>
    {_fatores_html if _fatores_html else '<div style="color:#475569;font-size:0.8rem">Nenhum fator disponível</div>'}
  </div>
</div>
</body></html>"""
        components.html(_risk_html, height=max(160, 50 + len(_fatores) * 36), scrolling=False)
    except Exception as _e:
        st.info(f"Risk Score não disponível: {_e}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # Rodapé
    st.markdown("""
    <div style="
        margin-top:2.5rem;
        padding-top:1rem;
        border-top:1px solid #0A1628;
        text-align:center;
        color:#1E3A5F;
        font-size:0.72rem;
        letter-spacing:0.05em;
        font-weight:500
    ">
        Análise para fins informativos · Não constitui recomendação de investimento ·
        IL calculado pelo modelo AMM x*y=k
    </div>
    """, unsafe_allow_html=True)
