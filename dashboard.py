import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="HappyRobot Dashboard", layout="wide")

st.title("Inbound Carrier Sales Dashboard")

file_path = "data/call_logs.csv"

if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
    st.warning("No call logs found yet.")
    st.stop()

df = pd.read_csv(file_path)

if df.empty:
    st.warning("Call log file is empty.")
    st.stop()

# Normalizar columnas booleanas por si vienen como texto
for col in ["eligible", "transferred_to_rep"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.lower().map({
            "true": True,
            "false": False
        }).fillna(df[col])

st.subheader("Overview")

total_calls = len(df)
eligible_carriers = int((df["eligible"] == True).sum()) if "eligible" in df.columns else 0
agreed_deals = int((df["outcome"] == "agreed_and_transferred").sum()) if "outcome" in df.columns else 0
transferred_calls = int((df["transferred_to_rep"] == True).sum()) if "transferred_to_rep" in df.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Calls", total_calls)
col2.metric("Eligible Carriers", eligible_carriers)
col3.metric("Agreed Deals", agreed_deals)
col4.metric("Transferred Calls", transferred_calls)

st.subheader("Outcomes")
if "outcome" in df.columns and not df["outcome"].dropna().empty:
    st.bar_chart(df["outcome"].value_counts())
else:
    st.info("No outcome data available.")

st.subheader("Sentiment")
if "sentiment" in df.columns and not df["sentiment"].dropna().empty:
    st.bar_chart(df["sentiment"].value_counts())
else:
    st.info("No sentiment data available.")

st.subheader("Negotiation Metrics")

col5, col6, col7 = st.columns(3)

avg_initial_rate = df["initial_rate"].dropna().mean() if "initial_rate" in df.columns else None
avg_final_rate = df["final_rate"].dropna().mean() if "final_rate" in df.columns else None
avg_rounds = df["negotiation_rounds"].dropna().mean() if "negotiation_rounds" in df.columns else None

col5.metric("Avg Initial Rate", f"{avg_initial_rate:.2f}" if pd.notna(avg_initial_rate) else "N/A")
col6.metric("Avg Final Rate", f"{avg_final_rate:.2f}" if pd.notna(avg_final_rate) else "N/A")
col7.metric("Avg Negotiation Rounds", f"{avg_rounds:.2f}" if pd.notna(avg_rounds) else "N/A")

st.subheader("Call Logs")
st.dataframe(df, use_container_width=True)