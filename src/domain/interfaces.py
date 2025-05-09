# src/domain/interfaces.py
import abc
from typing import List, Optional, Callable, Any # Importamos Any para tipo de imagen flexible

# Importamos los modelos que definiremos en models.py
from .models import TranslationRequest, TranslationResult, Language

class ITranslator(abc.ABC):
    """Interfaz para el servicio de traducción."""

    @abc.abstractmethod
    def get_available_languages(self) -> List[Language]:
        """
        Obtiene la lista de idiomas disponibles para la traducción.

        Returns:
            Una lista de objetos Language.
        """
        pass

    @abc.abstractmethod
    def translate(self, request: TranslationRequest) -> TranslationResult:
        """
        Realiza una solicitud de traducción.

        Args:
            request: Un objeto TranslationRequest con el texto, idioma de origen y destino.

        Returns:
            Un objeto TranslationResult con el texto traducido y posibles errores.
        """
        pass

class IOCRService(abc.ABC):
    """Interfaz para el servicio de reconocimiento óptico de caracteres (OCR)."""

    @abc.abstractmethod
    def extract_text_from_image_data(self, image_data: Any) -> str:
        """
        Extrae texto de datos de imagen.

        Args:
            image_data: Los datos de la imagen (el tipo exacto dependerá de la implementación
                        de infraestructura, por ejemplo, un objeto PIL.Image.Image).

        Returns:
            El texto extraído de la imagen.
        """
        pass

    # Eliminamos el método extract_text_from_screen_region de la interfaz de Dominio,
    # ya que la captura de pantalla es una preocupación de Infraestructura/Aplicación,
    # no del servicio de OCR en sí. El servicio de OCR solo procesa la imagen que recibe.


class ITTSService(abc.ABC):
    """Interfaz para el servicio de síntesis de voz (Text-to-Speech)."""

    @abc.abstractmethod
    def speak(self, text: str, language: Optional[str] = None):
        """
        Reproduce un texto usando síntesis de voz.

        Args:
            text: El texto a reproducir.
            language: Código opcional del idioma para la síntesis de voz.
        """
        pass

class IHotkeyManager(abc.ABC):
    """Interfaz para gestionar hotkeys globales del sistema."""

    @abc.abstractmethod
    def register_hotkey(self, hotkey: str, callback: Callable[[], None]):
        """
        Registra una hotkey global y asocia una función de callback a ella.

        Args:
            hotkey: La combinación de teclas a registrar (formato específico de la implementación).
            callback: La función a ejecutar cuando la hotkey es presionada.
        """
        pass

    @abc.abstractmethod
    def unregister_hotkey(self, hotkey: str):
        """
        Elimina el registro de una hotkey global previamente registrada.

        Args:
            hotkey: La combinación de teclas a eliminar.
        """
        pass

    @abc.abstractmethod
    def start_listening(self):
        """
        Inicia el monitoreo global de hotkeys.
        Esto usualmente bloquea la ejecución hasta que se detiene.
        Puede requerir ejecutarse en un hilo separado en aplicaciones GUI.
        """
        pass

    @abc.abstractmethod
    def stop_listening(self):
        """
        Detiene el monitoreo global de hotkeys.
        """
        pass

# Podemos añadir interfaces para ConfigManager, etc. más adelante
