import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
from datetime import date
import database as db
import calculators as calc
import utils


# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────

def _metric_card(label: str, value: str, color: str = "#F1F5F9", sub: str = "") -> str:
    sub_html = f'<div style="color:#64748B;font-size:11px;margin-top:4px">{sub}</div>' if sub else ""
    return f"""
    <div style="background:#0D1F33;border-radius:12px;padding:18px 20px;flex:1;min-width:140px">
        <div style="color:#94A3B8;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px">{label}</div>
        <div style="color:{color};font-size:22px;font-weight:700;line-height:1">{value}</div>
        {sub_html}
    </div>"""


def _render_cards(cards_html: list[str], gap: str = "12px"):
    html = f'<div style="display:flex;gap:{gap};flex-wrap:wrap;margin-bottom:16px">{"".join(cards_html)}</div>'
    components.html(html, height=110, scrolling=False)


def _pool_header_html(pool: dict) -> str:
    chain_cor = utils.CHAIN_CORES.get(pool["chain"], "#64748B")
    proto_icone = utils.PROTOCOLO_ICONES.get(pool["protocolo"], "🏦")
    fee = f' · {pool["fee_tier"]}' if pool.get("fee_tier") else ""
    ativa_badge = (
        '<span style="background:#10B98122;color:#10B981;border-radius:20px;padding:3px 10px;font-size:11px;font-weight:600">● Ativa</span>'
        if pool["ativa"]
        else '<span style="background:#EF444422;color:#EF4444;border-radius:20px;padding:3px 10px;font-size:11px;font-weight:600">● Inativa</span>'
    )
    range_html = ""
    if pool.get("preco_min") and pool.get("preco_max"):
        range_html = f'<span style="background:#1E3A5F;color:#60A5FA;border-radius:6px;padding:3px 10px;font-size:11px;margin-left:8px">⬌ {utils.fmt_usd(pool["preco_min"])} – {utils.fmt_usd(pool["preco_max"])}</span>'

    return f"""
    <div style="background:#0D1F33;border-radius:12px;padding:16px 20px;margin-bottom:4px;display:flex;align-items:center;gap:14px;flex-wrap:wrap">
        <div style="background:{chain_cor}22;border-radius:8px;padding:8px 12px;font-size:20px">{proto_icone}</div>
        <div style="flex:1">
            <div style="color:#F1F5F9;font-size:17px;font-weight:700">{pool['nome']}</div>
            <div style="color:#64748B;font-size:12px;margin-top:2px">
                {pool['token_a']}/{pool['token_b']}{fee} · {pool['protocolo']} · {pool['chain']}
            </div>
        </div>
        {ativa_badge}{range_html}
    </div>"""


def _posicao_card_html(pos: dict, token_a: str, token_b: str, idx: int) -> str:
    obs = pos.get("observacao") or ""
    obs_html = f'<div style="color:#64748B;font-size:11px;margin-top:6px;font-style:italic">💬 {obs}</div>' if obs else ""
    return f"""
    <div style="background:#0D1F33;border-radius:10px;padding:14px 18px;margin-bottom:8px;border-left:3px solid #2563EB">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
            <div style="display:flex;gap:20px;flex-wrap:wrap;align-items:center">
                <div>
                    <div style="color:#64748B;font-size:10px;text-transform:uppercase;letter-spacing:0.07em">Data</div>
                    <div style="color:#F1F5F9;font-size:14px;font-weight:600">{pos['data']}</div>
                </div>
                <div>
                    <div style="color:#64748B;font-size:10px;text-transform:uppercase;letter-spacing:0.07em">{token_a}</div>
                    <div style="color:#60A5FA;font-size:14px;font-weight:600">{utils.fmt_token(pos['token_a_amount'])}</div>
                    <div style="color:#475569;font-size:10px">@ {utils.fmt_usd(pos['token_a_price_usd'])}</div>
                </div>
                <div>
                    <div style="color:#64748B;font-size:10px;text-transform:uppercase;letter-spacing:0.07em">{token_b}</div>
                    <div style="color:#60A5FA;font-size:14px;font-weight:600">{utils.fmt_token(pos['token_b_amount'])}</div>
                    <div style="color:#475569;font-size:10px">@ {utils.fmt_usd(pos['token_b_price_usd'])}</div>
                </div>
            </div>
            <div style="text-align:right">
                <div style="color:#64748B;font-size:10px;text-transform:uppercase;letter-spacing:0.07em">Capital</div>
                <div style="color:#10B981;font-size:16px;font-weight:700">{utils.fmt_usd(pos['capital_usd'])}</div>
            </div>
        </div>
        {obs_html}
    </div>"""


