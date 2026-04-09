"""
APIs externas para notificaciones.
  - Email REAL via Gmail SMTP (nativo de Python, sin dependencias extra)
  - WhatsApp y SMS: simulados con logs en consola

CONFIGURACION (solo 2 lineas en .env):
    EMAIL_SMTP_USER=tu_email@gmail.com
    EMAIL_SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # App Password de Google

Para obtener el App Password:
  1. Ir a https://myaccount.google.com/security
  2. Activar verificacion en 2 pasos
  3. Ir a "Contrasenas de aplicacion"
  4. Generar para Correo
"""
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from app.core.configuracion import configuracion
    _CONFIGURACION_DISPONIBLE = True
except Exception:
    configuracion = None
    _CONFIGURACION_DISPONIBLE = False


class EmailRequest:
    def __init__(self, to: str, subject: str, body: str):
        self.to = to
        self.subject = subject
        self.body = body


class EmailResponse:
    def __init__(self, delivered: str, message_id: str = ""):
        self.delivered = delivered
        self.message_id = message_id


class EmailAPI:
    """
    Envia emails REALES via Gmail SMTP.
    Sin credenciales en .env: modo simulacion (log en consola).
    """

    @staticmethod
    def send_email(request: EmailRequest) -> EmailResponse:
        if not request.to or "@" not in request.to:
            return EmailResponse(delivered="N")

        smtp_user = None
        smtp_password = None
        if _CONFIGURACION_DISPONIBLE and configuracion:
            smtp_user = getattr(configuracion, "email_smtp_user", None)
            smtp_password = getattr(configuracion, "email_smtp_password", None)

        if not smtp_user or not smtp_password:
            msg_id = f"EMAIL-SIM-{uuid.uuid4().hex[:10]}"
            print(f"[Email Simulado] {msg_id} -> {request.to} | Asunto: {request.subject}")
            print("  Agrega EMAIL_SMTP_USER y EMAIL_SMTP_PASSWORD al .env para envio real")
            return EmailResponse(delivered="Y", message_id=msg_id)

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = request.subject
            msg["From"] = smtp_user
            msg["To"] = request.to

            html_body = f"""
<html><body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px;">
  <div style="background:white;padding:24px;border-radius:10px;max-width:520px;
              margin:0 auto;border-top:4px solid #6c63ff;">
    <h2 style="color:#6c63ff;margin-top:0;font-size:18px;">
      TaskFlow &mdash; Notificacion
    </h2>
    <p style="color:#333;line-height:1.7;font-size:14px;">
      {request.body.replace(chr(10), "<br>")}
    </p>
    <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
    <p style="color:#999;font-size:11px;text-align:center;margin:0;">
      Mensaje automatico enviado desde TaskFlow
    </p>
  </div>
</body></html>"""

            msg.attach(MIMEText(html_body, "html"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            msg_id = f"GMAIL-{uuid.uuid4().hex[:12]}"
            print(f"[Email REAL enviado] {msg_id} -> {request.to}")
            return EmailResponse(delivered="Y", message_id=msg_id)

        except smtplib.SMTPAuthenticationError:
            print("[Email] Error de autenticacion Gmail — verifica EMAIL_SMTP_PASSWORD")
            return EmailResponse(delivered="N")
        except Exception as e:
            print(f"[Email] Error: {str(e)}")
            return EmailResponse(delivered="N")


class WhatsAppRequest:
    def __init__(self, phone: str, body: str):
        self.phone = phone
        self.body = body


class WhatsAppResponse:
    def __init__(self, status: str, message_id: str):
        self.status = status
        self.message_id = message_id


class WhatsAppAPI:
    @staticmethod
    def send_message(request: WhatsAppRequest) -> WhatsAppResponse:
        if not request.phone or not request.body:
            return WhatsAppResponse(status="failed", message_id="")
        msg_id = f"WA-SIM-{uuid.uuid4().hex[:8].upper()}"
        print(f"[WhatsApp Simulado] {msg_id} -> {request.phone} | {request.body[:80]}...")
        return WhatsAppResponse(status="sent", message_id=msg_id)


class SmsRequest:
    def __init__(self, number: str, text: str):
        self.number = number
        self.text = text


class SmsResponse:
    def __init__(self, code: int, description: str, message_id: str = ""):
        self.code = code
        self.description = description
        self.message_id = message_id


class SmsAPI:
    @staticmethod
    def send_sms(request: SmsRequest) -> SmsResponse:
        if not request.number or not request.text:
            return SmsResponse(code=400, description="Invalid")
        msg_id = f"SMS-SIM-{uuid.uuid4().hex[:8].upper()}"
        print(f"[SMS Simulado] {msg_id} -> {request.number} | {request.text[:80]}...")
        return SmsResponse(code=200, description="Simulated OK", message_id=msg_id)