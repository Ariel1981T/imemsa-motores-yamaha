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
    "dgonzalez": {
        "password_hash": _h("Lf280606"),
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
        "password_hash": _h("1967Jep1"),
        "name": "Jaime Espinoza",
        "role": "Líder Comercial",
        "email": "jespinoza@imemsa.com.mx",
        "can_create_orders": False,
        "avatar": "JE",
        "color": "#059669",
    },
    "kmerino": {
        "password_hash": _h("Kmerino23*"),
        "name": "Karla Merino",
        "role": "Líder Tesorería",
        "email": "kmerino@imemsa.com.mx",
        "can_create_orders": False,
        "avatar": "KM",
        "color": "#D97706",
    },
    "cmuniz": {
        "password_hash": _h("Motor3s"),
        "name": "Claudia Muñoz",
        "role": "Líder Logística",
        "email": "cmuniz@imemsa.com.mx",
        "can_create_orders": False,
        "avatar": "CM",
        "color": "#DC2626",
    },
    # ── Nuevo usuario: Karla Merino (Tesorería) ──────────────────────────────
    "ratlaco": {
        "password_hash": _h("Imemsa2026*"),
        "name": "Karla Merino",
        "role": "Tesorería",
        "email": "kmerino@imemsa.com.mx",
        "can_create_orders": False,
        "avatar": "KM",
        "color": "#0891B2",
    },
}

