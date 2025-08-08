
import streamlit as st
import pandas as pd
import zipfile
import io
import glob
import os

st.set_page_config(page_title="Top Companies Hiring Supervisors - LA County", layout="wide")
st.title("📊 Top Companies Hiring First-Line Supervisors in Los Angeles County")
st.markdown("""
This dashboard shows job postings from **August 2024 to July 2025** for top companies hiring across different supervisor occupations in Los Angeles County.
""")

# --- Load the zip archive ---
uploaded_file = st.file_uploader("Upload the tar.gz file from Lightcast:", type=["tar.gz"])

if uploaded_file is not None:
    import tarfile
    with tarfile.open(fileobj=uploaded_file, mode="r:gz") as tar:
        members = [m for m in tar.getmembers() if m.isfile() and m.name.endswith(".csv")]
        all_data = []
        for member in members:
            f = tar.extractfile(member)
            if f:
                df = pd.read_csv(f)
                df['Occupation'] = os.path.splitext(os.path.basename(member.name))[0]
                df['Occupation'] = df['Occupation'].str.replace('Job_Postings_Table_', '').str.replace('_in_Los_Angeles_County_CA.*', '', regex=True).str.replace('_', ' ')
                all_data.append(df)

        if not all_data:
            st.warning("No CSVs found in the archive.")
        else:
            data = pd.concat(all_data, ignore_index=True)

            # --- UI Controls ---
            occs = sorted(data['Occupation'].unique())
            selected_occ = st.selectbox("Choose an Occupation:", occs)

            filtered = data[data['Occupation'] == selected_occ].copy()
            filtered = filtered.sort_values("Unique Postings", ascending=False)

            st.markdown(f"### 📌 {selected_occ}")
            st.dataframe(filtered[['Company', 'Unique Postings']], use_container_width=True)

            st.bar_chart(filtered.set_index("Company")["Unique Postings"].head(20))

else:
    st.info("Please upload the `job_postings_top_companies_los_angeles.csvs.tar.gz` file to begin.")
