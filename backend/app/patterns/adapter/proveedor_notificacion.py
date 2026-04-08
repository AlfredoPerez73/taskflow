"""
PATRÓN FACTORY METHOD — FabricaNotificaciones
Combinado con ADAPTER para seleccionar y crear el adaptador correcto
según el canal de notificación, siguiendo exactamente el mismo patrón
del ejemplo bancario (FactoryBankAdapter + BankAdapterProvider).

Equivalencia:
  FactoryBankAdapter      → FabricaNotificacion (abstract)
  FactoryXBankAdapter     → FabricaWhatsApp
  FactoryYBankAdapter     → FabricaEmail
                          → FabricaSms
  BankAdapterProvider     → ProveedorNotificacion
"""
from abc import ABC, abstractmethod
from app.patterns.adapter.notificacion_adapter import INotificacionAdapter
from app.patterns.adapter.adaptees import WhatsAppAdaptee, EmailAdaptee, SmsAdaptee


# ── Fábrica abstracta (equivalente a FactoryBankAdapter) ─────────────────────

class FabricaNotificacion(ABC):
    """
    Factory Method abstracto.
    Define el método get() que llama a create() — exactamente como
    FactoryBankAdapter.get() llama a FactoryBankAdapter.create().
    """

    def get(self) -> INotificacionAdapter:
        """Retorna el adaptador creado por la fábrica concreta."""
        return self.create()

    @abstractmethod
    def create(self) -> INotificacionAdapter:
        """Las subclases deciden qué adaptador concreto instanciar."""
        pass


# ── Fábricas concretas (equivalente a FactoryXBankAdapter, FactoryYBankAdapter)

class FabricaWhatsApp(FabricaNotificacion):
    """Fábrica concreta que crea un WhatsAppAdaptee."""

    def create(self) -> INotificacionAdapter:
        return WhatsAppAdaptee()


class FabricaEmail(FabricaNotificacion):
    """Fábrica concreta que crea un EmailAdaptee."""

    def create(self) -> INotificacionAdapter:
        return EmailAdaptee()


class FabricaSms(FabricaNotificacion):
    """Fábrica concreta que crea un SmsAdaptee."""

    def create(self) -> INotificacionAdapter:
        return SmsAdaptee()


# ── Proveedor (equivalente a BankAdapterProvider) ─────────────────────────────

class ProveedorNotificacion:
    """
    Registra los canales disponibles y devuelve la fábrica correspondiente.
    Equivalente a BankAdapterProvider que mapea "XBank"→FactoryXBankAdapter.

    Uso:
        proveedor = ProveedorNotificacion()
        fabrica = proveedor.get("email")
        adapter = fabrica.get()
        respuesta = adapter.enviar(solicitud)
    """

    def __init__(self) -> None:
        self._fabricas: dict[str, FabricaNotificacion] = {
            "whatsapp": FabricaWhatsApp(),
            "email":    FabricaEmail(),
            "sms":      FabricaSms(),
        }

    def get(self, canal: str) -> FabricaNotificacion:
        fabrica = self._fabricas.get(canal.lower())
        if not fabrica:
            canales = list(self._fabricas.keys())
            raise ValueError(f"Canal '{canal}' no soportado. Disponibles: {canales}")
        return fabrica

    def canales_disponibles(self) -> list[str]:
        return list(self._fabricas.keys())