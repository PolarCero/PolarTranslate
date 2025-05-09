# src/application/translator_service.py

from typing import List, Any # Importamos Any para el tipo de datos de imagen
from PySide6.QtCore import QObject, Signal, Slot, QCoreApplication, QEvent # <-- Importamos QEvent
import sys

# Importar las interfaces y modelos de la capa de Dominio
from src.domain.interfaces import ITranslator, IHotkeyManager, IOCRService # Importamos IOCRService
from src.domain.models import TranslationRequest, TranslationResult, Language

# Importar la utilidad de portapapeles de la capa de Infraestructura
from src.infrastructure.system_utils import get_clipboard_text, set_clipboard_text

# Creamos un QObject para emitir señales desde el hilo secundario al hilo principal (UI)
class HotkeySignalEmitter(QObject):
    """Emite señales para comunicar resultados de hotkey al hilo principal de la UI."""
    # Señal que lleva el resultado de la traducción (TranslationResult)
    translation_finished = Signal(TranslationResult)
    # Señal para indicar un error (string)
    error_occurred = Signal(str)

# Ya no necesitamos este emisor en la capa de aplicación con el patrón de hilo estándar en la UI
# class OCRTranslationSignalEmitter(QObject):
#     """Emite señales para comunicar resultados de OCR/Traducción al hilo principal de la UI."""
#     # Señal que lleva el resultado de la traducción (TranslationResult) después de OCR
#     ocr_translation_finished = Signal(TranslationResult)
#     # Señal para indicar un error (string) durante OCR o traducción
#     ocr_error_occurred = Signal(str)
#     # Señal para indicar progreso (opcional)
#     # progress_updated = Signal(int)


# --- Clases de evento personalizadas para postEvent (MOVIDAS FUERA DE LA CLASE) ---
# Aseguramos que QEvent está importado arriba
class _TranslationFinishedEvent(QEvent):
    EventType = QEvent.Type(QEvent.registerEventType()) # Registrar un tipo de evento único
    def __init__(self, result: TranslationResult):
        super().__init__(self.EventType)
        self.result = result # Almacenar el resultado de la traducción

class _ErrorOccurredEvent(QEvent):
    EventType = QEvent.Type(QEvent.registerEventType()) # Registrar otro tipo de evento único
    def __init__(self, message: str):
        super().__init__(self.EventType)
        self.message = message # Almacenar el mensaje de error
# --- FIN Clases de evento personalizadas ---


