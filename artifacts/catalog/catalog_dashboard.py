#!/usr/bin/env python3
"""
Local Catalog Dashboard v1.0 — Director
Simple Streamlit web UI for the visual_assets.db
"""

import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Visual Asset Catalog", layout="wide")
st.title("Visual Asset Catalog — Magazine + Video")

db_path = Path(__file__).resolve().parent / "../Studio/Magazine_Assets/visual_assets.db"
conn = sqlite3.connect(str(db_path.resolve()))
df = pd.read_sql_query("SELECT * FROM assets", conn)
conn.close()

st.dataframe(df, use_container_width=True)

model_names = df["model_name"].dropna().unique().tolist() if not df.empty else []
model_filter = st.selectbox("Filter by Model", ["All"] + sorted(model_names))
if model_filter != "All":
    st.dataframe(df[df["model_name"] == model_filter], use_container_width=True)

if st.button("Export Current View as JSON"):
    export_path = Path(__file__).resolve().parent / "exported_assets.json"
    view = df if model_filter == "All" else df[df["model_name"] == model_filter]
    view.to_json(export_path, orient="records", indent=2)
    st.success(f"Exported to {export_path}")