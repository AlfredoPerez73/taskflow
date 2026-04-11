"""
APIs externas para notificaciones.
  - Email REAL via Gmail SMTP (nativo de Python, sin dependencias extra)
  - WhatsApp y SMS REALES via Twilio (si esta configurado)
  - Si faltan credenciales de Twilio, devuelve error explícito
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from app.core.configuracion import configuracion
    _CONFIGURACION_DISPONIBLE = True
except Exception:
    configuracion = None
    _CONFIGURACION_DISPONIBLE = False


def _twilio_config():
    if not (_CONFIGURACION_DISPONIBLE and configuracion):
        return None, None, None, None

    return (
        (getattr(configuracion, "twilio_account_sid", None) or "").strip(),
        (getattr(configuracion, "twilio_auth_token", None) or "").strip(),
        (getattr(configuracion, "twilio_sms_from", None) or "").strip(),
        (getattr(configuracion, "twilio_whatsapp_from", None) or "").strip(),
    )


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
            print("[Email] Falta configuración SMTP: EMAIL_SMTP_USER y EMAIL_SMTP_PASSWORD")
            return EmailResponse(delivered="N", message_id="")

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

            msg_id = msg.get("Message-ID", "")
            print(f"[Email REAL enviado] -> {request.to}")
            return EmailResponse(delivered="Y", message_id=msg_id)

        except smtplib.SMTPAuthenticationError:
            print("[Email] Error de autenticacion Gmail — verifica EMAIL_SMTP_PASSWORD")
            return EmailResponse(delivered="N")
        except Exception as e:
            print(f"[Email] Error: {str(e)}")
            return EmailResponse(delivered="N")


class WhatsAppRequest:
    def __init__(self, phone: str, body: str = "", content_sid: str = "", content_variables: str = ""):
        self.phone = phone
        self.body = body
        self.content_sid = content_sid
        self.content_variables = content_variables


class WhatsAppResponse:
    def __init__(self, status: str, message_id: str, error_code: str = "", error_message: str = ""):
        self.status = status
        self.message_id = message_id
        self.error_code = error_code
        self.error_message = error_message


class WhatsAppAPI:
    @staticmethod
    def send_message(request: WhatsAppRequest) -> WhatsAppResponse:
        if not request.phone:
            return WhatsAppResponse(status="failed", message_id="")
        if not request.body and not request.content_sid:
            return WhatsAppResponse(status="failed", message_id="")

        account_sid, auth_token, _sms_from, wa_from = _twilio_config()

        if account_sid and auth_token and wa_from:
            try:
                from twilio.rest import Client

                client = Client(account_sid, auth_token)
                from_number = wa_from if wa_from.startswith("whatsapp:") else f"whatsapp:{wa_from}"
                to_number = request.phone if request.phone.startswith("whatsapp:") else f"whatsapp:{request.phone}"
                payload = {"from_": from_number, "to": to_number}
                if request.content_sid:
                    payload["content_sid"] = request.content_sid
                    if request.content_variables:
                        payload["content_variables"] = request.content_variables
                else:
                    payload["body"] = request.body
                mensaje = client.messages.create(**payload)
                return WhatsAppResponse(
                    status=(mensaje.status or ""),
                    message_id=mensaje.sid or "",
                    error_code=str(mensaje.error_code or ""),
                    error_message=str(mensaje.error_message or ""),
                )
            except Exception as e:
                print(f"[WhatsApp Twilio] Error: {str(e)}")
                return WhatsAppResponse(status="failed", message_id="", error_message=str(e))

        print("  Falta configuración Twilio: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN y TWILIO_WHATSAPP_FROM")
        return WhatsAppResponse(status="failed", message_id="")


class SmsRequest:
    def __init__(self, number: str, text: str):
        self.number = number
        self.text = text


class SmsResponse:
    def __init__(
        self,
        code: int,
        description: str,
        message_id: str = "",
        status: str = "",
        error_code: str = "",
        error_message: str = "",
    ):
        self.code = code
        self.description = description
        self.message_id = message_id
        self.status = status
        self.error_code = error_code
        self.error_message = error_message


class SmsAPI:
    @staticmethod
    def send_sms(request: SmsRequest) -> SmsResponse:
        if not request.number or not request.text:
            return SmsResponse(code=400, description="Invalid")

        account_sid, auth_token, sms_from, _wa_from = _twilio_config()

        if account_sid and auth_token and sms_from:
            try:
                from twilio.rest import Client

                client = Client(account_sid, auth_token)
                mensaje = client.messages.create(
                    body=request.text,
                    from_=sms_from,
                    to=request.number,
                )
                estado = (mensaje.status or "").lower()
                aceptado = estado in {"accepted", "queued", "sending", "sent", "delivered"}
                return SmsResponse(
                    code=200 if aceptado else 500,
                    description=f"Twilio status: {mensaje.status}",
                    message_id=mensaje.sid or "",
                    status=mensaje.status or "",
                    error_code=str(mensaje.error_code or ""),
                    error_message=str(mensaje.error_message or ""),
                )
            except Exception as e:
                print(f"[SMS Twilio] Error: {str(e)}")
                return SmsResponse(
                    code=500,
                    description=f"Twilio error: {str(e)}",
                    status="failed",
                    error_message=str(e),
                )

        print("  Falta configuración Twilio: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN y TWILIO_SMS_FROM")
        return SmsResponse(code=500, description="Twilio no configurado", message_id="")
