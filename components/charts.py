import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Indigo/violet palette
PRIMARY  = "#6366f1"
SECONDARY= "#8b5cf6"
ACCENT   = "#06b6d4"
DANGER   = "#ef4444"
WARNING  = "#f59e0b"
SUCCESS  = "#10b981"
COLORS   = [PRIMARY, SECONDARY, ACCENT, "#ec4899", DANGER, WARNING, SUCCESS, "#f97316"]

def _layout(h=300, title=""):
    return dict(
        height=h, title=dict(text=title, font=dict(size=14, color="#1e1b4b"), x=0, pad=dict(l=4)),
        margin=dict(l=8,r=8,t=44,b=8),
        plot_bgcolor="rgba(238,242,255,0.4)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12, color="#374151"),
        showlegend=True,
        legend=dict(font=dict(size=11)),
    )

def chart_gmv_by_category(data):
    d = data.get("loss_by_category",{})
    if not d: return None
    df = pd.DataFrame(list(d.items()),columns=["Category","GMV Loss (AED)"]).sort_values("GMV Loss (AED)")
    fig = px.bar(df,x="GMV Loss (AED)",y="Category",orientation="h",
                 color="GMV Loss (AED)",color_continuous_scale=[[0,"#c7d2fe"],[1,PRIMARY]],
                 title="GMV Loss by Category")
    fig.update_coloraxes(showscale=False)
    fig.update_traces(hovertemplate="<b>%{y}</b><br>AED %{x:,.0f}<extra></extra>")
    fig.update_layout(**_layout(max(240,len(df)*36),"📊 GMV Loss by Category"))
    return fig

def chart_gmv_by_brand(data):
    d = data.get("loss_by_brand",{})
    if not d: return None
    df = pd.DataFrame(list(d.items()),columns=["Brand","GMV Loss (AED)"]).sort_values("GMV Loss (AED)").tail(8)
    fig = px.bar(df,x="GMV Loss (AED)",y="Brand",orientation="h",
                 color="GMV Loss (AED)",color_continuous_scale=[[0,"#ddd6fe"],[1,SECONDARY]],
                 title="Top Brands by GMV Loss")
    fig.update_coloraxes(showscale=False)
    fig.update_traces(hovertemplate="<b>%{y}</b><br>AED %{x:,.0f}<extra></extra>")
    fig.update_layout(**_layout(max(240,len(df)*36),"🏷️ Top Brands by GMV Loss"))
    return fig

def chart_root_cause(data):
    bd = data.get("breakdown",[])
    if not bd: return None
    df = pd.DataFrame(bd)
    df = df[df["sku_count"]>0]
    if df.empty: return None
    fig = px.pie(df,names="root_cause",values="gmv_impact_aed",
                 color_discrete_sequence=COLORS,hole=0.5)
    fig.update_traces(textposition="outside",
                      hovertemplate="<b>%{label}</b><br>AED %{value:,.0f}<br>%{percent}<extra></extra>")
    fig.update_layout(**_layout(320,"🔍 Root Cause Breakdown"))
    return fig

def chart_oos_trend(data):
    rows = data.get("daily_data",[])
    if not rows: return None
    df = pd.DataFrame(rows).sort_values("date")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"],y=df["lost_gmv_aed"],name="GMV Loss (AED)",
        fill="tozeroy",line=dict(color=PRIMARY,width=2.5),
        fillcolor="rgba(99,102,241,0.08)",
        hovertemplate="<b>%{x}</b><br>AED %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["date"],y=(df["oos_rate"]*100).round(1),name="OOS Rate (%)",yaxis="y2",
        line=dict(color=ACCENT,width=2,dash="dot"),
        hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        yaxis=dict(title="GMV Loss (AED)",tickformat=",.0f",gridcolor="rgba(99,102,241,0.1)"),
        yaxis2=dict(title="OOS Rate (%)",overlaying="y",side="right",ticksuffix="%"),
        legend=dict(orientation="h",y=1.12,x=0),
        **_layout(320,"📈 OOS Trend Over Time"),
    )
    return fig

def chart_at_risk(data):
    skus = data.get("skus",[])
    if not skus: return None
    df = pd.DataFrame(skus).head(12)
    df["label"] = df["sku_id"]+" | "+df["category"]
    df = df.sort_values("days_of_supply")
    fig = px.bar(df,x="days_of_supply",y="label",orientation="h",
                 color="days_of_supply",
                 color_continuous_scale=[[0,DANGER],[0.4,WARNING],[1,SUCCESS]])
    fig.update_coloraxes(showscale=False)
    fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x:.1f} days left<extra></extra>")
    fig.update_layout(**_layout(max(260,len(df)*28),"⚠️ At-Risk SKUs — Days of Supply"))
    return fig

def chart_category_summary(data):
    cats = data.get("categories",[])
    if not cats: return None
    df = pd.DataFrame(cats).sort_values("gmv_loss_aed",ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(name="OOS Rate (%)",x=df["category"],y=df["oos_rate_pct"],
                         marker_color=PRIMARY,yaxis="y",
                         hovertemplate="<b>%{x}</b><br>OOS: %{y:.1f}%<extra></extra>"))
    fig.add_trace(go.Bar(name="GMV Loss",x=df["category"],y=df["gmv_loss_aed"],
                         marker_color=ACCENT,yaxis="y2",
                         hovertemplate="<b>%{x}</b><br>AED %{y:,.0f}<extra></extra>"))
    fig.update_layout(
        barmode="group",
        yaxis=dict(title="OOS Rate (%)"),
        yaxis2=dict(title="GMV Loss (AED)",overlaying="y",side="right"),
        legend=dict(orientation="h",y=1.1),
        **_layout(320,"📂 Category Summary"),
    )
    return fig

def chart_brand_analysis(data):
    brands = data.get("brands",[])
    if not brands: return None
    df = pd.DataFrame(brands).sort_values("gmv_loss_aed")
    fig = px.bar(df,x="gmv_loss_aed",y="brand",orientation="h",
                 color="gmv_loss_aed",color_continuous_scale=[[0,"#ede9fe"],[1,SECONDARY]],
                 text="oos_skus")
    fig.update_coloraxes(showscale=False)
    fig.update_traces(texttemplate="%{text} SKUs",
                      hovertemplate="<b>%{y}</b><br>AED %{x:,.0f}<extra></extra>")
    fig.update_layout(**_layout(max(260,len(df)*28),"🏷️ Brand OOS Analysis"))
    return fig

CHART_MAP = {
    "get_gmv_loss":            [chart_gmv_by_category,chart_gmv_by_brand],
    "get_root_cause_breakdown":[chart_root_cause],
    "get_oos_trend":           [chart_oos_trend],
    "get_at_risk_skus":        [chart_at_risk],
    "get_category_summary":    [chart_category_summary],
    "get_brand_analysis":      [chart_brand_analysis],
}

def render_charts_for_tool(tool_name,tool_result):
    for builder in CHART_MAP.get(tool_name,[]):
        try:
            fig = builder(tool_result)
            if fig:
                st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        except Exception:
            pass