# Modificamos TranslatorService para incluir la dependencia de IOCRService
class TranslatorService(QObject): # <-- Aseguramos que hereda de QObject para customEvent
    """
    Servicio de aplicación para manejar las operaciones de traducción, hotkeys y OCR.
    Depende de las interfaces ITranslator, IHotkeyManager y IOCRService de la capa de Dominio.
    """

    def __init__(self, translator: ITranslator, hotkey_manager: IHotkeyManager, ocr_service: IOCRService):
        """
        Constructor del servicio de traducción.

        Args:
            translator: Una implementación de la interfaz ITranslator.
            hotkey_manager: Una implementación de la interfaz IHotkeyManager.
            ocr_service: Una implementación de la interfaz IOCRService. # Nueva dependencia
        """
        super().__init__() # <-- Llamamos al constructor de QObject

        if not isinstance(translator, ITranslator):
             raise TypeError("translator must implement ITranslator interface")
        if not isinstance(hotkey_manager, IHotkeyManager):
             raise TypeError("hotkey_manager must implement IHotkeyManager interface")
        if not isinstance(ocr_service, IOCRService): # Verificar la nueva dependencia
             raise TypeError("ocr_service must implement IOCRService interface")


        self.translator = translator
        self.hotkey_manager = hotkey_manager
        self.ocr_service = ocr_service # Almacenar la instancia del servicio OCR

        # Instancia de los emisores de señales para comunicación entre hilos
        if QCoreApplication.instance() is None:
             print("Advertencia: QApplication no inicializada. Las señales podrían no funcionar.")

        self._hotkey_signal_emitter = HotkeySignalEmitter()
        # self._ocr_translation_signal_emitter = OCRTranslationSignalEmitter() # Ya no necesario en el servicio


        # Atributos para almacenar los idiomas por defecto (eventualmente desde la Configuración)
        self._default_source_lang_code = "en" # Temporal
        self._default_target_lang_code = "es" # Temporal

    # Método existente para obtener idiomas soportados
    def get_supported_languages(self) -> List[Language]:
        """
        Obtiene la lista de idiomas soportados por el traductor subyacente.

        Returns:
            Una lista de objetos Language.
        """
        print("Application Layer: Getting supported languages...")
        try:
            languages = self.translator.get_available_languages()
            print(f"Application Layer: get_available_languages() returned {len(languages)} languages.")
            return languages
        except Exception as e:
            print(f"Application Layer Error: Error in get_supported_languages: {e}")
            # Retornar lista vacía o manejar según necesidad
            return []

    # Método existente para realizar traducción manual
    def perform_translation(self, text: str, source_lang_code: str, target_lang_code: str) -> TranslationResult:
        """
        Realiza una traducción de texto utilizando el traductor configurado.

        Args:
            text: El texto a traducir.
            source_lang_code: Código del idioma de origen (e.g., "en").
            target_lang_code: Código del idioma de destino (e.g., "es").

        Returns:
            Un objeto TranslationResult con el texto traducido o un error.
        """
        print(f"Application Layer: Performing translation for text='{text[:50]}...' from {source_lang_code} to {target_lang_code}")

        available_languages = self.get_supported_languages()
        source_language = next((lang for lang in available_languages if lang.code == source_lang_code), None)
        target_language = next((lang for lang in available_languages if lang.code == target_lang_code), None)

        if not source_language:
            error_msg = f"Idioma de origen no soportado: {source_lang_code}"
            print(f"Application Layer Error: {error_msg}")
            return TranslationResult(error=error_msg)
        if not target_language:
            error_msg = f"Idioma de destino no soportado: {target_lang_code}"
            print(f"Application Layer Error: {error_msg}")
            return TranslationResult(error=error_msg)

        request = TranslationRequest(text, source_language, target_language)
        print("Application Layer: Calling translator.translate()...")
        try:
            translation_result = self.translator.translate(request)
            print("Application Layer: translator.translate() returned.")
            print(f"Application Layer: Translation result: {translation_result}")
            # Asegurarse de que el resultado retornado es un TranslationResult
            if isinstance(translation_result, TranslationResult):
                 return translation_result
            else:
                 error_msg = f"Translator returned unexpected type: {type(translation_result).__name__}"
                 print(f"Application Layer Error: {error_msg}")
                 return TranslationResult(error=error_msg)

        except Exception as e:
            error_msg = f"Error during translator.translate(): {e}"
            print(f"Application Layer Error: {error_msg}")
            return TranslationResult(error=error_msg)


    # --- Métodos para Hotkeys y Portapapeles (existente) ---

    def register_clipboard_translation_hotkey(self, hotkey: str):
        """
        Registra una hotkey global que, al ser presionada, traducirá el texto del portapapeles.
        """
        print(f"Application Layer: Registrando hotkey para traducción de portapapeles: {hotkey}")
        self.hotkey_manager.register_hotkey(hotkey, self._on_hotkey_pressed)
        self.hotkey_manager.start_listening()

    def unregister_clipboard_translation_hotkey(self, hotkey: str):
        """
        Desregistra la hotkey de traducción del portapapeles.
        """
        print(f"Application Layer: Desregistrando hotkey de traducción de portapapeles: {hotkey}")
        self.hotkey_manager.unregister_hotkey(hotkey)

    def get_hotkey_signal_emitter(self) -> HotkeySignalEmitter:
        """
        Retorna el emisor de señales de hotkey para que la UI pueda conectarse a él.
        """
        return self._hotkey_signal_emitter

    def _on_hotkey_pressed(self):
        """
        Método callback que se ejecuta en el hilo del hotkey manager cuando se presiona la hotkey.
        Obtiene texto del portapapeles, realiza la traducción y emite una señal con el resultado.
        """
        print("Application Layer: Hotkey presionada. Iniciando traducción de portapapeles...")
        try:
            clipboard_text = get_clipboard_text()

            if not clipboard_text:
                 print("Application Layer: Portapapeles vacío o error al obtener texto.")
                 # Emitir TranslationResult con error al hilo principal de la UI via la señal
                 # Usamos QCoreApplication.instance() para asegurar que la señal se emite en el hilo principal
                 QCoreApplication.instance().postEvent(
                     self, # <-- Emitimos el evento a sí mismo (TranslatorService)
                     _TranslationFinishedEvent(TranslationResult(error="Portapapeles vacío o error al obtener texto."))
                 )
                 return

            # Usamos perform_translation directamente, que ya maneja errores y retorna TranslationResult
            translation_result = self.perform_translation(
                clipboard_text,
                self._default_source_lang_code,
                self._default_target_lang_code
            )

            # Emitir TranslationResult al hilo principal de la UI via la señal
            # Usamos QCoreApplication.instance() para asegurar que la señal se emite en el hilo principal
            QCoreApplication.instance().postEvent(
                self, # <-- Emitimos el evento a sí mismo (TranslatorService)
                _TranslationFinishedEvent(translation_result)
            )
            print("Application Layer: Señal de traducción de portapapeles emitida.")

        except Exception as e:
            print(f"Application Layer Error: Error inesperado en callback de hotkey: {e}")
            # Emitir error al hilo principal de la UI via la señal
            QCoreApplication.instance().postEvent(
                 self, # <-- Emitimos el evento a sí mismo (TranslatorService)
                 _ErrorOccurredEvent(f"Error inesperado durante la traducción por hotkey: {e}")
            )

    # Sobreescribir customEvent para manejar los eventos personalizados
    # Este método se ejecuta en el hilo principal de la UI porque TranslatorService
    # está instanciado en el hilo principal.
    def customEvent(self, event: QEvent):
        # Verificamos el tipo de evento usando los EventType registrados
        if event.type() == _TranslationFinishedEvent.EventType: # <-- Ahora accesibles
            print("Application Layer: customEvent received _TranslationFinishedEvent.")
            # Emitimos la señal del emisor de hotkey para que la UI la reciba
            self._hotkey_signal_emitter.translation_finished.emit(event.result)
        elif event.type() == _ErrorOccurredEvent.EventType: # <-- Ahora accesibles
            print("Application Layer: customEvent received _ErrorOccurredEvent.")
             # Emitimos la señal de error del emisor de hotkey para que la UI la reciba
            self._hotkey_signal_emitter.error_occurred.emit(event.message)
        else:
            # Si no es uno de nuestros eventos personalizados, llamar al método base
            super().customEvent(event)


    def stop_hotkey_listening(self):
         """
         Detiene el monitoreo global de hotkeys a través del hotkey manager.
         Debería llamarse al cerrar la aplicación.
         """
         print("Application Layer: Solicitando detener monitoreo de hotkeys.")
         self.hotkey_manager.stop_listening()

    # --- Nuevos métodos para OCR y Traducción ---

    def perform_ocr_and_translate(self, image_data: Any, source_lang_code: str, target_lang_code: str) -> TranslationResult:
        """
        Realiza OCR en datos de imagen, extrae el texto y luego lo traduce.
        Retorna un TranslationResult. Asegura que siempre retorna TranslationResult.
        """
        print("Application Layer: perform_ocr_and_translate() iniciado.")
        extracted_text = "" # Inicializar extracted_text

        try:
            # 1. Realizar OCR utilizando el servicio de OCR inyectado
            print("Application Layer: Calling ocr_service.extract_text_from_image_data()...")
            # Capturamos errores específicos de OCR aquí si es posible, o un error general
            try:
                extracted_text = self.ocr_service.extract_text_from_image_data(image_data)
                print("Application Layer: ocr_service.extract_text_from_image_data() returned.")
            except Exception as ocr_e:
                error_msg = f"Error durante la extracción de texto por OCR: {ocr_e}"
                print(f"Application Layer Error: {error_msg}")
                # Si falla el OCR, retornamos un TranslationResult con el error de OCR
                return TranslationResult(error=error_msg)


            if not extracted_text:
                print("Application Layer: OCR no extrajo texto o el texto extraído está vacío.")
                # Devolvemos un TranslationResult con error si no se extrajo texto
                return TranslationResult(error="No se pudo extraer texto de la imagen.")

            print(f"Application Layer: Texto extraído por OCR (primeros 50 chars): {extracted_text[:50]}...")

            # 2. Realizar la traducción del texto extraído
            # perform_translation ya retorna un TranslationResult y maneja sus propios errores
            print("Application Layer: Calling perform_translation() after OCR...")
            translation_result = self.perform_translation(
                extracted_text,
                source_lang_code,
                target_lang_code
            )
            print("Application Layer: perform_translation() after OCR returned.")

            # 3. Retornar el resultado (que ya es un TranslationResult)
            print("Application Layer: Operación de OCR y Traducción finalizada.")
            return translation_result

        except Exception as e:
            # Capturar cualquier otro error inesperado durante el proceso combinado
            error_msg = f"Error inesperado durante OCR o Traducción: {e}"
            print(f"Application Layer Error: {error_msg}")
            # Si ocurre un error inesperado, retornamos un TranslationResult con el error
            return TranslationResult(error=error_msg)

    # Este método ya no es necesario que la UI lo llame con el patrón de hilo estándar
    # def get_ocr_translation_signal_emitter(self):
    #    pass

