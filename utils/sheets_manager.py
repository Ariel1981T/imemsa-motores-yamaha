# utils/sheets_manager.py  v2.0
# ────────────────────────────────────────────────────────────
#  Persistencia en Google Sheets — formato v2
#
#  Formato v1 (anterior): todo el JSON en una sola celda A1
#  Formato v2 (nuevo):    metadata en A1, un pedido por fila
#
#  Estructura:
#    Fila A1  → {"version":2, "last_order_seq":N, ...}
#    Fila A2  → JSON completo del pedido 1
#    Fila A3  → JSON completo del pedido 2
#    ...
#
#  Capacidad: ~8,500 chars por pedido << límite de 50,000 por celda
#  Pedidos soportados: ilimitados en la práctica
# ────────────────────────────────────────────────────────────

from __future__ import annotations
import json


# ── Detección dinámica ────────────────────────────────────────────────────────
def _gsheets_available() -> bool:
    try:
        import gspread                                              # noqa: F401
        import streamlit as st
        from google.oauth2.service_account import Credentials      # noqa: F401
        _ = st.secrets["gcp_service_account"]["client_email"]
        _ = st.secrets["gsheets"]["spreadsheet_id"]
        return True
    except Exception:
        return False


# ── Cliente gspread ───────────────────────────────────────────────────────────
def _get_client():
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
    import streamlit as st
    client = _get_client()
    spreadsheet_id = st.secrets["gsheets"]["spreadsheet_id"]
    sh = client.open_by_key(spreadsheet_id)
    try:
        ws = sh.worksheet("orders_data")
    except Exception:
        # Crear hoja nueva con metadata v2 inicial
        ws = sh.add_worksheet(title="orders_data", rows=200, cols=2)
        meta = json.dumps({
            "version": 2,
            "last_order_seq": 0,
            "total_orders": 0,
        })
        ws.update(range_name="A1", values=[[meta]])
    return ws


# ── Detectar formato ──────────────────────────────────────────────────────────
def _is_v2(raw_a1: str) -> bool:
    """Devuelve True si la celda A1 contiene metadata v2."""
    try:
        obj = json.loads(raw_a1)
        return obj.get("version") == 2
    except Exception:
        return False


# ── API pública ───────────────────────────────────────────────────────────────

def load_from_sheets() -> dict:
    """
    Lee los datos desde Google Sheets.
    Soporta ambos formatos: v1 (todo en A1) y v2 (un pedido por fila).
    """
    try:
        ws      = _get_worksheet()
        raw_a1  = ws.acell("A1").value or ""

        if not raw_a1.strip():
            return {"orders": [], "last_order_seq": 0}

        # ── Formato v1: todo el JSON en A1 (compatibilidad) ──────────────────
        if not _is_v2(raw_a1):
            print("[SHEETS v1] Leyendo formato legacy (todo en A1)")
            return json.loads(raw_a1)

        # ── Formato v2: metadata en A1, pedidos en filas ─────────────────────
        meta        = json.loads(raw_a1)
        seq         = meta.get("last_order_seq", 0)
        total       = meta.get("total_orders", 0)

        if total == 0:
            return {"orders": [], "last_order_seq": seq}

        # Leer todas las filas de pedidos de una sola llamada (eficiente)
        last_row    = total + 1          # fila 2 a fila (total+1)
        all_values  = ws.col_values(1)   # columna A completa

        orders = []
        for i in range(1, total + 1):    # índice 0 = A1 (metadata)
            if i < len(all_values) and all_values[i]:
                try:
                    order = json.loads(all_values[i])
                    orders.append(order)
                except Exception as e:
                    print(f"[SHEETS READ] Error en fila {i+1}: {e}")

        print(f"[SHEETS v2] {len(orders)} pedidos leídos")
        return {"orders": orders, "last_order_seq": seq}

    except Exception as e:
        print(f"[SHEETS READ ERROR] {e}")
        return {"orders": [], "last_order_seq": 0}


def _strip_evidence(data: dict) -> dict:
    """Elimina binarios base64 antes de guardar (conserva solo el nombre)."""
    import copy
    clean = copy.deepcopy(data)
    for order in clean.get("orders", []):
        for act in order.get("activities", []):
            if act.get("evidence_data"):
                act["evidence_data"] = None
            if act.get("ev_data"):
                act["ev_data"] = None
    return clean


def save_to_sheets(data: dict) -> bool:
    """
    Guarda los datos en Google Sheets en formato v2 (un pedido por fila).
    Si la hoja todavía está en v1, hace la migración automática al guardar.
    """
    try:
        ws      = _get_worksheet()
        raw_a1  = ws.acell("A1").value or ""
        clean   = _strip_evidence(data)
        orders  = clean.get("orders", [])
        seq     = clean.get("last_order_seq", len(orders))

        # ── Si sigue en v1, migrar automáticamente ────────────────────────────
        if not _is_v2(raw_a1):
            print("[SHEETS] Detectado formato v1 — migrando a v2 automáticamente...")

        # ── Escribir metadata en A1 ───────────────────────────────────────────
        meta = json.dumps({
            "version":        2,
            "last_order_seq": seq,
            "total_orders":   len(orders),
        }, ensure_ascii=False)

        # ── Preparar batch: A1=meta, A2...AN=pedidos ──────────────────────────
        batch_values = [[meta]]
        for order in orders:
            payload = json.dumps(order, ensure_ascii=False)
            batch_values.append([payload])
            print(f"  [v2] {order.get('order_number','?')} → {len(payload)} chars")

        # ── Limpiar filas extra si hay menos pedidos que antes ────────────────
        current_rows = ws.row_count
        needed_rows  = len(batch_values) + 10   # +10 de margen
        if current_rows < needed_rows:
            ws.add_rows(needed_rows - current_rows)

        # ── Escritura única en batch (una sola llamada a la API) ──────────────
        range_end = f"A{len(batch_values)}"
        ws.update(range_name=f"A1:{range_end}", values=batch_values)

        # ── Limpiar filas sobrantes (si se borraron pedidos) ──────────────────
        last_used_row = len(batch_values)
        total_rows    = ws.row_count
        if total_rows > last_used_row + 1:
            ws.batch_clear([f"A{last_used_row + 1}:A{total_rows}"])

        print(f"[SHEETS v2 WRITE OK] meta={len(meta)} chars | {len(orders)} pedidos")
        return True

    except Exception as e:
        print(f"[SHEETS WRITE ERROR] {e}")
        return False


# ── Referencia de tipo (no se usa en lógica) ──────────────────────────────────
USE_SHEETS: bool = False
