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

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
[data-testid="stAppViewContainer"]>.main{background:#f5f6ff;min-height:100vh}
#MainMenu,footer,header{visibility:hidden}

[data-testid="stSidebar"]>div:first-child{
    background:linear-gradient(180deg,#1e1b4b 0%,#312e81 45%,#1e1b4b 100%);
    border-right:none;
}
[data-testid="stSidebar"] .block-container{padding:0 !important}
[data-testid="stSidebar"] *{color:#e0e7ff}

.sbar-section{
    font-size:9.5px;font-weight:700;letter-spacing:0.12em;
    text-transform:uppercase;color:rgba(165,180,252,0.65);
    padding:14px 16px 5px;margin:0;
    border-top:1px solid rgba(255,255,255,0.06);
}

[data-testid="stSidebar"] .stButton>button{
    background:none;border:none;color:rgba(199,210,254,0.82);
    font-size:12px;font-weight:400;text-align:left;
    padding:7px 16px 7px 32px;width:100%;border-radius:0;
    position:relative;line-height:1.5;height:auto;
    white-space:normal;transition:all .15s;
    border-left:2px solid transparent;
}
[data-testid="stSidebar"] .stButton>button::before{
    content:'›';position:absolute;left:13px;top:50%;
    transform:translateY(-50%);
    color:rgba(99,102,241,0.55);font-size:16px;font-weight:700;
    transition:all .18s;
}
[data-testid="stSidebar"] .stButton>button:hover{
    background:rgba(99,102,241,0.18);color:#fff;
    border-left-color:#818cf8;padding-left:36px;
}
[data-testid="stSidebar"] .stButton>button:hover::before{color:#a5b4fc}
[data-testid="stSidebar"] .stButton>button:focus{box-shadow:none;outline:none}

.s-user{display:flex;align-items:center;gap:10px;padding:16px;border-bottom:1px solid rgba(255,255,255,0.08)}
.s-avatar{width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:800;color:#fff;flex-shrink:0}
.s-name{font-size:13px;font-weight:600;color:#fff}
.s-role{font-size:10px;color:rgba(165,180,252,0.55);text-transform:capitalize;margin-top:1px}

.kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;padding:12px 14px}
.kpi-c{background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:10px 11px}
.kpi-l{font-size:9px;text-transform:uppercase;letter-spacing:0.08em;color:rgba(165,180,252,0.55);margin-bottom:2px}
.kpi-v{font-size:18px;font-weight:800;color:#fff;line-height:1}
.kpi-s{font-size:9px;color:rgba(165,180,252,0.4);margin-top:2px}

.main-header{
    background:linear-gradient(135deg,#4338ca 0%,#6366f1 45%,#7c3aed 100%);
    border-radius:16px;padding:26px 30px 20px;margin-bottom:16px;
    box-shadow:0 8px 32px rgba(99,102,241,0.25);position:relative;overflow:hidden;
}
.main-header::before{content:'';position:absolute;top:-50px;right:-50px;width:220px;height:220px;border-radius:50%;background:rgba(255,255,255,0.05)}
.hdr-badge{display:inline-flex;align-items:center;gap:5px;background:rgba(255,255,255,0.14);border-radius:20px;padding:3px 11px;font-size:10px;color:rgba(255,255,255,0.85);margin-bottom:8px}
.hdr-title{font-size:24px;font-weight:800;color:#fff;letter-spacing:-0.4px}
.hdr-sub{font-size:11.5px;color:rgba(255,255,255,0.6);margin-top:4px}
.hdr-pills{display:flex;gap:8px;margin-top:14px;flex-wrap:wrap}
.hdr-pill{background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);border-radius:9px;padding:7px 15px;text-align:center}
.hdr-pill-v{font-size:15px;font-weight:800;color:#fff}
.hdr-pill-l{font-size:8.5px;color:rgba(255,255,255,0.6);text-transform:uppercase;letter-spacing:0.06em;margin-top:1px}

.divider-label{display:flex;align-items:center;gap:8px;font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#a5b4fc;margin-bottom:6px}
.divider-label::before,.divider-label::after{content:'';flex:1;height:1px;background:#e0e7ff}

.welcome-card{background:linear-gradient(135deg,#eef2ff,#f5f3ff);border:1px solid #c7d2fe;border-radius:14px;padding:18px 22px;margin-bottom:12px}
.welcome-title{font-size:14px;font-weight:700;color:#3730a3;margin-bottom:5px}
.welcome-sub{font-size:12.5px;color:#4338ca;line-height:1.6}

[data-testid="stChatMessage"]{background:transparent !important}
[data-testid="stChatInput"]>div{border:2px solid #e0e7ff !important;border-radius:14px !important;background:#fff !important}
[data-testid="stChatInput"]>div:focus-within{border-color:#6366f1 !important;box-shadow:0 0 0 4px rgba(99,102,241,0.1) !important}

[data-testid="stSidebar"] [data-testid="baseButton-secondary"]{
    background:rgba(255,255,255,0.07) !important;
    border:1px solid rgba(255,255,255,0.12) !important;
    color:rgba(199,210,254,0.8) !important;
    border-radius:8px !important;font-size:11px !important;
}
[data-testid="stSidebar"] [data-testid="baseButton-secondary"]:hover{
    background:rgba(255,255,255,0.14) !important;color:#fff !important;
}
[data-testid="stSidebar"] details{
    background:rgba(255,255,255,0.04) !important;
    border:1px solid rgba(255,255,255,0.08) !important;
    border-radius:8px;margin:0 12px 8px;
}
[data-testid="stSidebar"] details summary{color:rgba(165,180,252,0.65) !important;font-size:11px !important;padding:6px 10px}
[data-testid="stSidebar"] details p,[data-testid="stSidebar"] details div{font-size:11px !important;color:rgba(165,180,252,0.55) !important}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("messages", []), ("agent_history", []), ("pending_prompt", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Safe KPI helpers ──────────────────────────────────────────────────────────
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

# ── Suggestions ───────────────────────────────────────────────────────────────
SUGGESTIONS = {
    "📊  GMV & stock overview": [
        "What's the total GMV loss from OOS today?",
        "Which category is losing the most GMV?",
        "Show me top OOS SKUs by revenue impact",
        "Which brands have the highest OOS GMV loss?",
    ],
    "🔍  Root cause analysis": [
        "What's causing OOS across the catalogue?",
        "Which SKUs have supplier lead time > 14 days?",
        "How many OOS SKUs have no incoming stock?",
        "Break down root causes by category",
    ],
    "⚠️  Risk & urgency": [
        "Which SKUs will go OOS in the next 7 days?",
        "Flag SKUs where stock runs out before supplier delivers",
        "Which categories are most at risk this week?",
        "Show me SKUs with zero incoming stock",
    ],
    "📈  Trends & comparison": [
        "Is OOS getting better or worse this week?",
        "Compare OOS rate across all categories",
        "Show GMV loss trend over last 14 days",
        "Which category improved the most recently?",
    ],
    "🏷️  Brand deep-dive": [
        "Which brand has the most OOS SKUs?",
        "Show brand-level GMV loss breakdown",
        "Which brands have incoming stock ready?",
        "Top brands to prioritise for restock",
    ],
}

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div class="s-user">
      <div class="s-avatar">{st.session_state.user_name[0].upper()}</div>
      <div>
        <div class="s-name">{st.session_state.user_name}</div>
        <div class="s-role">{st.session_state.user_role}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

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
      <div class="kpi-c" style="border-color:rgba(99,102,241,0.35)">
        <div class="kpi-l">Daily GMV Loss</div>
        <div class="kpi-v" style="color:#a5b4fc;font-size:13px">AED {loss:,.0f}</div>
        <div class="kpi-s">from OOS events</div>
      </div>
      <div class="kpi-c" style="border-color:rgba(139,92,246,0.35)">
        <div class="kpi-l">Avg Lead Time</div>
        <div class="kpi-v" style="color:#c4b5fd">{lt}</div>
        <div class="kpi-s">OOS suppliers</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Sparkline
    if not HISTORY_DF.empty and {"date","lost_gmv_aed"}.issubset(HISTORY_DF.columns):
        spark = HISTORY_DF.tail(14).copy()
        if not spark.empty:
            fig_s = go.Figure(go.Scatter(
                x=spark["date"], y=spark["lost_gmv_aed"],
                fill="tozeroy", line=dict(color="#818cf8", width=1.5),
                fillcolor="rgba(129,140,248,0.15)", mode="lines",
            ))
            fig_s.update_layout(height=64, margin=dict(l=0,r=0,t=0,b=0),
                showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(visible=False), yaxis=dict(visible=False))
            st.markdown("<div style='padding:2px 14px 0'><div style='font-size:9px;color:rgba(165,180,252,0.45);letter-spacing:0.06em;text-transform:uppercase'>GMV Loss — 14d trend</div></div>", unsafe_allow_html=True)
            st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar": False})

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
        st.caption(f"SKUs: {', '.join(CSV_INFO['skus'])}")
        st.caption(f"Categories: {', '.join(CSV_INFO['categories'])}")
        st.caption(f"Brands: {', '.join(CSV_INFO['brands'])}")

# ── MAIN ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
  <div class="hdr-badge">📦 &nbsp;AI-Powered · Data from oos_data.csv</div>
  <div class="hdr-title">noon OOS Analytics Agent</div>
  <div class="hdr-sub">
    Ask anything in plain English · Powered by Claude AI ·
    <code style="background:rgba(0,0,0,0.2);padding:1px 8px;border-radius:5px;font-size:10.5px">
      {CSV_INFO['date_range']} · {CSV_INFO['total_rows']:,} rows
    </code>
  </div>
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
    "7-day trend",
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
      <div class="welcome-title">👋 Hi, I'm your OOS Intelligence Agent</div>
      <div class="welcome-sub">
        I'm loaded with your inventory data ({CSV_INFO['total_rows']:,} records,
        {len(CSV_INFO['skus'])} SKUs across {len(CSV_INFO['categories'])} categories).
        Ask me about GMV loss, root causes, at-risk SKUs, supplier delays,
        brand performance, or OOS trends — in plain English.
      </div>
    </div>
    """, unsafe_allow_html=True)

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
                    msg = "⚠️ Invalid API key. Check your ANTHROPIC_API_KEY in .env"
                else:
                    msg = f"⚠️ Error: {err}"
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})

    st.rerun()
