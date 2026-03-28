# app.py  ─  IMEMSA · Sistema de Compra de Motores Yamaha
# ══════════════════════════════════════════════════════════
# Ejecutar:  streamlit run app.py
# ══════════════════════════════════════════════════════════

from __future__ import annotations
import base64
import os
from datetime import datetime

import streamlit as st

st.set_page_config(
    page_title="IMEMSA · Motores Yamaha",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",   # "expanded" en cada carga de página
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
#  CAPA DE DATOS EN MEMORIA
# ══════════════════════════════════════════════════════════

def _app_data() -> dict:
    if "_app_data_store" not in st.session_state:
        st.session_state["_app_data_store"] = load_data()
    return st.session_state["_app_data_store"]


def _app_save(data: dict) -> None:
    """Guarda en session_state (inmediato) y en Sheets. Avisa si Sheets falla."""
    st.session_state["_app_data_store"] = data
    try:
        from utils.sheets_manager import _gsheets_available, save_to_sheets, _strip_evidence
        if _gsheets_available():
            ok = save_to_sheets(data)
            if not ok:
                st.toast("⚠️ No se pudo guardar en Google Sheets. Intenta de nuevo.", icon="⚠️")
        else:
            save_data(data)
    except Exception as e:
        st.toast(f"⚠️ Error al guardar: {e}", icon="⚠️")


def _app_invalidate() -> None:
    st.session_state.pop("_app_data_store", None)


# ══════════════════════════════════════════════════════════
#  CSS GLOBAL
# ══════════════════════════════════════════════════════════

def inject_css() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@300;400;600;700&family=Barlow+Condensed:wght@400;600;700;800&display=swap');

    /* ── FONDO MARINO (todas las páginas) ── */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Rajdhani', sans-serif;
        background: radial-gradient(ellipse 120% 80% at 50% -10%,
            #1a3a8f 0%, #0a1d5e 30%, #020b22 68%) !important;
        min-height: 100vh;
    }
    #MainMenu, footer { visibility: hidden; }
    /* NO ocultar header — contiene el botón toggle del sidebar */
    [data-testid="stHeader"] { background: transparent !important; border-bottom: none !important; }
    [data-testid="stToolbar"] { visibility: hidden; }
    /* Botón de reabrir sidebar cuando está colapsado */
    [data-testid="stSidebarCollapsedControl"] {
        background: rgba(4,12,42,0.85) !important;
        border: 1px solid rgba(100,150,255,.15) !important;
        border-radius: 0 8px 8px 0 !important;
    }
    [data-testid="stSidebarCollapsedControl"] svg { color: #c8d8f0 !important; }

    /* Scanlines */
    [data-testid="stAppViewContainer"]::before {
        content: ''; position: fixed; inset: 0; z-index: 0; pointer-events: none;
        background: repeating-linear-gradient(
            0deg, transparent, transparent 3px,
            rgba(0,0,0,0.06) 3px, rgba(0,0,0,0.06) 4px);
    }

    /* Burbujas (todas las páginas) */
    @keyframes rise-bubble {
        0%   { transform: translateY(0);      opacity: 0.55; }
        80%  { opacity: 0.1; }
        100% { transform: translateY(-105vh); opacity: 0; }
    }
    .bbl {
        position: fixed; border-radius: 50%;
        background: rgba(180,210,255,0.18); border: 1px solid rgba(180,210,255,0.28);
        animation: rise-bubble linear infinite;
        pointer-events: none; z-index: 1; bottom: -20px;
    }

    /* Esquinas decorativas */
    .corner-tl, .corner-tr, .corner-bl, .corner-br {
        position: fixed; width: 40px; height: 40px; z-index: 200; pointer-events: none;
    }
    .corner-tl { top:14px; left:14px;  border-top:2px solid #C41E2E; border-left:2px solid #C41E2E; }
    .corner-tr { top:14px; right:14px; border-top:2px solid #C41E2E; border-right:2px solid #C41E2E; }
    .corner-bl { bottom:14px; left:14px;  border-bottom:2px solid #C41E2E; border-left:2px solid #C41E2E; }
    .corner-br { bottom:14px; right:14px; border-bottom:2px solid #C41E2E; border-right:2px solid #C41E2E; }

    /* ── SIDEBAR — siempre visible, nunca colapsar ── */
    [data-testid="stSidebar"] {
        background: rgba(4,12,42,0.92) !important;
        border-right: 1px solid rgba(100,150,255,0.12) !important;
        backdrop-filter: blur(10px) !important;
        display: flex !important;
        visibility: visible !important;
        transform: translateX(0) !important;
        min-width: 244px !important;
        width: 244px !important;
        margin-left: 0 !important;
        left: 0 !important;
    }
    /* Ocultar botón de colapso dentro del sidebar — el usuario nunca lo cierra */
    [data-testid="stSidebarCollapseButton"],
    button[title="Close sidebar"],
    button[aria-label="Close sidebar"] { display: none !important; }
    /* Ocultar el control de reabrir — tampoco se necesita */
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    /* Asegurar que el contenido principal respete el sidebar */
    section.main > div.block-container {
        margin-left: 0 !important;
    }
    [data-testid="stSidebar"] * { color: #E8EDF7 !important; }
    [data-testid="stSidebar"] .sidebar-divider {
        border-top: 1px solid rgba(255,255,255,.10); margin: 10px 0;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        background: rgba(255,255,255,.06) !important;
        border: 1px solid rgba(255,255,255,.14) !important;
        color: #E8EDF7 !important; border-radius: 8px !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 14px !important; font-weight: 600 !important;
        letter-spacing: 1px !important; transition: all .2s !important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button:hover {
        background: rgba(255,255,255,.14) !important;
    }
    .nav-active button {
        background: rgba(196,30,46,.18) !important;
        border-color: rgba(196,30,46,.45) !important; color: #fff !important;
    }

    /* ── ÁREA PRINCIPAL ── */
    .main .block-container {
        padding: 1.5rem 2rem 3rem 2rem; max-width: 1400px;
        position: relative; z-index: 10;
    }

    /* Contenedores internos transparentes */
    [data-testid="stVerticalBlock"],
    [data-testid="column"] > div:first-child,
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: transparent !important;
    }

    /* ── SECTION HEADER ── */
    .section-header {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.6rem; letter-spacing: 3px; color: #ffffff;
        border-bottom: 2px solid #C41E2E;
        padding-bottom: 6px; margin-bottom: 20px;
    }

    /* ── METRIC CARDS ── */
    .metric-card {
        background: rgba(13,43,110,0.50);
        border: 1px solid rgba(100,150,255,0.18);
        border-radius: 12px; padding: 18px 20px;
        border-left: 4px solid var(--card-accent, #C41E2E);
        transition: transform .15s;
        backdrop-filter: blur(6px);
    }
    .metric-card:hover { transform: translateY(-2px); }
    .metric-card .mc-value {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.6rem; letter-spacing: 2px; line-height: 1; color: #ffffff;
    }
    .metric-card .mc-label {
        font-size: .78rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 2px; color: rgba(180,210,255,.55); margin-top: 5px;
    }

    /* ── ORDER CARDS ── */
    .order-card {
        background: rgba(13,43,110,0.50);
        border: 1px solid rgba(100,150,255,0.18);
        border-radius: 12px; padding: 18px 20px; margin-bottom: 12px;
        border-top: 3px solid rgba(100,150,255,0.3);
        transition: transform .15s; backdrop-filter: blur(6px);
    }
    .order-card:hover { transform: translateY(-2px); border-top-color: #C41E2E; }
    .order-number {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.2rem; letter-spacing: 2px; color: #ffffff;
    }
    .order-model { font-size: .84rem; color: rgba(180,210,255,.65); margin-top: 2px; }

    /* Badges */
    .badge {
        display: inline-block; padding: 3px 10px; border-radius: 20px;
        font-size: .70rem; font-weight: 700; text-transform: uppercase; letter-spacing: .5px;
    }
    .badge-active    { background: rgba(37,99,235,.25);  color: #93c5fd; border:1px solid rgba(37,99,235,.3); }
    .badge-completed { background: rgba(34,197,94,.15);  color: #86efac; border:1px solid rgba(34,197,94,.2); }
    .badge-cancelled { background: rgba(255,255,255,.08); color: rgba(180,210,255,.5); border:1px solid rgba(255,255,255,.1); }

    /* Progress bar */
    .progress-wrap { background: rgba(255,255,255,.12); border-radius: 6px; height: 7px; overflow:hidden; margin: 8px 0; }
    .progress-fill { height: 7px; border-radius: 6px;
                     background: linear-gradient(90deg, #1d4ed8, #60a5fa); transition: width .4s; }

    /* Semáforos */
    .semaphore-dot {
        display: inline-block; width: 12px; height: 12px;
        border-radius: 50%; margin-right: 6px; vertical-align: middle;
    }
    .sem-green  { background: #22C55E; box-shadow: 0 0 6px rgba(34,197,94,.7); }
    .sem-yellow { background: #F59E0B; box-shadow: 0 0 6px rgba(245,158,11,.7); }
    .sem-red    { background: #EF4444; box-shadow: 0 0 6px rgba(239,68,68,.7); animation: pulse-red 1.2s infinite; }
    .sem-gray   { background: rgba(255,255,255,.25); }
    @keyframes pulse-red {
        0%,100% { box-shadow: 0 0 6px rgba(239,68,68,.6); }
        50%      { box-shadow: 0 0 16px rgba(239,68,68,1); }
    }

    /* ── ACTIVITY ROWS ── */
    .act-row {
        background: rgba(13,43,110,0.45);
        border: 1px solid rgba(100,150,255,0.15);
        border-radius: 10px; padding: 14px 18px; margin-bottom: 8px;
        border-left: 4px solid var(--act-color, rgba(255,255,255,.2));
        backdrop-filter: blur(4px);
    }
    .act-row-completed  { --act-color: #22C55E; background: rgba(34,197,94,.08); }
    .act-row-inprogress { --act-color: #3b82f6; }
    .act-row-waiting    { --act-color: #F59E0B; background: rgba(245,158,11,.08); }
    .act-row-pending    { --act-color: rgba(255,255,255,.15); }
    .act-row-blocked    { --act-color: #EF4444; background: rgba(239,68,68,.08); }
    .act-name { font-family:'Bebas Neue',sans-serif; font-size:1.05rem; letter-spacing:1px; color:#ffffff; }
    .act-meta { font-size:.76rem; color:rgba(180,210,255,.55); margin-top:2px; }

    /* Phase chip */
    .phase-chip {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: .68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;
        background: rgba(100,150,255,.15); color: #93c5fd;
        border: 1px solid rgba(100,150,255,.25); margin-right: 6px;
    }

    /* Avatar */
    .avatar {
        display: inline-flex; align-items:center; justify-content:center;
        width: 36px; height: 36px; border-radius: 50%;
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1rem; color: #fff; margin-right: 8px;
    }

    /* ── INPUTS / FORMS ── */
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] select,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {
        border-radius: 8px !important;
        border: 1px solid rgba(100,150,255,.25) !important;
        background: rgba(255,255,255,.92) !important;
        color: #1a2a5e !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 15px !important;
    }
    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder { color: #8899bb !important; }

    /* Labels en blanco */
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span,
    .main label p, .main label span,
    [data-testid="stForm"] label { color: #ffffff !important; }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label { color: #E8EDF7 !important; }

    /* Form container */
    [data-testid="stForm"] {
        background: rgba(13,43,110,0.40) !important;
        border: 1px solid rgba(100,150,255,.18) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(8px) !important;
    }

    /* Botones primarios */
    [data-testid="stButton"] button[kind="primary"],
    [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #d42030 0%, #a8151f 100%) !important;
        border: none !important; border-radius: 8px !important;
        color: #ffffff !important;
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 16px !important; letter-spacing: 3px !important;
        box-shadow: 0 4px 18px rgba(196,30,46,.45) !important;
        transition: all .25s !important;
    }
    [data-testid="stButton"] button[kind="primary"]:hover,
    [data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 24px rgba(196,30,46,.65) !important;
    }

    /* Alerts / info boxes */
    .stAlert { border-radius: 8px !important; }
    [data-testid="stAlert"] {
        background: rgba(196,30,46,0.10) !important;
        border: 1px solid rgba(196,30,46,.30) !important;
        border-radius: 8px !important;
    }

    /* Expander */
    [data-testid="stExpander"] {
        background: rgba(13,43,110,.40) !important;
        border: 1px solid rgba(100,150,255,.18) !important;
        border-radius: 8px !important;
    }
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span { color: #ffffff !important; font-weight: 600 !important; }

    /* Tabs */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background: rgba(13,43,110,.35) !important;
        border-radius: 8px !important; padding: 4px !important;
        border: 1px solid rgba(100,150,255,.15) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        color: rgba(180,210,255,.7) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important; letter-spacing: 1px !important;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        background: rgba(196,30,46,.25) !important;
        color: #ffffff !important;
        border-radius: 6px !important;
    }

    /* Versión label */
    .ver-label {
        position: fixed; bottom: 16px; right: 20px; z-index: 200;
        font-size: 9px; letter-spacing: 3px;
        color: rgba(200,216,240,.25); text-transform: uppercase;
        font-family: 'Rajdhani', sans-serif; pointer-events: none;
    }
    </style>

    <!-- Decoración global (esquinas + burbujas + versión) -->
    <div class="corner-tl"></div>
    <div class="corner-tr"></div>
    <div class="corner-bl"></div>
    <div class="corner-br"></div>
    <div class="ver-label">Sistema v2.0 · 2026</div>

    <div class="bbl" style="width:5px;height:5px;left:4%;animation-duration:9s;animation-delay:-2s;"></div>
    <div class="bbl" style="width:8px;height:8px;left:10%;animation-duration:14s;animation-delay:-7s;"></div>
    <div class="bbl" style="width:4px;height:4px;left:17%;animation-duration:11s;animation-delay:-1s;"></div>
    <div class="bbl" style="width:9px;height:9px;left:25%;animation-duration:16s;animation-delay:-11s;"></div>
    <div class="bbl" style="width:5px;height:5px;left:33%;animation-duration:8s;animation-delay:-4s;"></div>
    <div class="bbl" style="width:7px;height:7px;left:41%;animation-duration:13s;animation-delay:-9s;"></div>
    <div class="bbl" style="width:3px;height:3px;left:49%;animation-duration:10s;animation-delay:-0s;"></div>
    <div class="bbl" style="width:9px;height:9px;left:57%;animation-duration:17s;animation-delay:-6s;"></div>
    <div class="bbl" style="width:4px;height:4px;left:65%;animation-duration:12s;animation-delay:-13s;"></div>
    <div class="bbl" style="width:6px;height:6px;left:73%;animation-duration:9s;animation-delay:-3s;"></div>
    <div class="bbl" style="width:10px;height:10px;left:80%;animation-duration:15s;animation-delay:-8s;"></div>
    <div class="bbl" style="width:4px;height:4px;left:87%;animation-duration:11s;animation-delay:-5s;"></div>
    <div class="bbl" style="width:6px;height:6px;left:94%;animation-duration:13s;animation-delay:-10s;"></div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  LOGO IMEMSA
# ══════════════════════════════════════════════════════════

def _load_logo_b64() -> str:
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_imemsa.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

_LOGO_B64 = _load_logo_b64()

def _logo_img_tag(width: int = 160, style: str = "") -> str:
    if _LOGO_B64:
        return (f'<img src="data:image/png;base64,{_LOGO_B64}" '
                f'width="{width}" style="display:block;{style}" alt="IMEMSA"/>')
    return '<span style="font-family:Barlow Condensed,sans-serif;font-size:1.6rem;font-weight:800;color:#fff;">IMEMSA</span>'


def logo_sidebar() -> None:
    st.markdown(
        '<div style="padding:20px 18px 14px 18px;">'
        '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:30px;'
        'letter-spacing:6px;color:#ffffff;line-height:1;'
        'text-shadow:0 0 20px rgba(100,150,255,.4);">IMEMSA</div>'
        '<div style="height:2px;margin:8px 0 5px;'
        'background:linear-gradient(to right,#C41E2E 60%,transparent);'
        'box-shadow:0 0 8px rgba(196,30,46,.5);"></div>'
        '<div style="font-size:9px;letter-spacing:4px;color:#8EA8D8;'
        'text-transform:uppercase;font-family:\'Rajdhani\',sans-serif;opacity:.8;">Motores Yamaha</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def logo_login() -> None:
    st.markdown(
        '<div style="text-align:center;margin-bottom:24px;">'
        '<div style="display:inline-block;background:#0D2B6E;border-radius:10px;padding:14px 24px 10px;">'
        + _logo_img_tag(width=180) +
        '<div style="font-family:Source Sans 3,Arial,sans-serif;font-size:.7rem;'
        'font-weight:600;color:#8EA8D8;letter-spacing:2.5px;margin-top:5px;">MOTORES YAMAHA</div>'
        '<div style="height:2px;background:#C41E2E;border-radius:1px;margin-top:5px;"></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════
#  HELPERS UI
# ══════════════════════════════════════════════════════════

def _sem_dot(color: str) -> str:
    return f'<span class="semaphore-dot sem-{color}"></span>'

def _progress_bar(pct: int) -> str:
    return (f'<div class="progress-wrap">'
            f'<div class="progress-fill" style="width:{pct}%;"></div>'
            f'</div><span style="font-size:.75rem;color:#8592A3;">{pct}% completado</span>')

def _badge(status: str) -> str:
    cls = {"active": "badge-active", "completed": "badge-completed",
           "cancelled": "badge-cancelled"}.get(status, "badge-active")
    return f'<span class="badge {cls}">{ORDER_STATUS_LABELS.get(status, status)}</span>'

def _avatar(initials: str, color: str) -> str:
    return f'<span class="avatar" style="background:{color};">{initials}</span>'

def _act_row_class(status: str) -> str:
    return {"completed": "act-row-completed", "in_progress": "act-row-inprogress",
            "waiting_closure": "act-row-waiting", "pending": "act-row-pending",
            "blocked": "act-row-blocked"}.get(status, "act-row-pending")


# ══════════════════════════════════════════════════════════
#  PÁGINA 1 — LOGIN
# ══════════════════════════════════════════════════════════

def page_login() -> None:
    # ── CSS cinematográfico IMEMSA v2.0 ──────────────────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@300;400;600;700&display=swap');

    /* Fondo principal */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(ellipse 90% 70% at 50% -5%,
            #1a3a8f 0%, #0a1d5e 28%, #020b22 65%) !important;
        min-height: 100vh;
    }
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent !important; border-bottom: none !important; }
    [data-testid="stToolbar"] { visibility: hidden; }
    .main .block-container { padding-top: 0 !important; }

    /* Scanlines overlay */
    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed; inset: 0; z-index: 0; pointer-events: none;
        background: repeating-linear-gradient(
            0deg, transparent, transparent 3px,
            rgba(0,0,0,0.07) 3px, rgba(0,0,0,0.07) 4px
        );
    }

    /* Quitar fondos blancos de contenedores internos */
    [data-testid="stAppViewContainer"] [data-testid="stVerticalBlock"],
    [data-testid="stAppViewContainer"] [data-testid="column"] > div:first-child,
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* ── FIX 1: Labels "Usuario" y "Contraseña" en blanco ── */
    [data-testid="stTextInput"] label,
    [data-testid="stTextInput"] label p,
    [data-testid="stTextInput"] label span,
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span {
        color: #ffffff !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 13px !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
    }

    /* Inputs */
    [data-testid="stTextInput"] input {
        background: rgba(255,255,255,0.93) !important;
        border: none !important;
        border-radius: 7px !important;
        color: #1a2a5e !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 15px !important;
        transition: box-shadow 0.25s !important;
    }
    [data-testid="stTextInput"] input:focus {
        box-shadow: 0 0 0 2px #C41E2E !important;
    }
    [data-testid="stTextInput"] input::placeholder {
        color: #8899bb !important;
    }

    /* ── FIX 2: Estilo del form container via CSS (sin div wrapper vacío) ── */
    [data-testid="stForm"] {
        background: rgba(13,43,110,0.45) !important;
        border: 1px solid rgba(100,150,255,0.18) !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        backdrop-filter: blur(10px) !important;
    }

    /* Botón submit */
    [data-testid="stFormSubmitButton"] button {
        width: 100% !important;
        background: linear-gradient(135deg, #d42030 0%, #a8151f 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 20px !important;
        letter-spacing: 5px !important;
        padding: 13px !important;
        box-shadow: 0 4px 20px rgba(196,30,46,0.55) !important;
        transition: all 0.25s !important;
    }
    [data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 28px rgba(196,30,46,0.7) !important;
    }

    /* Mensaje de error */
    [data-testid="stAlert"] {
        background: rgba(196,30,46,0.12) !important;
        border: 1px solid rgba(196,30,46,0.35) !important;
        border-radius: 8px !important;
        color: #f07080 !important;
    }

    /* Esquinas decorativas */
    .corner-tl, .corner-tr, .corner-bl, .corner-br {
        position: fixed; width: 40px; height: 40px; z-index: 100; pointer-events: none;
    }
    .corner-tl { top:16px; left:16px;  border-top:2px solid #C41E2E; border-left:2px solid #C41E2E; }
    .corner-tr { top:16px; right:16px; border-top:2px solid #C41E2E; border-right:2px solid #C41E2E; }
    .corner-bl { bottom:16px; left:16px;  border-bottom:2px solid #C41E2E; border-left:2px solid #C41E2E; }
    .corner-br { bottom:16px; right:16px; border-bottom:2px solid #C41E2E; border-right:2px solid #C41E2E; }

    /* ── FIX 3: Burbujas en HTML puro (sin JS) ── */
    @keyframes rise-bubble {
        0%   { transform: translateY(0);      opacity: 0.65; }
        80%  { opacity: 0.15; }
        100% { transform: translateY(-105vh); opacity: 0; }
    }
    .bbl {
        position: fixed; border-radius: 50%;
        background: rgba(180,210,255,0.20);
        border: 1px solid rgba(180,210,255,0.32);
        animation: rise-bubble linear infinite;
        pointer-events: none; z-index: 1;
        bottom: -20px;
    }
    </style>

    <!-- Esquinas decorativas -->
    <div class="corner-tl"></div>
    <div class="corner-tr"></div>
    <div class="corner-bl"></div>
    <div class="corner-br"></div>

    <!-- FIX 3: Burbujas con HTML puro, sin JS -->
    <div class="bbl" style="width:5px;height:5px;left:4%;animation-duration:9s;animation-delay:-2s;"></div>
    <div class="bbl" style="width:8px;height:8px;left:10%;animation-duration:14s;animation-delay:-7s;"></div>
    <div class="bbl" style="width:4px;height:4px;left:17%;animation-duration:11s;animation-delay:-1s;"></div>
    <div class="bbl" style="width:10px;height:10px;left:24%;animation-duration:16s;animation-delay:-11s;"></div>
    <div class="bbl" style="width:5px;height:5px;left:31%;animation-duration:8s;animation-delay:-4s;"></div>
    <div class="bbl" style="width:7px;height:7px;left:38%;animation-duration:13s;animation-delay:-9s;"></div>
    <div class="bbl" style="width:3px;height:3px;left:45%;animation-duration:10s;animation-delay:-0s;"></div>
    <div class="bbl" style="width:9px;height:9px;left:52%;animation-duration:17s;animation-delay:-6s;"></div>
    <div class="bbl" style="width:4px;height:4px;left:59%;animation-duration:12s;animation-delay:-13s;"></div>
    <div class="bbl" style="width:6px;height:6px;left:66%;animation-duration:9s;animation-delay:-3s;"></div>
    <div class="bbl" style="width:11px;height:11px;left:72%;animation-duration:15s;animation-delay:-8s;"></div>
    <div class="bbl" style="width:4px;height:4px;left:79%;animation-duration:11s;animation-delay:-5s;"></div>
    <div class="bbl" style="width:7px;height:7px;left:85%;animation-duration:13s;animation-delay:-10s;"></div>
    <div class="bbl" style="width:5px;height:5px;left:91%;animation-duration:8s;animation-delay:-15s;"></div>
    <div class="bbl" style="width:9px;height:9px;left:97%;animation-duration:16s;animation-delay:-2s;"></div>
    <div class="bbl" style="width:3px;height:3px;left:13%;animation-duration:10s;animation-delay:-18s;"></div>
    <div class="bbl" style="width:6px;height:6px;left:55%;animation-duration:12s;animation-delay:-16s;"></div>
    <div class="bbl" style="width:8px;height:8px;left:42%;animation-duration:7s;animation-delay:-12s;"></div>

    <!-- Label versión -->
    <div style="position:fixed;bottom:18px;right:22px;z-index:100;
        font-size:9px;letter-spacing:3px;color:rgba(200,216,240,0.3);
        text-transform:uppercase;font-family:'Rajdhani',sans-serif;">
        Sistema v2.0 · 2026
    </div>
    """, unsafe_allow_html=True)

    # ── Espaciado superior ────────────────────────────────────────────────────
    st.markdown("<div style='height:5vh'></div>", unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1.1, 1])
    with col_c:

        # ── Logo block ────────────────────────────────────────────────────────
        st.markdown("""
        <div style="
            background: rgba(13,43,110,0.60);
            border: 1px solid rgba(100,150,255,0.20);
            border-radius: 12px;
            padding: 22px 24px 18px;
            text-align: center;
            backdrop-filter: blur(8px);
            margin-bottom: 20px;
        ">
            <div style="
                font-family: 'Bebas Neue', sans-serif;
                font-size: 46px; letter-spacing: 6px;
                color: #ffffff;
                text-shadow: 0 0 30px rgba(100,150,255,0.5);
                line-height: 1;
            ">IMEMSA</div>
            <div style="
                width: 200px; height: 2px; margin: 10px auto;
                background: linear-gradient(to right, transparent, #C41E2E 30%, #C41E2E 70%, transparent);
                box-shadow: 0 0 10px rgba(196,30,46,0.55);
            "></div>
            <div style="
                font-size: 11px; letter-spacing: 6px;
                color: #c8d8f0; opacity: 0.7; text-transform: uppercase;
                font-family: 'Rajdhani', sans-serif;
            ">Motores Yamaha</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Subtítulo (FIX 2: sin div wrapper que genera rectángulo) ─────────
        st.markdown("""
        <p style="text-align:center; margin-bottom:18px; font-size:14px;
            letter-spacing:1px; color:#c8d8f0; line-height:1.6;
            font-family:'Rajdhani',sans-serif;">
            Sistema de Seguimiento ·
            <span style="color:#ffffff;font-weight:600;">Proceso Transversal</span><br>
            de Compra de Motores
        </p>
        """, unsafe_allow_html=True)

        # ── Form (FIX 2: sin st.markdown wrapper, estilo aplicado por CSS) ───
        with st.form("login_form"):
            username  = st.text_input("👤  Usuario",    placeholder="Ej. dgonzalez")
            password  = st.text_input("🔒  Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar al Sistema",
                                              use_container_width=True, type="primary")

        # ── Lógica de autenticación (sin cambios) ─────────────────────────────
        if submitted:
            ok, user_info = verify_login(username, password)
            if ok:
                st.session_state["user"]              = user_info
                st.session_state["page"]              = "dashboard"
                st.session_state["selected_order_id"] = None
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

        # ── Footer ────────────────────────────────────────────────────────────
        st.markdown(
            '<p style="text-align:center;color:rgba(255,255,255,.30);'
            'font-size:.72rem;margin-top:20px;font-family:\'Rajdhani\',sans-serif;">'
            '© 2026 IMEMSA — Uso interno. Acceso restringido.</p>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════
#  SIDEBAR NAVEGACIÓN
# ══════════════════════════════════════════════════════════

def render_sidebar() -> str:
    user = st.session_state["user"]
    page = st.session_state.get("page", "dashboard")

    # Forzar sidebar siempre expandido en cada rerun
    st.session_state["sidebar_state"] = "expanded"

    with st.sidebar:
        logo_sidebar()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        av = _avatar(user["avatar"], user["color"])
        st.markdown(
            f'<div style="padding:4px 16px 12px;">'
            f'{av}<span style="font-size:.9rem;font-weight:700;">{user["name"]}</span>'
            f'<br><span style="font-size:.75rem;padding-left:46px;opacity:.7;">{user["role"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

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

        data = _app_data()
        sem  = get_semaphore_summary(data)
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

        if sem["red"] > 0:
            st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
            if st.button("🚨  Enviar alertas vencidas", use_container_width=True):
                _send_overdue_alerts(_app_data())

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        if st.button("🚪  Cerrar sesión", use_container_width=True):
            _app_invalidate()
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    return page


def _send_overdue_alerts(data: dict) -> None:
    reds = get_red_activities(data)
    sent = 0
    for act in reds:
        ok = send_overdue_alert(
            to_email=act["_responsible_email"], to_name=act["_responsible_name"],
            order_number=act["_order_number"], activity_name=act["name"],
            due_date=act.get("due_date", "—"),
        )
        if ok:
            sent += 1
    if sent:
        st.toast(f"✅ {sent} alerta(s) enviadas.", icon="📧")
    else:
        st.toast("No se pudo enviar correos (verifica SMTP).", icon="⚠️")


# ══════════════════════════════════════════════════════════
#  PÁGINA 2 — TABLERO DE PEDIDOS
# ══════════════════════════════════════════════════════════

def page_dashboard() -> None:
    data         = _app_data()
    user         = st.session_state["user"]
    orders       = get_orders_for_user(data, user["username"])
    active       = [o for o in orders if o["status"] == "active"]
    completed    = [o for o in orders if o["status"] == "completed"]
    sem          = get_semaphore_summary(data)
    year         = datetime.today().year
    annual_count = len(orders)  # todos los pedidos activos + completados (no cancelados)

    st.markdown(
        f'<div style="display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:20px;">'
        f'<div>'
        f'  <div class="section-header" style="margin-bottom:0;">Tablero de Pedidos</div>'
        f'</div>'
        f'<span style="font-size:10px;letter-spacing:2px;color:rgba(180,210,255,.4);'
        f'font-family:Rajdhani,sans-serif;text-transform:uppercase;'
        f'padding:5px 12px;border:1px solid rgba(100,150,255,.18);border-radius:6px;'
        f'background:rgba(13,43,110,.35);">{datetime.today().strftime("%d/%m/%Y %H:%M")}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    _kpi(c1, str(len(active)),    "Pedidos Activos",   "#3b82f6")
    _kpi(c2, str(len(completed)), "Completados",        "#22c55e")
    _kpi(c3, str(annual_count),   f"Pedidos {year}",   "#a78bfa")
    _kpi(c4, str(sem["red"]),     "Actividades Venc.",  "#C41E2E")
    _kpi(c5, str(sem["yellow"]),  "En Riesgo",          "#f59e0b")

    st.markdown("<br>", unsafe_allow_html=True)

    if sem["red"] > 0:
        st.markdown(
            f'<div style="background:rgba(239,68,68,.10);border:1px solid rgba(239,68,68,.30);'
            f'border-radius:10px;padding:12px 18px;margin-bottom:16px;'
            f'display:flex;align-items:center;gap:10px;">'
            f'{_sem_dot("red")}'
            f'<span style="color:#fca5a5;font-weight:600;font-size:.88rem;font-family:Rajdhani,sans-serif;">'
            f'{sem["red"]} actividad(es) vencida(s). Usa "Enviar alertas" en el menú lateral.</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    my_tasks = get_my_pending_activities(data, user["username"])
    if my_tasks:
        st.markdown('<div class="section-header" style="font-size:1.2rem;">Mis Tareas Activas</div>',
                    unsafe_allow_html=True)
        for t in my_tasks:
            sem_color = get_semaphore(t)
            st.markdown(
                f'<div class="act-row act-row-inprogress" style="margin-bottom:6px;">'
                f'{_sem_dot(sem_color)}<span class="act-name">{t["name"]}</span>'
                f'<span class="phase-chip">{t["phase"]}</span>'
                f'<span class="act-meta"> · {t["_order_number"]} · Vence: {t.get("due_date","—")}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)

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
    acts            = order.get("activities", [])
    active_act      = next((a for a in acts if a["status"] in ("in_progress", "waiting_closure")), None)
    responsible_key = active_act["responsible_key"] if active_act else None
    responsible     = USERS.get(responsible_key, {})
    prog            = order.get("progress", 0)
    sem_color       = get_semaphore(active_act) if active_act else "gray"

    with st.container():
        st.markdown(
            f'<div class="order-card">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            f'  <div>'
            f'    <div class="order-number">{order["order_number"]}</div>'
            f'    <div class="order-model">📋 {order["motor_model"]} — Cant: {order["quantity"]} u. · {order["supplier"]}</div>'
            f'  </div>'
            f'  <div style="text-align:right;">'
            f'    {_badge(order["status"])}'
            f'    <div class="act-meta" style="margin-top:4px;">Creado: {order["created_at"]}</div>'
            f'  </div>'
            f'</div>'
            f'<div style="margin-top:10px;">{_progress_bar(prog)}</div>'
            f'<div style="margin-top:10px;display:flex;align-items:center;gap:12px;">'
            f'  {_sem_dot(sem_color)}'
            f'  <span style="font-size:.80rem;color:#4B5563;">'
            f'    {"Actividad activa: <strong>" + active_act["name"] + "</strong>" if active_act else "Sin actividad activa"}'
            f'  </span>'
            f'  {"· Resp: " + _avatar(responsible.get("avatar","?"), responsible.get("color","#ccc")) + "<span style=\'font-size:.78rem;\'>" + responsible.get("name","") + "</span>" if responsible_key else ""}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        col_btn, _ = st.columns([1, 4])
        with col_btn:
            if st.button("Ver actividades →", key=f"open_order_{order['id']}"):
                st.session_state["selected_order_id"] = order["id"]
                st.session_state["page"] = "activities"
                st.rerun()


# ══════════════════════════════════════════════════════════
#  PÁGINA 3 — ACTIVIDADES DEL PEDIDO
# ══════════════════════════════════════════════════════════

def page_activities() -> None:
    data     = _app_data()
    user     = st.session_state["user"]
    order_id = st.session_state.get("selected_order_id")

    orders    = get_orders_for_user(data, user["username"])
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

    sem_counts = {"green": 0, "yellow": 0, "red": 0, "gray": 0}
    for a in acts:
        c = get_semaphore(a)
        sem_counts[c] = sem_counts.get(c, 0) + 1

    st.markdown(
        f'<div style="background:rgba(13,43,110,.55);border-radius:12px;padding:20px 24px;'
        f'margin-bottom:18px;border:1px solid rgba(100,150,255,.20);border-top:3px solid #C41E2E;'
        f'backdrop-filter:blur(8px);">'
        f'<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">'
        f'<div>'
        f'  <div style="font-family:\'Bebas Neue\',sans-serif;font-size:1.5rem;letter-spacing:3px;color:#fff;">'
        f'  {order["order_number"]}</div>'
        f'  <div style="font-size:.84rem;color:rgba(180,210,255,.65);margin-top:3px;">'
        f'  {order["motor_model"]} &nbsp;·&nbsp; {order["quantity"]} unidades &nbsp;·&nbsp; {order["supplier"]}</div>'
        f'</div>'
        f'<div style="text-align:right;">{_badge(order["status"])}'
        f'  <div style="font-size:.76rem;color:rgba(180,210,255,.45);margin-top:4px;">Creado: {order["created_at"]}</div>'
        f'</div></div>'
        f'<div style="margin-top:14px;">{_progress_bar(prog)}</div>'
        f'<div style="margin-top:10px;display:flex;gap:16px;flex-wrap:wrap;">'
        f'  {_sem_dot("green")}<span style="font-size:.8rem;color:rgba(180,210,255,.7);">{sem_counts["green"]} en tiempo</span>'
        f'  {_sem_dot("yellow")}<span style="font-size:.8rem;color:rgba(180,210,255,.7);">{sem_counts["yellow"]} en riesgo</span>'
        f'  {_sem_dot("red")}<span style="font-size:.8rem;color:rgba(180,210,255,.7);">{sem_counts["red"]} vencidas</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-header">Actividades del Proceso (19)</div>',
                unsafe_allow_html=True)

    current_phase = None
    for act in acts:
        phase = act.get("phase", "")
        if phase != current_phase:
            current_phase = phase
            phase_acts = [a for a in acts if a.get("phase") == phase]
            phase_done = sum(1 for a in phase_acts if a["status"] == "completed")
            st.markdown(
                f'<div style="margin:18px 0 8px;display:flex;align-items:center;gap:8px;">'
                f'<span style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.1rem;'
                f'font-weight:700;color:#0D2B6E;">{phase}</span>'
                f'<span style="font-size:.72rem;color:#8592A3;">({phase_done}/{len(phase_acts)} completadas)</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        _render_activity_row(act, order, user, data)


def _render_activity_row(act: dict, order: dict, user: dict, data: dict) -> None:
    status          = act.get("status", "pending")
    sem_color       = get_semaphore(act)
    row_cls         = _act_row_class(status)
    responsible_key = act.get("responsible_key", "")
    responsible     = USERS.get(responsible_key, {})
    is_mine         = (responsible_key == user["username"])

    st.markdown(
        f'<div class="act-row {row_cls}">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">'
        f'  <div style="display:flex;align-items:center;gap:8px;">'
        f'    <span style="font-family:\'Barlow Condensed\',sans-serif;font-size:.85rem;'
        f'    font-weight:700;color:#8592A3;min-width:22px;">{act["id"]:02d}</span>'
        f'    {_sem_dot(sem_color)}'
        f'    <div><div class="act-name">{act["name"]}</div>'
        f'    <div class="act-meta">{act["description"]}</div></div>'
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
        + (f'<div style="margin-top:4px;font-size:.75rem;color:#6B7280;">📎 Evidencia: {act["evidence_name"]}</div>'
           if act.get("evidence_name") else "")
        + '</div>',
        unsafe_allow_html=True,
    )

    if is_mine and status == "in_progress":
        with st.expander(f"📋  Solicitar cierre — Actividad {act['id']:02d}: {act['name']}", expanded=False):
            with st.form(f"closure_form_{order['id']}_{act['id']}"):
                notes    = st.text_area("Observaciones / notas de cierre", height=90)
                evidence = st.file_uploader(
                    "Adjuntar evidencia (PDF, imagen, Excel…)",
                    type=["pdf", "png", "jpg", "jpeg", "xlsx", "docx"],
                    key=f"ev_{order['id']}_{act['id']}",
                )
                submitted = st.form_submit_button("✅  Enviar solicitud de cierre",
                                                   type="primary", use_container_width=True)
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
                        ok2, msg2, alerts = approve_closure(data, order["id"], act["id"])
                        if ok2:
                            for alert in alerts:
                                send_activation_email(**alert)
                            st.success(f"✅ Actividad cerrada al 100 %. {msg2}")
                            _app_save(data)
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

    data  = _app_data()
    year  = datetime.today().year
    count = len([o for o in data["orders"]
                 if o.get("year") == year and o.get("status") != "cancelled"])

    st.markdown('<div class="section-header">Registrar Nuevo Pedido de Motores</div>',
                unsafe_allow_html=True)

    remaining = MAX_ANNUAL_ORDERS - count
    color_bar = "#22c55e" if remaining > 5 else "#f59e0b" if remaining > 2 else "#ef4444"
    st.markdown(
        f'<div style="background:rgba(13,43,110,.50);border-radius:10px;padding:14px 20px;'
        f'margin-bottom:20px;border:1px solid rgba(100,150,255,.18);'
        f'border-left:4px solid {color_bar};backdrop-filter:blur(6px);">'
        f'<span style="font-family:\'Rajdhani\',sans-serif;font-weight:700;'
        f'letter-spacing:1px;color:{color_bar};">Pedidos {year}: {count} / {MAX_ANNUAL_ORDERS}</span>'
        f'<span style="font-size:.8rem;color:rgba(180,210,255,.5);margin-left:12px;">'
        f'Disponibles: {remaining}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if remaining == 0:
        st.error(f"🚫 Límite anual de {MAX_ANNUAL_ORDERS} pedidos alcanzado para {year}.")
        return

    with st.form("new_order_form"):
        col1, col2 = st.columns(2)
        with col1:
            motor_model  = st.text_input("Nombre del pedido",
                                         placeholder="Ej. Compra Motores 40HP — Temporada 2026")
            quantity     = st.number_input("Cantidad de motores", min_value=1, value=1, step=1)
        with col2:
            supplier     = st.text_input("Monto aproximado de O.C.",
                                         placeholder="Ej. $250,000 MXN")
            order_date   = st.date_input("Fecha de Pedido",
                                         value=datetime.today(),
                                         help="Puedes seleccionar una fecha anterior para registrar pedidos ya realizados.")

        notes = st.text_area("Justificación / Notas adicionales", height=100,
                             placeholder="Descripción del requerimiento, destino, prioridad…")

        st.markdown("<br>", unsafe_allow_html=True)
        col_b1, col_b2 = st.columns([1, 3])
        with col_b1:
            submitted = st.form_submit_button("🚀  Crear pedido", type="primary", use_container_width=True)
        with col_b2:
            st.info("Al crear el pedido se activará automáticamente la primera actividad "
                    "asignada a **David González** con fecha límite de 1 día hábil.")

        if submitted:
            if not motor_model.strip():
                st.error("El campo Nombre del pedido es obligatorio.")
            else:
                ok, msg, new_order = create_order(
                    data, motor_model, int(quantity),
                    supplier.strip(), notes, user["username"],
                    order_date.year,
                    order_date.strftime("%Y-%m-%d"),
                )
                if ok:
                    st.success(f"🎉 {msg}")
                    st.balloons()
                    _app_save(data)
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

    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "page" not in st.session_state:
        st.session_state["page"] = "login"
    if "selected_order_id" not in st.session_state:
        st.session_state["selected_order_id"] = None

    if st.session_state["user"] is None:
        page_login()
        return

    page = render_sidebar()

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
