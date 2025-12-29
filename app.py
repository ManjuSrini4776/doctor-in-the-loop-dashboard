import json
import streamlit as st

st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide"
)

st.title("🩺 Doctor-in-the-Loop Clinical Dashboard")
st.caption("Evidence-based AI report validation with doctor oversight")

JSON_PATH = "pregnancy_normal.json"

with open(JSON_PATH, "r") as f:
    data = json.load(f)

st.subheader("DEBUG: JSON content")
st.write(data)

st.subheader("DEBUG: JSON keys")
st.write(list(data.keys()))

