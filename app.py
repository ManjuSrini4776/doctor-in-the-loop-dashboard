import json
import streamlit as st
import pandas as pd

st.title("Doctor-in-the-Loop Clinical AI Dashboard")

# Load RAG output
with open("rag_output.json") as f:
    rag_data = json.load(f)

st.subheader("Clinical Query")
st.write(rag_data["query"])

st.subheader("Retrieved Guideline Evidence")
st.write(rag_data["retrieved_context"])

st.subheader("Clinical Explanation")
st.write(rag_data["generated_explanation"])

st.subheader("RAG Evaluation Metrics")

metrics = rag_data["metrics"]

metrics_df = pd.DataFrame({
    "Metric": list(metrics.keys()),
    "Score": list(metrics.values())
})

st.table(metrics_df)

st.bar_chart(metrics_df.set_index("Metric"))
