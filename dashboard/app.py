
import streamlit as st
import pandas as pd
from pathlib import Path
import time

st.set_page_config(
    page_title="Wind Turbine Predictive Maintenance",
    page_icon="🌬️",
    layout="wide"
)

st.title("🌬️ Wind Turbine Predictive Maintenance")
st.caption("Real-Time Predictive Maintenance Using Big Data Streaming Architecture")

DATA_FILE = Path(__file__).resolve().parent / "predictions.csv"

st.sidebar.header("Dashboard Settings")
refresh = st.sidebar.checkbox("Auto refresh every 5 seconds", value=True)

if DATA_FILE.exists():
    df = pd.read_csv(DATA_FILE)

    if not df.empty:
        total = len(df)
        anomalies = int((df["prediction"] == "anomaly").sum())
        normal = total - anomalies
        alarms = int(df["alarm"].astype(str).str.lower().isin(["true", "1"]).sum())

        st.subheader("System Overview")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Records", total)
        col2.metric("Normal Predictions", normal)
        col3.metric("Anomalies", anomalies)
        col4.metric("Active Alarms", alarms)

        st.divider()

        left, right = st.columns(2)

        with left:
            st.subheader("Prediction Distribution")
            distribution = pd.DataFrame({
                "Status": ["Normal", "Anomaly"],
                "Count": [normal, anomalies]
            })
            st.bar_chart(distribution.set_index("Status"))

        with right:
            st.subheader("Anomaly Probability")
            if "anomaly_probability" in df.columns:
                chart_data = df[["anomaly_probability"]].copy()
                chart_data.index = range(1, len(chart_data) + 1)
                st.line_chart(chart_data)

        st.divider()
        st.subheader("Recent Turbine Predictions")

        display_columns = [
            column for column in [
                "asset_id",
                "time_stamp",
                "prediction",
                "anomaly_probability",
                "alarm",
                "consecutive_anomalies"
            ]
            if column in df.columns
        ]

        st.dataframe(
            df[display_columns].tail(100).iloc[::-1],
            use_container_width=True
        )

        st.caption("Dashboard data refreshes automatically when new predictions are saved.")
    else:
        st.info("No prediction records available yet.")
else:
    st.info("Waiting for prediction data from the Spark streaming application.")
    st.write("Start the Spark Kafka consumer to populate the dashboard.")

if refresh:
    time.sleep(5)
    st.rerun()
