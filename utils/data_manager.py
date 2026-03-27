# utils/data_manager.py
# ─────────────────────────────────────────────
#  Gestión de datos: lectura / escritura JSON
# ─────────────────────────────────────────────

from __future__ import annotations
import json
import os
from datetime import datetime, timedelta
from copy import deepcopy
from typing import Optional
from utils.constants import ACTIVITIES_TEMPLATE, USERS

DATA_FILE = os.path.join("data", "orders.json")


# ── Helpers de fecha ────────────────────────────────────────────────────────

def today_str() -> str:
    return datetime.today().strftime("%Y-%m-%d")


def parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def add_business_days(start: datetime, days: int) -> datetime:
    """Suma `days` días hábiles a `start` (omite sábado/domingo)."""
    d = start
    added = 0
    while added < days:
        d += timedelta(days=1)
        if d.weekday() < 5:  # lunes-viernes
            added += 1
    return d


# ── Semáforo ─────────────────────────────────────────────────────────────────

def get_semaphore(activity: dict) -> str:
    """
    Verde  → completada O sin iniciar (pendiente)
    Amarillo → entre 70 % y 100 % del plazo consumido
    Rojo   → vencida (> 100 %)
    """
    status = activity.get("status", "pending")
    if status == "completed":
        return "green"
    if status in ("pending", "blocked"):
        return "gray"

    start_raw = activity.get("start_date")
    due_raw   = activity.get("due_date")
    if not start_raw or not due_raw:
        return "gray"

    start = parse_date(start_raw)
    due   = parse_date(due_raw)
    today = datetime.today()
    total_days = max((due - start).days, 1)
    elapsed    = (today - start).days

    ratio = elapsed / total_days
    if ratio < 0.70:
        return "green"
    elif ratio < 1.0:
        return "yellow"
    else:
        return "red"


# ── Carga / Guardado ────────────────────────────────────────────────────────

def _ensure_data_dir() -> None:
    os.makedirs("data", exist_ok=True)


def _local_load() -> dict:
    """Lee datos desde archivo JSON local (desarrollo)."""
    _ensure_data_dir()
    if not os.path.exists(DATA_FILE):
        seed = {"orders": [], "last_order_seq": 0}
        _local_write(seed)
        return seed
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _local_write(data: dict) -> None:
    """Escribe datos al archivo JSON local."""
    _ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_data() -> dict:
    """Carga datos: Google Sheets si disponible, sino JSON local."""
    try:
        from utils.sheets_manager import _gsheets_available, load_from_sheets
        if _gsheets_available():
            return load_from_sheets()
    except Exception as e:
        print(f"[LOAD_DATA fallback] {e}")
    return _local_load()


def save_data(data: dict) -> None:
    """Guarda datos: Google Sheets si disponible, sino JSON local."""
    try:
        from utils.sheets_manager import _gsheets_available, save_to_sheets
        if _gsheets_available():
            ok = save_to_sheets(data)
            if ok:
                return
    except Exception as e:
        print(f"[SAVE_DATA fallback] {e}")
    _local_write(data)


# ── Creación de pedido ────────────────────────────────────────────────────────

def create_order(
    data: dict,
    motor_model: str,
    quantity: int,
    supplier: str,
    notes: str,
    created_by: str,
    year: Optional[int] = None,
) -> tuple[bool, str, dict | None]:
    """
    Regresa (ok, mensaje, orden_creada).
    Rechaza si ya se alcanzó el máximo de 20 pedidos anuales.
    """
    from utils.constants import MAX_ANNUAL_ORDERS
    year = year or datetime.today().year
    annual = [
        o for o in data["orders"]
        if o.get("year") == year and o.get("status") != "cancelled"
    ]
    if len(annual) >= MAX_ANNUAL_ORDERS:
        return False, f"Límite de {MAX_ANNUAL_ORDERS} pedidos anuales alcanzado para {year}.", None

    seq = data.get("last_order_seq", 0) + 1
    order_number = f"IMEMSA-YAM-{year}-{seq:03d}"

    # Construir lista de actividades a partir de la plantilla
    activities: list[dict] = []
    for tmpl in ACTIVITIES_TEMPLATE:
        act = deepcopy(tmpl)
        act["status"]     = "pending"
        act["start_date"] = None
        act["due_date"]   = None
        act["completion_date"] = None
        act["evidence_name"]   = None
        act["evidence_data"]   = None  # base64
        act["notes"]           = ""
        act["closure_requested_by"] = None
        act["closure_requested_at"] = None
        activities.append(act)

    # Activar la primera actividad
    _activate_activity(activities, 0)

    order: dict = {
        "id":           seq,
        "order_number": order_number,
        "year":         year,
        "motor_model":  motor_model,
        "quantity":     quantity,
        "supplier":     supplier,
        "notes":        notes,
        "created_by":   created_by,
        "created_at":   today_str(),
        "status":       "active",
        "activities":   activities,
        "progress":     0,
    }
    order["progress"] = _calc_progress(activities)

    data["orders"].append(order)
    data["last_order_seq"] = seq
    save_data(data)
    return True, f"Pedido {order_number} creado exitosamente.", order


