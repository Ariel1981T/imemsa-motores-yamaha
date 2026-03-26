# utils/sheets_manager.py
# ────────────────────────────────────────────────────────────
#  Persistencia en Google Sheets para Streamlit Cloud
#  Estrategia: almacena TODO el JSON en una sola celda A1
#  de la hoja "orders_data" dentro del Spreadsheet indicado.
#  Esto evita refactorizar data_manager.py — funciona como
#  un drop-in replacement de load_data() / save_data().
# ────────────────────────────────────────────────────────────

from __future__ import annotations
import json
import os
from typing import Any

# ── Detección de entorno ──────────────────────────────────────────────────────
def _gsheets_available() -> bool:
    """True si gspread está instalado y los secrets de GCP existen."""
    try:
        import gspread          # noqa: F401
        import streamlit as st  # noqa: F401
        _ = st.secrets["gcp_service_account"]
        return True
    except Exception:
        return False


# ── Cliente gspread (singleton en session_state) ──────────────────────────────
def _get_client():
    """Regresa cliente gspread autenticado con Service Account."""
    import gspread
    import streamlit as st
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    return gspread.authorize(creds)


def _get_worksheet():
    """Abre (o crea) la hoja 'orders_data' dentro del spreadsheet configurado."""
    import streamlit as st

    client = _get_client()
    spreadsheet_id = st.secrets["gsheets"]["spreadsheet_id"]
    sh = client.open_by_key(spreadsheet_id)

    # Buscar o crear la hoja
    try:
        ws = sh.worksheet("orders_data")
    except Exception:
        ws = sh.add_worksheet(title="orders_data", rows=10, cols=2)
        # Inicializar con estructura vacía
        ws.update("A1", json.dumps({"orders": [], "last_order_seq": 0}))
    return ws


# ── API pública ───────────────────────────────────────────────────────────────

def load_from_sheets() -> dict:
    """Lee el JSON completo desde la celda A1 de Google Sheets."""
    try:
        ws   = _get_worksheet()
        raw  = ws.acell("A1").value or ""
        if not raw.strip():
            return {"orders": [], "last_order_seq": 0}
        return json.loads(raw)
    except Exception as e:
        print(f"[SHEETS READ ERROR] {e}")
        return {"orders": [], "last_order_seq": 0}


def save_to_sheets(data: dict) -> bool:
    """Escribe el JSON completo en la celda A1 de Google Sheets."""
    try:
        ws = _get_worksheet()
        ws.update("A1", json.dumps(data, ensure_ascii=False))
        return True
    except Exception as e:
        print(f"[SHEETS WRITE ERROR] {e}")
        return False


# ── Wrapper transparente para data_manager ───────────────────────────────────
#  data_manager llama a estas funciones; aquí decidimos si usar
#  Google Sheets (nube) o JSON local (desarrollo).

USE_SHEETS = _gsheets_available()

def smart_load() -> dict:
    if USE_SHEETS:
        return load_from_sheets()
    # Fallback: JSON local
    from utils.data_manager import _local_load
    return _local_load()

def smart_save(data: dict) -> None:
    if USE_SHEETS:
        save_to_sheets(data)
    else:
        from utils.data_manager import _local_write
        _local_write(data)
