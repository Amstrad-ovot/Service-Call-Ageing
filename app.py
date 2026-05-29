import streamlit as st
import pandas as pd
from datetime import datetime

from main import func1, calculate_ageing, STATUS_COLS
from src.sidebar import render_sidebar
from src.utils import connect_gsheet, show_popup

st.set_page_config(page_title="Service Calls Ageing Calculator", layout="wide")

page = render_sidebar()


# ─────────────────────────────────────────────
# Helper — load working_data sheet (no cache)
# ─────────────────────────────────────────────

def load_working_data() -> pd.DataFrame:
    """Fetches 'working_data' sheet and returns a DataFrame."""
    try:
        spreadsheet = connect_gsheet()
        worksheet   = spreadsheet.worksheet("working_data")
        records     = worksheet.get_all_records()
        df = pd.DataFrame(records)
        print(f"Loaded working_data: {df.shape}")
        return df
    except Exception as e:
        show_popup(f"Failed to load working data: {e}", type="error")
        return pd.DataFrame()

def save_ageing_result(data: pd.DataFrame) -> bool:

    if data.empty:
        show_popup("No ageing data to save.", type="warning")
        return False
    try:
        spreadsheet = connect_gsheet()

        try:
            worksheet = spreadsheet.worksheet("ageing")
            worksheet.clear()
            print("Cleared existing 'ageing' sheet.")
        except Exception:
            worksheet = spreadsheet.add_worksheet(
                title="ageing",
                rows=len(data) + 10,
                cols=len(data.columns) + 5,
            )
            print("Created new 'ageing' sheet.")

        # Convert date columns → strings
        export_df = data.copy()
        for col in export_df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
            export_df[col] = export_df[col].dt.strftime("%Y-%m-%d").fillna("")
        export_df = export_df.fillna("")

        worksheet.update(
            [export_df.columns.tolist()] + export_df.values.tolist(),
            value_input_option="USER_ENTERED",
        )
        print(f"Saved {len(export_df)} rows × {len(export_df.columns)} cols → 'ageing'")
        show_popup(f"Ageing result saved to sheet ({len(export_df):,} rows).", type="success")
        return True

    except Exception as e:
        print(f"Error in save_ageing_result: {e}")
        show_popup(f"Failed to save ageing result: {e}", type="error")
        return False
    
# ═════════════════════════════════════════════
# PAGE — Upload & Create Report
# ═════════════════════════════════════════════
if page == "upload":
    st.header("📤 Upload File & Create Report")

    uploaded_raw_file    = st.file_uploader("Choose the Open Calls Excel file",     type=["xlsx"])
    completed_calls_file = st.file_uploader("Choose the Completed Calls Excel file", type=["xlsx"])

    if uploaded_raw_file is not None or completed_calls_file is not None:
        if st.button("Generate Report"):
            with st.spinner("Processing data and pushing to Database..."):
                try:
                    # Read whichever files were uploaded, use empty DF as fallback
                    open_call_data = pd.read_excel(uploaded_raw_file) if uploaded_raw_file is not None else pd.DataFrame()
                    cc_data = pd.read_excel(completed_calls_file) if completed_calls_file is not None else pd.DataFrame()

                    final_df = func1(open_call_data, cc_data)

                    if isinstance(final_df, pd.DataFrame) and not final_df.empty:
                        st.success("✅ Report Generated Successfully!")
                        st.dataframe(final_df, use_container_width=True)

                        # Clear stale working data so next visit fetches fresh
                        st.session_state.pop("working_df", None)
                        st.session_state.pop("working_df_loaded_at", None)

                except Exception as e:
                    st.error(f"Error during processing: {e}")
    else:
        st.warning("⚠️ Please upload at least one file to proceed.")
    st.divider()


# ═════════════════════════════════════════════
# PAGE — Calculate Ageing
# ═════════════════════════════════════════════

