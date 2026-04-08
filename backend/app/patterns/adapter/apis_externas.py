"""
APIs externas simuladas de notificación.
En producción estas clases se reemplazarían por las SDKs reales
(Twilio para WhatsApp/SMS, SendGrid para Email, etc.)

NOTA: Pueden ser integradas fácilmente con SDKs reales reemplazando
los tipos de datos y la lógica de send_* manteniendo la interfaz.
"""
import uuid
from datetime import datetime


# ── WhatsApp API (simulada — equivalente a XBankAPI) ─────────────────────────
class WhatsAppRequest:
    def __init__(self, phone: str, body: str):
        self.phone = phone
        self.body = body


class WhatsAppResponse:
    def __init__(self, status: str, message_id: str):
        self.status = status      # "sent" | "failed"
        self.message_id = message_id


class WhatsAppAPI:
    """
    Simula la API de WhatsApp Business (Twilio, Meta Cloud API, etc.)
    
    Para integración real, reemplazar con:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(...)
    """

    @staticmethod
    def send_message(request: WhatsAppRequest) -> WhatsAppResponse:
        """
        Simula envío de mensaje a WhatsApp.
        En producción: valida el número, usa SDK oficial, maneja errores API.
        """
        # Simulación: mensajes a números válidos (7+ dígitos) se envían
        if request.phone and len(request.phone.replace(" ", "")) >= 7:
            # Generar ID único para simular API real
            msg_id = f"WA-{uuid.uuid4().hex[:12].upper()}"
            # Log simulado (en producción: almacenar en DB)
            print(f"[WhatsApp] {msg_id} → {request.phone} | {request.body[:60]}...")
            return WhatsAppResponse(status="sent", message_id=msg_id)
        return WhatsAppResponse(status="failed", message_id="")


# ── Email API (simulada — equivalente a YBankAPI) ────────────────────────────
class EmailRequest:
    def __init__(self, to: str, subject: str, body: str):
        self.to = to
        self.subject = subject
        self.body = body


class EmailResponse:
    def __init__(self, delivered: str, message_id: str = None):
        self.delivered = delivered    # "Y" | "N"
        self.message_id = message_id or ""


class EmailAPI:
    """
    Simula la API de Email (SendGrid, AWS SES, etc.)
    
    Para integración real, reemplazar con:
        import sendgrid
        sg = sendgrid.SendGridAPIClient(SENDGRID_API_KEY)
        mail = Mail(from_email, to_email, subject, html_content)
        response = sg.send(mail)
    """

    @staticmethod
    def send_email(request: EmailRequest) -> EmailResponse:
        """
        Simula envío de email.
        En producción: valida email, usa SMTP o SDK, maneja bounces.
        """
        if request.to and "@" in request.to:
            # Email ID simulado (en producción: ID real de SendGrid, AWS SES, etc.)
            email_id = f"EMAIL-{uuid.uuid4().hex[:12].upper()}"
            # Log simulado
            print(f"[Email] {email_id} → {request.to} | {request.subject}")
            return EmailResponse(delivered="Y", message_id=email_id)
        return EmailResponse(delivered="N")


# ── SMS API (simulada) ────────────────────────────────────────────────────────
class SmsRequest:
    def __init__(self, number: str, text: str):
        self.number = number
        self.text = text


class SmsResponse:
    def __init__(self, code: int, description: str, message_id: str = None):
        self.code = code           # 200 = éxito
        self.description = description
        self.message_id = message_id or ""


class SmsAPI:
    """
    Simula la API de SMS (Twilio SMS, AWS SNS, etc.)
    
    Para integración real, reemplazar con:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(body=..., from_=..., to=...)
    """

    @staticmethod
    def send_sms(request: SmsRequest) -> SmsResponse:
        """
        Simula envío de SMS.
        En producción: valida número, usa API oficial, maneja entregas.
        """
        # Simulación: números con prefijo válido (7+ dígitos) se envían
        if request.number and len(request.number) >= 7:
            sms_id = f"SMS-{uuid.uuid4().hex[:12].upper()}"
            # Log simulado
            print(f"[SMS] {sms_id} → {request.number} | {request.text[:60]}...")
            return SmsResponse(code=200, description="Message enqueued", message_id=sms_id)
        return SmsResponse(code=400, description="Invalid phone number")