def _activate_activity(activities: list[dict], idx: int) -> None:
    """Marca la actividad en `idx` como 'in_progress' y calcula fechas."""
    if idx >= len(activities):
        return
    act = activities[idx]
    if act["status"] == "pending":
        start = datetime.today()
        act["status"]     = "in_progress"
        act["start_date"] = start.strftime("%Y-%m-%d")
        act["due_date"]   = add_business_days(start, act["days_allocated"]).strftime("%Y-%m-%d")


def _calc_progress(activities: list[dict]) -> int:
    completed = sum(1 for a in activities if a["status"] == "completed")
    return round((completed / len(activities)) * 100)


# ── Solicitar cierre de actividad ────────────────────────────────────────────

def request_closure(
    data: dict,
    order_id: int,
    activity_id: int,
    requested_by: str,
    evidence_name: Optional[str],
    evidence_data: Optional[str],  # base64 string
    notes: str = "",
) -> tuple[bool, str]:
    order = _find_order(data, order_id)
    if not order:
        return False, "Pedido no encontrado."
    act = _find_activity(order, activity_id)
    if not act:
        return False, "Actividad no encontrada."
    if act["status"] == "completed":
        return False, "Esta actividad ya fue completada."
    if act["status"] != "in_progress":
        return False, "La actividad no está en proceso."

    act["status"]                 = "waiting_closure"
    act["evidence_name"]          = evidence_name
    act["evidence_data"]          = evidence_data
    act["notes"]                  = notes
    act["closure_requested_by"]   = requested_by
    act["closure_requested_at"]   = today_str()
    order["progress"]             = _calc_progress(order["activities"])
    save_data(data)
    return True, "Solicitud de cierre enviada. La actividad se marcará como completada al 100 %."


# ── Aprobar cierre (automático al solicitar) ─────────────────────────────────

def approve_closure(
    data: dict,
    order_id: int,
    activity_id: int,
) -> tuple[bool, str, list[dict]]:
    """
    Cierra la actividad y activa la siguiente.
    Regresa (ok, mensaje, actividades_con_alertas_email).
    """
    order = _find_order(data, order_id)
    if not order:
        return False, "Pedido no encontrado.", []
    act = _find_activity(order, activity_id)
    if not act:
        return False, "Actividad no encontrada.", []

    act["status"]           = "completed"
    act["completion_date"]  = today_str()

    # Activar la siguiente actividad pendiente
    alerts: list[dict] = []
    acts = order["activities"]
    current_idx = next((i for i, a in enumerate(acts) if a["id"] == activity_id), -1)
    next_idx = current_idx + 1
    if next_idx < len(acts):
        _activate_activity(acts, next_idx)
        next_act = acts[next_idx]
        # Construir alerta para el responsable de la siguiente actividad
        responsible_key = next_act.get("responsible_key", "")
        user_info = USERS.get(responsible_key, {})
        alerts.append({
            "to_email": user_info.get("email", ""),
            "to_name":  user_info.get("name", ""),
            "order_number": order["order_number"],
            "activity_name": next_act["name"],
            "due_date": next_act.get("due_date", ""),
        })
    else:
        # Última actividad completada → cerrar pedido
        order["status"] = "completed"

    order["progress"] = _calc_progress(acts)
    save_data(data)
    return True, "Actividad cerrada y siguiente actividad activada.", alerts


# ── Consultas ────────────────────────────────────────────────────────────────

def get_orders_for_user(data: dict, username: str) -> list[dict]:
    """Regresa todos los pedidos activos (todos los usuarios pueden ver todos)."""
    return [o for o in data["orders"] if o.get("status") != "cancelled"]


def get_my_pending_activities(data: dict, username: str) -> list[dict]:
    """Actividades 'in_progress' o 'waiting_closure' del usuario actual."""
    results = []
    for order in data["orders"]:
        if order.get("status") == "cancelled":
            continue
        for act in order.get("activities", []):
            if act.get("responsible_key") == username and act.get("status") in (
                "in_progress", "waiting_closure"
            ):
                results.append({**act, "_order_number": order["order_number"], "_order_id": order["id"]})
    return results


def get_semaphore_summary(data: dict) -> dict:
    """Cuenta semáforos en pedidos activos."""
    counts = {"green": 0, "yellow": 0, "red": 0, "gray": 0}
    for order in data["orders"]:
        if order.get("status") != "active":
            continue
        for act in order.get("activities", []):
            color = get_semaphore(act)
            counts[color] = counts.get(color, 0) + 1
    return counts


def get_red_activities(data: dict) -> list[dict]:
    """Devuelve actividades vencidas con datos de pedido para envío de correos."""
    results = []
    for order in data["orders"]:
        if order.get("status") != "active":
            continue
        for act in order.get("activities", []):
            if get_semaphore(act) == "red":
                responsible_key = act.get("responsible_key", "")
                user_info = USERS.get(responsible_key, {})
                results.append({
                    **act,
                    "_order_number": order["order_number"],
                    "_order_id": order["id"],
                    "_responsible_email": user_info.get("email", ""),
                    "_responsible_name":  user_info.get("name", ""),
                })
    return results


# ── Utilidades privadas ───────────────────────────────────────────────────────

def _find_order(data: dict, order_id: int) -> Optional[dict]:
    return next((o for o in data["orders"] if o["id"] == order_id), None)


def _find_activity(order: dict, activity_id: int) -> Optional[dict]:
    return next((a for a in order["activities"] if a["id"] == activity_id), None)
