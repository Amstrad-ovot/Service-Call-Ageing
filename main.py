import io
import sys
import time
import pytz
import pandas as pd
import streamlit as st
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import gspread

from src.utils import connect_gsheet, show_popup



# ─────────────────────────────────────────────
# STATUS COLUMNS
# ─────────────────────────────────────────────

STATUS_COLS = [
    "status_updated_date", "call_date", "work_allocated", "work_initiated",
    "work_in_progress", "part_pending", "part_declared_not_available",
    "part_not_available_in_stores", "to_be_rejected", "sit_wh_to_asp",
    "sit_masp_to_se", "ran_c_proposed", "ran_d_proposed", "ran_c_reapply",
    "ran_d_reapply", "ran_c_approved", "ran_d_approved", "ran_c_cn_due",
    "ran_d_cn_due", "ran_c_repair_due", "part_delivered", "complete_date",
]

# ─────────────────────────────────────────────
# Save prepared data → "working_data" sheet
# ─────────────────────────────────────────────

def save_working_data(data: pd.DataFrame) -> bool:

    if data.empty:
        show_popup("No data to save — DataFrame is empty.", type="warning")
        return False

    try:
        spreadsheet = connect_gsheet()

        # ── Get or create the worksheet ───────────────────────────────────
        try:
            worksheet = spreadsheet.worksheet("working_data")
            print("Worksheet 'working_data' found.")

            # Sheet exists → wipe all existing content first
            worksheet.clear()
            print("Existing data cleared from 'working_data'.")

        except gspread.exceptions.WorksheetNotFound:
            # Sheet doesn't exist → create it fresh
            worksheet = spreadsheet.add_worksheet(
                title="working_data",
                rows=len(data) + 10,
                cols=len(data.columns) + 5,
            )
            print("Created new worksheet: 'working_data'.")

        # ── Convert Timestamps → strings ──────────────────────────────────
        export_df = data.copy()
        for col in export_df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
            export_df[col] = export_df[col].dt.strftime("%Y-%m-%d").fillna("")

        # Fill remaining NaN / NaT with empty string
        export_df = export_df.fillna("")

        # ── Write header + rows ───────────────────────────────────────────
        worksheet.update(
            [export_df.columns.tolist()] + export_df.values.tolist(),
            value_input_option="USER_ENTERED",
        )

        print(f"Saved {len(export_df)} rows × {len(export_df.columns)} cols → 'working_data'")
        show_popup(f"Working data saved successfully ({len(export_df):,} rows).", type="success")
        return True

    except Exception as e:
        print(f"Error in save_working_data: {e}")
        show_popup(f"Failed to save working data: {e}", type="error")
        return False
    

def prepare_data(open_call_data: pd.DataFrame,
                 completed_call_data: pd.DataFrame,
                 save_to_sheet: bool = True) -> pd.DataFrame: 
    try:
        data = pd.concat([open_call_data, completed_call_data], ignore_index=True)

        data.columns = (
            data.columns
            .str.lower()
            .str.replace(" ", "_")
            .str.replace(".", "_")
            .str.strip()
        )
        print("Concatenated data shape:", data.shape)

        data["phone1"] = "'" + data["phone1"].fillna("").astype(str)
        data["provider_phone1"] = "'" + data["provider_phone1"].fillna("").astype(str)


        present_date_cols = [c for c in STATUS_COLS if c in data.columns]
        for col in present_date_cols:
            data[col] = pd.to_datetime(data[col], errors="coerce").dt.normalize()

        today = pd.Timestamp("today").normalize()
        print("Todays date is:", today)
        today = pd.to_datetime('today').date()
        data["today_date"] = pd.to_datetime(today)
        data = data[data["call_date"] != today].reset_index(drop=True)

        # ── Save to Google Sheet ────
        if save_to_sheet:
            save_working_data(data)

        return data

    except Exception as e:
        print(f"Error in prepare_data: {e}")
        return pd.DataFrame()

def calculate_ageing(data: pd.DataFrame,
                     from_status: str = "call_date",
                     to_status: str = "complete_date") -> pd.DataFrame:
    
    if data.empty:
        print("calculate_ageing received an empty DataFrame — skipping.")
        return data

    try:
        # 1. Consecutive-status ageing
        for col1, col2 in zip(STATUS_COLS[1:], STATUS_COLS[2:]):
            if col1 in data.columns and col2 in data.columns:
                data[f"age_betn_{col1}_and_{col2}"] = (
                    data[col2] - data[col1]
                ).dt.days.abs()

        # 2. Custom (user-selected) ageing
        if from_status in data.columns and to_status in data.columns:
            data[f"age_betn_{from_status}_and_{to_status}"] = (
                data[to_status] - data[from_status]
            ).dt.days.abs()
        else:
            missing = [c for c in (from_status, to_status) if c not in data.columns]
            print(f"calculate_ageing: columns not found → {missing}")
            data[f"age_{from_status}_to_{to_status}"] = None

        return data

    except Exception as e:
        print(f"Error in calculate_ageing: {e}")
        return data


def func1(open_call_data: pd.DataFrame,
          completed_call_data: pd.DataFrame,
          from_status: str = "call_date",
          to_status: str = "complete_date") -> pd.DataFrame:

    data = prepare_data(open_call_data, completed_call_data)
    # data = calculate_ageing(data, from_status=from_status, to_status=to_status)
    return data

