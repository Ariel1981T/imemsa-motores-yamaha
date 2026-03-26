# app.py  ─  IMEMSA · Sistema de Compra de Motores Yamaha
# ══════════════════════════════════════════════════════════
# Ejecutar:  streamlit run app.py
# ══════════════════════════════════════════════════════════

from __future__ import annotations
import base64
import os
from datetime import datetime

import streamlit as st

# ── Configuración inicial de página (debe ser la primera llamada st.*) ───────
st.set_page_config(
    page_title="IMEMSA · Motores Yamaha",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.auth         import verify_login
from utils.constants    import (USERS, ACTIVITIES_TEMPLATE, PHASES,
                                MOTOR_MODELS, STATUS_LABELS,
                                ORDER_STATUS_LABELS, MAX_ANNUAL_ORDERS,
                                IMEMSA_NAVY, IMEMSA_RED)
from utils.data_manager import (load_data, save_data, create_order,
                                request_closure, approve_closure,
                                get_orders_for_user, get_semaphore,
                                get_semaphore_summary, get_red_activities,
                                get_my_pending_activities)
from utils.email_utils  import send_activation_email, send_overdue_alert

# ══════════════════════════════════════════════════════════
#  CSS Global
# ══════════════════════════════════════════════════════════

def inject_css() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Source+Sans+3:wght@300;400;600;700&display=swap');

    /* ── Reset & Base ─────────────────────────────── */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Source Sans 3', sans-serif;
        background: #F0F3F9;
    }
    h1,h2,h3,h4 { font-family: 'Barlow Condensed', sans-serif; letter-spacing:.5px; }

    /* ── Sidebar ──────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D2B6E 0%, #091D4E 100%) !important;
        border-right: none !important;
    }
    [data-testid="stSidebar"] * { color: #E8EDF7 !important; }
    [data-testid="stSidebar"] .sidebar-divider {
        border-top: 1px solid rgba(255,255,255,.15);
        margin: 12px 0;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        background: rgba(255,255,255,.08) !important;
        border: 1px solid rgba(255,255,255,.18) !important;
        color: #fff !important;
        border-radius: 8px !important;
        font-family: 'Source Sans 3', sans-serif !important;
        font-weight: 600 !important;
        transition: background .2s;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button:hover {
        background: rgba(255,255,255,.18) !important;
    }

    /* ── Main area ────────────────────────────────── */
    .main .block-container { padding: 1.5rem 2rem 3rem 2rem; max-width:1400px; }

    /* ── Metric card ──────────────────────────────── */
    .metric-card {
        background: #fff;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 1px 6px rgba(13,43,110,.10);
        border-left: 4px solid var(--card-accent, #0D2B6E);
        transition: transform .15s, box-shadow .15s;
    }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 4px 14px rgba(13,43,110,.14); }
    .metric-card .mc-value {
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 2.4rem; font-weight: 800; line-height: 1;
        color: #0D2B6E;
    }
    .metric-card .mc-label {
        font-size: .82rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: .6px; color: #8592A3; margin-top: 4px;
    }
    .metric-card .mc-sub { font-size: .80rem; color: #8592A3; margin-top: 2px; }

    /* ── Order card ───────────────────────────────── */
    .order-card {
        background: #fff;
        border-radius: 12px;
        padding: 20px 22px;
        box-shadow: 0 1px 6px rgba(13,43,110,.09);
        margin-bottom: 14px;
        border-top: 3px solid #0D2B6E;
        transition: transform .15s, box-shadow .15s;
        cursor: pointer;
    }
    .order-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(13,43,110,.14); }
    .order-number {
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 1.15rem; font-weight: 700; color: #0D2B6E;
    }
    .order-model { font-size: .85rem; color: #4B5563; margin-top: 2px; }
    .badge {
        display: inline-block;
        padding: 3px 10px; border-radius: 20px;
        font-size: .72rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: .5px;
    }
    .badge-active   { background: #DBEAFE; color: #1E40AF; }
    .badge-completed{ background: #D1FAE5; color: #065F46; }
    .badge-cancelled{ background: #F3F4F6; color: #6B7280; }

    /* ── Progress bar ─────────────────────────────── */
    .progress-wrap { background: #E5E7EB; border-radius: 6px; height: 8px; overflow:hidden; margin: 8px 0; }
    .progress-fill { height: 8px; border-radius: 6px;
                     background: linear-gradient(90deg, #0D2B6E, #2563EB); transition: width .4s; }

    /* ── Semaphore ────────────────────────────────── */
    .semaphore-dot {
        display: inline-block; width: 12px; height: 12px;
        border-radius: 50%; margin-right: 6px; vertical-align: middle;
    }
    .sem-green  { background: #22C55E; box-shadow: 0 0 6px #22C55E88; }
    .sem-yellow { background: #F59E0B; box-shadow: 0 0 6px #F59E0B88; }
    .sem-red    { background: #EF4444; box-shadow: 0 0 6px #EF444488; animation: pulse-red 1.2s infinite; }
    .sem-gray   { background: #D1D5DB; }
    @keyframes pulse-red {
        0%,100% { box-shadow: 0 0 6px #EF444488; }
        50%      { box-shadow: 0 0 14px #EF4444CC; }
    }

    /* ── Activity row ─────────────────────────────── */
    .act-row {
        background: #fff; border-radius: 10px;
        padding: 14px 18px; margin-bottom: 8px;
        border-left: 4px solid var(--act-color, #D1D5DB);
        box-shadow: 0 1px 4px rgba(0,0,0,.06);
    }
    .act-row-completed { --act-color: #22C55E; background: #F0FDF4; }
    .act-row-inprogress{ --act-color: #2563EB; }
    .act-row-waiting   { --act-color: #F59E0B; background: #FFFBEB; }
    .act-row-pending   { --act-color: #D1D5DB; }
    .act-row-blocked   { --act-color: #EF4444; background: #FEF2F2; }
    .act-name { font-family:'Barlow Condensed',sans-serif; font-size:1.05rem; font-weight:700; color:#0D2B6E; }
    .act-meta { font-size:.78rem; color:#8592A3; margin-top:2px; }

    /* ── Phase chip ───────────────────────────────── */
    .phase-chip {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: .70rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: .5px; background: #EEF2FF; color: #3730A3; margin-right: 6px;
    }

    /* ── Section header ───────────────────────────── */
    .section-header {
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 1.5rem; font-weight: 800; color: #0D2B6E;
        border-bottom: 3px solid #C41E2E;
        padding-bottom: 6px; margin-bottom: 20px; letter-spacing: .4px;
    }

    /* ── Login ────────────────────────────────────── */
    .login-card {
        background: #fff; border-radius: 16px;
        padding: 40px 44px; max-width: 420px; margin: 60px auto;
        box-shadow: 0 8px 32px rgba(13,43,110,.16);
        border-top: 5px solid #C41E2E;
    }

    /* ── Avatar circle ────────────────────────────── */
    .avatar {
        display: inline-flex; align-items:center; justify-content:center;
        width: 38px; height: 38px; border-radius: 50%;
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 800; font-size: 1rem; color: #fff;
        margin-right: 8px;
    }

    /* ── Page nav button active ───────────────────── */
    .nav-active button {
        background: rgba(196,30,46,.20) !important;
        border-color: #C41E2E !important;
        color: #fff !important;
    }

    /* ── General Streamlit overrides ─────────────── */
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] select,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {
        border-radius: 8px !important;
        border: 1.5px solid #D1D9E8 !important;
        font-family: 'Source Sans 3', sans-serif !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: #0D2B6E !important;
        box-shadow: 0 0 0 2px rgba(13,43,110,.15) !important;
    }
    div[data-testid="stForm"] {
        border: none !important; padding: 0 !important;
    }
    [data-testid="stButton"] button[kind="primary"] {
        background: #0D2B6E !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Source Sans 3', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: .3px !important;
        transition: background .2s !important;
    }
    [data-testid="stButton"] button[kind="primary"]:hover {
        background: #C41E2E !important;
    }
    .stAlert { border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  LOGO IMEMSA (imagen real en base64)
# ══════════════════════════════════════════════════════════

def _load_logo_b64() -> str:
    """Carga el logo desde assets/ como base64. Fallback a texto si no existe."""
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_imemsa.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

_LOGO_B64 = _load_logo_b64()

def _logo_img_tag(width: int = 160, style: str = "") -> str:
    if _LOGO_B64:
        return (
            f'<img src="data:image/png;base64,{_LOGO_B64}" '
            f'width="{width}" style="display:block;{style}" alt="IMEMSA"/>'
        )
    # Fallback texto
    return (
        f'<span style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.6rem;'
        f'font-weight:800;color:#fff;letter-spacing:2px;">IMEMSA</span>'
    )


def logo_sidebar() -> None:
    st.markdown(
        f'<div style="padding:18px 16px 10px 16px;">'
        f'{_logo_img_tag(width=150, style="filter:brightness(0) invert(1);" )}'
        f'<div style="font-family:\'Source Sans 3\',sans-serif;font-size:.7rem;'
        f'font-weight:600;color:#8EA8D8;letter-spacing:2px;margin-top:4px;padding-left:2px;">'
        f'MOTORES YAMAHA</div>'
        f'<div style="height:2px;background:#C41E2E;border-radius:1px;margin-top:4px;"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def logo_login() -> None:
    st.markdown(
        f'<div style="text-align:center;margin-bottom:24px;">'
        f'<div style="display:inline-block;background:#0D2B6E;border-radius:10px;'
        f'padding:14px 24px 10px;">'
        f'{_logo_img_tag(width=180)}'
        f'<div style="font-family:\'Source Sans 3\',sans-serif;font-size:.7rem;'
        f'font-weight:600;color:#8EA8D8;letter-spacing:2.5px;margin-top:5px;">'
        f'MOTORES YAMAHA</div>'
        f'<div style="height:2px;background:#C41E2E;border-radius:1px;margin-top:5px;"></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════
#  HELPERS UI
# ══════════════════════════════════════════════════════════

def _sem_dot(color: str) -> str:
    return f'<span class="semaphore-dot sem-{color}"></span>'


def _progress_bar(pct: int) -> str:
    return (
        f'<div class="progress-wrap">'
        f'<div class="progress-fill" style="width:{pct}%;"></div>'
        f'</div><span style="font-size:.75rem;color:#8592A3;">{pct}% completado</span>'
    )


def _badge(status: str) -> str:
    cls = {"active": "badge-active", "completed": "badge-completed",
           "cancelled": "badge-cancelled"}.get(status, "badge-active")
    label = ORDER_STATUS_LABELS.get(status, status)
    return f'<span class="badge {cls}">{label}</span>'


def _avatar(initials: str, color: str) -> str:
    return f'<span class="avatar" style="background:{color};">{initials}</span>'


def _act_row_class(status: str) -> str:
    return {
        "completed":       "act-row-completed",
        "in_progress":     "act-row-inprogress",
        "waiting_closure": "act-row-waiting",
        "pending":         "act-row-pending",
        "blocked":         "act-row-blocked",
    }.get(status, "act-row-pending")


# ══════════════════════════════════════════════════════════
#  PÁGINA 1 — LOGIN
# ══════════════════════════════════════════════════════════

def page_login() -> None:
    # ── Estilos exclusivos de la página de login ─────────────────────────────
    st.markdown("""
    <style>
    /* Fondo degradado navy */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg,#0D2B6E 0%,#1A3F8F 55%,#16387A 100%) !important;
    }
    /* Ocultar fondos blancos que Streamlit inyecta en la columna central */
    [data-testid="stAppViewContainer"] [data-testid="stVerticalBlock"],
    [data-testid="stAppViewContainer"] [data-testid="column"] > div:first-child {
        background: transparent !important;
        box-shadow: none !important;
    }
    /* Tarjeta login: aplicada al bloque de la columna central */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    /* Campos del formulario en login con fondo oscuro semitransparente */
    .login-col [data-testid="stTextInput"] input {
        background: rgba(255,255,255,.12) !important;
        border: 1.5px solid rgba(255,255,255,.30) !important;
        color: #fff !important;
        border-radius: 8px !important;
    }
    .login-col [data-testid="stTextInput"] input::placeholder { color: rgba(255,255,255,.45) !important; }
    .login-col [data-testid="stTextInput"] label { color: rgba(255,255,255,.85) !important; font-weight:600 !important; }
    /* Botón "Ingresar" con color IMEMSA */
    .login-col [data-testid="stFormSubmitButton"] button {
        background: #C41E2E !important;
        border: none !important;
        color: #fff !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        letter-spacing: .4px !important;
        padding: 12px !important;
        transition: background .2s !important;
    }
    .login-col [data-testid="stFormSubmitButton"] button:hover {
        background: #0D2B6E !important;
    }
    /* Error message en login */
    .login-col [data-testid="stAlert"] {
        background: rgba(196,30,46,.18) !important;
        border: 1px solid #C41E2E !important;
        color: #fff !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1.1, 1])
    with col_c:
        # Clase para apuntar CSS
        st.markdown('<div class="login-col">', unsafe_allow_html=True)

        # Logo IMEMSA centrado
        logo_login()

        # Subtítulo en blanco
        st.markdown(
            '<p style="text-align:center;color:rgba(255,255,255,.82);font-size:.88rem;'
            'margin-bottom:28px;margin-top:4px;letter-spacing:.2px;">'
            'Sistema de Seguimiento · Proceso Transversal de Compra de Motores</p>',
            unsafe_allow_html=True,
        )

        # Formulario
        with st.form("login_form"):
            username  = st.text_input("👤  Usuario", placeholder="Ej. dgonzalez")
            password  = st.text_input("🔒  Contraseña", type="password")
            submitted = st.form_submit_button(
                "Ingresar al sistema", use_container_width=True, type="primary"
            )

        if submitted:
            ok, user_info = verify_login(username, password)
            if ok:
                st.session_state["user"]             = user_info
                st.session_state["page"]             = "dashboard"
                st.session_state["selected_order_id"] = None
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

        # Pie de página — año 2026
        st.markdown(
            '<p style="text-align:center;color:rgba(255,255,255,.40);font-size:.74rem;margin-top:24px;">'
            '© 2026 IMEMSA — Uso interno. Acceso restringido.</p>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  SIDEBAR NAVEGACIÓN
# ══════════════════════════════════════════════════════════

def render_sidebar() -> str:
    """Renderiza el sidebar y regresa la página activa."""
    user = st.session_state["user"]
    page = st.session_state.get("page", "dashboard")

    with st.sidebar:
        logo_sidebar()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        # Info usuario
        av = _avatar(user["avatar"], user["color"])
        st.markdown(
            f'<div style="padding:4px 16px 12px;">'
            f'{av}<span style="font-size:.9rem;font-weight:700;">{user["name"]}</span>'
            f'<br><span style="font-size:.75rem;padding-left:46px;opacity:.7;">{user["role"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        # Navegación
        st.markdown(
            '<p style="font-size:.7rem;font-weight:700;text-transform:uppercase;'
            'letter-spacing:1px;padding-left:4px;opacity:.55;margin-bottom:6px;">Navegación</p>',
            unsafe_allow_html=True,
        )

        nav_items = [
            ("📊", "Tablero de Pedidos", "dashboard"),
            ("📋", "Detalle de Actividades", "activities"),
        ]
        if user.get("can_create_orders"):
            nav_items.append(("➕", "Nuevo Pedido", "new_order"))

        for icon, label, key in nav_items:
            active_style = "nav-active" if page == key else ""
            st.markdown(f'<div class="{active_style}">', unsafe_allow_html=True)
            if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
                st.session_state["page"] = key
                st.session_state["selected_order_id"] = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        # Semáforo resumen
        data = load_data()
        sem = get_semaphore_summary(data)
        st.markdown(
            '<p style="font-size:.7rem;font-weight:700;text-transform:uppercase;'
            'letter-spacing:1px;padding-left:4px;opacity:.55;margin-bottom:8px;">Estado General</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="background:rgba(255,255,255,.07);border-radius:10px;padding:12px 14px;">'
            f'{_sem_dot("green")}<span style="font-size:.85rem;">{sem["green"]} En tiempo</span><br>'
            f'<div style="margin-top:5px;">{_sem_dot("yellow")}<span style="font-size:.85rem;">{sem["yellow"]} En riesgo</span></div><br>'
            f'<div style="margin-top:-8px;">{_sem_dot("red")}<span style="font-size:.85rem;">{sem["red"]} Vencidas</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Botón de alertas de semáforo rojo
        if sem["red"] > 0:
            st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
            if st.button("🚨  Enviar alertas vencidas", use_container_width=True):
                _send_overdue_alerts(data)

        st.markdown('<div class="sidebar-divider" style="margin-top:auto;"></div>', unsafe_allow_html=True)

        if st.button("🚪  Cerrar sesión", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    return page


def _send_overdue_alerts(data: dict) -> None:
    reds = get_red_activities(data)
    sent = 0
    for act in reds:
        ok = send_overdue_alert(
            to_email=act["_responsible_email"],
            to_name=act["_responsible_name"],
            order_number=act["_order_number"],
            activity_name=act["name"],
            due_date=act.get("due_date", "—"),
        )
        if ok:
            sent += 1
    if sent:
        st.toast(f"✅ {sent} alerta(s) enviadas por correo.", icon="📧")
    else:
        st.toast("No se pudo enviar correos (verifica configuración SMTP).", icon="⚠️")


# ══════════════════════════════════════════════════════════
#  PÁGINA 2 — TABLERO DE PEDIDOS
# ══════════════════════════════════════════════════════════

def page_dashboard() -> None:
    data = load_data()
    user = st.session_state["user"]
    orders = get_orders_for_user(data, user["username"])

    active    = [o for o in orders if o["status"] == "active"]
    completed = [o for o in orders if o["status"] == "completed"]
    sem       = get_semaphore_summary(data)
    year      = datetime.today().year
    annual_count = len([o for o in data["orders"] if o.get("year") == year and o.get("status") != "cancelled"])

    # ── Header ──────────────────────────────────────────────────
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">'
        f'<div class="section-header" style="margin-bottom:0;">📊 Tablero de Pedidos</div>'
        f'<span style="font-size:.82rem;color:#8592A3;">'
        f'Actualizado: {datetime.today().strftime("%d/%m/%Y %H:%M")}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── KPI Cards ─────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    _kpi(c1, str(len(active)),          "Pedidos Activos",  "#0D2B6E")
    _kpi(c2, str(len(completed)),        "Completados",      "#059669")
    _kpi(c3, f"{annual_count}/{MAX_ANNUAL_ORDERS}", "Pedidos {year}", "#7C3AED")
    _kpi(c4, str(sem["red"]),            "Actividades Venc.", "#C41E2E")
    _kpi(c5, str(sem["yellow"]),         "En Riesgo",        "#D97706")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Semáforo visual ─────────────────────────────────────────
    if sem["red"] > 0:
        st.markdown(
            f'<div style="background:#FEF2F2;border:1.5px solid #FECACA;border-radius:10px;'
            f'padding:12px 18px;margin-bottom:16px;display:flex;align-items:center;gap:10px;">'
            f'{_sem_dot("red")}'
            f'<span style="color:#991B1B;font-weight:700;font-size:.88rem;">'
            f'{sem["red"]} actividad(es) vencida(s) requieren atención inmediata. '
            f'Usa el botón "Enviar alertas" en el menú lateral.</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Mis tareas pendientes ────────────────────────────────────
    my_tasks = get_my_pending_activities(data, user["username"])
    if my_tasks:
        st.markdown('<div class="section-header" style="font-size:1.1rem;">🔔 Mis tareas activas</div>', unsafe_allow_html=True)
        for t in my_tasks:
            sem_color = get_semaphore(t)
            st.markdown(
                f'<div class="act-row act-row-inprogress" style="margin-bottom:6px;">'
                f'{_sem_dot(sem_color)}'
                f'<span class="act-name">{t["name"]}</span>'
                f'<span class="phase-chip">{t["phase"]}</span>'
                f'<span class="act-meta"> · {t["_order_number"]}'
                f' · Vence: {t.get("due_date","—")}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Lista de pedidos ─────────────────────────────────────────
    tabs = st.tabs([f"🔄  Activos  ({len(active)})", f"✅  Completados  ({len(completed)})"])

    with tabs[0]:
        if not active:
            st.info("No hay pedidos activos actualmente.")
        else:
            for order in sorted(active, key=lambda o: o["id"], reverse=True):
                _render_order_card(order)

    with tabs[1]:
        if not completed:
            st.info("No hay pedidos completados.")
        else:
            for order in sorted(completed, key=lambda o: o["id"], reverse=True):
                _render_order_card(order)


def _kpi(col, value: str, label: str, color: str) -> None:
    with col:
        st.markdown(
            f'<div class="metric-card" style="--card-accent:{color};">'
            f'<div class="mc-value">{value}</div>'
            f'<div class="mc-label">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _render_order_card(order: dict) -> None:
    acts = order.get("activities", [])
    active_act = next((a for a in acts if a["status"] in ("in_progress", "waiting_closure")), None)
    responsible_key = active_act["responsible_key"] if active_act else None
    responsible = USERS.get(responsible_key, {})
    prog = order.get("progress", 0)
    sem_color = get_semaphore(active_act) if active_act else "gray"

    with st.container():
        st.markdown(
            f'<div class="order-card">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            f'  <div>'
            f'    <div class="order-number">{order["order_number"]}</div>'
            f'    <div class="order-model">⚙️ {order["motor_model"]} — Cant: {order["quantity"]} u.'
            f'     · {order["supplier"]}</div>'
            f'  </div>'
            f'  <div style="text-align:right;">'
            f'    {_badge(order["status"])}'
            f'    <div class="act-meta" style="margin-top:4px;">Creado: {order["created_at"]}</div>'
            f'  </div>'
            f'</div>'
            f'<div style="margin-top:10px;">'
            f'  {_progress_bar(prog)}'
            f'</div>'
            f'<div style="margin-top:10px;display:flex;align-items:center;gap:12px;">'
            f'  {_sem_dot(sem_color)}'
            f'  <span style="font-size:.80rem;color:#4B5563;">'
            f'    {"Actividad activa: <strong>" + active_act["name"] + "</strong>" if active_act else "Sin actividad activa"}'
            f'  </span>'
            f'  {"·  Resp: " + _avatar(responsible.get("avatar","?"), responsible.get("color","#ccc")) + "<span style=\'font-size:.78rem;\'>" + responsible.get("name","") + "</span>" if responsible_key else ""}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        col_btn, col_empty = st.columns([1, 4])
        with col_btn:
            if st.button("Ver actividades →", key=f"open_order_{order['id']}"):
                st.session_state["selected_order_id"] = order["id"]
                st.session_state["page"] = "activities"
                st.rerun()


# ══════════════════════════════════════════════════════════
#  PÁGINA 3 — ACTIVIDADES DEL PEDIDO
# ══════════════════════════════════════════════════════════

def page_activities() -> None:
    data  = load_data()
    user  = st.session_state["user"]
    order_id = st.session_state.get("selected_order_id")

    # Selector de pedido
    orders = get_orders_for_user(data, user["username"])
    order_map = {o["order_number"]: o["id"] for o in orders}

    col_sel, col_back = st.columns([3, 1])
    with col_sel:
        selected_label = st.selectbox(
            "Seleccionar pedido",
            options=list(order_map.keys()),
            index=0 if not order_id else
                  next((i for i, k in enumerate(order_map) if order_map[k] == order_id), 0),
            key="order_selector",
        )
    with col_back:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Tablero", use_container_width=True):
            st.session_state["page"] = "dashboard"
            st.rerun()

    if not selected_label:
        st.info("No hay pedidos disponibles.")
        return

    order_id = order_map[selected_label]
    st.session_state["selected_order_id"] = order_id
    order = next((o for o in data["orders"] if o["id"] == order_id), None)
    if not order:
        st.error("Pedido no encontrado.")
        return

    acts = order.get("activities", [])
    prog = order.get("progress", 0)

    # ── Header del pedido ─────────────────────────────────────
    sem_counts = {"green": 0, "yellow": 0, "red": 0, "gray": 0}
    for a in acts:
        sem_counts[get_semaphore(a)] = sem_counts.get(get_semaphore(a), 0) + 1

    st.markdown(
        f'<div style="background:#fff;border-radius:12px;padding:20px 24px;'
        f'margin-bottom:18px;box-shadow:0 1px 6px rgba(13,43,110,.10);border-top:4px solid #0D2B6E;">'
        f'<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">'
        f'<div>'
        f'  <div style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.5rem;font-weight:800;color:#0D2B6E;">'
        f'  📋 {order["order_number"]}</div>'
        f'  <div style="font-size:.85rem;color:#4B5563;margin-top:3px;">'
        f'  ⚙️ {order["motor_model"]} &nbsp;·&nbsp; {order["quantity"]} unidades'
        f'  &nbsp;·&nbsp; {order["supplier"]}</div>'
        f'</div>'
        f'<div style="text-align:right;">'
        f'  {_badge(order["status"])}'
        f'  <div style="font-size:.78rem;color:#8592A3;margin-top:4px;">Creado: {order["created_at"]}</div>'
        f'</div>'
        f'</div>'
        f'<div style="margin-top:14px;">{_progress_bar(prog)}</div>'
        f'<div style="margin-top:10px;display:flex;gap:14px;flex-wrap:wrap;">'
        f'  {_sem_dot("green")}<span style="font-size:.8rem;">{sem_counts["green"]} en tiempo</span>'
        f'  {_sem_dot("yellow")}<span style="font-size:.8rem;">{sem_counts["yellow"]} en riesgo</span>'
        f'  {_sem_dot("red")}<span style="font-size:.8rem;">{sem_counts["red"]} vencidas</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Lista de actividades por fase ─────────────────────────
    st.markdown('<div class="section-header">🔢 Actividades del Proceso (19)</div>', unsafe_allow_html=True)

    current_phase = None
    for act in acts:
        phase = act.get("phase", "")
        if phase != current_phase:
            current_phase = phase
            phase_acts   = [a for a in acts if a.get("phase") == phase]
            phase_done   = sum(1 for a in phase_acts if a["status"] == "completed")
            st.markdown(
                f'<div style="margin:18px 0 8px;display:flex;align-items:center;gap:8px;">'
                f'<span style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.1rem;'
                f'font-weight:700;color:#0D2B6E;">{phase}</span>'
                f'<span style="font-size:.72rem;color:#8592A3;">'
                f'({phase_done}/{len(phase_acts)} completadas)</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        _render_activity_row(act, order, user, data)


def _render_activity_row(act: dict, order: dict, user: dict, data: dict) -> None:
    status    = act.get("status", "pending")
    sem_color = get_semaphore(act)
    row_cls   = _act_row_class(status)
    responsible_key = act.get("responsible_key", "")
    responsible = USERS.get(responsible_key, {})
    is_mine = (responsible_key == user["username"])

    # ── Fila de actividad ──────────────────────────────────────
    st.markdown(
        f'<div class="act-row {row_cls}">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">'
        f'  <div style="display:flex;align-items:center;gap:8px;">'
        f'    <span style="font-family:\'Barlow Condensed\',sans-serif;font-size:.85rem;'
        f'    font-weight:700;color:#8592A3;min-width:22px;">{act["id"]:02d}</span>'
        f'    {_sem_dot(sem_color)}'
        f'    <div>'
        f'      <div class="act-name">{act["name"]}</div>'
        f'      <div class="act-meta">{act["description"]}</div>'
        f'    </div>'
        f'  </div>'
        f'  <div style="text-align:right;">'
        f'    <span style="font-size:.75rem;padding:3px 10px;border-radius:20px;'
        f'    background:#F3F4F6;color:#374151;font-weight:600;">{STATUS_LABELS.get(status,"")}</span>'
        f'    <div class="act-meta" style="margin-top:4px;">'
        f'    Resp: {_avatar(responsible.get("avatar","?"), responsible.get("color","#ccc"))}'
        f'    {responsible.get("name","")}</div>'
        f'  </div>'
        f'</div>'
        f'<div class="act-meta" style="margin-top:6px;">'
        f'  Plazo: {act["days_allocated"]} días hábiles'
        f'  {"  ·  Inicio: " + act["start_date"] if act.get("start_date") else ""}'
        f'  {"  ·  Límite: " + act["due_date"] if act.get("due_date") else ""}'
        f'  {"  ·  Cierre: " + act["completion_date"] if act.get("completion_date") else ""}'
        f'</div>'
        + (
            f'<div style="margin-top:4px;font-size:.75rem;color:#6B7280;">'
            f'📎 Evidencia: {act["evidence_name"]}</div>'
            if act.get("evidence_name") else ""
        )
        + f'</div>',
        unsafe_allow_html=True,
    )

    # ── Acciones: el responsable puede solicitar cierre ────────
    if is_mine and status == "in_progress":
        with st.expander(f"📋  Solicitar cierre — Actividad {act['id']:02d}: {act['name']}", expanded=False):
            with st.form(f"closure_form_{order['id']}_{act['id']}"):
                notes    = st.text_area("Observaciones / notas de cierre", height=90)
                evidence = st.file_uploader(
                    "Adjuntar evidencia (PDF, imagen, Excel…)",
                    type=["pdf", "png", "jpg", "jpeg", "xlsx", "docx"],
                    key=f"ev_{order['id']}_{act['id']}",
                )
                submitted = st.form_submit_button("✅  Enviar solicitud de cierre", type="primary",
                                                   use_container_width=True)
                if submitted:
                    ev_name = ev_data = None
                    if evidence:
                        ev_name = evidence.name
                        ev_data = base64.b64encode(evidence.read()).decode()
                    ok, msg = request_closure(
                        data, order["id"], act["id"],
                        user["username"], ev_name, ev_data, notes,
                    )
                    if ok:
                        # Auto-aprobación: cerrar y activar siguiente
                        ok2, msg2, alerts = approve_closure(data, order["id"], act["id"])
                        if ok2:
                            for alert in alerts:
                                send_activation_email(**alert)
                            st.success(f"✅ Actividad cerrada al 100 %. {msg2}")
                            st.rerun()
                        else:
                            st.warning(msg2)
                    else:
                        st.error(msg)

    elif status == "waiting_closure":
        st.markdown(
            '<div style="font-size:.80rem;color:#92400E;font-weight:600;'
            'padding:4px 10px;background:#FEF3C7;border-radius:6px;display:inline-block;'
            'margin-top:4px;">⏳ Cierre solicitado — procesando…</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════
#  PÁGINA 4 — NUEVO PEDIDO (solo David González)
# ══════════════════════════════════════════════════════════

def page_new_order() -> None:
    user = st.session_state["user"]
    if not user.get("can_create_orders"):
        st.error("⛔ Acceso restringido. Solo David González puede crear nuevos pedidos.")
        return

    data  = load_data()
    year  = datetime.today().year
    count = len([o for o in data["orders"]
                 if o.get("year") == year and o.get("status") != "cancelled"])

    st.markdown('<div class="section-header">➕ Registrar Nuevo Pedido de Motores</div>',
                unsafe_allow_html=True)

    # Alerta de cupo
    remaining = MAX_ANNUAL_ORDERS - count
    color_bar  = "#22C55E" if remaining > 5 else "#F59E0B" if remaining > 2 else "#EF4444"
    st.markdown(
        f'<div style="background:#fff;border-radius:10px;padding:16px 20px;'
        f'margin-bottom:20px;box-shadow:0 1px 4px rgba(13,43,110,.08);'
        f'border-left:4px solid {color_bar};">'
        f'<span style="font-weight:700;color:{color_bar};">'
        f'Capacidad anual {year}: {count}/{MAX_ANNUAL_ORDERS} pedidos registrados</span>'
        f'  · <span style="color:#6B7280;">Disponibles: {remaining}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if remaining == 0:
        st.error(f"🚫 Límite anual de {MAX_ANNUAL_ORDERS} pedidos alcanzado para {year}.")
        return

    with st.form("new_order_form"):
        col1, col2 = st.columns(2)
        with col1:
            motor_model = st.selectbox("Modelo de motor Yamaha", MOTOR_MODELS)
            quantity    = st.number_input("Cantidad de motores", min_value=1, max_value=50, value=1, step=1)
        with col2:
            supplier    = st.text_input("Proveedor / Distribuidor",
                                        placeholder="Ej. Distribuidora Marítima del Golfo SA de CV")
            _           = st.empty()

        notes = st.text_area("Justificación / Notas adicionales", height=100,
                             placeholder="Descripción del requerimiento, destino, prioridad…")

        st.markdown("<br>", unsafe_allow_html=True)
        col_b1, col_b2 = st.columns([1, 3])
        with col_b1:
            submitted = st.form_submit_button("🚀  Crear pedido", type="primary", use_container_width=True)
        with col_b2:
            st.info(f"Al crear el pedido se activará automáticamente la primera actividad "
                    f"asignada a **David González** con fecha límite de 2 días hábiles.")

        if submitted:
            if not supplier.strip():
                st.error("El campo Proveedor es obligatorio.")
            else:
                ok, msg, new_order = create_order(
                    data, motor_model, int(quantity),
                    supplier.strip(), notes, user["username"], year,
                )
                if ok:
                    st.success(f"🎉 {msg}")
                    st.balloons()
                    st.session_state["selected_order_id"] = new_order["id"]
                    st.session_state["page"] = "activities"
                    st.rerun()
                else:
                    st.error(msg)


# ══════════════════════════════════════════════════════════
#  MAIN ROUTER
# ══════════════════════════════════════════════════════════

def main() -> None:
    inject_css()

    # Inicializar estado de sesión
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "page" not in st.session_state:
        st.session_state["page"] = "login"
    if "selected_order_id" not in st.session_state:
        st.session_state["selected_order_id"] = None

    # Si no hay usuario → mostrar login
    if st.session_state["user"] is None:
        page_login()
        return

    # Sidebar de navegación
    page = render_sidebar()

    # Router de páginas
    if page == "dashboard":
        page_dashboard()
    elif page == "activities":
        page_activities()
    elif page == "new_order":
        page_new_order()
    else:
        page_dashboard()


if __name__ == "__main__":
    main()
