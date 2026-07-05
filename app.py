import streamlit as st
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(page_title="Lab Operations Master Dashboard", layout="wide")
st.title("🔬 Laboratory Operations Master Performance Dashboard")

# File uploader widget
uploaded_file = st.file_uploader("📂 Upload your daily Lab Excel/CSV file (Accepts any filename format like 05/07/26)", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    # Explicit Mappings based on verified file schema
    folder_date_col = 'FOLDER_RECEIVE_DATE'
    ack_date_col = 'ACKNOWLEDGEMENT_DATE'
    commit_date_col = 'FOLDER_COMMITTED_DATE'
    buyer_col = 'BUYER'
    service_col = 'SERVICE_LEVEL'
    comm_by_col = 'COMMITTED_BY'
    reg_group_col = 'REG_GROUP'
    lab_type_col = 'LAB_TYPE'
    bill_client_col = 'BILL_TO_CLIENT'
    style_col = 'STYLE_NO'
    color_col = 'SAMPLE_COLOUR'
    folder_id_col = 'FOLDER#'
    sample_id_col = 'SAMPLE_NUMBER'
    charges_col = 'TOTAL_CHARGES'

    # Clean and convert Date columns safely to handle complex sub-second timestamps & "T" values
    for col in [folder_date_col, ack_date_col, commit_date_col]:
        if col in df.columns:
            # Step A: Convert to string and handle NaN values safely
            df[col] = df[col].fillna("").astype(str)
            # Step B: Replace the "T" separator with a space if it exists
            df[col] = df[col].str.replace('T', ' ', regex=False)
            # Step C: Strip trailing sub-seconds/nanoseconds
            df[col] = df[col].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
            # Step D: Parse safely into true system dates
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Calculate operational intervals safely
    if commit_date_col in df.columns and folder_date_col in df.columns:
        df['commit_gap_hours'] = (df[commit_date_col] - df[folder_date_col]).dt.total_seconds() / 3600
    if ack_date_col in df.columns and folder_date_col in df.columns:
        df['ack_gap_hours'] = (df[ack_date_col] - df[folder_date_col]).dt.total_seconds() / 3600

    # 11. Separate/Filter whole dashboard by REG_GROUP (Column O)
    st.sidebar.header("🎛️ Master Filters")
    if reg_group_col in df.columns:
        groups = ['All Groups'] + sorted(df[reg_group_col].dropna().unique().tolist())
        selected_group = st.sidebar.selectbox("Filter by REG_GROUP (Column O)", options=groups)
        if selected_group != 'All Groups':
            df = df[df[reg_group_col] == selected_group]

    # Global cross filters for Metric 10
    st.sidebar.subheader("💰 Financial Intersect Filters")
    filter_buyer = st.sidebar.multiselect("Buyer (Column D)", options=sorted(df[buyer_col].dropna().unique().tolist()) if buyer_col in df.columns else [])
    filter_service = st.sidebar.multiselect("Service Level (Column F)", options=sorted(df[service_col].dropna().unique().tolist()) if service_col in df.columns else [])
    filter_client = st.sidebar.multiselect("Bill To Client (Column AF)", options=sorted(df[bill_client_col].dropna().unique().tolist()) if bill_client_col in df.columns else [])

    finance_df = df.copy()
    if filter_buyer: finance_df = finance_df[finance_df[buyer_col].isin(filter_buyer)]
    if filter_service: finance_df = finance_df[finance_df[service_col].isin(filter_service)]
    if filter_client: finance_df = finance_df[finance_df[bill_client_col].isin(filter_client)]

    # ---- CARDS METRIC RUN (Items 01 - 06) ----
    st.subheader("📊 Key Operational Summary Cards")
    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)

    # 01. Commit within 3 hours
    with c1:
        if 'commit_gap_hours' in df.columns and sample_id_col in df.columns:
            total_samples = df[sample_id_col].nunique()
            commit_under_3 = df[df['commit_gap_hours'] <= 3][sample_id_col].nunique()
            pct = (commit_under_3 / total_samples * 100) if total_samples > 0 else 0
            st.metric("✅ 01. Commits <= 3 Hours", f"{commit_under_3} Samples", f"{pct:.1f}% of total")

    # 02. Acknowledgement within 2 hours
    with c2:
        if 'ack_gap_hours' in df.columns and sample_id_col in df.columns:
            total_samples = df[sample_id_col].nunique()
            ack_under_2 = df[df['ack_gap_hours'] <= 2][sample_id_col].nunique()
            pct = (ack_under_2 / total_samples * 100) if total_samples > 0 else 0
            st.metric("⏱️ 02. ACK <= 2 Hours", f"{ack_under_2} Samples", f"{pct:.1f}% of total")

    # 03. Team Commits counts
    with c3:
        if comm_by_col in df.columns and sample_id_col in df.columns:
            active_staff = df[df[comm_by_col].notna()].groupby(comm_by_col)[sample_id_col].nunique()
            st.metric("👤 03. Total Team Active Commits", f"{len(active_staff)} Staff Members")
            with st.expander("Show breakdowns per person"):
                st.dataframe(active_staff.rename("Samples Committed"))

    # 04. Samples per Buyer card summary
    with c4:
        if buyer_col in df.columns and sample_id_col in df.columns:
            top_buyer = df.groupby(buyer_col)[sample_id_col].nunique().idxmax() if not df.empty else "N/A"
            st.metric("🏢 04. Top Performing Buyer", f"{top_buyer}")
            with st.expander("Show breakdowns per buyer"):
                st.dataframe(df.groupby(buyer_col)[sample_id_col].nunique().rename("Samples Received"))

    # 05. Lab breakdown metrics
    with c5:
        if lab_type_col in df.columns and sample_id_col in df.columns:
            df_lower = df[lab_type_col].astype(str).str.lower()
            chem_only = df[(df_lower.str.contains('chemical')) & (~df_lower.str.contains('physical'))][sample_id_col].nunique()
            phys_only = df[(df_lower.str.contains('physical')) & (~df_lower.str.contains('chemical'))][sample_id_col].nunique()
            shared_count = df[(df_lower.str.contains('chemical')) & (df_lower.str.contains('physical'))][sample_id_col].nunique()
            st.metric("🔬 05. Sample Type Breakdown", f"Single Chem: {chem_only} | Phys: {phys_only}", f"Shared: {shared_count} Samples")

    # 06. Total Unique Folders
    with c6:
        if folder_id_col in df.columns:
            st.metric("📁 06. Unique Folders Committed", f"{df[folder_id_col].nunique()} Folders")

    # 10. Financial Metric Segment
    st.markdown("---")
    st.subheader("💰 10. Financial Charge Segment Analysis")
    if charges_col in df.columns:
        st.metric(label="Total Cross-Filtered Financial Revenue", value=f"{finance_df[charges_col].sum():,.2f}")
        st.caption("💡 Adjust the 'Financial Intersect Filters' on the left sidebar to change calculations Buyer-wise, Service-wise, or Client-wise.")

    # ---- DATAFRAMES / TABLES SECTION (Items 07 - 09) ----
    st.markdown("---")
    st.subheader("📋 Exception and SLA Breach Tables")

    def apply_neon_styling(val, color_hex):
        return f'background-color: {color_hex}; color: black; font-weight: bold'

    # 07. Missing ACK Validation Table
    st.markdown("#### 🚨 07. Missing Folder Acknowledgements")
    if folder_id_col in df.columns and ack_date_col in df.columns and buyer_col in df.columns:
        missing_ack = df[df[ack_date_col].isna()][[folder_id_col, buyer_col]].drop_duplicates()
        if not missing_ack.empty:
            st.dataframe(missing_ack.style.map(lambda v: apply_neon_styling(v, '#ffcccc'), subset=[folder_id_col, buyer_col]), use_container_width=True)
        else:
            st.success("Perfect! Zero missing folder acknowledgements found.")

    # 08. Commits Breach Table (> 3 Hours) Neon Green
    st.markdown("#### 🟢 08. Commits Breaching SLA (> 3 Hours Target)")
    if 'commit_gap_hours' in df.columns and folder_id_col in df.columns and buyer_col in df.columns:
        breach_3h = df[df['commit_gap_hours'] > 3][[folder_id_col, buyer_col]].drop_duplicates()
        if not breach_3h.empty:
            st.dataframe(breach_3h.style.map(lambda v: apply_neon_styling(v, '#39FF14'), subset=[folder_id_col, buyer_col]), use_container_width=True)
        else:
            st.success("Great job! Zero folders breached the 3-hour commitment SLA.")

    # 09. ACK Breach Table (> 2 Hours) Neon Orange
    st.markdown("#### 🟠 09. Acknowledgements Breaching SLA (> 2 Hours Target)")
    if 'ack_gap_hours' in df.columns and folder_id_col in df.columns and buyer_col in df.columns:
        breach_2h = df[df['ack_gap_hours'] > 2][[folder_id_col, buyer_col]].drop_duplicates()
        if not breach_2h.empty:
            st.dataframe(breach_2h.style.map(lambda v: apply_neon_styling(v, '#FF5F1F'), subset=[folder_id_col, buyer_col]), use_container_width=True)
        else:
            st.success("Great job! Zero folders breached the 2-hour acknowledgement SLA.")

    # ---- 12. FOLDER SEARCH DRILLDOWN ----
    st.markdown("---")
    st.subheader("🔍 12. Deep Folder Inspection Panel")
    if folder_id_col in df.columns:
        folder_list = sorted(df[folder_id_col].dropna().astype(str).unique().tolist())
        selected_folder = st.selectbox("Select or Type a Specific Folder Number to Inspect Details:", options=folder_list)
        
        if selected_folder:
            f_df = df[df[folder_id_col].astype(str) == selected_folder]
            if not f_df.empty:
                detail_row = f_df.iloc[0]
                
                d1, d2, d3 = st.columns(3)
                d4, d5, d6 = st.columns(3)
                
                with d1: st.info(f"**📅 Commitment Date (Col J):**\n\n{str(detail_row.get(commit_date_col, 'N/A'))}")
                with d2: st.info(f"**🏢 Buyer Name (Col D):**\n\n{detail_row.get(buyer_col, 'N/A')}")
                with d3: st.info(f"**👤 Committed By (Col Q):**\n\n{detail_row.get(comm_by_col, 'N/A')}")
                with d4: st.info(f"**🧾 Bill To Client (Col AF):**\n\n{detail_row.get(bill_client_col, 'N/A')}")
                with d5: st.info(f"**👔 Style Number (Col AK):**\n\n{detail_row.get(style_col, 'N/A')}")
                with d6: st.info(f"**🎨 Sample Colour (Col AN):**\n\n{detail_row.get(color_col, 'N/A')}")
else:
    st.info("👋 Upload your operational data file above to generate the full dashboard.")
