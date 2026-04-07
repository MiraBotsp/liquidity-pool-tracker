import streamlit as st
import database as db
from pages import pg_dashboard, pg_posicoes, pg_taxas, pg_analise

st.set_page_config(
    page_title="Liquidity Pool Tracker",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()

# ── CSS Global ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"], .main {
    background-color: #060B14 !important;
    color: #F1F5F9 !important;
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
}

/* ── Chrome / Header / Decorations ── */
[data-testid="stHeader"]     { background-color: #060B14 !important; }
[data-testid="stToolbar"]    { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Layout principal ── */
.main .block-container {
    padding: 2rem 3rem 3rem 3rem !important;
    max-width: 1440px;
}

/* ── Scrollbar customizado ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #060B14; border-radius: 10px; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #1A2D42, #2563EB44);
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover { background: #2563EB88; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #0A1628 !important;
    border-right: 1px solid #0F1F35 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}
[data-testid="stSidebar"] .block-container {
    padding: 1rem 1rem 2rem 1rem !important;
}

/* ── Botões Streamlit ── */
.stButton > button {
    background-color: #1E3A5F !important;
    color: #CBD5E1 !important;
    border: 1px solid #1E3A5F !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    transition: all 0.2s ease !important;
    padding: 0.45rem 1rem !important;
}
.stButton > button:hover {
    background-color: #2563EB !important;
    border-color: #2563EB !important;
    color: #FFFFFF !important;
    box-shadow: 0 0 12px #2563EB44 !important;
    transform: translateY(-1px);
}
.stButton > button:active {
    transform: translateY(0px);
    box-shadow: none !important;
}
/* Botão primário (página ativa) */
.stButton > button[kind="primary"] {
    background-color: #2563EB !important;
    border-color: #2563EB !important;
    color: #FFFFFF !important;
    box-shadow: 0 0 14px #2563EB33 !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #3B82F6 !important;
    border-color: #3B82F6 !important;
    box-shadow: 0 0 20px #3B82F655 !important;
}

/* ── Inputs, Selects, Text Areas ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input,
.stTimeInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #0D1F33 !important;
    border: 1px solid #1E3A5F !important;
    border-radius: 8px !important;
    color: #F1F5F9 !important;
    font-size: 0.875rem !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px #2563EB22 !important;
    outline: none !important;
}
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background-color: #0D1F33 !important;
    border: 1px solid #1E3A5F !important;
    border-radius: 8px !important;
    color: #F1F5F9 !important;
}
.stSelectbox > div > div:hover,
.stMultiSelect > div > div:hover {
    border-color: #2563EB !important;
}
/* Dropdown options */
[data-baseweb="select"] [role="listbox"],
[data-baseweb="popover"] {
    background-color: #0D1F33 !important;
    border: 1px solid #1E3A5F !important;
    border-radius: 8px !important;
}
[data-baseweb="select"] [role="option"]:hover {
    background-color: #1E3A5F !important;
}

/* ── Labels ── */
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stMultiSelect label, .stDateInput label, .stTextArea label,
.stSlider label {
    color: #94A3B8 !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}

/* ── Dataframes / Tabelas ── */
[data-testid="stDataFrame"],
[data-testid="stTable"] {
    background-color: #0A1628 !important;
    border: 1px solid #0F1F35 !important;
    border-radius: 10px !important;
    overflow: hidden;
}
[data-testid="stDataFrame"] table,
[data-testid="stTable"] table {
    background-color: #0A1628 !important;
    color: #F1F5F9 !important;
}
[data-testid="stDataFrame"] thead tr th,
[data-testid="stTable"] thead tr th {
    background-color: #0D1F33 !important;
    color: #60A5FA !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    border-bottom: 1px solid #1E3A5F !important;
}
[data-testid="stDataFrame"] tbody tr:hover td,
[data-testid="stTable"] tbody tr:hover td {
    background-color: #0F1F35 !important;
}
[data-testid="stDataFrame"] tbody tr td,
[data-testid="stTable"] tbody tr td {
    border-bottom: 1px solid #0F1F3566 !important;
    color: #CBD5E1 !important;
    font-size: 0.875rem !important;
}

/* ── Métricas Streamlit ── */
[data-testid="stMetric"] {
    background-color: #0D1F33 !important;
    border-left: 3px solid #2563EB !important;
    border-radius: 0 8px 8px 0 !important;
    padding: 1rem 1.25rem !important;
}
[data-testid="stMetricLabel"] {
    color: #64748B !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
[data-testid="stMetricValue"] {
    color: #F1F5F9 !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}
[data-testid="stMetricDelta"] svg { display: none; }
[data-testid="stMetricDelta"] > div {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
}

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    background-color: #0A1628 !important;
    border-bottom: 1px solid #0F1F35 !important;
    gap: 0.25rem;
}
[data-baseweb="tab"] {
    background-color: transparent !important;
    color: #64748B !important;
    border-radius: 6px 6px 0 0 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 0.6rem 1.2rem !important;
    transition: color 0.2s ease;
}
[data-baseweb="tab"]:hover {
    color: #94A3B8 !important;
    background-color: #0F1F3555 !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    color: #60A5FA !important;
    border-bottom: 2px solid #2563EB !important;
    background-color: transparent !important;
}
[data-baseweb="tab-panel"] {
    background-color: #060B14 !important;
    padding-top: 1.5rem !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background-color: #0A1628 !important;
    border: 1px solid #0F1F35 !important;
    border-radius: 10px !important;
}
[data-testid="stExpander"] summary {
    color: #94A3B8 !important;
    font-weight: 500 !important;
}
[data-testid="stExpander"] summary:hover {
    color: #60A5FA !important;
}

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid #0F1F35 !important;
    margin: 1.5rem 0 !important;
}

/* ── Alertas / Info / Warning ── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    border: none !important;
    font-size: 0.875rem !important;
}

/* ── Progress / Spinner ── */
[data-testid="stProgress"] > div > div {
    background-color: #2563EB !important;
}

/* ── Headings ── */
h1 { color: #F1F5F9 !important; font-weight: 700 !important; letter-spacing: -0.03em; }
h2 { color: #E2E8F0 !important; font-weight: 600 !important; letter-spacing: -0.02em; }
h3 { color: #CBD5E1 !important; font-weight: 600 !important; }
h4 { color: #94A3B8 !important; font-weight: 500 !important; }

/* ── Animações ── */
@keyframes pulse-green {
    0%   { box-shadow: 0 0 0 0 #22C55E44; }
    70%  { box-shadow: 0 0 0 8px #22C55E00; }
    100% { box-shadow: 0 0 0 0 #22C55E00; }
}
@keyframes pulse-blue {
    0%   { box-shadow: 0 0 0 0 #2563EB44; }
    70%  { box-shadow: 0 0 0 8px #2563EB00; }
    100% { box-shadow: 0 0 0 0 #2563EB00; }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}
@keyframes shimmer {
    0%   { background-position: -200% center; }
    100% { background-position:  200% center; }
}

/* ── Cards LP ── */
.lp-card {
    background: #0D1F33;
    border: 1px solid #1E3A5F;
    border-radius: 12px;
    padding: 1.5rem;
    animation: fadeInUp 0.35s ease both;
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}
.lp-card:hover {
    border-color: #2563EB66;
    box-shadow: 0 4px 24px #2563EB11;
    transform: translateY(-2px);
}

.lp-card-highlight {
    background: #0D1F33;
    border: 1px solid #2563EB;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 0 20px #2563EB22;
    animation: fadeInUp 0.35s ease both;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.lp-card-highlight:hover {
    box-shadow: 0 0 32px #2563EB44;
    transform: translateY(-2px);
}

/* Card de status positivo */
.lp-card-positive {
    background: #0D1F33;
    border: 1px solid #166534;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 0 16px #22C55E11;
    animation: pulse-green 2.5s infinite;
}

/* Card de status negativo */
.lp-card-negative {
    background: #0D1F33;
    border: 1px solid #7F1D1D;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 0 16px #EF444411;
}

/* ── Badges / Tags ── */
.lp-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.lp-badge-blue   { background: #1E3A5F; color: #60A5FA; border: 1px solid #2563EB44; }
.lp-badge-green  { background: #14532D; color: #4ADE80; border: 1px solid #22C55E44; }
.lp-badge-red    { background: #450A0A; color: #F87171; border: 1px solid #EF444444; }
.lp-badge-yellow { background: #422006; color: #FCD34D; border: 1px solid #F59E0B44; }
.lp-badge-purple { background: #2E1065; color: #C084FC; border: 1px solid #A855F744; }

/* ── Stat Row ── */
.lp-stat-row {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
}
.lp-stat-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.lp-stat-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: #F1F5F9;
    letter-spacing: -0.02em;
    line-height: 1.2;
}
.lp-stat-delta-pos { font-size: 0.8rem; font-weight: 600; color: #4ADE80; }
.lp-stat-delta-neg { font-size: 0.8rem; font-weight: 600; color: #F87171; }

/* ── Section title ── */
.lp-section-title {
    font-size: 0.72rem;
    font-weight: 700;
    color: #334155;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #0F1F35;
}

/* ── Pool logo placeholder ── */
.lp-pool-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #1E3A5F, #2563EB44);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
    border: 1px solid #2563EB44;
}

/* ── Shimmer loading effect ── */
.lp-shimmer {
    background: linear-gradient(90deg,
        #0D1F33 25%, #1E3A5F44 50%, #0D1F33 75%);
    background-size: 200% auto;
    animation: shimmer 1.5s linear infinite;
    border-radius: 6px;
}

/* ── Gráficos Plotly ── */
[data-testid="stPlotlyChart"] {
    background: transparent !important;
    border-radius: 12px;
}
.js-plotly-plot .plotly .modebar {
    background: #0D1F33 !important;
}
.js-plotly-plot .plotly .modebar-btn path {
    fill: #475569 !important;
}
.js-plotly-plot .plotly .modebar-btn:hover path {
    fill: #60A5FA !important;
}

/* ── Toast / Notification ── */
[data-testid="stToast"] {
    background-color: #0D1F33 !important;
    border: 1px solid #1E3A5F !important;
    border-radius: 10px !important;
    color: #F1F5F9 !important;
}

/* ── Sidebar Nav Buttons ── */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid rgba(37,99,235,0.12) !important;
    border-radius: 10px !important;
    color: #64748B !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 0.55rem 1rem !important;
    text-align: left !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.01em !important;
    margin-bottom: 2px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(37,99,235,0.10) !important;
    border-color: rgba(37,99,235,0.35) !important;
    color: #F1F5F9 !important;
    transform: translateX(3px) !important;
}
/* Botão ativo (primary) */
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, rgba(37,99,235,0.25), rgba(16,185,129,0.10)) !important;
    border: 1px solid rgba(37,99,235,0.5) !important;
    color: #F1F5F9 !important;
    font-weight: 700 !important;
    box-shadow: 0 0 12px rgba(37,99,235,0.20), inset 0 0 0 1px rgba(37,99,235,0.15) !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, #2563EB, #10B981);
    border-radius: 3px 0 0 3px;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    position: relative;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="padding:1.2rem 0 1.5rem 0;border-bottom:1px solid rgba(37,99,235,0.12);margin-bottom:1.2rem">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem">
        <div style="width:36px;height:36px;border-radius:10px;
                    background:linear-gradient(135deg,#1E3A5F,#2563EB);
                    display:flex;align-items:center;justify-content:center;
                    font-size:1.1rem;box-shadow:0 0 12px rgba(37,99,235,0.3)">💧</div>
        <div>
            <div style="font-size:0.92rem;font-weight:700;color:#F1F5F9;line-height:1.2">Liquidity Pool</div>
            <div style="font-size:0.65rem;font-weight:700;color:#2563EB;letter-spacing:0.1em;text-transform:uppercase">Tracker</div>
        </div>
    </div>
    <div style="font-size:0.72rem;color:#1E3A5F;letter-spacing:0.03em">
        Gestão de Pools DeFi
    </div>
</div>
""", unsafe_allow_html=True)

    if "pagina" not in st.session_state:
        st.session_state.pagina = "Dashboard"

    paginas = {
        "Dashboard": "📊",
        "Posições":  "🏊",
        "Taxas":     "💰",
        "Análise":   "📈",
    }

    for nome, icone in paginas.items():
        ativo = st.session_state.pagina == nome
        tipo  = "primary" if ativo else "secondary"
        label = f"{icone}  {nome}"
        if st.button(label, key=f"nav_{nome}", use_container_width=True, type=tipo):
            st.session_state.pagina = nome
            st.rerun()

    st.markdown("""
<div style="margin-top:1.5rem;padding-top:1rem;border-top:1px solid rgba(37,99,235,0.10);
     color:#1E3A5F;font-size:0.68rem;text-align:center;letter-spacing:0.04em">
    v 1.0.0 · DeFi Tracker
</div>
""", unsafe_allow_html=True)

# ── Dispatcher ─────────────────────────────────────────────────────────────────
pagina = st.session_state.get("pagina", "Dashboard")

if   pagina == "Dashboard": pg_dashboard.render()
elif pagina == "Posições":  pg_posicoes.render()
elif pagina == "Taxas":     pg_taxas.render()
elif pagina == "Análise":   pg_analise.render()
