import streamlit as st
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(page_title="Lab Operations Master Dashboard", layout="wide")
st.title("🔬 Laboratory Operations Master Performance Dashboard")

# ---------------------------------------------------------
# CACHED DATA LOAD & CLEANING (Runs ONCE per file upload)
# ---------------------------------------------------------
@st.cache_data(show_spinner="⚡ Processing data and parsing dates...")
def load_and_preprocess_data(file):
    if file.name.endswith('.csv'):
        df_raw = pd.read_csv(file)
    else:
        df_raw = pd.read_excel(file)

    # Column Schema Mappings
    folder_date_col = 'FOLDER_RECEIVE_DATE'
    ack_date_col = 'ACKNOWLEDGEMENT_DATE'
    commit_date_col = 'FOLDER_COMMITTED_DATE'

    # Fast Date Parsing (Vectorized)
    for col in [folder_date_col, ack_date_col, commit_date_col]:
        if col in df_raw.columns:
            # Clean string T/decimals fast
            s = df_raw[col].fillna("").astype(str).str.replace('T', ' ', regex=False)
            s = s.str.split('.').str[0]
            df_raw[col] = pd.to_datetime(s, errors='coerce')

    # Committed Date Only for daily grouping
    if commit_date_col in df_raw.columns:
        df_raw['COMMIT_DATE_ONLY'] = df_raw[commit_date_col].dt.date

    # Operational gaps in hours
    if commit_date_col in df_raw.columns and folder_date_col in df_raw.columns:
        df_raw['commit_gap_hours'] = (df_raw[commit_date_col] - df_raw[folder_date_col]).dt.total_seconds() / 3600.0
    if ack_date_col in df_raw.columns and folder_date_col in df_raw.columns:
        df_raw['ack_gap_hours'] = (df_raw[ack_date_col] - df_raw[folder_date_col]).dt.total_seconds() / 3600.0

    return df_raw


# File uploader widget
uploaded_file = st.file_uploader(
    "📂 Upload your daily Lab Excel/CSV file (Accepts any filename format like 05/07/26)", 
    type=["xlsx", "csv"]
)

