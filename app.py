import streamlit as st
import pandas as pd
import numpy as np
import datetime

# 1. Page Configuration
st.set_page_config(
    page_title="Lab Operations Executive Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom Executive CSS (Grey & Orange Styling)
st.markdown("""
<style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 22px 30px;
        border-radius: 12px;
        color: #ffffff;
        margin-bottom: 25px;
        border-left: 6px solid #ff6b00;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    .main-header h1 {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 2.1rem !important;
        margin: 0 !important;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #94a3b8 !important;
        margin: 5px 0 0 0 !important;
        font-size: 0.95rem;
    }

    .kpi-card {
        background: rgba(30, 41, 59, 0.85);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        padding: 18px 20px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        min-height: 110px;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(255, 107, 0, 0.15);
    }
    
    .kpi-card-orange { border-left: 5px solid #ff6b00; }
    .kpi-card-grey { border-left: 5px solid #64748b; }

    .kpi-title {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.2;
    }
    
    .kpi-percentage {
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        margin-left: 10px;
        color: #ff8c00 !important;
    }

    .sub-badge-orange {
        display: inline-block;
        background: rgba(255, 107, 0, 0.15);
        color: #ff8c00;
        border: 1px solid rgba(255, 107, 0, 0.3);
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 6px;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 25px 0 15px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HIGH-SPEED CACHED DATA LOAD & VECTORIZED PREPROCESSING
# ---------------------------------------------------------
@st.cache_data(show_spinner="⚡ Processing Lab Operations Data...", max_entries=5)
def load_and_preprocess_data(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    folder_date_col = 'FOLDER_RECEIVE_DATE'
    ack_date_col = 'ACKNOWLEDGEMENT_DATE'
    commit_date_col = 'FOLDER_COMMITTED_DATE'
    sample_rec_date_col = 'SAMPLE_RECEIVE_DATE'

    # Fast Vectorized Date Parsing
    for col in [folder_date_col, ack_date_col, commit_date_col, sample_rec_date_col]:
        if col in df.columns:
            s = df[col].fillna("").astype(str).str.replace('T', ' ', regex=False).str.split('.').str[0]
            df[col] = pd.to_datetime(s, errors='coerce')

    if commit_date_col in df.columns:
        df['COMMIT_DATE_ONLY'] = df[commit_date_col].dt.date

    # Pre-compute hours and SLA boolean flags
    if commit_date_col in df.columns and folder_date_col in df.columns:
        df['commit_gap_hours'] = (df[commit_date_col] - df[folder_date_col]).dt.total_seconds() / 3600.0
        df['is_commit_3h'] = df['commit_gap_hours'] <= 3.0
    else:
        df['commit_gap_hours'] = np.nan
        df['is_commit_3h'] = False

    if ack_date_col in df.columns and folder_date_col in df.columns:
        df['ack_gap_hours'] = (df[ack_date_col] - df[folder_date_col]).dt.total_seconds() / 3600.0
        df['is_ack_2h'] = df['ack_gap_hours'] <= 2.0
    else:
        df['ack_gap_hours'] = np.nan
        df['is_ack_2h'] = False

    # Extract Sample Receive Time for fast slicer filtering
    if sample_rec_date_col in df.columns:
        df['sample_rec_time'] = df[sample_rec_date_col].dt.time
    else:
        df['sample_rec_time'] = None

    # Pre-compute lab type flags
    lab_type_col = 'TEST_GROUP'
    if lab_type_col in df.columns:
        lab_str = df[lab_type_col].fillna("").astype(str).str.lower()
        df['has_chem'] = lab_str.str.contains('chem')
        df['has_phys'] = lab_str.str.contains('phys')
    else:
        df['has_chem'] = False
        df['has_phys'] = False

    return df

# Main Header
st.markdown("""
<div class="main-header">
    <h1>🔬 Laboratory Operations Executive Dashboard</h1>
    <p>Real-time SLA tracking, operational commitments, and financial segment analytics</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "📂 Upload daily Excel/CSV operational dump", 
    type=["xlsx", "csv"]
)

if uploaded_file is not None:
    try:
        df_raw = load_and_preprocess_data(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    folder_date_col = 'FOLDER_RECEIVE_DATE'
    ack_date_col = 'ACKNOWLEDGEMENT_DATE'
    commit_date_col = 'FOLDER_COMMITTED_DATE'
    sample_rec_date_col = 'SAMPLE_RECEIVE_DATE'
    buyer_col = 'BUYER'
    service_col = 'SERVICE_LEVEL'
    comm_by_col = 'COMMITTED_BY'
    ack_by_col = 'ACKNOWLEDGEMENT_BY'
    reg_group_col = 'REG_GROUP'
    bill_client_col = 'BILL_TO_CLIENT'
    folder_id_col = 'FOLDER#'
    sample_id_col = 'SAMPLE_NUMBER'
    currency_col = 'CURRENCY'        
    ex_rate_col = 'EXCHANGE_RATE'    
    charges_col = 'TOTAL_CHARGES'    

    # SIDEBAR CONTROLS
    st.sidebar.markdown("### 🎛️ Executive Filters")

    df_filtered = df_raw
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
                (df_filtered['COMMIT_DATE_ONLY'] >= start_date) & 
                (df_filtered['COMMIT_DATE_ONLY'] <= end_date)
            ]

    if reg_group_col in df_filtered.columns:
        groups = ['All Groups'] + sorted(df_filtered[reg_group_col].dropna().astype(str).unique().tolist())
        selected_group = st.sidebar.selectbox("Filter by REG_GROUP", options=groups)
        if selected_group != 'All Groups':
            df_filtered = df_filtered[df_filtered[reg_group_col] == selected_group]

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗓️ Committed Day Analysis")
    unique_commit_dates = sorted(df_filtered['COMMIT_DATE_ONLY'].dropna().unique().tolist()) if 'COMMIT_DATE_ONLY' in df_filtered.columns else []
    date_options = ['All Combined Days'] + [str(d) for d in unique_commit_dates]
    selected_date_card = st.sidebar.radio("Select Committed Day:", options=date_options)

    if selected_date_card != 'All Combined Days':
        df_active_view = df_filtered[df_filtered['COMMIT_DATE_ONLY'].astype(str) == selected_date_card]
    else:
        df_active_view = df_filtered

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⏰ ACK SLA Time Cutoff Slicer")
    enable_time_cutoff = st.sidebar.checkbox("Enable ACK Time Cutoff Filter", value=True)
    ack_cutoff_time = st.sidebar.time_input("Exclude ACK SLA Before Time:", value=datetime.time(21, 0))

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🚫 ACK Exclusions")
    all_buyers_list = sorted(df_filtered[buyer_col].dropna().astype(str).unique().tolist()) if buyer_col in df_filtered.columns else []
    default_excluded_buyers = [b for b in all_buyers_list if 'siplec' in str(b).lower()]
    exclude_buyers = st.sidebar.multiselect("Exclude Buyers (Entirely)", options=all_buyers_list, default=default_excluded_buyers)

    hm_clients_default = [
        "FAKIR KNITWEARS LTD.", "FAKIR APPARELS LTD", "FLAMINGO FASHIONS LTD",
        "KC LINGERIE LTD. (KNIT CONCERN GROUP)", "SAIHAM KNIT COMPOSITE LTD"
    ]
    all_clients_list = sorted(df_filtered[bill_client_col].dropna().astype(str).unique().tolist()) if bill_client_col in df_filtered.columns else []
    exclude_hm_clients = st.sidebar.multiselect("H&M Non-Eligible Clients", options=all_clients_list, default=[c for c in hm_clients_default if c in all_clients_list])

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💰 Financial Intersects")
    filter_buyer = st.sidebar.multiselect("Buyer Filter", options=all_buyers_list)
    filter_service = st.sidebar.multiselect("Service Level Filter", options=sorted(df_filtered[service_col].dropna().astype(str).unique().tolist()) if service_col in df_filtered.columns else [])
    filter_client = st.sidebar.multiselect("Client Filter", options=all_clients_list)

    # Fast eligibility mask including time cutoff
    def apply_ack_eligibility_filter(df_in):
        df_out = df_in
        
        # 1. Buyer & Client Exclusions
        if exclude_buyers and buyer_col in df_out.columns:
            df_out = df_out[~df_out[buyer_col].isin(exclude_buyers)]
        if exclude_hm_clients and buyer_col in df_out.columns and bill_client_col in df_out.columns:
            hm_mask = (df_out[buyer_col].astype(str).str.upper().str.contains("H&M")) & (df_out[bill_client_col].isin(exclude_hm_clients))
            df_out = df_out[~hm_mask]
            
        # 2. Time Cutoff Slicer (Exclude folders with SAMPLE_RECEIVE_DATE before selected time)
        if enable_time_cutoff and 'sample_rec_time' in df_out.columns:
            time_mask = df_out['sample_rec_time'].notna() & (df_out['sample_rec_time'] >= ack_cutoff_time)
            df_out = df_out[time_mask]

        return df_out

    def render_dashboard(df, date_label):
        st.markdown(f"<div class='section-title'>📅 Active Operating View: <span style='color:#ff6b00;'>{date_label}</span></div>", unsafe_allow_html=True)

        ack_filtered_df = apply_ack_eligibility_filter(df)

        finance_mask = pd.Series(True, index=df.index)
        if filter_buyer and buyer_col in df.columns:
            finance_mask &= df[buyer_col].isin(filter_buyer)
        if filter_service and service_col in df.columns:
            finance_mask &= df[service_col].isin(filter_service)
        if filter_client and bill_client_col in df.columns:
            finance_mask &= df[bill_client_col].isin(filter_client)

        finance_df = df[finance_mask]

        c1, c2, c3 = st.columns(3)
        c4, c5, c6 = st.columns(3)

        # C1: Commit SLA
        with c1:
            total_samples = df[sample_id_col].nunique() if sample_id_col in df.columns else 0
            commit_under_3 = df[df['is_commit_3h']][sample_id_col].nunique() if sample_id_col in df.columns else 0
            pct_c1 = (commit_under_3 / total_samples * 100) if total_samples > 0 else 0
            st.markdown(f"""
            <div class="kpi-card kpi-card-orange">
                <div class="kpi-title">01. Commits ≤ 3 Hours SLA</div>
                <div class="kpi-value">{commit_under_3:,}<span class="kpi-percentage">({pct_c1:.1f}%)</span></div>
            </div>
            """, unsafe_allow_html=True)

        # C2: ACK SLA (Uses Time Cutoff Filter)
        with c2:
            ack_total_samples = ack_filtered_df[sample_id_col].nunique() if sample_id_col in ack_filtered_df.columns else 0
            ack_under_2 = ack_filtered_df[ack_filtered_df['is_ack_2h']][sample_id_col].nunique() if sample_id_col in ack_filtered_df.columns else 0
            pct_c2 = (ack_under_2 / ack_total_samples * 100) if ack_total_samples > 0 else 0
            st.markdown(f"""
            <div class="kpi-card kpi-card-orange">
                <div class="kpi-title">02. ACK ≤ 2 Hours SLA</div>
                <div class="kpi-value">{ack_under_2:,}<span class="kpi-percentage">({pct_c2:.1f}%)</span></div>
            </div>
            """, unsafe_allow_html=True)

        # C3: Active Staff
        with c3:
            active_staff = df[df[comm_by_col].notna()][comm_by_col].nunique() if comm_by_col in df.columns else 0
            st.markdown(f"""
            <div class="kpi-card kpi-card-grey">
                <div class="kpi-title">03. Active Commits Staff</div>
                <div class="kpi-value">{active_staff} <span style="font-size:1.1rem; font-weight:500; color:#cbd5e1;">Members</span></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # C4: Top Buyer
        with c4:
            top_buyer = df.groupby(buyer_col)[sample_id_col].nunique().idxmax() if (buyer_col in df.columns and not df.empty) else "N/A"
            st.markdown(f"""
            <div class="kpi-card kpi-card-grey">
                <div class="kpi-title">04. Top Performing Buyer</div>
                <div class="kpi-value" style="font-size: 1.3rem; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; color:#f8fafc;">{top_buyer}</div>
            </div>
            """, unsafe_allow_html=True)

        # C5: Sample Breakdown
        with c5:
            if sample_id_col in df.columns:
                chem_only = df[df['has_chem'] & ~df['has_phys']][sample_id_col].nunique()
                phys_only = df[df['has_phys'] & ~df['has_chem']][sample_id_col].nunique()
                shared_count = df[df['has_chem'] & df['has_phys']][sample_id_col].nunique()
            else:
                chem_only = phys_only = shared_count = 0
            st.markdown(f"""
            <div class="kpi-card kpi-card-orange">
                <div class="kpi-title">05. Sample Breakdown</div>
                <div class="kpi-value" style="font-size: 1.25rem;">Chem: {chem_only} | Phys: {phys_only}</div>
                <div class="sub-badge-orange">Shared: {shared_count} Samples</div>
            </div>
            """, unsafe_allow_html=True)

        # C6: Unique Folders
        with c6:
            unique_folders = df[folder_id_col].nunique() if folder_id_col in df.columns else 0
            st.markdown(f"""
            <div class="kpi-card kpi-card-grey">
                <div class="kpi-title">06. Unique Folders Committed</div>
                <div class="kpi-value">{unique_folders:,} <span style="font-size:1.1rem; font-weight:500; color:#cbd5e1;">Folders</span></div>
            </div>
            """, unsafe_allow_html=True)

        # STAFF PERFORMANCE MATRIX
        st.markdown("<div class='section-title'>👤 Staff Performance & SLA Compliance Matrix</div>", unsafe_allow_html=True)
        if comm_by_col in df.columns and folder_id_col in df.columns:
            comm_grp = df.groupby(comm_by_col).agg(
                Total_Folders=(folder_id_col, 'nunique'),
                Buyers=(buyer_col, lambda s: ", ".join(s.dropna().unique()))
            ).reset_index()

            commit_3h_grp = df[df['is_commit_3h']].groupby(comm_by_col)[folder_id_col].nunique().reset_index()
            commit_3h_grp.columns = [comm_by_col, 'Commit_3h']

            summary_matrix = pd.merge(comm_grp, commit_3h_grp, on=comm_by_col, how='left').fillna({'Commit_3h': 0})

            if ack_by_col in ack_filtered_df.columns:
                ack_grp = ack_filtered_df[ack_filtered_df['is_ack_2h']].groupby(ack_by_col)[folder_id_col].nunique().reset_index()
                ack_grp.columns = [comm_by_col, "Folders Acknowledged (≤ 2h)"]
                summary_matrix = pd.merge(summary_matrix, ack_grp, on=comm_by_col, how='left').fillna({"Folders Acknowledged (≤ 2h)": 0})
            else:
                summary_matrix["Folders Acknowledged (≤ 2h)"] = 0

            summary_matrix["Commit SLA Compliance"] = (summary_matrix["Commit_3h"] / summary_matrix["Total_Folders"] * 100).round(1).astype(str) + "%"
            
            summary_matrix.columns = [
                "Person Name", "Total Folders Actioned", "Associated Buyer(s)", 
                "Folders Committed (≤ 3h)", "Folders Acknowledged (≤ 2h)", "Commit SLA Compliance"
            ]
            
            ordered_cols = ["Person Name", "Associated Buyer(s)", "Total Folders Actioned", "Folders Committed (≤ 3h)", "Commit SLA Compliance", "Folders Acknowledged (≤ 2h)"]
            st.dataframe(summary_matrix[ordered_cols], use_container_width=True, hide_index=True)

        # FINANCIAL ANALYSIS
        st.markdown("<div class='section-title'>💰 Financial Charge Segment Analysis</div>", unsafe_allow_html=True)

        if charges_col in finance_df.columns and folder_id_col in finance_df.columns:
            fin_cols = [folder_id_col, charges_col]
            if currency_col in finance_df.columns:
                fin_cols.append(currency_col)
            if ex_rate_col in finance_df.columns:
                fin_cols.append(ex_rate_col)

            unique_folder_charges = finance_df[fin_cols].drop_duplicates(subset=[folder_id_col])
            charges_vec = pd.to_numeric(unique_folder_charges[charges_col], errors='coerce').fillna(0)
            
            if ex_rate_col in unique_folder_charges.columns:
                ex_vec = pd.to_numeric(unique_folder_charges[ex_rate_col], errors='coerce').fillna(1.0).replace(0, 1.0)
            else:
                ex_vec = pd.Series(1.0, index=unique_folder_charges.index)

            if currency_col in unique_folder_charges.columns:
                curr_vec = unique_folder_charges[currency_col].fillna("BDT").astype(str).str.upper()
            else:
                curr_vec = pd.Series("BDT", index=unique_folder_charges.index)

            is_bdt = (curr_vec == 'BDT')
            charges_usd = np.where(is_bdt, charges_vec / ex_vec, charges_vec)
            charges_bdt = np.where(~is_bdt, charges_vec * ex_vec, charges_vec)

            total_usd = charges_usd.sum()
            total_bdt = charges_bdt.sum()

            f1, f2 = st.columns(2)
            with f1:
                st.markdown(f"""
                <div class="kpi-card" style="border-left: 5px solid #ff6b00;">
                    <div class="kpi-title">Total Financial Revenue (USD)</div>
                    <div class="kpi-value" style="color:#ff8c00;">${total_usd:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            with f2:
                st.markdown(f"""
                <div class="kpi-card" style="border-left: 5px solid #94a3b8;">
                    <div class="kpi-title">Total Financial Revenue (BDT)</div>
                    <div class="kpi-value" style="color:#f1f5f9;">৳{total_bdt:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

        # SLA BREACH TABLES
        st.markdown("<div class='section-title'>📋 Exception & SLA Breach Logs</div>", unsafe_allow_html=True)

        def apply_orange_highlight(val):
            return 'background-color: #ff6b00; color: white; font-weight: bold;'

        st.markdown("##### 🚨 Missing Folder Acknowledgements")
        missing_ack_df = ack_filtered_df[ack_filtered_df[ack_date_col].isna()] if ack_date_col in ack_filtered_df.columns else ack_filtered_df
        available_cols = [c for c in [folder_id_col, buyer_col, bill_client_col, comm_by_col] if c in missing_ack_df.columns]
        missing_ack_unique = missing_ack_df[available_cols].drop_duplicates()
        
        if not missing_ack_unique.empty:
            st.dataframe(missing_ack_unique, hide_index=True, use_container_width=True)
        else:
            st.success("Zero missing folder acknowledgements for eligible buyers/clients/times.")

        st.markdown("##### 🟠 Commits Breaching SLA (> 3 Hours Target)")
        if 'commit_gap_hours' in df.columns and folder_id_col in df.columns and buyer_col in df.columns:
            breach_3h = df[df['commit_gap_hours'] > 3][[folder_id_col, buyer_col, comm_by_col]].drop_duplicates()
            if not breach_3h.empty:
                st.dataframe(breach_3h.style.map(apply_orange_highlight, subset=[folder_id_col, buyer_col]), use_container_width=True, hide_index=True)
            else:
                st.success("Zero folders breached the 3-hour commitment SLA.")

        st.markdown("##### 🟠 Acknowledgements Breaching SLA (> 2 Hours Target)")
        if 'ack_gap_hours' in ack_filtered_df.columns and folder_id_col in ack_filtered_df.columns and buyer_col in ack_filtered_df.columns:
            breach_2h = ack_filtered_df[ack_filtered_df['ack_gap_hours'] > 2][[folder_id_col, buyer_col, ack_by_col if ack_by_col in ack_filtered_df.columns else buyer_col]].drop_duplicates()
            if not breach_2h.empty:
                st.dataframe(breach_2h.style.map(apply_orange_highlight, subset=[folder_id_col, buyer_col]), use_container_width=True, hide_index=True)
            else:
                st.success("Zero folders breached the 2-hour acknowledgement SLA.")

    render_dashboard(df_active_view, selected_date_card)

else:
    st.info("👋 Upload your operational data file above to generate the executive dashboard.")