elif page == "calculate_ageing":
    st.header("📊 Calculate Ageing")

    ctrl_col, info_col = st.columns([1, 3])
    with ctrl_col:
        refresh_clicked = st.button("🔄 Refresh Data", type="secondary")

    if refresh_clicked or "working_df" not in st.session_state:
        with st.spinner("Fetching data from Database..."):
            st.session_state["working_df"] = load_working_data()
            st.session_state["working_df_loaded_at"] = datetime.now().strftime("%d %b %Y, %H:%M:%S")
        # Clear previous result when data is refreshed
        st.session_state.pop("ageing_result", None)

    working_df = st.session_state["working_df"]

    with info_col:
        if "working_df_loaded_at" in st.session_state:
            st.caption(f"🕒 Last loaded: {st.session_state['working_df_loaded_at']}  |  "
                       f"📦 {len(working_df):,} rows")

    if working_df.empty:
        st.warning("⚠️ No working data found. Please upload files and generate a report first.")
        st.stop()

    working_df.columns = (
        working_df.columns.str.lower().str.replace(" ", "_")
        .str.replace(".", "_").str.strip()
    )
    for col in [c for c in STATUS_COLS if c in working_df.columns]:
        working_df[col] = pd.to_datetime(working_df[col], errors="coerce").dt.normalize()

    # ── Filters ───────────────────────────────────────────────────────────
    st.subheader("🔍 Filter & Select")
    col1, col2 = st.columns(2)

    with col1:
        service_id_col = next((c for c in working_df.columns if "service" in c and "id" in c), None)
        if service_id_col:
            service_ids = ["All"] + sorted(working_df[service_id_col].dropna().unique().tolist())
            selected_service_id = st.selectbox("🔖 Service ID", options=service_ids)
        else:
            st.warning("'Service ID' column not found.")
            selected_service_id = "All"

    with col2:
        circle_col = next((c for c in working_df.columns if c == "circle"), None)
        if circle_col:
            circles = ["All"] + sorted(working_df[circle_col].dropna().unique().tolist())
            selected_circle = st.selectbox("🌐 Circle", options=circles)
        else:
            st.warning("'Circle' column not found.")
            selected_circle = "All"

    st.divider()

    # ── Multi-pair status selector ────────────────────────────────────────
    st.subheader("⏱ Status Pairs")
    st.caption("Add one or more From → To pairs. Ageing will be calculated for each.")

    available_status_cols = [c for c in STATUS_COLS[1:] if c in working_df.columns]

    if "ageing_pairs" not in st.session_state:
        st.session_state["ageing_pairs"] = [
            {"from": available_status_cols[0], "to": available_status_cols[-1]}
        ]

    pairs = st.session_state["ageing_pairs"]
    to_delete = None

    for i, pair in enumerate(pairs):
        c1, c2, c3, c4 = st.columns([3, 0.3, 3, 0.5])
        with c1:
            from_idx = available_status_cols.index(pair["from"]) if pair["from"] in available_status_cols else 0
            pairs[i]["from"] = st.selectbox(
                f"From Status #{i+1}", options=available_status_cols,
                index=from_idx, key=f"from_{i}"
            )
        with c2:
            st.markdown("<div style='padding-top:28px; text-align:center'>→</div>", unsafe_allow_html=True)
        with c3:
            to_opts = [c for c in available_status_cols if c != pairs[i]["from"]]
            to_idx  = to_opts.index(pair["to"]) if pair["to"] in to_opts else len(to_opts) - 1
            pairs[i]["to"] = st.selectbox(
                f"To Status #{i+1}", options=to_opts,
                index=to_idx, key=f"to_{i}"
            )
        with c4:
            st.markdown("<div style='padding-top:24px'>", unsafe_allow_html=True)
            if len(pairs) > 1 and st.button("✕", key=f"del_{i}", help="Remove this pair"):
                to_delete = i
            st.markdown("</div>", unsafe_allow_html=True)

    if to_delete is not None:
        st.session_state["ageing_pairs"].pop(to_delete)
        st.session_state.pop("ageing_result", None)   # clear stale result
        st.rerun()

    if st.button("➕ Add another pair"):
        st.session_state["ageing_pairs"].append({
            "from": available_status_cols[0],
            "to":   available_status_cols[-1],
        })
        st.rerun()

    st.divider()

    # ── Calculate button ──────────────────────────────────────────────────
    if st.button("Calculate Ageing", type="primary"):

        filtered_df = working_df.copy()

        if selected_service_id != "All" and service_id_col:
            filtered_df = filtered_df[filtered_df[service_id_col] == selected_service_id]
        if selected_circle != "All" and circle_col:
            filtered_df = filtered_df[filtered_df[circle_col] == selected_circle]

        if filtered_df.empty:
            st.warning("⚠️ No records match the selected filters.")
            st.stop()

        with st.spinner("Calculating ageing..."):
            result_df = calculate_ageing(
                filtered_df.copy(),
                from_status=st.session_state["ageing_pairs"][0]["from"],
                to_status=st.session_state["ageing_pairs"][0]["to"],
            )
            for pair in st.session_state["ageing_pairs"][1:]:
                col_name = f"age_betn_{pair['from']}_and_{pair['to']}"
                if col_name not in result_df.columns:
                    result_df = calculate_ageing(
                        result_df,
                        from_status=pair["from"],
                        to_status=pair["to"],
                    )

        DISPLAY_COLS = [
            "service_id", "customer_name", "phone1", "circle", "city",
            "company_name", "provider_phone1", "call_date", "status_code",
        ]
        base_cols    = [c for c in DISPLAY_COLS if c in result_df.columns]
        all_age_cols = [c for c in result_df.columns if c.startswith("age_betn_")]
        result_display = result_df[base_cols + all_age_cols]
        result_display['service_id'] = result_display['service_id'].apply(lambda x: f"{x:.0f}")

        # ── Persist result in session_state so reruns don't wipe it ──────
        st.session_state["ageing_result"]      = result_display
        st.session_state["ageing_result_cols"] = all_age_cols

        # ── Save to Google Sheet ──────────────────────────────────────────
        save_ageing_result(result_display)

    # ═══════════════════════════════════════════════════════════════════════
    # Render result — OUTSIDE the button block so it survives reruns
    # ═══════════════════════════════════════════════════════════════════════
    if "ageing_result" in st.session_state:
        result_display = st.session_state["ageing_result"]
        all_age_cols   = st.session_state["ageing_result_cols"]

        st.success(
            f"✅ Ageing calculated for {len(result_display):,} records — "
            f"{len(all_age_cols)} ageing column(s)."
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Records", f"{len(result_display):,}")
        if all_age_cols and result_display[all_age_cols[0]].notna().any():
            m2.metric("Avg Ageing (days)", f"{result_display[all_age_cols[0]].mean():.1f}")
            m3.metric("Max Ageing (days)", f"{result_display[all_age_cols[0]].max():.0f}")

        # st.dataframe(result_display, use_container_width=True)
        
        csv = result_display.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Download Result as CSV",
            data=csv,
            file_name=f"ageing_result_{datetime.today().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            )
        st.dataframe(result_display, use_container_width=True)
