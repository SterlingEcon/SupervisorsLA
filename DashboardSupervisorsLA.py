import streamlit as st
import pandas as pd
import zipfile
import io
import glob
import os
import re

st.set_page_config(page_title="Top Companies Hiring Supervisors - LA County", layout="wide")
st.title("📊 Top Employers and Industries Hiring First-Line Supervisors in Los Angeles County")
st.markdown("""
This dashboard shows job postings from **August 2024 to July 2025** for top companies and industries hiring across different supervisor occupations in Los Angeles County.
""")

uploaded_file = st.file_uploader("Upload the tar.gz file from Lightcast:", type=["tar.gz"])

if uploaded_file is not None:
    import tarfile

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

            # Show employers
            matching_company_dfs = [df for df in company_data if df['Occupation'].iloc[0] == selected_occ]
            if matching_company_dfs:
                company_df = pd.concat(matching_company_dfs, ignore_index=True)
                company_col = next((c for c in company_df.columns if c.strip().lower() == "company"), None)
                if company_col and 'Unique Postings' in company_df.columns:
                    top_companies = company_df.groupby(company_col, as_index=False)['Unique Postings'].sum()
                    top_companies = top_companies.sort_values("Unique Postings", ascending=False)
                    st.subheader("🏢 Top Companies")
                    st.dataframe(top_companies, use_container_width=True)
                    st.bar_chart(top_companies.set_index(company_col)["Unique Postings"].head(20))

            # Show industries
            matching_industry_dfs = [df for df in industry_data if df['Occupation'].iloc[0] == selected_occ]
            if matching_industry_dfs:
                industry_df = pd.concat(matching_industry_dfs, ignore_index=True)
                industry_col = next((c for c in industry_df.columns if c.strip().lower() == "industry"), None)
                if industry_col:
                    st.subheader("🏭 Top Industries")
                    st.dataframe(industry_df[["NAICS", industry_col, "Occupation Jobs in Industry (2024)", "Occupation Jobs in Industry (2029)", "Change (2024 - 2029)", "% Change (2024 - 2029)", "% of Occupation in Industry (2024)", "% of Total Jobs in Industry (2024)"]], use_container_width=True)
else:
    st.info("Please upload the `.tar.gz` file containing both company and industry CSVs.")
