import streamlit as st
import pandas as pd
import zipfile
import io
import glob
import os
import re
import matplotlib.pyplot as plt
import tarfile

st.set_page_config(page_title="Top Companies Hiring Supervisors - LA County", layout="wide")
st.title("📊 Top Employers and Industries Hiring First-Line Supervisors in Los Angeles County")
st.markdown("""
This dashboard shows job postings from **August 2024 to July 2025** for top companies and industries hiring across different supervisor occupations in Los Angeles County.
""")

uploaded_file = st.file_uploader("Upload the tar.gz file from Lightcast:", type=["tar.gz"])

default_data_path = "data/"  # adjust if you use a different folder

if uploaded_file is None:
    local_csvs = glob.glob(os.path.join(default_data_path, "*.csv"))
    if local_csvs:
        st.info("No file uploaded — using default data from repository.")
        uploaded_file = io.BytesIO()
        with tarfile.open(fileobj=uploaded_file, mode="w:gz") as tar:
            for file_path in local_csvs:
                tar.add(file_path, arcname=os.path.basename(file_path))
        uploaded_file.seek(0)

if uploaded_file is not None:
    with tarfile.open(fileobj=uploaded_file, mode="r:gz") as tar:
        members = [m for m in tar.getmembers() if m.isfile() and m.name.endswith(".csv")]
        company_data = []
        industry_data = []

        for member in members:
            f = tar.extractfile(member)
            if f:
                content = f.read()
                if not content.strip():
                    continue
                f = io.StringIO(content.decode('utf-8'))
                df = pd.read_csv(f)
                base_name = os.path.splitext(os.path.basename(member.name))[0]

                # Normalize occupation name from filename
                occupation = base_name
                occupation = re.sub(r'(_)?in_Los_Angeles_County_CA', '', occupation)
                occupation = re.sub(r'(_)?(Company|Industry|company|industry|COMPANY|INDUSTRY)', '', occupation)
                occupation = re.sub(r'(_)?[a-f0-9]{16,}', '', occupation)  # remove hashes
                occupation = occupation.replace('_', ' ').strip()
                occupation = re.sub(r'\s+', ' ', occupation)
                occupation = re.sub(r'\bLA$', '', occupation).strip()
                df['Occupation'] = occupation

                # Normalize column names
                df.columns = [col.strip() for col in df.columns]
                for col in df.columns:
                    if col.lower().startswith("unique postings"):
                        df.rename(columns={col: "Unique Postings"}, inplace=True)

                has_company = any(col.strip().lower() == "company" for col in df.columns)
                has_industry = any(col.strip().lower() == "industry" or col.strip().lower() == "naics" for col in df.columns)

                if has_company:
                    company_data.append(df)
                elif has_industry:
                    industry_data.append(df)

        if not company_data and not industry_data:
            st.warning("No valid company or industry CSVs found in the archive.")
        else:
            occs = sorted(set([df['Occupation'].iloc[0] for df in company_data + industry_data]))
            selected_occ = st.selectbox("Choose an Occupation:", occs)

            st.markdown(f"### 📌 {selected_occ}")

            col1, col2 = st.columns([3, 2])

            # Show employers
            matching_company_dfs = [df for df in company_data if df['Occupation'].iloc[0] == selected_occ]
            if matching_company_dfs:
                company_df = pd.concat(matching_company_dfs, ignore_index=True)
                company_col = next((c for c in company_df.columns if c.strip().lower() == "company"), None)
                if company_col and 'Unique Postings' in company_df.columns:
                    top_companies = company_df.groupby(company_col, as_index=False)['Unique Postings'].sum()
                    top_companies = top_companies.sort_values("Unique Postings", ascending=False)

                    with col1:
                        st.subheader("📉 Unique Postings by Company")
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.barh(top_companies[company_col], top_companies['Unique Postings'])
                        ax.invert_yaxis()
                        ax.set_xlabel("Unique Postings")
                        st.pyplot(fig)

                    with col2:
                        st.subheader("🏢 Top Companies")
                        fmt_df = top_companies.copy()
                        fmt_df['Unique Postings'] = fmt_df['Unique Postings'].round(0).astype(int).map("{:,}".format)
                        st.dataframe(fmt_df, use_container_width=True)

            # Show industries
            matching_industry_dfs = [df for df in industry_data if df['Occupation'].iloc[0] == selected_occ]
            if matching_industry_dfs:
                industry_df = pd.concat(matching_industry_dfs, ignore_index=True)
                industry_col = next((c for c in industry_df.columns if c.strip().lower() == "industry"), None)
                if industry_col:
                    st.subheader("🏭 Top Industries")
                    st.dataframe(
                        industry_df[[
                            "NAICS",
                            industry_col,
                            "Occupation Jobs in Industry (2024)",
                            "Occupation Jobs in Industry (2029)",
                            "Change (2024 - 2029)",
                            "% Change (2024 - 2029)",
                            "% of Occupation in Industry (2024)",
                            "% of Total Jobs in Industry (2024)"
                        ]],
                        use_container_width=True
                    )
else:
    st.info("Please upload the `.tar.gz` file containing both company and industry CSVs.")

