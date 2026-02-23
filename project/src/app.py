import streamlit as st
import pandas as pd
from pathlib import Path
import os

# Set page config
st.set_page_config(page_title="Engagement Index", layout="wide")

# Paths
BASE_DIR = Path(__file__).resolve().parents[1]
OUTDIR = BASE_DIR / "outputs"

st.title("Engagement Index Results")

st.markdown("""
This application displays the results of the Engagement Index pipeline.
The data is processed on startup and the resulting CSV files are available below.
""")

if not OUTDIR.exists():
    st.error(f"Output directory not found: {OUTDIR}")
else:
    # List CSV files
    csv_files = sorted(list(OUTDIR.glob("*.csv")))
    
    if not csv_files:
        st.warning("No CSV files found in output directory.")
    else:
        st.write(f"Found {len(csv_files)} CSV files.")
        
        for csv_file in csv_files:
            with st.expander(csv_file.name, expanded=False):
                try:
                    df = pd.read_csv(csv_file)
                    st.dataframe(df)
                    
                    # Download button
                    with open(csv_file, "rb") as f:
                        st.download_button(
                            label=f"Download {csv_file.name}",
                            data=f,
                            file_name=csv_file.name,
                            mime="text/csv"
                        )
                except Exception as e:
                    st.error(f"Error reading {csv_file.name}: {e}")
