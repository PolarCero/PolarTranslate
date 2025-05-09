# Polar Translate - https://github.com/PolarCero
# Author: David Pollard / PolarCero
# License: AGPL-3.0
# main.py
import sys

# Importar las clases necesarias de las diferentes capas
from src.ui.main_window import MainWindow
from src.application.translator_service import TranslatorService
from src.infrastructure.argos_translator import ArgosTranslator
from src.infrastructure.system_hotkey_manager import SystemHotkeyManager
from src.infrastructure.pytesseract_ocr import PytesseractOCRService

# Importar QApplication de PySide6 para iniciar la aplicación GUI
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication

# Importar modelos del dominio para la llamada de prueba
from src.domain.models import TranslationRequest, Language


if __name__ == "__main__":
    # --- Composición de las capas (Inyección de Dependencias) ---

    # 1. Crear la aplicación PySide6 PRIMERO
    app = QApplication(sys.argv)
    print("main.py: Instancia de QApplication creada.")

    # 2. Crear instancia de la implementación de Infraestructura (ArgosTranslator)
    infrastructure_translator = ArgosTranslator()
    print("main.py: Instancia de ArgosTranslator creada.")

    # --- INTENTAR FORZAR LA CARGA DE MODELOS DE ARGOS TRANSLATE ---
    # Realizar una traducción de prueba simple en el hilo principal
    # Esto puede ayudar a que argostranslate cargue sus modelos o realice inicializaciones
    # que podrían causar problemas si se hacen por primera vez en un hilo secundario.
    try:
        print("main.py: Intentando traducción de prueba para forzar carga de modelo Argos...")
        # Usamos códigos de idioma que deberían estar instalados (en a es)
        test_request = TranslationRequest("hello", Language("en", "English"), Language("es", "Spanish"))
        test_result = infrastructure_translator.translate(test_request)
        if test_result.is_successful:
            print(f"main.py: Traducción de prueba exitosa: {test_result.translated_text}")
        else:
            print(f"main.py: Traducción de prueba fallida (esto puede ser normal si los modelos no están instalados): {test_result.error}")
    except Exception as e:
        print(f"main.py: Error inesperado durante la traducción de prueba: {e}")
    print("main.py: Finalizada traducción de prueba.")
    # --- FIN INTENTO DE CARGA ---


    # 3. Crear instancia de la implementación de Infraestructura (SystemHotkeyManager)
    infrastructure_hotkey_manager = SystemHotkeyManager()
    print("main.py: Instancia de SystemHotkeyManager creada.")

    # 4. Crear instancia de la implementación de Infraestructura (PytesseractOCRService)
    infrastructure_ocr_service = PytesseractOCRService(tesseract_cmd_path=None)
    print("main.py: Instancia de PytesseractOCRService creada.")


    # 5. Crear instancia del servicio de Aplicación (TranslatorService)
    # Inyectamos las implementaciones de ITranslator, IHotkeyManager y IOCRService.
    application_translator_service = TranslatorService(
        translator=infrastructure_translator,
        hotkey_manager=infrastructure_hotkey_manager,
        ocr_service=infrastructure_ocr_service # Inyectamos el servicio OCR
    )
    print("main.py: Instancia de TranslatorService creada con dependencias inyectadas.")

    # 6. Registrar la hotkey de traducción de portapapeles
    default_hotkey = "ctrl+space+c"
    application_translator_service.register_clipboard_translation_hotkey(default_hotkey)
    print(f"main.py: Registrada hotkey de traducción de portapapeles: {default_hotkey}")

    # 7. Conectar la detención del listener de hotkeys al cierre de la aplicación
    QCoreApplication.instance().aboutToQuit.connect(application_translator_service.stop_hotkey_listening)
    print("main.py: Conectado stop_hotkey_listening al evento aboutToQuit.")

    # 8. Crear instancia de la ventana principal de la UI (MainWindow)
    main_window = MainWindow(translator_service=application_translator_service)
    print("main.py: Instancia de MainWindow creada con TranslatorService inyectado.")

    # 9. Mostrar la ventana principal
    main_window.show()
    print("main.py: Mostrando la ventana principal.")

    # 10. Iniciar el bucle de eventos de la aplicación
    sys.exit(app.exec())