# ──────────────────────────────────────────────────────────────
# RENDER PRINCIPAL
# ──────────────────────────────────────────────────────────────

def render():
    st.title("Posições em Pools")

    todas_pools = db.listar_pools(apenas_ativas=False)
    pools_ativas = [p for p in todas_pools if p["ativa"]]

    # ── Tab principal ──────────────────────────────────────────
    tab_visao, tab_aporte, tab_historico, tab_gerenciar = st.tabs([
        "📊  Visão Geral",
        "➕  Registrar Aporte",
        "📋  Histórico",
        "⚙️  Gerenciar Pools",
    ])

    # ══════════════════════════════════════════════════════════
    # TAB 1 — VISÃO GERAL
    # ══════════════════════════════════════════════════════════
    with tab_visao:
        if not pools_ativas:
            st.info("Nenhuma pool ativa. Crie uma pool na aba ⚙️ Gerenciar Pools.")
        else:
            opcoes = {f"{p['nome']}  ({p['token_a']}/{p['token_b']})": p for p in pools_ativas}
            label = st.selectbox("Pool", list(opcoes.keys()), key="sel_visao")
            pool = opcoes[label]

            # Header visual da pool
            components.html(_pool_header_html(pool), height=90, scrolling=False)

            posicoes = db.listar_posicoes(pool["id"])

            if not posicoes:
                st.info("Nenhum aporte registrado para esta pool. Use a aba ➕ Registrar Aporte.")
            else:
                token_a = pool["token_a"]
                token_b = pool["token_b"]

                pm_a = calc.calcular_preco_medio(posicoes, token="a")
                pm_b = calc.calcular_preco_medio(posicoes, token="b")
                cap = calc.calcular_capital_total(posicoes)
                n = len(posicoes)
                total_a = sum(p["token_a_amount"] for p in posicoes)
                total_b = sum(p["token_b_amount"] for p in posicoes)

                cards = [
                    _metric_card(f"Preço Médio {token_a}", utils.fmt_usd(pm_a), "#10B981"),
                    _metric_card(f"Preço Médio {token_b}", utils.fmt_usd(pm_b), "#10B981"),
                    _metric_card("Capital Investido", utils.fmt_usd(cap), "#F1F5F9"),
                    _metric_card("Aportes", str(n), "#60A5FA"),
                    _metric_card(f"Total {token_a}", utils.fmt_token(total_a), "#94A3B8"),
                    _metric_card(f"Total {token_b}", utils.fmt_token(total_b), "#94A3B8"),
                ]
                html_row = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">' + "".join(cards) + "</div>"
                components.html(html_row, height=120, scrolling=False)

                # Gráfico
                df = pd.DataFrame(posicoes)
                df["data"] = pd.to_datetime(df["data"])
                df = df.sort_values("data")
                df["acumulado"] = df["capital_usd"].cumsum()

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df["data"], y=df["capital_usd"],
                    name="Aporte", marker_color="#2563EB", opacity=0.75,
                ))
                fig.add_trace(go.Scatter(
                    x=df["data"], y=df["acumulado"],
                    name="Acumulado", mode="lines+markers",
                    line=dict(color="#10B981", width=2),
                    fill="tozeroy", fillcolor="rgba(16,185,129,0.08)",
                    yaxis="y2",
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(13,31,51,0.8)",
                    font=dict(color="#F1F5F9"),
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=240,
                    legend=dict(orientation="h", y=1.08, x=1, xanchor="right"),
                    yaxis=dict(title="Aporte USD", gridcolor="#1E3A5F"),
                    yaxis2=dict(title="Acumulado", overlaying="y", side="right", gridcolor="#1E3A5F"),
                    xaxis=dict(gridcolor="#1E3A5F"),
                    title="Evolução do Capital Investido",
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="posicoes_evolucao")

    # ══════════════════════════════════════════════════════════
    # TAB 2 — REGISTRAR APORTE
    # ══════════════════════════════════════════════════════════
    with tab_aporte:
        if not pools_ativas:
            st.info("Crie e ative uma pool na aba ⚙️ Gerenciar Pools para registrar aportes.")
        else:
            opcoes2 = {f"{p['nome']}  ({p['token_a']}/{p['token_b']})": p for p in pools_ativas}
            label2 = st.selectbox("Pool", list(opcoes2.keys()), key="sel_aporte")
            pool2 = opcoes2[label2]
            token_a2 = pool2["token_a"]
            token_b2 = pool2["token_b"]

            st.markdown("---")

            modo = st.radio(
                "Como informar o preço?",
                ["💰  Valor total pago  (ex: paguei $26,72 por 0.012 ETH)", "📈  Preço unitário  (ex: ETH = $2,100)"],
                horizontal=True, key="modo_preco2",
            )
            usar_total = modo.startswith("💰")

            with st.form("form_aporte2", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**{token_a2}**")
                    qtd_a = st.number_input(f"Quantidade {token_a2}", min_value=0.0, step=0.000001, format="%.6f", key="qtd_a2")
                    if usar_total:
                        total_a_pago = st.number_input(f"Total pago em {token_a2} (USD)", min_value=0.0, step=0.01, format="%.2f",
                                                        help=f"Ex: 0.012 {token_a2} custou $26.72 → informe 26.72")
                    else:
                        preco_a = st.number_input(f"Preço unitário {token_a2} (USD)", min_value=0.0, step=0.01, format="%.2f")

                with c2:
                    st.markdown(f"**{token_b2}**")
                    qtd_b = st.number_input(f"Quantidade {token_b2}", min_value=0.0, step=0.000001, format="%.6f", key="qtd_b2")
                    if usar_total:
                        total_b_pago = st.number_input(f"Total pago em {token_b2} (USD)", min_value=0.0, step=0.01, format="%.2f")
                    else:
                        preco_b = st.number_input(f"Preço unitário {token_b2} (USD)", min_value=0.0, step=0.01, format="%.2f")

                c3, c4 = st.columns([1, 2])
                with c3:
                    data_ap = st.date_input("Data", value=date.today())
                with c4:
                    obs_ap = st.text_input("Observação (opcional)")

                submitted = st.form_submit_button("✅  Registrar Aporte", use_container_width=True, type="primary")
                if submitted:
                    if qtd_a <= 0 and qtd_b <= 0:
                        st.error("Informe ao menos a quantidade de um token.")
                    else:
                        if usar_total:
                            pa = (total_a_pago / qtd_a) if qtd_a > 0 else 0.0
                            pb = (total_b_pago / qtd_b) if qtd_b > 0 else 0.0
                            cap2 = total_a_pago + total_b_pago
                        else:
                            pa, pb = preco_a, preco_b
                            cap2 = qtd_a * pa + qtd_b * pb
                        db.adicionar_posicao(
                            pool_id=pool2["id"], data=str(data_ap),
                            token_a_amount=qtd_a, token_b_amount=qtd_b,
                            token_a_price_usd=pa, token_b_price_usd=pb,
                            capital_usd=cap2, observacao=obs_ap,
                        )
                        st.success("Aporte registrado!")
                        st.rerun()

    # ══════════════════════════════════════════════════════════
    # TAB 3 — HISTÓRICO
    # ══════════════════════════════════════════════════════════
    with tab_historico:
        if not pools_ativas:
            st.info("Nenhuma pool ativa.")
        else:
            opcoes3 = {f"{p['nome']}  ({p['token_a']}/{p['token_b']})": p for p in pools_ativas}
            label3 = st.selectbox("Pool", list(opcoes3.keys()), key="sel_hist")
            pool3 = opcoes3[label3]
            token_a3 = pool3["token_a"]
            token_b3 = pool3["token_b"]

            posicoes3 = db.listar_posicoes(pool3["id"])

            if not posicoes3:
                st.info("Nenhum aporte registrado para esta pool ainda.")
            else:
                posicoes3_sorted = sorted(posicoes3, key=lambda x: x["data"], reverse=True)

                # Resumo rápido
                cap3 = sum(p["capital_usd"] for p in posicoes3)
                st.caption(f"{len(posicoes3)} aportes · Capital total: **{utils.fmt_usd(cap3)}**")
                st.markdown("---")

                for pos in posicoes3_sorted:
                    # Card visual
                    card_h = 100 if not pos.get("observacao") else 120
                    components.html(_posicao_card_html(pos, token_a3, token_b3, pos["id"]), height=card_h, scrolling=False)

                    # Botão de deletar logo abaixo do card
                    del_key = f"del_confirm_{pos['id']}"
                    if del_key not in st.session_state:
                        st.session_state[del_key] = False

                    col_space, col_btn = st.columns([8, 2])
                    with col_btn:
                        if not st.session_state[del_key]:
                            if st.button("🗑  Excluir", key=f"del_btn_{pos['id']}", use_container_width=True):
                                st.session_state[del_key] = True
                                st.rerun()
                        else:
                            st.warning("Confirmar exclusão?")
                            cc1, cc2 = st.columns(2)
                            with cc1:
                                if st.button("✅ Sim", key=f"del_yes_{pos['id']}", use_container_width=True, type="primary"):
                                    db.deletar_posicao(pos["id"])
                                    st.session_state.pop(del_key, None)
                                    st.rerun()
                            with cc2:
                                if st.button("❌ Não", key=f"del_no_{pos['id']}", use_container_width=True):
                                    st.session_state[del_key] = False
                                    st.rerun()

    # ══════════════════════════════════════════════════════════
    # TAB 4 — GERENCIAR POOLS
    # ══════════════════════════════════════════════════════════
    with tab_gerenciar:
        # ── Criar nova pool ───────────────────────────────────
        with st.expander("➕  Cadastrar Nova Pool", expanded=not bool(todas_pools)):
            with st.form("form_criar_pool", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    nome = st.text_input("Nome da Pool", placeholder="Ex: ETH/USDC Main")
                    protocolo = st.selectbox("Protocolo", [
                        "Uniswap v3","Uniswap v2","PancakeSwap","Curve",
                        "Balancer","SushiSwap","Raydium","Orca","Outro",
                    ])
                    chain = st.selectbox("Chain", [
                        "Ethereum","Arbitrum","Base","BSC","Polygon",
                        "Avalanche","Solana","Optimism","Outra",
                    ])
                with c2:
                    token_a_new = st.text_input("Token A", placeholder="ETH")
                    token_b_new = st.text_input("Token B", placeholder="USDC")
                    fee_tier = st.selectbox("Fee Tier", ["","0.01%","0.05%","0.3%","1%","Personalizado"])

                st.markdown("**Range de Preço** *(opcional — Concentrated Liquidity)*")
                cr1, cr2 = st.columns(2)
                with cr1:
                    pmin = st.number_input("Preço mínimo (USD)", min_value=0.0, step=0.01, format="%.4f", key="new_pmin")
                with cr2:
                    pmax = st.number_input("Preço máximo (USD)", min_value=0.0, step=0.01, format="%.4f", key="new_pmax")

                if st.form_submit_button("Criar Pool", use_container_width=True, type="primary"):
                    if not nome.strip():
                        st.error("Informe o nome.")
                    elif not token_a_new.strip() or not token_b_new.strip():
                        st.error("Informe os dois tokens.")
                    else:
                        db.criar_pool(
                            nome.strip(), protocolo, chain,
                            token_a_new.strip().upper(), token_b_new.strip().upper(),
                            fee_tier,
                            preco_min=pmin if pmin > 0 else None,
                            preco_max=pmax if pmax > 0 else None,
                        )
                        st.success(f"Pool '{nome.strip()}' criada!")
                        st.rerun()

        if not todas_pools:
            st.info("Nenhuma pool cadastrada ainda.")
        else:
            st.markdown("### Pools")
            for pool in todas_pools:
                components.html(_pool_header_html(pool), height=86, scrolling=False)

                c_act, c_range, c_del = st.columns([2, 4, 2])

                with c_act:
                    label_btn = "⏸  Desativar" if pool["ativa"] else "▶  Ativar"
                    if st.button(label_btn, key=f"status_{pool['id']}", use_container_width=True):
                        db.atualizar_pool_status(pool["id"], not pool["ativa"])
                        st.rerun()

                with c_range:
                    _pmin = pool.get("preco_min")
                    _pmax = pool.get("preco_max")
                    range_label = (
                        f"⬌  Range atual: {utils.fmt_usd(_pmin)} – {utils.fmt_usd(_pmax)}  (clique para editar)"
                        if (_pmin and _pmax) else "⬌  Definir Range de Preço"
                    )
                    with st.expander(range_label, expanded=False):
                        rc1, rc2 = st.columns(2)
                        with rc1:
                            new_pmin = st.number_input(
                                f"Mínimo {pool['token_a']} (USD)", min_value=0.0,
                                value=float(_pmin) if _pmin else 0.0,
                                step=0.01, format="%.4f", key=f"emin_{pool['id']}",
                            )
                        with rc2:
                            new_pmax = st.number_input(
                                f"Máximo {pool['token_a']} (USD)", min_value=0.0,
                                value=float(_pmax) if _pmax else 0.0,
                                step=0.01, format="%.4f", key=f"emax_{pool['id']}",
                            )
                        if st.button("Salvar Range", key=f"save_range_{pool['id']}", use_container_width=True):
                            db.atualizar_pool_range(pool["id"],
                                new_pmin if new_pmin > 0 else None,
                                new_pmax if new_pmax > 0 else None,
                            )
                            st.success("Range atualizado!")
                            st.rerun()

                with c_del:
                    del_pool_key = f"del_pool_confirm_{pool['id']}"
                    if del_pool_key not in st.session_state:
                        st.session_state[del_pool_key] = False

                    if not st.session_state[del_pool_key]:
                        if st.button("🗑  Deletar", key=f"del_pool_btn_{pool['id']}", use_container_width=True):
                            st.session_state[del_pool_key] = True
                            st.rerun()
                    else:
                        st.error("Apaga tudo?")
                        dc1, dc2 = st.columns(2)
                        with dc1:
                            if st.button("✅", key=f"dp_yes_{pool['id']}", use_container_width=True, type="primary"):
                                db.deletar_pool(pool["id"])
                                st.session_state.pop(del_pool_key, None)
                                st.rerun()
                        with dc2:
                            if st.button("❌", key=f"dp_no_{pool['id']}", use_container_width=True):
                                st.session_state[del_pool_key] = False
                                st.rerun()

                st.markdown('<div style="border-top:1px solid #1E3A5F;margin:12px 0"></div>', unsafe_allow_html=True)
