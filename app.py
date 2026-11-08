import streamlit as st
import pandas as pd
import numpy as np
import datetime

# 1. Page Configuration
st.set_page_config(
    page_title="Lab Operations Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Modern Executive CSS (Adaptive across Light, Dark & System Modes)
st.markdown("""
<style>
    /* Global Typography & Spacing */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 96%;
    }

    /* System Theme Aware Palette */
    :root {
        --card-bg-light: #ffffff;
        --card-border-light: #e2e8f0;
        --header-bg-light: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
        --text-sub-light: #64748b;
        --table-bg-light: #ffffff;
        
        --card-bg-dark: #1e293b;
        --card-border-dark: rgba(255, 255, 255, 0.08);
        --header-bg-dark: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        --text-sub-dark: #94a3b8;
        --table-bg-dark: #1e293b;
    }

    /* Executive Hero Banner */
    .main-header {
        background: var(--header-bg-light);
        padding: 24px 32px;
        border-radius: 14px;
        margin-bottom: 24px;
        border-left: 6px solid #ea580c;
        border-top: 1px solid var(--card-border-light);
        border-right: 1px solid var(--card-border-light);
        border-bottom: 1px solid var(--card-border-light);
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.06);
    }
    .main-header h1 {
        color: var(--text-color, #0f172a) !important;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        margin: 0 !important;
        letter-spacing: -0.6px;
    }
    .main-header p {
        color: #64748b !important;
        margin: 6px 0 0 0 !important;
        font-size: 0.95rem;
        font-weight: 500;
    }

    /* High-Impact Executive KPI Cards */
    .kpi-card {
        background: var(--card-bg-light);
        border-radius: 12px;
        padding: 20px 22px;
        border: 1px solid var(--card-border-light);
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
        transition: transform 0.18s ease, box-shadow 0.18s ease;
        min-height: 118px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(234, 88, 12, 0.12);
    }
    
    .kpi-card-orange { border-left: 5px solid #ea580c !important; }
    .kpi-card-grey { border-left: 5px solid #64748b !important; }

    .kpi-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .kpi-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        color: #64748b;
    }
    .kpi-value-row {
        display: flex;
        align-items: baseline;
        gap: 8px;
    }
    .kpi-value {
        font-size: 2.1rem;
        font-weight: 800;
        color: var(--text-color, #0f172a);
        line-height: 1.1;
        letter-spacing: -0.5px;
    }
    .kpi-percentage {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: #ea580c !important;
    }

    /* Sub-Headers & Section Bars */
    .section-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: var(--text-color, #0f172a);
        margin: 28px 0 16px 0;
        display: flex;
        align-items: center;
        gap: 10px;
        border-bottom: 2px solid rgba(234, 88, 12, 0.2);
        padding-bottom: 8px;
    }

    /* Micro Metric Counters */
    .mini-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 12px;
    }
    .pill-green { background: rgba(34, 197, 94, 0.12); color: #16a34a; border: 1px solid rgba(34, 197, 94, 0.3); }
    .pill-orange { background: rgba(234, 88, 12, 0.12); color: #c2410c; border: 1px solid rgba(234, 88, 12, 0.3); }
    .pill-slate { background: rgba(100, 116, 139, 0.12); color: #475569; border: 1px solid rgba(100, 116, 139, 0.3); }

    /* Dark Mode Theme Tuning */
    @media (prefers-color-scheme: dark) {
        .main-header {
            background: var(--header-bg-dark) !important;
            border-color: var(--card-border-dark) !important;
        }
        .main-header p {
            color: #94a3b8 !important;
        }
        .kpi-card {
            background: var(--card-bg-dark) !important;
            border-color: var(--card-border-dark) !important;
        }
        .kpi-title {
            color: #94a3b8 !important;
        }
        .kpi-percentage {
            color: #ff8c00 !important;
        }
        .pill-green { color: #4ade80; }
        .pill-orange { color: #fb923c; }
        .pill-slate { color: #cbd5e1; }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# CACHED HIGH-SPEED DATA PIPELINE
# ---------------------------------------------------------
@st.cache_data(show_spinner="⚡ Loading laboratory data...", max_entries=5)
def load_and_preprocess_data(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file, engine='c')
    else:
        try:
            df = pd.read_excel(file, engine='calamine')
        except Exception:
            df = pd.read_excel(file)

    folder_date_col = 'FOLDER_RECEIVE_DATE'
    ack_date_col = 'ACKNOWLEDGEMENT_DATE'
    commit_date_col = 'FOLDER_COMMITTED_DATE'
    sample_rec_date_col = 'SAMPLE_RECEIVE_DATE'

    for col in [folder_date_col, ack_date_col, commit_date_col, sample_rec_date_col]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    if commit_date_col in df.columns:
        df['COMMIT_DATE_ONLY'] = df[commit_date_col].dt.date

    # Vectorized hour diffs
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

    if ack_date_col in df.columns:
        df['has_ack'] = df[ack_date_col].notna()
    else:
        df['has_ack'] = False

    if sample_rec_date_col in df.columns:
        df['sample_rec_time'] = df[sample_rec_date_col].dt.time
    else:
        df['sample_rec_time'] = None

    return df

# Main Title Header
st.markdown("""
<div class="main-header">
    <h1>Lab Operations Dashboard</h1>
    <p>Operational turnaround tracking, commitment deadlines, and financial revenue segments</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "📂 Upload Operational Data File (.xlsx or .csv)", 
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
    st.sidebar.markdown("### 🎛️ Navigation & Filters")

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
    st.sidebar.markdown("### 🗓️ View By Day")
    unique_commit_dates = sorted(df_filtered['COMMIT_DATE_ONLY'].dropna().unique().tolist()) if 'COMMIT_DATE_ONLY' in df_filtered.columns else []
    date_options = ['All Combined Days'] + [str(d) for d in unique_commit_dates]
    selected_date_card = st.sidebar.radio("Select View Date:", options=date_options)

    if selected_date_card != 'All Combined Days':
        df_active_view = df_filtered[df_filtered['COMMIT_DATE_ONLY'].astype(str) == selected_date_card]
    else:
        df_active_view = df_filtered

    # Time Slicer & Exclusions (Clean default state)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⏰ Optional ACK Slicers")
    enable_time_cutoff = st.sidebar.checkbox("Enable Cutoff Filter", value=False)
    ack_cutoff_time = st.sidebar.time_input("Ignore Before Time:", value=datetime.time(21, 0))

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🚫 Exclusions")
    all_buyers_list = sorted(df_filtered[buyer_col].dropna().astype(str).unique().tolist()) if buyer_col in df_filtered.columns else []
    exclude_buyers = st.sidebar.multiselect("Exclude Buyers", options=all_buyers_list, default=[])

    all_clients_list = sorted(df_filtered[bill_client_col].dropna().astype(str).unique().tolist()) if bill_client_col in df_filtered.columns else []
    exclude_hm_clients = st.sidebar.multiselect("Exclude Specific Clients", options=all_clients_list, default=[])

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💰 Financial Slicers")
    filter_buyer = st.sidebar.multiselect("Buyer Filter", options=all_buyers_list)
    filter_service = st.sidebar.multiselect("Service Level Filter", options=sorted(df_filtered[service_col].dropna().astype(str).unique().tolist()) if service_col in df_filtered.columns else [])
    filter_client = st.sidebar.multiselect("Client Filter", options=all_clients_list)

    @st.cache_data
    def apply_ack_eligibility_filter(df_in, exclude_buyers_tuple, exclude_hm_tuple, enable_cutoff, cutoff_t):
        df_out = df_in
        if exclude_buyers_tuple and buyer_col in df_out.columns:
            df_out = df_out[~df_out[buyer_col].isin(exclude_buyers_tuple)]
        if exclude_hm_tuple and buyer_col in df_out.columns and bill_client_col in df_out.columns:
            hm_mask = (df_out[buyer_col].astype(str).str.upper().str.contains("H&M", regex=False)) & (df_out[bill_client_col].isin(exclude_hm_tuple))
            df_out = df_out[~hm_mask]
            
        if enable_cutoff and 'sample_rec_time' in df_out.columns:
            time_mask = df_out['sample_rec_time'].notna() & (df_out['sample_rec_time'] >= cutoff_t)
            df_out = df_out[time_mask]

        return df_out

    def render_dashboard(df, date_label):
        st.markdown(f"<div class='section-title'>📊 Operational Performance Overview: <span style='color:#ea580c;'>{date_label}</span></div>", unsafe_allow_html=True)

        ack_filtered_df = apply_ack_eligibility_filter(
            df, 
            tuple(exclude_buyers), 
            tuple(exclude_hm_clients), 
            enable_time_cutoff, 
            ack_cutoff_time
        )

        finance_mask = pd.Series(True, index=df.index)
        if filter_buyer and buyer_col in df.columns:
            finance_mask &= df[buyer_col].isin(filter_buyer)
        if filter_service and service_col in df.columns:
            finance_mask &= df[service_col].isin(filter_service)
        if filter_client and bill_client_col in df.columns:
            finance_mask &= df[bill_client_col].isin(filter_client)

        finance_df = df[finance_mask]

        # 6 KPI CARDS
        c1, c2, c3 = st.columns(3)
        c4, c5, c6 = st.columns(3)

        # C1: Commit SLA
        with c1:
            total_samples = df[sample_id_col].nunique() if sample_id_col in df.columns else 0
            commit_under_3 = df[df['is_commit_3h']][sample_id_col].nunique() if sample_id_col in df.columns else 0
            pct_c1 = (commit_under_3 / total_samples * 100) if total_samples > 0 else 0
            st.markdown(f"""
            <div class="kpi-card kpi-card-orange">
                <div class="kpi-header-row"><span class="kpi-title">01. Commits ≤ 3h SLA</span></div>
                <div class="kpi-value-row">
                    <span class="kpi-value">{commit_under_3:,}</span>
                    <span class="kpi-percentage">({pct_c1:.1f}%)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # C2: ACK SLA
        with c2:
            ack_total_samples = ack_filtered_df[sample_id_col].nunique() if sample_id_col in ack_filtered_df.columns else 0
            ack_under_2 = ack_filtered_df[ack_filtered_df['is_ack_2h']][sample_id_col].nunique() if sample_id_col in ack_filtered_df.columns else 0
            pct_c2 = (ack_under_2 / ack_total_samples * 100) if ack_total_samples > 0 else 0
            st.markdown(f"""
            <div class="kpi-card kpi-card-orange">
                <div class="kpi-header-row"><span class="kpi-title">02. ACK ≤ 2h SLA</span></div>
                <div class="kpi-value-row">
                    <span class="kpi-value">{ack_under_2:,}</span>
                    <span class="kpi-percentage">({pct_c2:.1f}%)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # C3: Active Staff
        with c3:
            active_staff = df[df[comm_by_col].notna()][comm_by_col].nunique() if comm_by_col in df.columns else 0
            st.markdown(f"""
            <div class="kpi-card kpi-card-grey">
                <div class="kpi-header-row"><span class="kpi-title">03. Active Team</span></div>
                <div class="kpi-value-row">
                    <span class="kpi-value">{active_staff}</span>
                    <span style="font-size:1.1rem; font-weight:600; color:#64748b;">Members</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # C4: Top Buyer
        with c4:
            top_buyer = df.groupby(buyer_col)[sample_id_col].nunique().idxmax() if (buyer_col in df.columns and not df.empty) else "N/A"
            st.markdown(f"""
            <div class="kpi-card kpi-card-grey">
                <div class="kpi-header-row"><span class="kpi-title">04. Top Buyer</span></div>
                <div class="kpi-value" style="font-size: 1.35rem; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">{top_buyer}</div>
            </div>
            """, unsafe_allow_html=True)

        # C5: Total ACK (No Time Barrier)
        with c5:
            if sample_id_col in ack_filtered_df.columns:
                total_eligible_samples = ack_filtered_df[sample_id_col].nunique()
                total_ack_count = ack_filtered_df[ack_filtered_df['has_ack']][sample_id_col].nunique()
                pct_ack_total = (total_ack_count / total_eligible_samples * 100) if total_eligible_samples > 0 else 0
            else:
                total_ack_count = 0
                pct_ack_total = 0
                
            st.markdown(f"""
            <div class="kpi-card kpi-card-orange">
                <div class="kpi-header-row"><span class="kpi-title">05. Total ACK (Overall)</span></div>
                <div class="kpi-value-row">
                    <span class="kpi-value">{total_ack_count:,}</span>
                    <span class="kpi-percentage">({pct_ack_total:.1f}%)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # C6: Unique Folders
        with c6:
            unique_folders = df[folder_id_col].nunique() if folder_id_col in df.columns else 0
            st.markdown(f"""
            <div class="kpi-card kpi-card-grey">
                <div class="kpi-header-row"><span class="kpi-title">06. Actioned Volume</span></div>
                <div class="kpi-value-row">
                    <span class="kpi-value">{unique_folders:,}</span>
                    <span style="font-size:1.1rem; font-weight:600; color:#64748b;">Folders</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # STAFF PERFORMANCE MATRIX
        st.markdown("<div class='section-title'>👤 Staff SLA Compliance & Output Matrix</div>", unsafe_allow_html=True)
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

            summary_matrix["Commit SLA %"] = (summary_matrix["Commit_3h"] / summary_matrix["Total_Folders"] * 100).round(1).astype(str) + "%"
            
            summary_matrix.columns = [
                "Person Name", "Total Folders Actioned", "Associated Buyer(s)", 
                "Folders Committed (≤ 3h)", "Folders Acknowledged (≤ 2h)", "Commit SLA %"
            ]
            
            ordered_cols = ["Person Name", "Associated Buyer(s)", "Total Folders Actioned", "Folders Committed (≤ 3h)", "Commit SLA %", "Folders Acknowledged (≤ 2h)"]
            st.dataframe(summary_matrix[ordered_cols], use_container_width=True, hide_index=True)

        # FINANCIAL REVENUE ANALYSIS
        st.markdown("<div class='section-title'>💰 Financial Charge & Revenue Segments</div>", unsafe_allow_html=True)

        if charges_col in finance_df.columns and folder_id_col in finance_df.columns:
            fin_cols = [folder_id_col, charges_col]
            if currency_col in finance_df.columns: fin_cols.append(currency_col)
            if ex_rate_col in finance_df.columns: fin_cols.append(ex_rate_col)

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
                <div class="kpi-card" style="border-left: 5px solid #ea580c;">
                    <div class="kpi-title">Total Revenue (USD)</div>
                    <div class="kpi-value" style="color:#ea580c;">${total_usd:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            with f2:
                st.markdown(f"""
                <div class="kpi-card" style="border-left: 5px solid #64748b;">
                    <div class="kpi-title">Total Revenue (BDT)</div>
                    <div class="kpi-value">৳{total_bdt:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

        # ACK & COMMITMENT SLA AUDIT LOG
        st.markdown("<div class='section-title'>📋 Acknowledgement & Commitment SLA Audit Log</div>", unsafe_allow_html=True)
        
        if folder_id_col in ack_filtered_df.columns:
            cols_needed = [folder_id_col]
            if buyer_col in ack_filtered_df.columns: cols_needed.append(buyer_col)
            if bill_client_col in ack_filtered_df.columns: cols_needed.append(bill_client_col)
            if ack_by_col in ack_filtered_df.columns: cols_needed.append(ack_by_col)
            if comm_by_col in ack_filtered_df.columns and comm_by_col not in cols_needed: cols_needed.append(comm_by_col)
            if 'ack_gap_hours' in ack_filtered_df.columns: cols_needed.append('ack_gap_hours')
            if 'commit_gap_hours' in ack_filtered_df.columns: cols_needed.append('commit_gap_hours')
            if ack_date_col in ack_filtered_df.columns: cols_needed.append(ack_date_col)

            ack_status_df = ack_filtered_df[cols_needed].drop_duplicates(subset=[folder_id_col]).copy()

            # Person resolution
            if ack_by_col in ack_status_df.columns and comm_by_col in ack_status_df.columns:
                ack_status_df['Concern Person'] = ack_status_df[ack_by_col].fillna(ack_status_df[comm_by_col]).fillna("Unassigned")
            elif ack_by_col in ack_status_df.columns:
                ack_status_df['Concern Person'] = ack_status_df[ack_by_col].fillna("Unassigned")
            elif comm_by_col in ack_status_df.columns:
                ack_status_df['Concern Person'] = ack_status_df[comm_by_col].fillna("Unassigned")
            else:
                ack_status_df['Concern Person'] = "Unassigned"

            is_missing = ack_status_df[ack_date_col].isna() if ack_date_col in ack_status_df.columns else pd.Series(False, index=ack_status_df.index)
            is_under_2 = (ack_status_df['ack_gap_hours'] <= 2.0) & (~is_missing)
            is_commit_under_3 = ack_status_df['commit_gap_hours'] <= 3.0 if 'commit_gap_hours' in ack_status_df.columns else pd.Series(False, index=ack_status_df.index)

            ack_status_df['ACK < 2 hours'] = np.where(is_under_2, "Yes", "No")
            ack_status_df['Commit < 3 hours'] = np.where(is_commit_under_3, "Yes", "No")
            ack_status_df['ACK Missing'] = np.where(is_missing, "Yes", "No")

            display_cols = [folder_id_col]
            if buyer_col in ack_status_df.columns: display_cols.append(buyer_col)
            if bill_client_col in ack_status_df.columns: display_cols.append(bill_client_col)
            display_cols.extend(['Concern Person', 'ACK < 2 hours', 'Commit < 3 hours', 'ACK Missing'])

            final_table = ack_status_df[display_cols].copy()

            # Summary badges directly above the table for immediate clarity
            c_ack_ok = (final_table['ACK < 2 hours'] == 'Yes').sum()
            c_com_ok = (final_table['Commit < 3 hours'] == 'Yes').sum()
            c_missing = (final_table['ACK Missing'] == 'Yes').sum()

            st.markdown(f"""
                <div>
                    <span class="mini-pill pill-green">✓ ACK ≤ 2h: <b>{c_ack_ok:,}</b></span>
                    <span class="mini-pill pill-orange">✓ Commit ≤ 3h: <b>{c_com_ok:,}</b></span>
                    <span class="mini-pill pill-slate">⚠ Missing ACK: <b>{c_missing:,}</b></span>
                </div>
            """, unsafe_allow_html=True)

            # Highlighting logic: Distinct & readable cell stylings
            def highlight_status_cells(val):
                if val == 'Yes':
                    return 'background-color: rgba(34, 197, 94, 0.18); color: #15803d; font-weight: 700;'
                elif val == 'No':
                    return 'background-color: rgba(100, 116, 139, 0.08); color: #64748b; font-weight: 500;'
                return ''

            def highlight_missing_ack(val):
                if val == 'Yes':
                    return 'background-color: rgba(234, 88, 12, 0.18); color: #c2410c; font-weight: 700;'
                elif val == 'No':
                    return 'color: #64748b;'
                return ''

            if not final_table.empty:
                styled_df = final_table.style\
                    .map(highlight_status_cells, subset=['ACK < 2 hours', 'Commit < 3 hours'])\
                    .map(highlight_missing_ack, subset=['ACK Missing'])
                
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            else:
                st.info("No records to display.")

    render_dashboard(df_active_view, selected_date_card)

else:
    st.info("👋 Upload your operational data file above to generate the executive dashboard.")
