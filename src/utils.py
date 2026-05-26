import streamlit as st
import gspread
from google.oauth2.service_account import Credentials


# ─────────────────────────────────────────────
# Google Sheets helpers
# ─────────────────────────────────────────────

def get_gsheet_conn():
    creds_dict = {
        "type":           st.secrets["connections"]["gsheets"]["type"],
        "project_id":     st.secrets["connections"]["gsheets"]["project_id"],
        "private_key_id": st.secrets["connections"]["gsheets"]["private_key_id"],
        "private_key":    st.secrets["connections"]["gsheets"]["private_key"],
        "client_email":   st.secrets["connections"]["gsheets"]["client_email"],
        "client_id":      st.secrets["connections"]["gsheets"]["client_id"],
        "auth_uri":       st.secrets["connections"]["gsheets"]["auth_uri"],
        "token_uri":      st.secrets["connections"]["gsheets"]["token_uri"],
    }
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)


def connect_gsheet():
    try:
        client = get_gsheet_conn()
        spreadsheet = client.open_by_key(
            st.secrets["connections"]["gsheets"]["spreadsheet_id"]
        )
        print("Connection successful...!!!")
        return spreadsheet
    except Exception as e:
        print(f"Unable to connect google sheet: {e}")
        show_popup(f"Unable to connect google sheet: {e}", type="error")


def show_popup(message, type="success"):
    icons = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
    st.toast(f"{icons.get(type, '')} {message}")