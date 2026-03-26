# utils/constants.py
# ─────────────────────────────────────────────
#  IMEMSA · Sistema de Compra de Motores Yamaha
# ─────────────────────────────────────────────

import hashlib

# ── Marca IMEMSA ────────────────────────────────────────────────────────────
IMEMSA_NAVY  = "#0D2B6E"
IMEMSA_RED   = "#C41E2E"
IMEMSA_LIGHT = "#F4F6FA"
IMEMSA_GRAY  = "#8592A3"
MAX_ANNUAL_ORDERS = 20

# ── Usuarios del sistema ─────────────────────────────────────────────────────
def _h(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

USERS: dict[str, dict] = {
    "dgonzalez@imemsa.com.mx": {
        "password_hash": _h("Imemsa2026*"),
        "name": "David González",
        "role": "Supervisor",
        "email": "dgonzalez@imemsa.com.mx",
        "can_create_orders": True,
        "avatar": "DG",
        "color": "#2563EB",
    },
    "fgarduno": {
        "password_hash": _h("Imemsa2024*"),
        "name": "Flor Garduño",
        "role": "Responsable de Proceso",
        "email": "fgarduno@imemsa.com.mx",
        "can_create_orders": False,
        "avatar": "FG",
        "color": "#7C3AED",
    },
    "jespinoza": {
        "password_hash": _h("Imemsa2024*"),
        "name": "Jaime Espinoza",
        "role": "Líder Comercial",
        "email": "jespinoza@imemsa.com.mx",
        "can_create_orders": False,
        "avatar": "JE",
        "color": "#059669",
    },
    "ccastaneda": {
        "password_hash": _h("Imemsa2024*"),
        "name": "Carmen Castañeda",
        "role": "Líder Tesorería",
        "email": "ccastaneda@imemsa.com.mx",
        "can_create_orders": False,
        "avatar": "CC",
        "color": "#D97706",
    },
    "cmunoz": {
        "password_hash": _h("Imemsa2024*"),
        "name": "Claudia Muñoz",
        "role": "Líder Logística",
        "email": "cmunoz@imemsa.com.mx",
        "can_create_orders": False,
        "avatar": "CM",
        "color": "#DC2626",
    },
}

# ── Catálogo de 19 actividades ───────────────────────────────────────────────
ACTIVITIES_TEMPLATE: list[dict] = [
    # Fase 1 — Solicitud y Autorización
    {
        "id": 1, "phase": "Solicitud",
        "name": "Solicitud de Compra",
        "description": "Generar la requisición formal indicando modelo, cantidad y justificación técnica.",
        "responsible_key": "dgonzalez",
        "days_allocated": 2,
    },
    {
        "id": 2, "phase": "Solicitud",
        "name": "Validación Técnica del Motor",
        "description": "Verificar especificaciones técnicas requeridas vs. catálogo Yamaha vigente.",
        "responsible_key": "dgonzalez",
        "days_allocated": 3,
    },
    # Fase 2 — Cotización
    {
        "id": 3, "phase": "Cotización",
        "name": "Solicitud de Cotización al Proveedor",
        "description": "Enviar RFQ formal al distribuidor Yamaha autorizado.",
        "responsible_key": "jespinoza",
        "days_allocated": 2,
    },
    {
        "id": 4, "phase": "Cotización",
        "name": "Recepción de Cotizaciones",
        "description": "Recibir y concentrar propuestas económicas del proveedor.",
        "responsible_key": "jespinoza",
        "days_allocated": 7,
    },
    {
        "id": 5, "phase": "Cotización",
        "name": "Análisis Comparativo",
        "description": "Elaborar cuadro comparativo de precios, tiempos y condiciones.",
        "responsible_key": "jespinoza",
        "days_allocated": 3,
    },
    # Fase 3 — Autorización y OC
    {
        "id": 6, "phase": "Autorización",
        "name": "Autorización de Dirección",
        "description": "Presentar comparativo y obtener visto bueno de Dirección General.",
        "responsible_key": "dgonzalez",
        "days_allocated": 2,
    },
    {
        "id": 7, "phase": "Autorización",
        "name": "Gestión de Presupuesto",
        "description": "Validar disponibilidad de presupuesto y afectación contable.",
        "responsible_key": "ccastaneda",
        "days_allocated": 3,
    },
    {
        "id": 8, "phase": "Autorización",
        "name": "Generación de Orden de Compra",
        "description": "Formalizar la OC en el sistema ERP con todos los datos del pedido.",
        "responsible_key": "fgarduno",
        "days_allocated": 2,
    },
    {
        "id": 9, "phase": "Autorización",
        "name": "Envío de OC al Proveedor",
        "description": "Transmitir la OC oficial firmada al distribuidor Yamaha.",
        "responsible_key": "fgarduno",
        "days_allocated": 1,
    },
    # Fase 4 — Seguimiento de Producción
    {
        "id": 10, "phase": "Producción",
        "name": "Confirmación del Proveedor",
        "description": "Recibir acuse de recibo y confirmación de fecha estimada de entrega.",
        "responsible_key": "jespinoza",
        "days_allocated": 5,
    },
    {
        "id": 11, "phase": "Producción",
        "name": "Anticipo / Primer Pago",
        "description": "Procesar transferencia de anticipo conforme condiciones pactadas.",
        "responsible_key": "ccastaneda",
        "days_allocated": 5,
    },
    {
        "id": 12, "phase": "Producción",
        "name": "Seguimiento de Fabricación",
        "description": "Monitorear avance de producción y comunicación con proveedor.",
        "responsible_key": "jespinoza",
        "days_allocated": 30,
    },
    {
        "id": 13, "phase": "Producción",
        "name": "Notificación de Embarque",
        "description": "Recibir documentos de embarque: BL, factura comercial, packing list.",
        "responsible_key": "jespinoza",
        "days_allocated": 3,
    },
    # Fase 5 — Importación y Logística
    {
        "id": 14, "phase": "Importación",
        "name": "Documentos de Importación",
        "description": "Validar y tramitar pedimento de importación con agente aduanal.",
        "responsible_key": "cmunoz",
        "days_allocated": 5,
    },
    {
        "id": 15, "phase": "Importación",
        "name": "Pago de Liquidación",
        "description": "Procesar pago final del saldo y derechos de importación (IVA/IGI).",
        "responsible_key": "ccastaneda",
        "days_allocated": 3,
    },
    {
        "id": 16, "phase": "Importación",
        "name": "Gestión con Agente Aduanal",
        "description": "Coordinar proceso de despacho aduanal y verificación de mercancias.",
        "responsible_key": "cmunoz",
        "days_allocated": 7,
    },
    {
        "id": 17, "phase": "Importación",
        "name": "Liberación en Aduana",
        "description": "Confirmar levante de mercancía y custodia para transporte.",
        "responsible_key": "cmunoz",
        "days_allocated": 5,
    },
    {
        "id": 18, "phase": "Importación",
        "name": "Transporte a Planta IMEMSA",
        "description": "Coordinar flete terrestre desde aduana hasta instalaciones en Veracruz.",
        "responsible_key": "cmunoz",
        "days_allocated": 3,
    },
    # Fase 6 — Recepción y Cierre
    {
        "id": 19, "phase": "Recepción",
        "name": "Recepción, Inspección y Cierre",
        "description": "Inspeccionar motores recibidos, dar alta en sistema ERP y cerrar expediente.",
        "responsible_key": "dgonzalez",
        "days_allocated": 2,
    },
]

PHASES = ["Solicitud", "Cotización", "Autorización", "Producción", "Importación", "Recepción"]

MOTOR_MODELS = [
    "Yamaha F15C", "Yamaha F20B", "Yamaha F25D",
    "Yamaha F40F", "Yamaha F60C", "Yamaha F70A",
    "Yamaha F80A", "Yamaha F100B", "Yamaha F115A",
    "Yamaha F150F", "Yamaha F200F", "Yamaha F225F",
]

STATUS_LABELS = {
    "pending":         "⏳ Pendiente",
    "in_progress":     "🔄 En Proceso",
    "waiting_closure": "📋 Solicitud de Cierre",
    "completed":       "✅ Completada",
    "blocked":         "🚫 Bloqueada",
}

ORDER_STATUS_LABELS = {
    "active":    "En Proceso",
    "completed": "Completado",
    "cancelled": "Cancelado",
}