# ── Catálogo de 19 actividades (nombres según Yamaha_StageCatalog col. C) ────
ACTIVITIES_TEMPLATE: list[dict] = [
    # Fase 1 — Planificación
    {
        "id": 1, "phase": "Planificación",
        "name": "Establecer presupuesto de compras",
        "description": "Definir el sugerido de compra y establecer el presupuesto anual para motores.",
        "responsible_key": "dgonzalez",
        "days_allocated": 1,
    },
    {
        "id": 2, "phase": "Planificación",
        "name": "Revisar y determinar el importe de compra",
        "description": "Analizar historial, mercado y necesidades para fijar el importe definitivo.",
        "responsible_key": "jespinoza",
        "days_allocated": 1,
    },
    {
        "id": 3, "phase": "Planificación",
        "name": "Ajustes finales",
        "description": "Realizar ajustes finales al sugerido de compra con base en retroalimentación comercial.",
        "responsible_key": "jespinoza",
        "days_allocated": 1,
    },
    {
        "id": 4, "phase": "Planificación",
        "name": "Autorizar el sugerido",
        "description": "Obtener autorización formal del sugerido de compra por parte de la supervisión.",
        "responsible_key": "dgonzalez",
        "days_allocated": 1,
    },
    # Fase 2 — Pedido y Confirmación
    {
        "id": 5, "phase": "Pedido y Confirmación",
        "name": "Colocación de pedido a Japón",
        "description": "Enviar orden de compra oficial a Yamaha Japón con especificaciones y cantidades.",
        "responsible_key": "jespinoza",
        "days_allocated": 1,
    },
    {
        "id": 6, "phase": "Pedido y Confirmación",
        "name": "Aviso a áreas sustantivas",
        "description": "Notificar a Tesorería, Logística y demás áreas involucradas sobre el pedido colocado.",
        "responsible_key": "jespinoza",
        "days_allocated": 1,
    },
    {
        "id": 7, "phase": "Pedido y Confirmación",
        "name": "Japón confirma la producción",
        "description": "Recibir confirmación formal de Yamaha Japón sobre aceptación y fechas de producción.",
        "responsible_key": "jespinoza",
        "days_allocated": 20,
    },
    # Fase 3 — Producción Proveedor
    {
        "id": 8, "phase": "Producción Proveedor",
        "name": "Producción de los motores",
        "description": "Seguimiento al proceso de fabricación de los motores en planta Yamaha Japón.",
        "responsible_key": "jespinoza",
        "days_allocated": 90,
    },
    # Fase 4 — Pedido y Confirmación (post-producción)
    {
        "id": 9, "phase": "Pedido y Confirmación",
        "name": "Sales confirmation",
        "description": "Recibir sales confirmation con fechas definitivas de pago y llegada de mercancía.",
        "responsible_key": "jespinoza",
        "days_allocated": 1,
    },
    # Fase 5 — Embarque y Pago
    {
        "id": 10, "phase": "Embarque y Pago",
        "name": "Pago de motores",
        "description": "Procesar transferencia internacional de pago de los motores conforme sales confirmation.",
        "responsible_key": "kmerino",
        "days_allocated": 2,
    },
    {
        "id": 11, "phase": "Embarque y Pago",
        "name": "Confirmación de pago",
        "description": "Enviar comprobante de pago al proveedor y obtener acuse de recibo.",
        "responsible_key": "jespinoza",
        "days_allocated": 1,
    },
    {
        "id": 12, "phase": "Embarque y Pago",
        "name": "Envío de facturas y lista de series",
        "description": "Recibir de Yamaha las facturas comerciales y listado de números de serie por motor.",
        "responsible_key": "cmuniz",
        "days_allocated": 7,
    },
    {
        "id": 13, "phase": "Embarque y Pago",
        "name": "Embarque",
        "description": "Confirmar el embarque de los motores en puerto de origen Japón.",
        "responsible_key": "cmuniz",
        "days_allocated": 1,
    },
    {
        "id": 14, "phase": "Embarque y Pago",
        "name": "Trayecto de contenedor en mar",
        "description": "Monitorear el trayecto marítimo del contenedor desde Japón hasta México.",
        "responsible_key": "cmuniz",
        "days_allocated": 30,
    },
    {
        "id": 15, "phase": "Embarque y Pago",
        "name": "Arribo a puerto",
        "description": "Confirmar arribo del contenedor al puerto mexicano y coordinar con agente aduanal.",
        "responsible_key": "cmuniz",
        "days_allocated": 2,
    },
    # Fase 6 — Aduana y Recepción
    {
        "id": 16, "phase": "Aduana y Recepción",
        "name": "Pago de impuestos",
        "description": "Procesar pago de impuestos de importación (IVA/IGI) y gastos aduanales.",
        "responsible_key": "cmuniz",
        "days_allocated": 1,
    },
    {
        "id": 17, "phase": "Aduana y Recepción",
        "name": "Confirmación de cita para despacho",
        "description": "Coordinar y confirmar la cita con el agente aduanal para el despacho de la mercancía.",
        "responsible_key": "cmuniz",
        "days_allocated": 2,
    },
    {
        "id": 18, "phase": "Aduana y Recepción",
        "name": "Despacho aduanal",
        "description": "Realizar el despacho aduanal y obtener el levante de la mercancía.",
        "responsible_key": "cmuniz",
        "days_allocated": 1,
    },
    {
        "id": 19, "phase": "Aduana y Recepción",
        "name": "Estancia en patio de transportista",
        "description": "Coordinar la estancia de la mercancía en patio del transportista previo a su traslado.",
        "responsible_key": "cmuniz",
        "days_allocated": 1,
    },
    {
        "id": 20, "phase": "Aduana y Recepción",
        "name": "Salida y monitoreo de embarque",
        "description": "Confirmar salida de aduana y monitorear el traslado terrestre hacia CEDIS.",
        "responsible_key": "cmuniz",
        "days_allocated": 1,
    },
    {
        "id": 21, "phase": "Aduana y Recepción",
        "name": "Arribo a CEDIS",
        "description": "Recibir el contenedor en el centro de distribución IMEMSA y programar descarga.",
        "responsible_key": "cmuniz",
        "days_allocated": 1,
    },
    {
        "id": 22, "phase": "Aduana y Recepción",
        "name": "Recibo de motores en sistema Oracle",
        "description": "Inspeccionar motores, dar de alta en sistema Oracle y cerrar el expediente del pedido.",
        "responsible_key": "dgonzalez",
        "days_allocated": 1,
    },
]

PHASES = [
    "Planificación",
    "Pedido y Confirmación",
    "Producción Proveedor",
    "Embarque y Pago",
    "Aduana y Recepción",
]

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
