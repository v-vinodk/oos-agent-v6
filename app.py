import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="noon OOS Agent",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auth ──────────────────────────────────────────────────────────────────────
from auth.auth import is_authenticated, login_page, logout
if not is_authenticated():
    login_page()
    st.stop()

# ── Data & agent ──────────────────────────────────────────────────────────────
from agent.core import run_agent
from components.charts import render_charts_for_tool
from data.loader import get_inventory_df, get_history_df, get_csv_info, _get_actual_columns

INVENTORY_DF = get_inventory_df()
HISTORY_DF   = get_history_df()
CSV_INFO     = get_csv_info()

# ── noon brand colours ────────────────────────────────────────────────────────
# Primary yellow : #FFCE00
# Dark bg        : #1A1A1A  /  #242424
# Accent yellow  : rgba(255,206,0,…)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
[data-testid="stAppViewContainer"]>.main{background:#f7f7f7;min-height:100vh}
#MainMenu,footer,header{visibility:hidden}

/* ── Sidebar ── */
[data-testid="stSidebar"]>div:first-child{
    background:linear-gradient(180deg,#1A1A1A 0%,#242424 50%,#1A1A1A 100%);
    border-right:none;
}
[data-testid="stSidebar"] .block-container{padding:0 !important}
[data-testid="stSidebar"] *{color:#f0f0f0}

.sbar-section{
    font-size:9.5px;font-weight:700;letter-spacing:0.12em;
    text-transform:uppercase;color:rgba(255,206,0,0.55);
    padding:14px 16px 5px;margin:0;
    border-top:1px solid rgba(255,255,255,0.06);
}

[data-testid="stSidebar"] .stButton>button{
    background:none;border:none;color:rgba(240,240,240,0.82);
    font-size:12px;font-weight:400;text-align:left;
    padding:7px 16px 7px 32px;width:100%;border-radius:0;
    position:relative;line-height:1.5;height:auto;
    white-space:normal;transition:all .15s;
    border-left:2px solid transparent;
}
[data-testid="stSidebar"] .stButton>button::before{
    content:'›';position:absolute;left:13px;top:50%;
    transform:translateY(-50%);
    color:rgba(255,206,0,0.45);font-size:16px;font-weight:700;
    transition:all .18s;
}
[data-testid="stSidebar"] .stButton>button:hover{
    background:rgba(255,206,0,0.12);color:#fff;
    border-left-color:#FFCE00;padding-left:36px;
}
[data-testid="stSidebar"] .stButton>button:hover::before{color:#FFCE00}
[data-testid="stSidebar"] .stButton>button:focus{box-shadow:none;outline:none}

/* noon logo strip */
.noon-logo-strip{
    padding:14px 16px 12px;
    border-bottom:1px solid rgba(255,206,0,0.14);
    display:flex;align-items:center;gap:10px;
}
.noon-logo-sub{
    font-size:9px;color:rgba(255,206,0,0.45);
    letter-spacing:0.1em;text-transform:uppercase;margin-top:2px;
}

/* User card */
.s-user{display:flex;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid rgba(255,255,255,0.07)}
.s-avatar{
    width:34px;height:34px;border-radius:9px;
    background:linear-gradient(135deg,#FFCE00,#e6b800);
    display:flex;align-items:center;justify-content:center;
    font-size:14px;font-weight:800;color:#1A1A1A;flex-shrink:0;
}
.s-name{font-size:13px;font-weight:600;color:#fff}
.s-role{font-size:10px;color:rgba(255,206,0,0.5);text-transform:capitalize;margin-top:1px}

/* KPI grid */
.kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;padding:12px 14px}
.kpi-c{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.09);border-radius:10px;padding:10px 11px}
.kpi-l{font-size:9px;text-transform:uppercase;letter-spacing:0.08em;color:rgba(255,206,0,0.5);margin-bottom:2px}
.kpi-v{font-size:18px;font-weight:800;color:#fff;line-height:1}
.kpi-s{font-size:9px;color:rgba(255,255,255,0.35);margin-top:2px}

/* Main header */
.main-header{
    background:linear-gradient(135deg,#1A1A1A 0%,#2C2C2C 50%,#1A1A1A 100%);
    border-radius:16px;padding:22px 30px 20px;margin-bottom:16px;
    box-shadow:0 8px 32px rgba(0,0,0,0.25);position:relative;overflow:hidden;
    border:1px solid rgba(255,206,0,0.15);
}
.main-header::before{
    content:'';position:absolute;top:-60px;right:-60px;
    width:240px;height:240px;border-radius:50%;
    background:rgba(255,206,0,0.04);
}
.hdr-logo-row{display:flex;align-items:center;gap:14px;margin-bottom:10px}
.hdr-divider{height:30px;width:1px;background:rgba(255,255,255,0.18)}
.hdr-agent-label{font-size:13px;color:rgba(255,255,255,0.55);font-weight:500}
.hdr-title{font-size:22px;font-weight:800;color:#fff;letter-spacing:-0.3px}
.hdr-pills{display:flex;gap:8px;margin-top:16px;flex-wrap:wrap}
.hdr-pill{
    background:rgba(255,206,0,0.1);
    border:1px solid rgba(255,206,0,0.25);
    border-radius:9px;padding:7px 15px;text-align:center;
}
.hdr-pill-v{font-size:15px;font-weight:800;color:#FFCE00}
.hdr-pill-l{font-size:8.5px;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:0.06em;margin-top:1px}

/* Divider label */
.divider-label{
    display:flex;align-items:center;gap:8px;
    font-size:9.5px;font-weight:700;text-transform:uppercase;
    letter-spacing:0.1em;color:rgba(255,206,0,0.7);margin-bottom:6px;
}
.divider-label::before,.divider-label::after{
    content:'';flex:1;height:1px;background:rgba(255,206,0,0.2);
}

/* Welcome card */
.welcome-card{
    background:linear-gradient(135deg,#fffbeb,#fef9db);
    border:1px solid rgba(255,206,0,0.35);
    border-radius:14px;padding:18px 22px;margin-bottom:12px;
}
.welcome-title{font-size:14px;font-weight:700;color:#1A1A1A;margin-bottom:5px}
.welcome-sub{font-size:12.5px;color:#555;line-height:1.6}

/* Chat */
[data-testid="stChatMessage"]{background:transparent !important}
[data-testid="stChatInput"]>div{
    border:2px solid rgba(255,206,0,0.3) !important;
    border-radius:14px !important;background:#fff !important;
}
[data-testid="stChatInput"]>div:focus-within{
    border-color:#FFCE00 !important;
    box-shadow:0 0 0 4px rgba(255,206,0,0.12) !important;
}

/* Sidebar secondary buttons */
[data-testid="stSidebar"] [data-testid="baseButton-secondary"]{
    background:rgba(255,255,255,0.06) !important;
    border:1px solid rgba(255,255,255,0.1) !important;
    color:rgba(240,240,240,0.8) !important;
    border-radius:8px !important;font-size:11px !important;
}
[data-testid="stSidebar"] [data-testid="baseButton-secondary"]:hover{
    background:rgba(255,206,0,0.15) !important;color:#fff !important;
}
[data-testid="stSidebar"] details{
    background:rgba(255,255,255,0.04) !important;
    border:1px solid rgba(255,255,255,0.07) !important;
    border-radius:8px;margin:0 12px 8px;
}
[data-testid="stSidebar"] details summary{
    color:rgba(255,206,0,0.55) !important;font-size:11px !important;padding:6px 10px;
}
[data-testid="stSidebar"] details p,[data-testid="stSidebar"] details div{
    font-size:11px !important;color:rgba(255,255,255,0.45) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("messages", []), ("agent_history", []), ("pending_prompt", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── KPI helpers ───────────────────────────────────────────────────────────────
def _oos_n(df):
    return int((df["stock_available"] == 0).sum()) if "stock_available" in df.columns else 0

def _risk_n(df, d=7):
    if "days_of_supply" not in df.columns: return 0
    return int(((df["days_of_supply"] > 0) & (df["days_of_supply"] <= d)).sum())

def _gmv_loss(df):
    if "gmv_daily" not in df.columns or "stock_available" not in df.columns: return 0.0
    return round(float(df.loc[df["stock_available"] == 0, "gmv_daily"].sum()), 0)

def _avg_lt(df):
    if "supplier_lead_time" not in df.columns or "stock_available" not in df.columns: return "—"
    oos = df[df["stock_available"] == 0]
    if oos.empty: return "—"
    v = oos["supplier_lead_time"].mean()
    return f"{v:.0f}d" if pd.notna(v) else "—"

oos_n   = _oos_n(INVENTORY_DF)
risk_n  = _risk_n(INVENTORY_DF)
loss    = _gmv_loss(INVENTORY_DF)
lt      = _avg_lt(INVENTORY_DF)
total   = len(INVENTORY_DF)
oos_pct = round(oos_n / total * 100, 1) if total else 0

# noon logo SVG (inline — yellow wordmark on transparent)
NOON_LOGO_SVG = """
<svg width="68" height="26" viewBox="0 0 68 26" xmlns="http://www.w3.org/2000/svg">
  <text x="1" y="22" font-family="'Arial Black',Arial,sans-serif"
        font-weight="900" font-size="24" fill="#FFCE00" letter-spacing="-0.5">noon</text>
</svg>"""

# ── Sidebar questions — dataset specific ──────────────────────────────────────
SUGGESTIONS = {
    "📊  GMV & stock": [
        "What is the total GMV loss from OOS today?",
        "Which category — Electronics, Fashion, Home or Beauty — has the highest GMV loss?",
        "Show top OOS SKUs ranked by daily revenue impact",
    ],
    "🔍  Root cause": [
        "Break down OOS root causes across all categories",
        "Which brands have supplier lead time above 14 days?",
        "How many SKUs have zero incoming stock?",
    ],
    "⚠️  At-risk SKUs": [
        "Which SKUs will go OOS within the next 7 days?",
        "Flag Electronics SKUs running out before supplier delivers",
        "Show Fashion & Home SKUs with days of supply under 5",
    ],
    "🏷️  Brand focus": [
        "Compare OOS rate: Apple vs Samsung vs Sony",
        "Which of Nike, Puma, IKEA or Loreal has the most OOS SKUs?",
        "Top 3 brands to prioritise for restocking today",
    ],
}

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # noon logo
    st.markdown(f"""
    <div class="noon-logo-strip">
      {NOON_LOGO_SVG}
      <div>
        <div class="noon-logo-sub">OOS Intelligence</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # User card
    st.markdown(f"""
    <div class="s-user">
      <div class="s-avatar">{st.session_state.user_name[0].upper()}</div>
      <div>
        <div class="s-name">{st.session_state.user_name}</div>
        <div class="s-role">{st.session_state.user_role}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # KPI cards
    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-c">
        <div class="kpi-l">OOS SKUs</div>
        <div class="kpi-v">{oos_n}</div>
        <div class="kpi-s">{oos_pct}% of catalogue</div>
      </div>
      <div class="kpi-c" style="border-color:rgba(239,68,68,0.3)">
        <div class="kpi-l">At Risk 7d</div>
        <div class="kpi-v" style="color:#fca5a5">{risk_n}</div>
        <div class="kpi-s">going OOS soon</div>
      </div>
      <div class="kpi-c" style="border-color:rgba(255,206,0,0.25)">
        <div class="kpi-l">Daily GMV Loss</div>
        <div class="kpi-v" style="color:#FFCE00;font-size:13px">AED {loss:,.0f}</div>
        <div class="kpi-s">from OOS events</div>
      </div>
      <div class="kpi-c" style="border-color:rgba(255,206,0,0.2)">
        <div class="kpi-l">Avg Lead Time</div>
        <div class="kpi-v" style="color:#FFE566">{lt}</div>
        <div class="kpi-s">OOS suppliers</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # GMV sparkline
    if not HISTORY_DF.empty and {"date","lost_gmv_aed"}.issubset(HISTORY_DF.columns):
        spark = HISTORY_DF.tail(14).copy()
        if not spark.empty:
            fig_s = go.Figure(go.Scatter(
                x=spark["date"], y=spark["lost_gmv_aed"],
                fill="tozeroy", line=dict(color="#FFCE00", width=1.5),
                fillcolor="rgba(255,206,0,0.10)", mode="lines",
            ))
            fig_s.update_layout(
                height=64, margin=dict(l=0,r=0,t=0,b=0),
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(visible=False), yaxis=dict(visible=False),
            )
            st.markdown("<div style='padding:2px 14px 0'><div style='font-size:9px;color:rgba(255,206,0,0.4);letter-spacing:0.06em;text-transform:uppercase'>GMV Loss — 14d trend</div></div>", unsafe_allow_html=True)
            st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar": False})

    # Suggested questions
    for section, items in SUGGESTIONS.items():
        st.markdown(f'<p class="sbar-section">{section}</p>', unsafe_allow_html=True)
        for item in items:
            if st.button(item, key=f"q_{item}", use_container_width=True):
                st.session_state.pending_prompt = item

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("🗑 Clear", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent_history = []
        st.rerun()
    if c2.button("🚪 Sign out", use_container_width=True):
        logout()
        st.rerun()

    with st.expander("📄 Data info", expanded=False):
        st.caption(f"Source: oos_data.csv")
        st.caption(f"Date range: {CSV_INFO['date_range']}")
        st.caption(f"Total rows: {CSV_INFO['total_rows']:,}")
        st.caption(f"Latest snapshot: {CSV_INFO['latest_date']}")
        st.caption(f"Categories: {', '.join(CSV_INFO['categories'])}")
        st.caption(f"Brands: {', '.join(CSV_INFO['brands'])}")

# ── MAIN HEADER ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
  <div class="hdr-logo-row">
    {NOON_LOGO_SVG}
    <div class="hdr-divider"></div>
    <div class="hdr-agent-label">OOS Analytics Agent</div>
  </div>
  <div class="hdr-title">Out-of-Stock Intelligence</div>
  <div class="hdr-pills">
    <div class="hdr-pill"><div class="hdr-pill-v">{oos_n}</div><div class="hdr-pill-l">OOS SKUs</div></div>
    <div class="hdr-pill"><div class="hdr-pill-v">AED {loss:,.0f}</div><div class="hdr-pill-l">Daily Loss</div></div>
    <div class="hdr-pill"><div class="hdr-pill-v">{risk_n}</div><div class="hdr-pill-l">At Risk 7d</div></div>
    <div class="hdr-pill"><div class="hdr-pill-v">{oos_pct}%</div><div class="hdr-pill-l">OOS Rate</div></div>
    <div class="hdr-pill"><div class="hdr-pill-v">{lt}</div><div class="hdr-pill-l">Avg Lead Time</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

# Quick chips
QUICK = [
    "Total GMV loss today?",
    "SKUs going OOS before restock?",
    "Worst category for OOS?",
    "Root cause breakdown",
    "14-day trend",
]
st.markdown('<div class="divider-label">Quick ask</div>', unsafe_allow_html=True)
chip_cols = st.columns(len(QUICK))
for i, q in enumerate(QUICK):
    if chip_cols[i].button(q, key=f"chip_{i}"):
        st.session_state.pending_prompt = q

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown(f"""
    <div class="welcome-card">
      <div class="welcome-title">👋 Hi, I'm your noon OOS Intelligence Agent</div>
      <div class="welcome-sub">
        I have <strong>{CSV_INFO['total_rows']:,}</strong> inventory records across
        <strong>{len(CSV_INFO['categories'])}</strong> categories
        (Electronics, Fashion, Home, Beauty) and
        <strong>{len(CSV_INFO['brands'])}</strong> brands including Apple, Samsung, Nike, IKEA and more.
        Ask me about GMV loss, root causes, at-risk SKUs, supplier delays, or OOS trends — in plain English.
      </div>
    </div>
    """, unsafe_allow_html=True)

# Chat history
for msg in st.session_state.messages:
    avatar = "🤖" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── Input ─────────────────────────────────────────────────────────────────────
prompt = None
if st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

typed = st.chat_input("Ask about OOS, GMV loss, root causes, at-risk SKUs…")
if typed:
    prompt = typed

if prompt:
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Analysing inventory data…"):
            try:
                response_text, updated_history, tool_calls = run_agent(
                    prompt, st.session_state.agent_history
                )
                for tc in tool_calls:
                    render_charts_for_tool(tc["name"], tc["result"])
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                st.session_state.agent_history = updated_history
            except Exception as e:
                err = str(e)
                if "529" in err or "overloaded" in err.lower():
                    msg = "⚠️ Claude API is temporarily overloaded. Please wait 30 seconds and try again."
                elif "rate_limit" in err.lower():
                    msg = "⚠️ Rate limit reached. Please wait a moment and try again."
                elif "401" in err or "authentication" in err.lower():
                    msg = "⚠️ Invalid API key. Check your ANTHROPIC_API_KEY in settings."
                else:
                    msg = f"⚠️ Error: {err}"
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})

    st.rerun()
