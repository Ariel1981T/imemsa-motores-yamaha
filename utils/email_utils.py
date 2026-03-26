# utils/email_utils.py
# ──────────────────────────────────────────────────────────────────
#  Envío de correos de alerta (semáforo rojo / activación de tarea)
#  Configura SMTP en .streamlit/secrets.toml
# ──────────────────────────────────────────────────────────────────

from __future__ import annotations
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

try:
    import streamlit as st
    _SECRETS_AVAILABLE = True
except Exception:
    _SECRETS_AVAILABLE = False


def _get_smtp_config() -> dict | None:
    if not _SECRETS_AVAILABLE:
        return None
    try:
        return {
            "host":     st.secrets["smtp"]["host"],
            "port":     st.secrets["smtp"]["port"],
            "user":     st.secrets["smtp"]["user"],
            "password": st.secrets["smtp"]["password"],
            "from":     st.secrets["smtp"].get("from", st.secrets["smtp"]["user"]),
        }
    except Exception:
        return None


def _html_email(subject: str, body_html: str) -> str:
    return f"""
    <html><body style="font-family:Arial,sans-serif;background:#F4F6FA;padding:24px;">
      <div style="max-width:600px;margin:auto;background:#fff;border-radius:8px;
                  box-shadow:0 2px 8px rgba(0,0,0,.12);overflow:hidden;">
        <div style="background:#0D2B6E;padding:20px 28px;display:flex;align-items:center;">
          <span style="color:#fff;font-size:22px;font-weight:700;letter-spacing:1px;">
            IMEMSA · Sistema de Compra de Motores
          </span>
        </div>
        <div style="padding:28px;">
          <h2 style="color:#0D2B6E;margin-top:0;">{subject}</h2>
          {body_html}
          <hr style="border:none;border-top:1px solid #E5E7EB;margin:24px 0;">
          <p style="color:#8592A3;font-size:12px;">
            Este mensaje fue generado automáticamente el {datetime.today().strftime('%d/%m/%Y %H:%M')}.
            Por favor no responda a este correo.
          </p>
        </div>
      </div>
    </body></html>
    """


def send_activation_email(to_email: str, to_name: str, order_number: str,
                           activity_name: str, due_date: str) -> bool:
    """Notifica al responsable que su actividad fue activada."""
    cfg = _get_smtp_config()
    if not cfg:
        return False

    subject = f"[IMEMSA] Nueva actividad asignada — {order_number}"
    body = f"""
    <p>Estimado(a) <strong>{to_name}</strong>,</p>
    <p>Se le notifica que la siguiente actividad ha sido activada y requiere su atención:</p>
    <table style="border-collapse:collapse;width:100%;">
      <tr><td style="padding:8px;font-weight:700;color:#0D2B6E;width:40%;">Pedido</td>
          <td style="padding:8px;">{order_number}</td></tr>
      <tr style="background:#F4F6FA;">
          <td style="padding:8px;font-weight:700;color:#0D2B6E;">Actividad</td>
          <td style="padding:8px;">{activity_name}</td></tr>
      <tr><td style="padding:8px;font-weight:700;color:#0D2B6E;">Fecha límite</td>
          <td style="padding:8px;color:#C41E2E;font-weight:700;">{due_date}</td></tr>
    </table>
    <p style="margin-top:20px;">Por favor ingrese al sistema para registrar avances y adjuntar evidencias.</p>
    """
    return _send(cfg, to_email, subject, _html_email(subject, body))


def send_overdue_alert(to_email: str, to_name: str, order_number: str,
                       activity_name: str, due_date: str) -> bool:
    """Alerta de actividad vencida (semáforo rojo)."""
    cfg = _get_smtp_config()
    if not cfg:
        return False

    subject = f"🔴 [IMEMSA] Actividad VENCIDA — {order_number}"
    body = f"""
    <p>Estimado(a) <strong>{to_name}</strong>,</p>
    <p style="color:#C41E2E;font-weight:700;">
      ⚠️ La siguiente actividad ha superado su fecha límite y requiere atención inmediata:
    </p>
    <table style="border-collapse:collapse;width:100%;border:2px solid #C41E2E;border-radius:6px;">
      <tr><td style="padding:8px;font-weight:700;color:#0D2B6E;width:40%;">Pedido</td>
          <td style="padding:8px;">{order_number}</td></tr>
      <tr style="background:#FFF5F5;">
          <td style="padding:8px;font-weight:700;color:#0D2B6E;">Actividad</td>
          <td style="padding:8px;">{activity_name}</td></tr>
      <tr><td style="padding:8px;font-weight:700;color:#0D2B6E;">Fecha límite</td>
          <td style="padding:8px;color:#C41E2E;font-weight:700;">{due_date}</td></tr>
    </table>
    <p style="margin-top:20px;">
      Por favor ingrese al sistema IMEMSA y registre la solicitud de cierre con la evidencia correspondiente.
    </p>
    """
    return _send(cfg, to_email, subject, _html_email(subject, body))


def _send(cfg: dict, to_email: str, subject: str, html: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = cfg["from"]
        msg["To"]      = to_email
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(cfg["user"], cfg["password"])
            server.sendmail(cfg["from"], [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False
