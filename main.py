# main.py
import sys
import os # Importar os para manejar rutas de archivos

# Importar las clases necesarias de las diferentes capas
from src.ui.main_window import MainWindow
from src.application.translator_service import TranslatorService
from src.infrastructure.argos_translator import ArgosTranslator
from src.infrastructure.system_hotkey_manager import SystemHotkeyManager
from src.infrastructure.pytesseract_ocr import PytesseractOCRService

# Importar QApplication y QTranslator de PySide6 para la localización
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, QTranslator, QLocale # Importar QTranslator y QLocale

# Importar modelos del dominio para la llamada de prueba
from src.domain.models import TranslationRequest, Language


if __name__ == "__main__":
    # --- Composición de las capas (Inyección de Dependencias) ---

    # 1. Crear la aplicación PySide6 PRIMERO
    app = QApplication(sys.argv)
    print("main.py: Instancia de QApplication creada.")

    # --- Configuración de Localización ---
    # Crear una instancia de QTranslator
    translator = QTranslator(app)

    # Determinar el idioma a cargar. Por ahora, cargaremos 'en' (inglés) si existe.
    # En una versión futura (Fase 6), esto podría basarse en la configuración del usuario
    # o la configuración regional del sistema.
    locale = QLocale.system().name() # Obtener la configuración regional del sistema (ej: "en_US", "es_ES")
    lang_code = locale.split('_')[0] # Obtener solo el código de idioma (ej: "en", "es")

    # Intentar cargar el archivo de traducción para el idioma detectado (si no es inglés)
    # O cargar inglés si el idioma del sistema no es inglés.
    # Los archivos .qm se guardarán en una carpeta 'i18n' en la raíz del proyecto.
    # El nombre del archivo .qm debe seguir el patrón <nombre_app>_<código_idioma>.qm
    # Por ejemplo: PolarTranslate_en.qm, PolarTranslate_es.qm

    # Ruta esperada del archivo .qm para el idioma del sistema
    qm_file_system = f"i18n/PolarTranslate_{lang_code}.qm"
    # Ruta esperada del archivo .qm para inglés (por defecto si el sistema no es inglés)
    qm_file_english = "i18n/PolarTranslate_en.qm"


    if lang_code != "en" and os.path.exists(qm_file_system):
        # Si el idioma del sistema no es inglés y existe un archivo .qm para ese idioma
        print(f"main.py: Intentando cargar archivo de traducción para idioma del sistema: {qm_file_system}")
        if translator.load(qm_file_system):
            app.installTranslator(translator)
            print(f"main.py: Archivo de traducción {qm_file_system} cargado exitosamente.")
        else:
            print(f"main.py: Advertencia: No se pudo cargar el archivo de traducción: {qm_file_system}")
            print("main.py: La aplicación se ejecutará en inglés.")
            # Intentar cargar el archivo de inglés si falla el del sistema
            if os.path.exists(qm_file_english) and translator.load(qm_file_english):
                 app.installTranslator(translator)
                 print(f"main.py: Archivo de traducción {qm_file_english} cargado como fallback.")
            else:
                 print(f"main.py: Advertencia: No se pudo cargar el archivo de traducción de inglés: {qm_file_english}")

    elif os.path.exists(qm_file_english):
        # Si el idioma del sistema es inglés o no se encontró el archivo del sistema, intentar cargar inglés
        print(f"main.py: Intentando cargar archivo de traducción de inglés: {qm_file_english}")
        if translator.load(qm_file_english):
            app.installTranslator(translator)
            print(f"main.py: Archivo de traducción {qm_file_english} cargado exitosamente.")
        else:
            print(f"main.py: Advertencia: No se pudo cargar el archivo de traducción de inglés: {qm_file_english}")
            print("main.py: La aplicación se ejecutará sin traducción (probablemente en inglés por defecto).")
    else:
        print("main.py: No se encontraron archivos de traducción (.qm) en la carpeta 'i18n'. La aplicación se ejecutará sin traducción.")


    # --- Fin Configuración de Localización ---


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
        # Nota: Los nombres de los idiomas en el modelo Language deben coincidir con los que argostranslate reporta
        # para que la búsqueda en get_supported_languages funcione correctamente.
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

