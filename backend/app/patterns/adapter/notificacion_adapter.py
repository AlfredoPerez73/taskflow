"""
PATRÓN ADAPTER — INotificacionAdapter
Define la interfaz común que todos los adaptadores de notificación deben implementar.
Cada canal externo (WhatsApp API, Email API, SMS API) tiene su propio formato,
y el Adapter traduce nuestra solicitud estándar al formato que cada API entiende.

Equivalente a IBankAdapter del ejemplo bancario:
  IBankAdapter          → INotificacionAdapter
  BankCreditRequest     → SolicitudNotificacion
  BankCreditResponse    → RespuestaNotificacion
  XBankAdaptee          → WhatsAppAdaptee
  YBankAdaptee          → EmailAdaptee
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SolicitudNotificacion:
    """Solicitud estándar de notificación — independiente del canal."""
    destinatario: str      # nombre del usuario
    contacto: str          # email / teléfono / número WA según canal
    mensaje: str           # cuerpo del mensaje
    asunto: str = ""       # usado por email


@dataclass
class RespuestaNotificacion:
    """Respuesta estándar — independiente del canal."""
    enviada: bool
    canal: str
    detalle: str = ""


class INotificacionAdapter(ABC):
    """
    Interfaz del Adapter. Define el contrato que todos los adaptadores
    concretos deben cumplir, sin importar la API externa que usen.
    """

    @abstractmethod
    def enviar(self, solicitud: SolicitudNotificacion) -> RespuestaNotificacion:
        """Envía la notificación usando la API externa correspondiente."""
        pass