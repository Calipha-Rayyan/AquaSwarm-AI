import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="AquaSwarm AI",
    page_icon="💧",
    layout="wide"
)

st.title("💧 AquaSwarm AI")
st.subheader("Autonomous Water Supply & Shortage Coordination")

st.write(
    "AquaSwarm AI monitors water levels, consumption, alerts, "
    "suppliers, deliveries, and verification."
)

st.divider()

# Load demo data
tanks = pd.read_csv("data/tanks.csv")
suppliers = pd.read_csv("data/suppliers.csv")
consumption = pd.read_csv("data/consumption.csv")

# Dashboard metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Water Sites", len(tanks))

with col2:
    st.metric("Suppliers", len(suppliers))

with col3:
    st.metric("Available Suppliers", suppliers["available"].sum())

with col4:
    st.metric("Total Consumption", f"{consumption['amount'].sum():,.0f}")

st.divider()

st.subheader("🚰 Tank Status")
st.dataframe(tanks, use_container_width=True)

st.subheader("🚚 Suppliers")
st.dataframe(suppliers, use_container_width=True)

st.subheader("📊 Consumption")
st.dataframe(consumption, use_container_width=True)