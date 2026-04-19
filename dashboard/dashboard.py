import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Acme Logistics — Carrier Sales Dashboard", layout="wide", page_icon="🚚")

st.title("🚚 Inbound Carrier Sales Dashboard")

file_path = "data/call_logs.csv"

if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
    st.warning("No call logs found yet. Calls will appear here once the agent starts receiving them.")
    st.stop()

df = pd.read_csv(file_path)

if df.empty:
    st.warning("Call log file is empty.")
    st.stop()

# Normalizar booleanos
if "eligible" in df.columns:
    df["eligible"] = df["eligible"].astype(str).str.lower().map({"true": True, "false": False}).fillna(False)

# Normalizar timestamp
if "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

# ── KPIs ─────────────────────────────────────────────────────────────────────
st.subheader("Overview")

total_calls = len(df)
eligible = int(df["eligible"].sum()) if "eligible" in df.columns else 0
ineligible = total_calls - eligible
agreed = int((df["outcome"] == "agreed_and_transferred").sum()) if "outcome" in df.columns else 0
conversion_rate = f"{(agreed / eligible * 100):.1f}%" if eligible > 0 else "N/A"
avg_rounds = df["negotiation_rounds"].dropna().mean() if "negotiation_rounds" in df.columns else None

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Calls", total_calls)
c2.metric("Eligible Carriers", eligible)
c3.metric("Ineligible / Blocked", ineligible)
c4.metric("Deals Agreed", agreed)
c5.metric("Conversion Rate", conversion_rate)

st.divider()

# ── Outcomes & Sentiment ──────────────────────────────────────────────────────
st.subheader("Call Results")
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("**Call Outcomes**")
    if "outcome" in df.columns and not df["outcome"].dropna().empty:
        outcome_counts = df["outcome"].value_counts().reset_index()
        outcome_counts.columns = ["outcome", "count"]
        color_map = {
            "agreed_and_transferred": "#639922",
            "rejected": "#E24B4A",
            "not_interested": "#BA7517",
            "no_loads_found": "#378ADD",
            "ineligible": "#888780"
        }
        fig = px.bar(
            outcome_counts, x="outcome", y="count",
            color="outcome",
            color_discrete_map=color_map,
            labels={"outcome": "", "count": "Calls"},
        )
        fig.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No outcome data available.")

with col_right:
    st.markdown("**Carrier Sentiment**")
    if "sentiment" in df.columns and not df["sentiment"].dropna().empty:
        sentiment_counts = df["sentiment"].value_counts().reset_index()
        sentiment_counts.columns = ["sentiment", "count"]
        colors = {"positive": "#639922", "neutral": "#888780", "negative": "#E24B4A"}
        fig2 = px.pie(
            sentiment_counts, names="sentiment", values="count",
            color="sentiment",
            color_discrete_map=colors,
            hole=0.4,
        )
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No sentiment data available.")

st.divider()

# ── Negotiation Metrics ───────────────────────────────────────────────────────
st.subheader("Negotiation Metrics")

avg_initial = df["initial_rate"].dropna().mean() if "initial_rate" in df.columns else None
avg_final = df["final_rate"].dropna().mean() if "final_rate" in df.columns else None

n1, n2, n3 = st.columns(3)
n1.metric("Avg Initial Rate", f"${avg_initial:,.0f}" if pd.notna(avg_initial) else "N/A")
n2.metric("Avg Final Rate", f"${avg_final:,.0f}" if pd.notna(avg_final) else "N/A")
n3.metric("Avg Negotiation Rounds", f"{avg_rounds:.1f}" if pd.notna(avg_rounds) else "N/A")

# Rate comparison: initial vs final per call
rate_cols = ["initial_rate", "final_rate"]
if all(c in df.columns for c in rate_cols) and df[rate_cols].dropna().shape[0] > 0:
    rate_df = df[rate_cols].dropna().reset_index(drop=True)
    rate_df["call"] = rate_df.index + 1
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=rate_df["call"], y=rate_df["initial_rate"],
        mode="lines+markers", name="Initial Rate",
        line=dict(color="#378ADD")))
    fig3.add_trace(go.Scatter(
        x=rate_df["call"], y=rate_df["final_rate"],
        mode="lines+markers", name="Final Rate",
        line=dict(color="#639922", dash="dash")))
    fig3.update_layout(
        xaxis_title="Call #", yaxis_title="Rate ($)",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── Calls Over Time ───────────────────────────────────────────────────────────
if "timestamp" in df.columns and df["timestamp"].notna().sum() > 1:
    st.subheader("Calls Over Time")
    df["date"] = df["timestamp"].dt.date
    daily = df.groupby("date").size().reset_index(name="calls")
    fig4 = px.bar(daily, x="date", y="calls", labels={"date": "Date", "calls": "Calls"})
    fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig4, use_container_width=True)
    st.divider()

# ── Call Log Table ────────────────────────────────────────────────────────────
st.subheader("Call Logs")
cols_order = [c for c in [
    "timestamp", "mc_number", "eligible", "outcome", "sentiment",
    "initial_rate", "final_rate", "negotiation_rounds", "load_id", "summary"
] if c in df.columns]
st.dataframe(df[cols_order], use_container_width=True, height=400)