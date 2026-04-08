"""
APIs externas SIMPLES para notificaciones.
✓ Email REAL vía Gmail SMTP (NATIVO de Python, sin dependencias)
✓ SMS/WhatsApp simulado con logs

REQUISITOS:
- Cambiar EMAIL_SMTP_USER y EMAIL_SMTP_PASSWORD en .env
  (Solo 2 credenciales, eso es todo!)
"""
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.configuracion import configuracion


# ── Email API (REAL con Gmail SMTP) ──────────────────────────────────────────
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
    Envía emails REALES vía Gmail SMTP.
    
    Setup simple (solo 3 pasos):
    1. Ir a https://myaccount.google.com/security
    2. Activar "2-Step Verification" (si no está)
    3. Ir a "App passwords" → generar para Correo
    4. Copiar contraseña a EMAIL_SMTP_PASSWORD en .env
    
    ¡Listo! Los emails se enviarán realmente a la bandeja.
    """

    @staticmethod
    def send_email(request: EmailRequest) -> EmailResponse:
        """Envía email REAL via Gmail SMTP"""
        
        if not request.to or "@" not in request.to:
            return EmailResponse(delivered="N", message_id="")

        try:
            # Obtener credenciales del .env usando pydantic
            smtp_user = configuracion.email_smtp_user
            smtp_password = configuracion.email_smtp_password

            if not smtp_user or not smtp_password:
                print("⚠️  EMAIL_SMTP_USER o EMAIL_SMTP_PASSWORD no configuradas en .env")
                return EmailResponse(delivered="N", message_id="")

            # Crear mensaje
            msg = MIMEMultipart("alternative")
            msg["Subject"] = request.subject
            msg["From"] = smtp_user
            msg["To"] = request.to

            # Cuerpo en HTML (bonito)
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
                    <div style="background: white; padding: 20px; border-radius: 8px; max-width: 500px; margin: 0 auto;">
                        <h2 style="color: #0066cc; margin-top: 0;">📬 Notificación TaskFlow</h2>
                        <p style="color: #333; line-height: 1.6;">
                            {request.body.replace(chr(10), '<br>')}
                        </p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                        <p style="color: #999; font-size: 12px; text-align: center;">
                            Este es un email automatizado desde TaskFlow.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, "html"))

            # Conectar a Gmail y enviar
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            msg_id = f"GMAIL-{uuid.uuid4().hex[:12]}"
            print(f"✅ Email enviado: {msg_id} → {request.to}")
            return EmailResponse(delivered="Y", message_id=msg_id)

        except smtplib.SMTPAuthenticationError:
            print("❌ Error: EMAIL_SMTP_PASSWORD incorrecta o no activada")
            return EmailResponse(delivered="N", message_id="")
        except Exception as e:
            print(f"❌ Error enviando email: {str(e)}")
            return EmailResponse(delivered="N", message_id="")


# ── WhatsApp API (SIMULADA con logs) ──────────────────────────────────────────
class WhatsAppRequest:
    def __init__(self, phone: str, body: str):
        self.phone = phone
        self.body = body


class WhatsAppResponse:
    def __init__(self, status: str, message_id: str):
        self.status = status
        self.message_id = message_id


class WhatsAppAPI:
    """
    Simula WhatsApp (para producción, usa Twilio).
    En desarrollo, muestra log de lo que se enviaría.
    """

    @staticmethod
    def send_message(request: WhatsAppRequest) -> WhatsAppResponse:
        """Simula envío de WhatsApp con log"""
        if not request.phone or not request.body:
            return WhatsAppResponse(status="failed", message_id="")

        msg_id = f"WA-SIM-{uuid.uuid4().hex[:8]}"
        print(f"📱 [WhatsApp Simulado] {msg_id} → {request.phone}")
        print(f"   Mensaje: {request.body[:80]}...")
        return WhatsAppResponse(status="sent", message_id=msg_id)


# ── SMS API (SIMULADA con logs) ───────────────────────────────────────────────
class SmsRequest:
    def __init__(self, number: str, text: str):
        self.number = number
        self.text = text


class SmsResponse:
    def __init__(self, code: int, description: str, message_id: str = None):
        self.code = code
        self.description = description
        self.message_id = message_id or ""


class SmsAPI:
    """
    Simula SMS (para producción, usa Twilio).
    En desarrollo, muestra log de lo que se enviaría.
    """

    @staticmethod
    def send_sms(request: SmsRequest) -> SmsResponse:
        """Simula envío de SMS con log"""
        if not request.number or not request.text:
            return SmsResponse(code=400, description="Invalid")

        msg_id = f"SMS-SIM-{uuid.uuid4().hex[:8]}"
        print(f"📞 [SMS Simulado] {msg_id} → {request.number}")
        print(f"   Mensaje: {request.text[:80]}...")
        return SmsResponse(code=200, description="Simulated", message_id=msg_id)
