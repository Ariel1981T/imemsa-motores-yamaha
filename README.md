# IMEMSA · Sistema de Compra de Motores Yamaha 🚤

Sistema web profesional para el seguimiento del **proceso transversal de compra de motores Yamaha**, desarrollado con Python y Streamlit.

---

## 📋 Funcionalidades

| Módulo | Descripción |
|--------|-------------|
| 🔐 **Login** | Autenticación segura con hash SHA-256 (5 usuarios) |
| 📊 **Tablero** | Vista general de todos los pedidos con KPIs, semáforo y tareas propias |
| 📋 **Actividades** | Las 19 etapas del proceso, con cierre y adjunto de evidencias |
| ➕ **Nuevo pedido** | Creación de pedido (exclusivo David González, máx. 20/año) |
| 🚨 **Alertas** | Envío automático de correos por semáforo rojo (SMTP configurable) |

---

## 👥 Usuarios del sistema

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| `dgonzalez` | `Imemsa2024*` | Supervisor (puede crear pedidos) |
| `fgarduno`  | `Imemsa2024*` | Responsable de Proceso |
| `jespinoza` | `Imemsa2024*` | Líder Comercial |
| `ccastaneda`| `Imemsa2024*` | Líder Tesorería |
| `cmunoz`    | `Imemsa2024*` | Líder Logística |

> ⚠️ **Cambia las contraseñas en `utils/constants.py`** antes de publicar.

---

## 🔄 Las 19 Actividades del Proceso

| # | Fase | Actividad | Responsable | Días hábiles |
|---|------|-----------|-------------|:---:|
| 01 | Solicitud | Solicitud de Compra | David González | 2 |
| 02 | Solicitud | Validación Técnica del Motor | David González | 3 |
| 03 | Cotización | Solicitud de Cotización | Jaime Espinoza | 2 |
| 04 | Cotización | Recepción de Cotizaciones | Jaime Espinoza | 7 |
| 05 | Cotización | Análisis Comparativo | Jaime Espinoza | 3 |
| 06 | Autorización | Autorización de Dirección | David González | 2 |
| 07 | Autorización | Gestión de Presupuesto | Carmen Castañeda | 3 |
| 08 | Autorización | Generación de Orden de Compra | Flor Garduño | 2 |
| 09 | Autorización | Envío de OC al Proveedor | Flor Garduño | 1 |
| 10 | Producción | Confirmación del Proveedor | Jaime Espinoza | 5 |
| 11 | Producción | Anticipo / Primer Pago | Carmen Castañeda | 5 |
| 12 | Producción | Seguimiento de Fabricación | Jaime Espinoza | 30 |
| 13 | Producción | Notificación de Embarque | Jaime Espinoza | 3 |
| 14 | Importación | Documentos de Importación | Claudia Muñoz | 5 |
| 15 | Importación | Pago de Liquidación | Carmen Castañeda | 3 |
| 16 | Importación | Gestión con Agente Aduanal | Claudia Muñoz | 7 |
| 17 | Importación | Liberación en Aduana | Claudia Muñoz | 5 |
| 18 | Importación | Transporte a Planta IMEMSA | Claudia Muñoz | 3 |
| 19 | Recepción | Recepción, Inspección y Cierre | David González | 2 |

---

## 🚦 Semáforo

| Color | Condición |
|-------|-----------|
| 🟢 Verde | Completada o < 70 % del plazo consumido |
| 🟡 Amarillo | Entre 70 % y 100 % del plazo (en riesgo) |
| 🔴 Rojo | Vencida (> 100 % del plazo) — envía alerta por correo |

---

## 🚀 Instalación y ejecución local

```bash
# 1. Clonar el repositorio
git clone https://github.com/imemsa/motores-yamaha.git
cd motores-yamaha

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
streamlit run app.py
```

La aplicación se abre en `http://localhost:8501`

---

## ☁️ Despliegue en Streamlit Cloud

1. Haz fork / push del repositorio a GitHub  
2. Entra a [share.streamlit.io](https://share.streamlit.io) → **New app**  
3. Conecta el repo, elige `app.py` como archivo principal  
4. En **Advanced settings → Secrets**, agrega tu configuración SMTP:

```toml
[smtp]
host     = "smtp.gmail.com"
port     = 587
user     = "noreply@imemsa.com.mx"
password = "tu_contraseña_app"
from     = "IMEMSA Motores <noreply@imemsa.com.mx>"
```

> ⚠️ **Nota sobre persistencia de datos en Streamlit Cloud**: el sistema de archivos se reinicia en cada deployment. Para producción, se recomienda migrar el almacenamiento a **Google Sheets** (via `gspread`) o **Supabase** (PostgreSQL gratuito). Contacta al administrador del sistema para configurar.

---

## 📁 Estructura del proyecto

```
imemsa_motores/
├── app.py                   # Aplicación principal
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   ├── config.toml          # Tema IMEMSA
│   └── secrets.toml         # ← NO subir al repo (está en .gitignore)
├── utils/
│   ├── __init__.py
│   ├── constants.py         # Usuarios, actividades, colores
│   ├── data_manager.py      # CRUD y lógica de negocio
│   ├── auth.py              # Autenticación
│   └── email_utils.py       # Alertas por correo
└── data/
    └── orders.json          # Base de datos local (auto-generado)
```

---

## 🛠️ Personalización

- **Cambiar contraseñas**: editar `utils/constants.py` → función `_h("nueva_contraseña")`
- **Modificar actividades**: editar `ACTIVITIES_TEMPLATE` en `utils/constants.py`
- **Agregar usuarios**: agregar entrada en el dict `USERS` en `utils/constants.py`
- **Colores IMEMSA**: `IMEMSA_NAVY = "#0D2B6E"` y `IMEMSA_RED = "#C41E2E"`

---

© 2024 IMEMSA · Desarrollado por el equipo de Sistemas
