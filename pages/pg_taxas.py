import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import date, datetime
import database as db
import calculators as calc
import utils


def render():
    st.markdown(
        """
        <style>
        .card-box {
            background: #0D1F33;
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 8px;
        }
        .card-label {
            color: #94A3B8;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 4px;
        }
        .card-value {
            color: #F1F5F9;
            font-size: 22px;
            font-weight: 700;
        }
        .card-value-green {
            color: #10B981;
            font-size: 22px;
            font-weight: 700;
        }
        .empty-state {
            background: #0D1F33;
            border-radius: 10px;
            padding: 40px 20px;
            text-align: center;
            color: #64748B;
            font-size: 15px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Taxas Coletadas")

    # ------------------------------------------------------------------ #
    # SEÇÃO 1: REGISTRAR TAXA
    # ------------------------------------------------------------------ #
    st.subheader("Registrar Taxa Coletada")

    pools_ativas = db.listar_pools(apenas_ativas=True)

    if not pools_ativas:
        st.markdown(
            '<div class="empty-state">Nenhuma pool ativa. Ative ou crie uma pool para registrar taxas.</div>',
            unsafe_allow_html=True,
        )
        return

    opcoes_pool = {f"{p['nome']} ({p['token_a']}/{p['token_b']})": p for p in pools_ativas}
    pool_selecionada_label = st.selectbox(
        "Selecionar Pool",
        list(opcoes_pool.keys()),
        key="sel_pool_taxa",
    )
    pool_sel = opcoes_pool[pool_selecionada_label]
    token_a_nome = pool_sel["token_a"]
    token_b_nome = pool_sel["token_b"]

    with st.form("form_taxa", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_taxa = st.date_input("Data", value=date.today())
            token_a_amount = st.number_input(
                f"Quantidade {token_a_nome} coletado",
                min_value=0.0, step=0.000001, format="%.6f",
            )
            token_b_amount = st.number_input(
                f"Quantidade {token_b_nome} coletado",
                min_value=0.0, step=0.000001, format="%.6f",
            )
            valor_usd = st.number_input(
                "Valor das taxas em USD",
                min_value=0.0, step=0.01, format="%.2f",
            )

        with col2:
            st.markdown(
                "<div style='color:#94A3B8;font-size:0.78rem;font-weight:600;"
                "letter-spacing:0.06em;text-transform:uppercase;margin-bottom:8px'>"
                "📸 Snapshot da Pool (opcional)</div>",
                unsafe_allow_html=True,
            )
            valor_pool_usd = st.number_input(
                "Valor total da pool hoje (USD)",
                min_value=0.0, step=0.01, format="%.2f",
                help="Valor total da sua posição na pool neste momento. Usado para calcular IL preciso.",
            )
            token_a_price = st.number_input(
                f"Preço atual {token_a_nome} (USD)",
                min_value=0.0, step=0.01, format="%.4f",
                help=f"Preço de mercado atual do {token_a_nome}",
            )
            token_b_price = st.number_input(
                f"Preço atual {token_b_nome} (USD)",
                min_value=0.0, step=0.01, format="%.4f",
                help=f"Preço de mercado atual do {token_b_nome}",
            )
            observacao = st.text_area("Observação (opcional)", height=68)

        submitted = st.form_submit_button("Registrar Taxa", use_container_width=True)
        if submitted:
            if valor_usd <= 0 and token_a_amount <= 0 and token_b_amount <= 0:
                st.error("Informe ao menos o valor em USD ou quantidade de tokens coletados.")
            else:
                db.adicionar_taxa(
                    pool_id=pool_sel["id"],
                    data=str(data_taxa),
                    token_a_amount=token_a_amount,
                    token_b_amount=token_b_amount,
                    valor_usd=valor_usd,
                    valor_pool_usd=valor_pool_usd if valor_pool_usd > 0 else None,
                    token_a_price_usd=token_a_price if token_a_price > 0 else None,
                    token_b_price_usd=token_b_price if token_b_price > 0 else None,
                    observacao=observacao,
                )
                st.success("Taxa registrada com sucesso!")
                st.rerun()

    # ------------------------------------------------------------------ #
    # SEÇÃO 2: MÉTRICAS
    # ------------------------------------------------------------------ #
    taxas = db.listar_taxas(pool_sel["id"])
    total_fees = db.total_taxas_pool(pool_sel["id"])

    if not taxas:
        st.markdown(
            '<div class="empty-state">Nenhuma taxa registrada para esta pool ainda.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.subheader("Métricas de Taxas")

        maior_fee = max(t["valor_usd"] for t in taxas)
        media_fee = total_fees / len(taxas) if taxas else 0.0
        num_coletas = len(taxas)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(
                f'<div class="card-box">'
                f'<div class="card-label">Total Fees</div>'
                f'<div class="card-value-green">{utils.fmt_usd(total_fees)}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f'<div class="card-box">'
                f'<div class="card-label">Maior Fee Única</div>'
                f'<div class="card-value">{utils.fmt_usd(maior_fee)}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f'<div class="card-box">'
                f'<div class="card-label">Média por Coleta</div>'
                f'<div class="card-value">{utils.fmt_usd(media_fee)}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
        with col4:
            st.markdown(
                f'<div class="card-box">'
                f'<div class="card-label">Nº de Coletas</div>'
                f'<div class="card-value">{num_coletas}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

        # ------------------------------------------------------------------ #
        # SEÇÃO 3: HISTÓRICO DE TAXAS
        # ------------------------------------------------------------------ #
        st.subheader("Histórico de Taxas")

        header_cols = st.columns([1.5, 1.5, 1.5, 1.5, 2, 2, 1])
        for col, h in zip(header_cols, ["Data", token_a_nome, token_b_nome, "Taxas USD", "Valor Pool", "Observação", ""]):
            col.markdown(f"**{h}**")

        for taxa in sorted(taxas, key=lambda x: x["data"], reverse=True):
            col_data, col_ta, col_tb, col_usd, col_pool, col_obs, col_del = st.columns([1.5, 1.5, 1.5, 1.5, 2, 2, 1])
            with col_data:
                st.write(taxa["data"])
            with col_ta:
                st.write(utils.fmt_token(taxa["token_a_amount"]))
            with col_tb:
                st.write(utils.fmt_token(taxa["token_b_amount"]))
            with col_usd:
                st.write(utils.fmt_usd(taxa["valor_usd"]))
            with col_pool:
                vp = taxa.get("valor_pool_usd")
                if vp:
                    pa = taxa.get("token_a_price_usd")
                    pb = taxa.get("token_b_price_usd")
                    tip = f"{token_a_nome}={utils.fmt_usd(pa)} / {token_b_nome}={utils.fmt_usd(pb)}" if pa and pb else ""
                    st.markdown(
                        f"<span style='color:#60A5FA;font-weight:600'>{utils.fmt_usd(vp)}</span>"
                        + (f"<br><span style='color:#475569;font-size:0.72rem'>{tip}</span>" if tip else ""),
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown("<span style='color:#334155'>—</span>", unsafe_allow_html=True)
            with col_obs:
                confirmar_key = f"confirmar_del_taxa_{taxa['id']}"
                confirmar = st.checkbox("Confirmar", key=confirmar_key, label_visibility="collapsed")
                st.caption(taxa.get("observacao") or "—")
            with col_del:
                confirmar_state = st.session_state.get(f"confirmar_del_taxa_{taxa['id']}", False)
                if st.button("🗑", key=f"del_taxa_{taxa['id']}", help="Deletar taxa"):
                    if confirmar_state:
                        db.deletar_taxa(taxa["id"])
                        st.success("Taxa deletada.")
                        st.rerun()
                    else:
                        st.warning("Marque 'Confirmar' antes de deletar.")

        st.divider()

        # ------------------------------------------------------------------ #
        # SEÇÃO 4: GRÁFICO — ACUMULAÇÃO DE FEES
        # ------------------------------------------------------------------ #
        st.subheader("Acumulação de Fees ao Longo do Tempo")

        df = pd.DataFrame(taxas)
        df["data"] = pd.to_datetime(df["data"])
        df = df.sort_values("data")
        df["mes"] = df["data"].dt.to_period("M").astype(str)

        df_mensal = df.groupby("mes", as_index=False)["valor_usd"].sum()
        df_mensal = df_mensal.sort_values("mes")
        df_mensal["acumulado"] = df_mensal["valor_usd"].cumsum()

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            subplot_titles=("Fees Mensais", "Fees Acumuladas"),
            vertical_spacing=0.12,
            row_heights=[0.5, 0.5],
        )

        # Barras mensais
        fig.add_trace(
            go.Bar(
                x=df_mensal["mes"],
                y=df_mensal["valor_usd"],
                name="Fee Mensal",
                marker_color="#10B981",
                opacity=0.85,
            ),
            row=1,
            col=1,
        )

        # Linha acumulativa
        fig.add_trace(
            go.Scatter(
                x=df_mensal["mes"],
                y=df_mensal["acumulado"],
                name="Acumulado",
                mode="lines+markers",
                line=dict(color="#10B981", width=2),
                fill="tozeroy",
                fillcolor="rgba(16,185,129,0.12)",
            ),
            row=2,
            col=1,
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,31,51,0.8)",
            font=dict(color="#F1F5F9", family="Inter, Segoe UI, sans-serif"),
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            showlegend=True,
        )

        fig.update_xaxes(gridcolor="#1E3A5F")
        fig.update_yaxes(gridcolor="#1E3A5F")

        # Subplot backgrounds
        fig.update_layout(
            **{
                "xaxis": dict(gridcolor="#1E3A5F"),
                "yaxis": dict(gridcolor="#1E3A5F", title="USD"),
                "xaxis2": dict(gridcolor="#1E3A5F"),
                "yaxis2": dict(gridcolor="#1E3A5F", title="USD"),
            }
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="taxas_evolucao")

    # ------------------------------------------------------------------ #
    # SEÇÃO 5: COMPARATIVO ENTRE POOLS (somente se há >1 pool)
    # ------------------------------------------------------------------ #
    todas_pools = db.listar_pools(apenas_ativas=False)

    if len(todas_pools) > 1:
        st.subheader("Comparativo de Fees entre Pools")

        dados_comp = []
        for pool in todas_pools:
            total = db.total_taxas_pool(pool["id"])
            if total > 0:
                dados_comp.append(
                    {
                        "pool": f"{pool['nome']}\n({pool['token_a']}/{pool['token_b']})",
                        "total": total,
                        "chain": pool["chain"],
                    }
                )

        if not dados_comp:
            st.markdown(
                '<div class="empty-state">Nenhuma pool com taxas registradas para comparar.</div>',
                unsafe_allow_html=True,
            )
        else:
            df_comp = pd.DataFrame(dados_comp).sort_values("total", ascending=True)

            cores_chain = [
                utils.CHAIN_CORES.get(row["chain"], "#2563EB") for _, row in df_comp.iterrows()
            ]

            fig_comp = go.Figure(
                go.Bar(
                    x=df_comp["total"],
                    y=df_comp["pool"],
                    orientation="h",
                    marker_color=cores_chain,
                    text=[utils.fmt_usd(v) for v in df_comp["total"]],
                    textposition="outside",
                )
            )

            fig_comp.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13,31,51,0.8)",
                font=dict(color="#F1F5F9", family="Inter, Segoe UI, sans-serif"),
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis=dict(title="Total Fees (USD)", gridcolor="#1E3A5F"),
                yaxis=dict(gridcolor="#1E3A5F"),
                title="Total de Fees por Pool",
            )

            st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar": False}, key="taxas_comparativo")
