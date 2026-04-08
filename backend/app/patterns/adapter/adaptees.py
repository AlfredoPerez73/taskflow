"""
PATRÓN ADAPTER — Adaptees concretos de notificación.

Cada clase adapta la interfaz estándar (INotificacionAdapter) a la API
externa específica del canal, traduciendo los tipos de datos en ambas
direcciones (request y response).

Equivalencia con el ejemplo bancario:
  XBankAdaptee  →  WhatsAppAdaptee
  YBankAdaptee  →  EmailAdaptee
                →  SmsAdaptee (canal adicional)
"""
from app.patterns.adapter.notificacion_adapter import (
    INotificacionAdapter,
    SolicitudNotificacion,
    RespuestaNotificacion,
)
from app.patterns.adapter.apis_externas import (
    WhatsAppAPI, WhatsAppRequest,
    EmailAPI, EmailRequest,
    SmsAPI, SmsRequest,
)


class WhatsAppAdaptee(INotificacionAdapter):
    """
    Adapta INotificacionAdapter a WhatsAppAPI.
    Traduce SolicitudNotificacion → WhatsAppRequest
    y WhatsAppResponse → RespuestaNotificacion.
    """

    def enviar(self, solicitud: SolicitudNotificacion) -> RespuestaNotificacion:
        # Traducir solicitud estándar al formato de WhatsApp API
        wa_request = WhatsAppRequest(
            phone=solicitud.contacto,
            body=f"🔔 TaskFlow\n{solicitud.mensaje}",
        )

        # Llamar a la API externa
        wa_response = WhatsAppAPI.send_message(wa_request)

        # Traducir respuesta de WhatsApp al formato estándar
        return RespuestaNotificacion(
            enviada=wa_response.status == "sent",
            canal="whatsapp",
            detalle=f"ID: {wa_response.message_id}" if wa_response.message_id else "Falló el envío",
        )


class EmailAdaptee(INotificacionAdapter):
    """
    Adapta INotificacionAdapter a EmailAPI.
    Traduce SolicitudNotificacion → EmailRequest
    y EmailResponse → RespuestaNotificacion.
    """

    def enviar(self, solicitud: SolicitudNotificacion) -> RespuestaNotificacion:
        # Traducir solicitud estándar al formato de Email API
        email_request = EmailRequest(
            to=solicitud.contacto,
            subject=solicitud.asunto or "Notificación TaskFlow",
            body=f"Hola {solicitud.destinatario},\n\n{solicitud.mensaje}\n\n— TaskFlow",
        )

        # Llamar a la API externa
        email_response = EmailAPI.send_email(email_request)

        # Traducir respuesta de Email al formato estándar
        return RespuestaNotificacion(
            enviada=email_response.delivered == "Y",
            canal="email",
            detalle="Entregado al servidor" if email_response.delivered == "Y" else "No entregado",
        )


class SmsAdaptee(INotificacionAdapter):
    """
    Adapta INotificacionAdapter a SmsAPI.
    Traduce SolicitudNotificacion → SmsRequest
    y SmsResponse → RespuestaNotificacion.
    """

    def enviar(self, solicitud: SolicitudNotificacion) -> RespuestaNotificacion:
        # Traducir solicitud estándar al formato de SMS API
        sms_request = SmsRequest(
            number=solicitud.contacto,
            text=f"TaskFlow: {solicitud.mensaje[:160]}",  # SMS tiene límite de 160 chars
        )

        # Llamar a la API externa
        sms_response = SmsAPI.send_sms(sms_request)

        # Traducir respuesta de SMS al formato estándar
        return RespuestaNotificacion(
            enviada=sms_response.code == 200,
            canal="sms",
            detalle=sms_response.description,
        )