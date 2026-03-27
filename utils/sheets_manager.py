# utils/sheets_manager.py
# ────────────────────────────────────────────────────────────
#  Persistencia en Google Sheets para Streamlit Cloud
#  Estrategia: almacena TODO el JSON en una sola celda A1
#  de la hoja "orders_data" dentro del Spreadsheet indicado.
# ────────────────────────────────────────────────────────────

from __future__ import annotations
import json

# ── Detección dinámica (se evalúa en cada llamada, no al importar) ────────────
def _gsheets_available() -> bool:
    """
    Verifica en tiempo real si gspread y los secrets de GCP están disponibles.
    Se llama en cada operación para evitar el bug de evaluación temprana.
    """
    try:
        import gspread                      # noqa: F401
        import streamlit as st
        from google.oauth2.service_account import Credentials  # noqa: F401
        _ = st.secrets["gcp_service_account"]["client_email"]  # campo específico
        _ = st.secrets["gsheets"]["spreadsheet_id"]
        return True
    except Exception:
        return False


# ── Cliente gspread ───────────────────────────────────────────────────────────
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
        dict(st.secrets["gcp_service_account"]), scopes=scopes
    )
    return gspread.authorize(creds)


def _get_worksheet():
    """Abre (o crea) la hoja 'orders_data' dentro del spreadsheet configurado."""
    import streamlit as st

    client = _get_client()
    spreadsheet_id = st.secrets["gsheets"]["spreadsheet_id"]
    sh = client.open_by_key(spreadsheet_id)

    try:
        ws = sh.worksheet("orders_data")
    except Exception:
        ws = sh.add_worksheet(title="orders_data", rows=10, cols=2)
        ws.update("A1", json.dumps({"orders": [], "last_order_seq": 0}))
    return ws


# ── API pública ───────────────────────────────────────────────────────────────

def load_from_sheets() -> dict:
    """Lee el JSON completo desde la celda A1 de Google Sheets."""
    try:
        ws  = _get_worksheet()
        raw = ws.acell("A1").value or ""
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
        ws.update("A1", [[json.dumps(data, ensure_ascii=False)]])
        return True
    except Exception as e:
        print(f"[SHEETS WRITE ERROR] {e}")
        return False


# ── USE_SHEETS ya NO es variable de módulo — se evalúa dinámicamente ──────────
#  Cada función en data_manager llama _gsheets_available() en el momento
#  de ejecutarse, garantizando que los secrets ya estén cargados.
USE_SHEETS: bool = False   # solo como referencia de tipo; no se usa en lógica
