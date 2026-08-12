import streamlit as st
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(page_title="Lab Operations Master Dashboard", layout="wide")
st.title("🔬 Laboratory Operations Master Performance Dashboard")

# File uploader widget
uploaded_file = st.file_uploader(
    "📂 Upload your daily Lab Excel/CSV file (Accepts any filename format like 05/07/26)", 
    type=["xlsx", "csv"]
)

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
    ack_by_col = 'ACKNOWLEDGEMENT_BY'
    reg_group_col = 'REG_GROUP'
    lab_type_col = 'TEST_GROUP'
    bill_client_col = 'BILL_TO_CLIENT'
    style_col = 'STYLE_NO'
    color_col = 'SAMPLE_COLOUR'
    folder_id_col = 'FOLDER#'
    sample_id_col = 'SAMPLE_NUMBER'
    charges_col = 'TOTAL_CHARGES'

    # Clean and convert Date columns safely
    for col in [folder_date_col, ack_date_col, commit_date_col]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
            df[col] = df[col].str.replace('T', ' ', regex=False)
            df[col] = df[col].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Calculate operational intervals safely in hours
    if commit_date_col in df.columns and folder_date_col in df.columns:
        df['commit_gap_hours'] = (df[commit_date_col] - df[folder_date_col]).dt.total_seconds() / 3600
    if ack_date_col in df.columns and folder_date_col in df.columns:
        df['ack_gap_hours'] = (df[ack_date_col] - df[folder_date_col]).dt.total_seconds() / 3600

    # Master Filter - REG_GROUP
    st.sidebar.header("🎛️ Master Filters")
    if reg_group_col in df.columns:
        groups = ['All Groups'] + sorted(df[reg_group_col].dropna().unique().tolist())
        selected_group = st.sidebar.selectbox("Filter by REG_GROUP (Column O)", options=groups)
        if selected_group != 'All Groups':
            df = df[df[reg_group_col] == selected_group]

    # ---- 01. ACK & Metric Exclusion Filters ----
    st.sidebar.subheader("🚫 Exclude Buyers/Clients from ACK ≤ 2h Metrics")
    exclude_buyers = st.sidebar.multiselect(
        "Exclude Buyer(s)", 
        options=sorted(df[buyer_col].dropna().unique().tolist()) if buyer_col in df.columns else []
    )
    exclude_clients = st.sidebar.multiselect(
        "Exclude Bill To Client(s)", 
        options=sorted(df[bill_client_col].dropna().unique().tolist()) if bill_client_col in df.columns else []
    )

    # Filtered dataframe for ACK calculation
    ack_filtered_df = df.copy()
    if exclude_buyers and buyer_col in ack_filtered_df.columns:
        ack_filtered_df = ack_filtered_df[~ack_filtered_df[buyer_col].isin(exclude_buyers)]
    if exclude_clients and bill_client_col in ack_filtered_df.columns:
        ack_filtered_df = ack_filtered_df[~ack_filtered_df[bill_client_col].isin(exclude_clients)]

    # Financial Intersect Filters
    st.sidebar.subheader("💰 Financial Intersect Filters")
    filter_buyer = st.sidebar.multiselect(
        "Buyer (Column D)", 
        options=sorted(df[buyer_col].dropna().unique().tolist()) if buyer_col in df.columns else []
    )
    filter_service = st.sidebar.multiselect(
        "Service Level (Column F)", 
        options=sorted(df[service_col].dropna().unique().tolist()) if service_col in df.columns else []
    )
    filter_client = st.sidebar.multiselect(
        "Bill To Client (Column AF)", 
        options=sorted(df[bill_client_col].dropna().unique().tolist()) if bill_client_col in df.columns else []
    )

    finance_mask = pd.Series(True, index=df.index)
    if filter_buyer and buyer_col in df.columns:
        finance_mask &= df[buyer_col].isin(filter_buyer)
    if filter_service and service_col in df.columns:
        finance_mask &= df[service_col].isin(filter_service)
    if filter_client and bill_client_col in df.columns:
        finance_mask &= df[bill_client_col].isin(filter_client)

    finance_df = df[finance_mask]

    # ---- CARDS METRIC RUN (Items 01 - 06) ----
    st.subheader("📊 Key Operational Summary Cards")
    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)

    # 01. Commit within 3 hours with larger percentage text (Req 02)
    with c1:
        if 'commit_gap_hours' in df.columns and sample_id_col in df.columns:
            total_samples = df[sample_id_col].nunique()
            commit_under_3 = df[df['commit_gap_hours'] <= 3][sample_id_col].nunique()
            pct_c1 = (commit_under_3 / total_samples * 100) if total_samples > 0 else 0
            
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745;">
                <p style="margin: 0; font-size: 14px; font-weight: bold; color: #555;">✅ 01. Commits ≤ 3 Hours</p>
                <h2 style="margin: 5px 0 0 0; color: #111;">{commit_under_3:,} <span style="font-size: 26px; color: #28a745; font-weight: bold;">({pct_c1:.1f}% of total)</span></h2>
            </div>
            """, unsafe_allow_html=True)

    # 02. ACK within 2 hours with exclusion logic & large percentage text (Req 01 & 02)
    with c2:
        if 'ack_gap_hours' in ack_filtered_df.columns and sample_id_col in ack_filtered_df.columns:
            ack_total_samples = ack_filtered_df[sample_id_col].nunique()
            ack_under_2 = ack_filtered_df[ack_filtered_df['ack_gap_hours'] <= 2][sample_id_col].nunique()
            pct_c2 = (ack_under_2 / ack_total_samples * 100) if ack_total_samples > 0 else 0
            
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #007bff;">
                <p style="margin: 0; font-size: 14px; font-weight: bold; color: #555;">⏱️ 02. ACK ≤ 2 Hours</p>
                <h2 style="margin: 5px 0 0 0; color: #111;">{ack_under_2:,} <span style="font-size: 26px; color: #007bff; font-weight: bold;">({pct_c2:.1f}% of total)</span></h2>
            </div>
            """, unsafe_allow_html=True)

    # 03. Total Team Active Commits
    with c3:
        if comm_by_col in df.columns and sample_id_col in df.columns:
            active_staff = df[df[comm_by_col].notna()][comm_by_col].nunique()
            st.metric("👤 03. Total Team Active Commits", f"{active_staff} Staff Members")

    # 04. Top Performing Buyer
    with c4:
        st.write("") # Spacing alignment
        if buyer_col in df.columns and sample_id_col in df.columns:
            top_buyer = df.groupby(buyer_col)[sample_id_col].nunique().idxmax() if not df.empty else "N/A"
            st.metric("🏢 04. Top Performing Buyer", f"{top_buyer}")
            with st.expander("Show breakdowns per buyer"):
                st.dataframe(df.groupby(buyer_col)[sample_id_col].nunique().rename("Samples Received"), use_container_width=True)

    # 05. Lab breakdown metrics
    with c5:
        st.write("")
        if lab_type_col in df.columns and sample_id_col in df.columns:
            df_lower = df[lab_type_col].fillna("").astype(str).str.lower()
            chem_only = df[(df_lower.str.contains('chem')) & (~df_lower.str.contains('phys'))][sample_id_col].nunique()
            phys_only = df[(df_lower.str.contains('phys')) & (~df_lower.str.contains('chem'))][sample_id_col].nunique()
            shared_count = df[(df_lower.str.contains('chem')) & (df_lower.str.contains('phys'))][sample_id_col].nunique()
            st.metric("🔬 05. Sample Type Breakdown", f"Chem: {chem_only} | Phys: {phys_only}", f"Shared: {shared_count} Samples")
        else:
            st.metric("🔬 05. Sample Type Breakdown", "N/A", "Column 'TEST_GROUP' Missing")

    # 06. Unique Folders
    with c6:
        st.write("")
        if folder_id_col in df.columns:
            st.metric("📁 06. Unique Folders Committed", f"{df[folder_id_col].nunique():,} Folders")

    # ---- 03. PERSON-WISE DETAILED PERFORMANCE TABLE (Req 03) ----
    st.markdown("---")
    st.subheader("👤 Detailed Person-Wise Performance Breakdown")
    
    if comm_by_col in df.columns and folder_id_col in df.columns:
        # Aggregate unique person metrics
        person_stats = []
        all_persons = sorted(list(set(df[comm_by_col].dropna().unique()).union(set(df[ack_by_col].dropna().unique() if ack_by_col in df.columns else []))))

        for person in all_persons:
            person_df_comm = df[df[comm_by_col] == person]
            person_df_ack = df[df[ack_by_col] == person] if ack_by_col in df.columns else pd.DataFrame()

            # Buyers handled
            buyers_handled = ", ".join(person_df_comm[buyer_col].dropna().unique().tolist()) if buyer_col in person_df_comm.columns else "N/A"
            if not buyers_handled:
                buyers_handled = "N/A"

            # Total unique folders
            total_folders = person_df_comm[folder_id_col].nunique()

            # Folders committed within 3 hours
            commit_3h = person_df_comm[person_df_comm['commit_gap_hours'] <= 3][folder_id_col].nunique() if 'commit_gap_hours' in person_df_comm.columns else 0

            # Folders acknowledged within 2 hours
            ack_2h = person_df_ack[person_df_ack['ack_gap_hours'] <= 2][folder_id_col].nunique() if ('ack_gap_hours' in person_df_ack.columns and not person_df_ack.empty) else 0

            person_stats.append({
                "Person Name": person,
                "Associated Buyer(s)": buyers_handled,
                "Total Folders Actioned": total_folders,
                "Folders Committed (≤ 3h)": commit_3h,
                "Folders Acknowledged (≤ 2h)": ack_2h
            })

        person_summary_df = pd.DataFrame(person_stats)
        st.dataframe(person_summary_df, use_container_width=True, hide_index=True)

    # 10. Financial Segment
    st.markdown("---")
    st.subheader("💰 10. Financial Charge Segment Analysis")
    if charges_col in finance_df.columns:
        total_rev = pd.to_numeric(finance_df[charges_col], errors='coerce').sum()
        st.metric(label="Total Cross-Filtered Financial Revenue", value=f"${total_rev:,.2f}")

    # Exception Tables
    st.markdown("---")
    st.subheader("📋 Exception and SLA Breach Tables")

    def apply_neon_styling(val, color_hex):
        return f'background-color: {color_hex}; color: black; font-weight: bold'

    st.markdown("### 🚨 07. Missing Folder Acknowledgements")
    if ack_date_col in df.columns:
        missing_ack_df = df[df[ack_date_col].isna()]
    else:
        missing_ack_df = df.copy()

    columns_to_show = [folder_id_col, buyer_col, bill_client_col, comm_by_col]
    available_cols = [col for col in columns_to_show if col in missing_ack_df.columns]
    st.dataframe(missing_ack_df[available_cols], hide_index=True, use_container_width=True)

    st.markdown("#### 🟢 08. Commits Breaching SLA (> 3 Hours Target)")
    if 'commit_gap_hours' in df.columns and folder_id_col in df.columns and buyer_col in df.columns:
        breach_3h = df[df['commit_gap_hours'] > 3][[folder_id_col, buyer_col]].drop_duplicates()
        if not breach_3h.empty:
            st.dataframe(
                breach_3h.style.map(lambda v: apply_neon_styling(v, '#39FF14'), subset=[folder_id_col, buyer_col]), 
                use_container_width=True, hide_index=True
            )
            csv_3h = breach_3h.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export 3H Breaches to CSV", data=csv_3h, file_name="commit_breaches_3h.csv", mime="text/csv")
        else:
            st.success("Zero folders breached the 3-hour commitment SLA.")

    st.markdown("#### 🟠 09. Acknowledgements Breaching SLA (> 2 Hours Target)")
    if 'ack_gap_hours' in df.columns and folder_id_col in df.columns and buyer_col in df.columns:
        breach_2h = df[df['ack_gap_hours'] > 2][[folder_id_col, buyer_col]].drop_duplicates()
        if not breach_2h.empty:
            st.dataframe(
                breach_2h.style.map(lambda v: apply_neon_styling(v, '#FF5F1F'), subset=[folder_id_col, buyer_col]), 
                use_container_width=True, hide_index=True
            )
            csv_2h = breach_2h.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export 2H Breaches to CSV", data=csv_2h, file_name="ack_breaches_2h.csv", mime="text/csv")
        else:
            st.success("Zero folders breached the 2-hour acknowledgement SLA.")

    # 12. Folder Deep Inspection
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
                with d1: st.info(f"**📅 Commitment Date:**\n\n{str(detail_row.get(commit_date_col, 'N/A'))}")
                with d2: st.info(f"**🏢 Buyer Name:**\n\n{detail_row.get(buyer_col, 'N/A')}")
                with d3: st.info(f"**👤 Committed By:**\n\n{detail_row.get(comm_by_col, 'N/A')}")
                with d4: st.info(f"**🧾 Bill To Client:**\n\n{detail_row.get(bill_client_col, 'N/A')}")
                with d5: st.info(f"**👔 Style Number:**\n\n{detail_row.get(style_col, 'N/A')}")
                with d6: st.info(f"**🎨 Sample Colour:**\n\n{detail_row.get(color_col, 'N/A')}")
else:
    st.info("👋 Upload your operational data file above to generate the full dashboard.")