if uploaded_file is not None:
    try:
        df_raw = load_and_preprocess_data(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    # Column Mappings
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
    folder_id_col = 'FOLDER#'
    sample_id_col = 'SAMPLE_NUMBER'
    charges_col = 'TOTAL_CHARGES'

    # SIDEBAR FILTERS
    st.sidebar.header("🎛️ Master Filters")

    # Date Range Filter
    df_filtered = df_raw.copy()
    if commit_date_col in df_filtered.columns and not df_filtered[commit_date_col].dropna().empty:
        min_date = df_filtered[commit_date_col].min().date()
        max_date = df_filtered[commit_date_col].max().date()
        selected_dates = st.sidebar.date_input(
            "📅 Committed Date Range", 
            [min_date, max_date], 
            min_value=min_date, 
            max_value=max_date
        )
        if len(selected_dates) == 2:
            start_date, end_date = selected_dates
            df_filtered = df_filtered[
                (df_filtered[commit_date_col].dt.date >= start_date) & 
                (df_filtered[commit_date_col].dt.date <= end_date)
            ]

    # REG_GROUP Filter
    if reg_group_col in df_filtered.columns:
        groups = ['All Groups'] + sorted(df_filtered[reg_group_col].dropna().astype(str).unique().tolist())
        selected_group = st.sidebar.selectbox("Filter by REG_GROUP (Column O)", options=groups)
        if selected_group != 'All Groups':
            df_filtered = df_filtered[df_filtered[reg_group_col] == selected_group]

    # DAY-WISE DATE CARDS SELECTOR
    st.sidebar.subheader("📅 Individual Committed Day Selector")
    unique_commit_dates = sorted(df_filtered['COMMIT_DATE_ONLY'].dropna().unique().tolist()) if 'COMMIT_DATE_ONLY' in df_filtered.columns else []
    date_options = ['All Combined Days'] + [str(d) for d in unique_commit_dates]
    selected_date_card = st.sidebar.radio("Select Specific Committed Day to Analyze:", options=date_options)

    # Filter active dataset based on selection
    if selected_date_card != 'All Combined Days':
        df_active_view = df_filtered[df_filtered['COMMIT_DATE_ONLY'].astype(str) == selected_date_card]
    else:
        df_active_view = df_filtered.copy()

    # NOT ELIGIBLE FOR SAMPLE ACKNOWLEDGEMENT CONFIGURATION
    st.sidebar.subheader("🚫 Not Eligible for Acknowledgement List")
    
    all_buyers_list = sorted(df_filtered[buyer_col].dropna().astype(str).unique().tolist()) if buyer_col in df_filtered.columns else []
    default_excluded_buyers = [b for b in all_buyers_list if 'siplec' in str(b).lower()]
    exclude_buyers = st.sidebar.multiselect(
        "Exclude Buyer (Entirely)", 
        options=all_buyers_list,
        default=default_excluded_buyers
    )

    hm_clients_default = [
        "FAKIR KNITWEARS LTD.",
        "FAKIR APPARELS LTD",
        "FLAMINGO FASHIONS LTD",
        "KC LINGERIE LTD. (KNIT CONCERN GROUP)",
        "SAIHAM KNIT COMPOSITE LTD"
    ]
    all_clients_list = sorted(df_filtered[bill_client_col].dropna().astype(str).unique().tolist()) if bill_client_col in df_filtered.columns else []
    exclude_hm_clients = st.sidebar.multiselect(
        "H&M Non-Eligible Bill To Clients",
        options=all_clients_list,
        default=[c for c in hm_clients_default if c in all_clients_list]
    )

    # Financial Filters
    st.sidebar.subheader("💰 Financial Intersect Filters")
    filter_buyer = st.sidebar.multiselect(
        "Buyer (Column D)", 
        options=all_buyers_list
    )
    filter_service = st.sidebar.multiselect(
        "Service Level (Column F)", 
        options=sorted(df_filtered[service_col].dropna().astype(str).unique().tolist()) if service_col in df_filtered.columns else []
    )
    filter_client = st.sidebar.multiselect(
        "Bill To Client (Column AF)", 
        options=all_clients_list
    )

    # HELPER FUNCTION: FILTER NON-ELIGIBLE ACKNOWLEDGEMENTS
    def apply_ack_eligibility_filter(df_in):
        df_out = df_in
        if exclude_buyers and buyer_col in df_out.columns:
            df_out = df_out[~df_out[buyer_col].isin(exclude_buyers)]
            
        if exclude_hm_clients and buyer_col in df_out.columns and bill_client_col in df_out.columns:
            hm_mask = (df_out[buyer_col].astype(str).str.upper().str.contains("H&M")) & (df_out[bill_client_col].isin(exclude_hm_clients))
            df_out = df_out[~hm_mask]
            
        return df_out

    # MAIN RENDER FUNCTION
    def render_dashboard(df, date_label):
        st.markdown(f"## 📅 Operating Data View (Committed Date): **{date_label}**")

        ack_filtered_df = apply_ack_eligibility_filter(df)

        finance_mask = pd.Series(True, index=df.index)
        if filter_buyer and buyer_col in df.columns:
            finance_mask &= df[buyer_col].isin(filter_buyer)
        if filter_service and service_col in df.columns:
            finance_mask &= df[service_col].isin(filter_service)
        if filter_client and bill_client_col in df.columns:
            finance_mask &= df[bill_client_col].isin(filter_client)

        finance_df = df[finance_mask]

        # CARDS METRIC RUN (Items 01 - 06)
        st.subheader("📊 Key Operational Summary Cards")
        c1, c2, c3 = st.columns(3)
        c4, c5, c6 = st.columns(3)

        # 01. Commit within 3 hours
        with c1:
            if 'commit_gap_hours' in df.columns and sample_id_col in df.columns:
                total_samples = df[sample_id_col].nunique()
                commit_under_3 = df[df['commit_gap_hours'] <= 3][sample_id_col].nunique()
                pct_c1 = (commit_under_3 / total_samples * 100) if total_samples > 0 else 0
                
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745;">
                    <p style="margin: 0; font-size: 14px; font-weight: bold; color: #555;">✅ 01. Commits ≤ 3 Hours</p>
                    <h2 style="margin: 5px 0 0 0; color: #111;">{commit_under_3:,} <span style="font-size: 24px; color: #28a745; font-weight: bold;">({pct_c1:.1f}% of total)</span></h2>
                </div>
                """, unsafe_allow_html=True)

        # 02. ACK within 2 hours
        with c2:
            if 'ack_gap_hours' in ack_filtered_df.columns and sample_id_col in ack_filtered_df.columns:
                ack_total_samples = ack_filtered_df[sample_id_col].nunique()
                ack_under_2 = ack_filtered_df[ack_filtered_df['ack_gap_hours'] <= 2][sample_id_col].nunique()
                pct_c2 = (ack_under_2 / ack_total_samples * 100) if ack_total_samples > 0 else 0
                
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #007bff;">
                    <p style="margin: 0; font-size: 14px; font-weight: bold; color: #555;">⏱️ 02. ACK ≤ 2 Hours</p>
                    <h2 style="margin: 5px 0 0 0; color: #111;">{ack_under_2:,} <span style="font-size: 24px; color: #007bff; font-weight: bold;">({pct_c2:.1f}% of total)</span></h2>
                </div>
                """, unsafe_allow_html=True)

        # 03. Total Active Commits Staff
        with c3:
            if comm_by_col in df.columns and sample_id_col in df.columns:
                active_staff = df[df[comm_by_col].notna()][comm_by_col].nunique()
                st.metric("👤 03. Total Team Active Commits", f"{active_staff} Staff Members")

        # 04. Top Buyer
        with c4:
            st.write("")
            if buyer_col in df.columns and sample_id_col in df.columns:
                top_buyer = df.groupby(buyer_col)[sample_id_col].nunique().idxmax() if not df.empty else "N/A"
                st.metric("🏢 04. Top Performing Buyer", f"{top_buyer}")
                with st.expander("Show breakdowns per buyer"):
                    st.dataframe(df.groupby(buyer_col)[sample_id_col].nunique().rename("Samples Received"), use_container_width=True)

        # 05. Sample Type Breakdown
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

        # FAST VECTORIZED STAFF PERFORMANCE MATRIX
        st.markdown("---")
        st.subheader("👤 Staff Performance & SLA Compliance Matrix")
        
        if comm_by_col in df.columns and folder_id_col in df.columns:
            # Vectorized Aggregations
            comm_grp = df.groupby(comm_by_col).agg(
                Total_Folders=(folder_id_col, 'nunique'),
                Commit_3h=(folder_id_col, lambda s: df.loc[s.index].query("commit_gap_hours <= 3")[folder_id_col].nunique()),
                Buyers=(buyer_col, lambda s: ", ".join(s.dropna().unique()))
            ).reset_index()

            if ack_by_col in ack_filtered_df.columns:
                ack_grp = ack_filtered_df.query("ack_gap_hours <= 2").groupby(ack_by_col)[folder_id_col].nunique().reset_index()
                ack_grp.columns = [comm_by_col, "Folders Acknowledged (≤ 2h)"]
                summary_matrix = pd.merge(comm_grp, ack_grp, on=comm_by_col, how='left').fillna(0)
            else:
                summary_matrix = comm_grp
                summary_matrix["Folders Acknowledged (≤ 2h)"] = 0

            summary_matrix["Commit SLA Compliance"] = (summary_matrix["Commit_3h"] / summary_matrix["Total_Folders"] * 100).round(1).astype(str) + "%"
            
            summary_matrix.columns = [
                "Person Name", "Total Folders Actioned", "Folders Committed (≤ 3h)", 
                "Associated Buyer(s)", "Folders Acknowledged (≤ 2h)", "Commit SLA Compliance"
            ]
            
            ordered_cols = ["Person Name", "Associated Buyer(s)", "Total Folders Actioned", "Folders Committed (≤ 3h)", "Commit SLA Compliance", "Folders Acknowledged (≤ 2h)"]
            st.dataframe(summary_matrix[ordered_cols], use_container_width=True, hide_index=True)

        # Financial Segment Analysis
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
        if ack_date_col in ack_filtered_df.columns:
            missing_ack_df = ack_filtered_df[ack_filtered_df[ack_date_col].isna()]
        else:
            missing_ack_df = ack_filtered_df.copy()

        columns_to_show = [folder_id_col, buyer_col, bill_client_col, comm_by_col]
        available_cols = [col for col in columns_to_show if col in missing_ack_df.columns]
        
        missing_ack_unique = missing_ack_df[available_cols].drop_duplicates()
        if not missing_ack_unique.empty:
            st.dataframe(missing_ack_unique, hide_index=True, use_container_width=True)
        else:
            st.success("Zero missing folder acknowledgements for eligible buyers/clients.")

        st.markdown("#### 🟢 08. Commits Breaching SLA (> 3 Hours Target)")
        if 'commit_gap_hours' in df.columns and folder_id_col in df.columns and buyer_col in df.columns:
            breach_3h = df[df['commit_gap_hours'] > 3][[folder_id_col, buyer_col, comm_by_col]].drop_duplicates()
            if not breach_3h.empty:
                st.dataframe(
                    breach_3h.style.map(lambda v: apply_neon_styling(v, '#39FF14'), subset=[folder_id_col, buyer_col]), 
                    use_container_width=True, hide_index=True
                )
            else:
                st.success("Zero folders breached the 3-hour commitment SLA.")

        st.markdown("#### 🟠 09. Acknowledgements Breaching SLA (> 2 Hours Target)")
        if 'ack_gap_hours' in ack_filtered_df.columns and folder_id_col in ack_filtered_df.columns and buyer_col in ack_filtered_df.columns:
            breach_2h = ack_filtered_df[ack_filtered_df['ack_gap_hours'] > 2][[folder_id_col, buyer_col, ack_by_col if ack_by_col in ack_filtered_df.columns else buyer_col]].drop_duplicates()
            if not breach_2h.empty:
                st.dataframe(
                    breach_2h.style.map(lambda v: apply_neon_styling(v, '#FF5F1F'), subset=[folder_id_col, buyer_col]), 
                    use_container_width=True, hide_index=True
                )
            else:
                st.success("Zero folders breached the 2-hour acknowledgement SLA.")

    # RENDER MAIN DASHBOARD WITH ACTIVE SELECTED DATE
    render_dashboard(df_active_view, selected_date_card)

else:
    st.info("👋 Upload your operational data file above to generate the full dashboard.")
