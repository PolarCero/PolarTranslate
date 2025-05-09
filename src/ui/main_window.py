# src/ui/main_window.py

import sys
import threading # Importamos la biblioteca threading
from typing import List, Any, Callable, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QComboBox, QStatusBar,
    QFileDialog, QMessageBox
)
# Importamos QObject, Signal, Slot, QCoreApplication, QBuffer, QByteArray de PySide6.QtCore
# Importamos QRect
from PySide6.QtCore import Qt, Signal, Slot, QObject, QCoreApplication, QBuffer, QByteArray, QRect, QTimer
# Importamos QGuiApplication, QClipboard, QPixmap, QScreen de PySide6.QtGui
from PySide6.QtGui import QGuiApplication, QClipboard, QPixmap, QScreen
from PIL import Image # Necesario para manejar imágenes para OCR
import io # Necesario para trabajar con bytes de imagen
import os # Para obtener la extensión del archivo
import time # Para pausas cortas si son necesarias
import tempfile # Necesario para crear archivos temporales
import ctypes # Para intentar configurar el DPI awareness

# Importar Tkinter y ImageGrab para el selector y la captura
import tkinter as tk
from tkinter import Canvas
# Importar mss para la captura de pantalla
import mss
import mss.tools


# Importar la nueva ventana pop-up
from .pop_up_window import PopUpTranslationWindow

# Importar el servicio de la capa de Aplicación y los modelos del Dominio
from src.application.translator_service import TranslatorService, HotkeySignalEmitter
from src.domain.models import Language, TranslationRequest, TranslationResult

# Bibliotecas para leer archivos de texto (no OCR)
try:
    from docx import Document
except ImportError:
    Document = None
    print("Advertencia: La biblioteca 'python-docx' no está instalada. No se podrán leer archivos .docx.")


# --- Intentar configurar el DPI awareness del proceso lo antes posible ---
# Esto es crucial para intentar que las coordenadas de PySide, Tkinter y PIL/mss sean consistentes.
# PROCESS_PER_MONITOR_DPI_AWARE = 2
try:
    # Usar shcore.SetProcessDpiAwareness (Windows 8.1+)
    ctypes.windll.shcore.SetProcessDpiAwareness(ctypes.c_int(2))
    print("DPI awareness set to PROCESS_PER_MONITOR_DPI_AWARE.")
except Exception as e:
    print(f"Failed to set process DPI awareness (shcore): {e}. Trying user32...")
    try:
        # Fallback para sistemas más antiguos (Windows Vista+)
        ctypes.windll.user32.SetProcessDPIAware()
        print("DPI awareness set using SetProcessDPIAware.")
    except Exception as e_user32:
        print(f"Failed to set process DPI awareness (user32): {e_user32}.")
        print("DPI awareness may not be consistent, expect potential coordinate issues.")


# --- Variables y funciones para el Selector Tkinter (ejecutado en hilo separado) ---
# Estas variables se usarán para comunicar las coordenadas de selección desde el hilo Tkinter
# de vuelta al hilo principal de PySide.
_tkinter_start_x = None
_tkinter_start_y = None
_tkinter_end_x = None
_tkinter_end_y = None
_tkinter_selection_complete = threading.Event() # Evento para señalar que la selección terminó
_tkinter_capture_error = None # Para comunicar errores desde el hilo Tkinter
_tkinter_captured_image_path = "captura_pil.png" # Ruta donde se guardará la captura temporal


def _run_tkinter_selector(desktop_geometry: QRect):
    """
    Función que ejecuta el selector de región de Tkinter en un hilo separado.
    Obtiene las coordenadas de selección y realiza la captura usando mss.
    Guarda la imagen capturada en un archivo temporal.
    """
    global _tkinter_start_x, _tkinter_start_y, _tkinter_end_x, _tkinter_end_y
    global _tkinter_selection_complete, _tkinter_capture_error, _tkinter_captured_image_path

    # Resetear variables globales y evento al inicio del hilo
    _tkinter_start_x = None
    _tkinter_start_y = None
    _tkinter_end_x = None
    _tkinter_end_y = None
    _tkinter_capture_error = None
    _tkinter_selection_complete.clear()

    root = None
    canvas = None
    selection_rect_id = None

    # Usaremos variables locales para capturar las coordenadas dentro de los handlers
    local_start_x = None
    local_start_y = None
    local_end_x = None
    local_end_y = None


    def on_mouse_down(event):
        nonlocal root, canvas, selection_rect_id, local_start_x, local_start_y
        local_start_x = event.x_root # Capturar en variable local (coordenadas globales físicas)
        local_start_y = event.y_root # Capturar en variable local (coordenadas globales físicas)
        print(f"UI Layer (Tkinter Thread): Mouse DOWN detected at ({local_start_x}, {local_start_y})")
        # Coordenadas del canvas coinciden con las globales si la ventana cubre el escritorio
        selection_rect_id = canvas.create_rectangle(local_start_x, local_start_y, local_start_x, local_start_y, outline='red', width=2)
        print(f"UI Layer (Tkinter Thread): Created rectangle with ID {selection_rect_id}")


    def on_mouse_drag(event):
        nonlocal canvas, selection_rect_id, local_start_x, local_start_y
        cur_x = event.x_root # Coordenadas globales físicas
        cur_y = event.y_root # Coordenadas globales físicas
        # Actualizar las coordenadas del rectángulo de selección en el canvas
        if selection_rect_id is not None and local_start_x is not None: # Asegurarse de que el rectángulo existe y el inicio está registrado
            canvas.coords(selection_rect_id, local_start_x, local_start_y, cur_x, cur_y)
        # print(f"UI Layer (Tkinter Thread): Mouse DRAG detected at ({cur_x}, {cur_y})") # Demasiado verboso, descomentar si es necesario


    def on_mouse_up(event):
        nonlocal root, local_end_x, local_end_y
        local_end_x = event.x_root # Capturar en variable local (coordenadas globales físicas)
        local_end_y = event.y_root # Capturar en variable local (coordenadas globales físicas)
        print(f"UI Layer (Tkinter Thread): Mouse UP detected at ({local_end_x}, {local_end_y})")
        root.destroy() # Cerrar la ventana de Tkinter al soltar


    def on_escape(event):
        nonlocal root, local_start_x # Necesitamos local_start_x para indicar cancelación
        print("UI Layer (Tkinter Thread): Escape detected.")
        # Si se presiona Escape, simplemente destruimos la ventana sin guardar coordenadas
        local_start_x = None # Indicar cancelación usando la variable local
        root.destroy()


    try:
        root = tk.Tk()
        root.overrideredirect(True) # Sin bordes ni barra de título

        # Establecer la geometría para cubrir el escritorio virtual físico
        # Usamos las coordenadas físicas calculadas por PySide
        root.geometry(f"{desktop_geometry.width()}x{desktop_geometry.height()}+{desktop_geometry.x()}+{desktop_geometry.y()}")

        root.attributes('-alpha', 0.3) # Semitransparente
        root.configure(background='black')
        root.attributes('-topmost', True) # Siempre encima

        canvas = Canvas(root, cursor="cross")
        canvas.pack(fill='both', expand=True)

        canvas.bind("<ButtonPress-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_drag)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)
        root.bind("<Escape>", on_escape)

        print("UI Layer (Tkinter Thread): Selector de región iniciado. tk.Tk().mainloop() called.")
        root.mainloop() # Iniciar el bucle de eventos de Tkinter (bloqueante para este hilo)
        print("UI Layer (Tkinter Thread): tk.Tk().mainloop() returned.")


        # --- Lógica de Captura después de que el bucle de Tkinter termine ---
        # Esto solo se ejecuta si root.destroy() fue llamado (selección o escape)

        # Copiar las coordenadas locales a las globales justo antes de finalizar el hilo
        _tkinter_start_x = local_start_x
        _tkinter_start_y = local_start_y
        _tkinter_end_x = local_end_x
        _tkinter_end_y = local_end_y

        print(f"UI Layer (Tkinter Thread): Checking selection status. Global _tkinter_start_x is {_tkinter_start_x}, Global _tkinter_end_x is {_tkinter_end_x}")

        # Verificar si la selección fue válida (no cancelada y con dimensiones)
        if _tkinter_start_x is not None and _tkinter_end_x is not None and _tkinter_start_y is not None and _tkinter_end_y is not None:
            # Asegurarse de que las coordenadas estén ordenadas (de menor a mayor)
            x1, y1 = min(_tkinter_start_x, _tkinter_end_x), min(_tkinter_start_y, _tkinter_end_y)
            x2, y2 = max(_tkinter_start_x, _tkinter_end_x), max(_tkinter_start_y, _tkinter_end_y)

            # Verificar que se seleccionó una región válida (evitar capturas de 0 ancho/alto)
            if x2 - x1 > 1 and y2 - y1 > 1:
                # Definir el cuadro de delimitación para mss (diccionario)
                # mss usa las mismas coordenadas de píxeles físicos que Tkinter event.x_root/y_root
                monitor = {"top": y1, "left": x1, "width": x2 - x1, "height": y2 - y1}
                print(f"UI Layer (Tkinter Thread): Valid selection detected. Performing capture with mss monitor: {monitor}")

                try:
                    # Realizar la captura con mss
                    with mss.mss() as sct:
                         # Get raw pixels from the screen region
                         sct_img = sct.grab(monitor)

                         # Convertir los datos de píxeles de mss a un objeto PIL Image
                         # sct_img.rgb contiene los píxeles en formato RGB
                         # sct_img.size es una tupla (width, height)
                         img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)


                    # Guardar la imagen PIL en el archivo temporal
                    # Usamos PNG para evitar pérdidas de calidad y porque Tesseract lo soporta bien
                    img.save(_tkinter_captured_image_path, "PNG")
                    print(f"UI Layer (Tkinter Thread): Capture saved successfully as {_tkinter_captured_image_path}")
                except Exception as e:
                    _tkinter_capture_error = f"Error al realizar la captura con mss o guardar imagen: {e}"
                    print(f"UI Layer (Tkinter Thread) Error: {_tkinter_capture_error}")
            else:
                 # Selección demasiado pequeña o inválida
                 _tkinter_start_x = None # Indicar que no hay selección válida para procesar
                 print("UI Layer (Tkinter Thread): Selection invalid (too small).")

        else:
            # Selección cancelada por Escape o Mouse UP no procesado correctamente
            print("UI Layer (Tkinter Thread): Selection cancelled or Mouse UP not processed.")


    except Exception as e:
        _tkinter_capture_error = f"Error inesperado en el hilo del selector Tkinter: {e}"
        print(f"UI Layer (Tkinter Thread) Error: {_tkinter_capture_error}")
    finally:
        # Señalar que la selección y captura han terminado (o fueron canceladas/hubo error)
        _tkinter_selection_complete.set()
        print("UI Layer (Tkinter Thread): Hilo del selector Tkinter finalizado.")


def _get_virtual_desktop_physical_geometry():
    """
    Obtiene la geometría física (posición y tamaño en píxeles físicos)
    del escritorio virtual utilizando PySide6.
    """
    # Usamos la instancia existente de QApplication del hilo principal PySide
    app = QApplication.instance()
    if not app:
        print("Error: No hay instancia de QApplication en _get_virtual_desktop_physical_geometry.")
        return None # No podemos obtener pantallas sin QApplication

    screens = QGuiApplication.screens()
    if not screens:
        print("Error: No se detectaron pantallas usando PySide6.")
        return None

    virtual_desktop_physical_rect = QRect()

    for screen in screens:
        logical_geometry = screen.geometry()
        device_pixel_ratio = screen.devicePixelRatio()

        # Calcular la geometría física para esta pantalla
        # Posición física = Posición lógica * factor de escala
        # Tamaño físico = Tamaño lógico * factor de escala
        # Usamos int() para asegurar que las coordenadas sean píxeles enteros
        physical_x = int(logical_geometry.x() * device_pixel_ratio)
        physical_y = int(logical_geometry.y() * device_pixel_ratio)
        physical_width = int(logical_geometry.width() * device_pixel_ratio)
        # CORRECCIÓN: Usar device_pixel_ratio aquí
        physical_height = int(logical_geometry.height() * device_pixel_ratio)

        physical_screen_rect = QRect(physical_x, physical_y, physical_width, physical_height)

        virtual_desktop_physical_rect = virtual_desktop_physical_rect.united(physical_screen_rect)

        print(f"UI Layer (PySide Thread): Screen: {screen.name()}, Logical: {logical_geometry}, Physical Calculated: {physical_screen_rect}, DPR: {device_pixel_ratio}")

    # No cerramos la instancia de QApplication aquí, ya que es la del hilo principal.
    print(f"UI Layer (PySide Thread): Geometría física calculada del escritorio virtual: {virtual_desktop_physical_rect}")
    return virtual_desktop_physical_rect


# --- Clase Emitter para comunicar desde el hilo estándar al hilo principal ---
class TranslationResultEmitter(QObject):
    """Emite señales para comunicar resultados de traducción/OCR al hilo principal de la UI."""
    # Señal que lleva el resultado de la traducción/OCR
    translation_finished = Signal(TranslationResult)
    # Señal que lleva un mensaje de error
    error_occurred = Signal(str)
    # Señal para indicar que una tarea ha comenzado (opcionalmente con un mensaje)
    task_started = Signal(str)
    # Señal para indicar que una tarea ha terminado
    task_finished = Signal()


# --- Resto de la clase MainWindow ---

class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación de traducción.
    Esta clase reside en la capa de Presentación y depende de TranslatorService.
    """

    def __init__(self, translator_service: TranslatorService):
        """
        Constructor de la ventana principal.
        """
        super().__init__()

        if not isinstance(translator_service, TranslatorService):
             raise TypeError("translator_service must be an instance of TranslatorService")

        self.translator_service = translator_service

        self.setWindowTitle("Polar Translate")
        self.setGeometry(100, 100, 700, 500) # Aumentamos un poco el tamaño

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Listo.")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Layout para la selección de idiomas y botón de traducción manual
        controls_layout = QHBoxLayout()

        self.source_lang_combo = QComboBox()
        self.source_lang_label = QLabel("Origen:")
        controls_layout.addWidget(self.source_lang_label)
        controls_layout.addWidget(self.source_lang_combo)

        self.target_lang_combo = QComboBox()
        self.target_lang_label = QLabel("Destino:")
        controls_layout.addWidget(self.target_lang_label)
        controls_layout.addWidget(self.target_lang_combo)

        self.translate_button = QPushButton("Traducir Texto Manual") # Cambiamos el texto del botón
        controls_layout.addWidget(self.translate_button)

        main_layout.addLayout(controls_layout)

        # --- Nuevos botones para OCR y Archivos ---
        file_ocr_layout = QHBoxLayout()

        self.ocr_file_button = QPushButton("Traducir Imagen") # OCR desde archivo
        file_ocr_layout.addWidget(self.ocr_file_button)
        self.ocr_file_button.setEnabled(True) # Habilitar botón de OCR Archivo

        self.ocr_clipboard_button = QPushButton("Imagen desde Portapapeles")
        file_ocr_layout.addWidget(self.ocr_clipboard_button)
        self.ocr_clipboard_button.setEnabled(True) # Habilitar botón de OCR Portapapeles

        self.translate_file_button = QPushButton("Traducir Archivo de Texto")
        file_ocr_layout.addWidget(self.translate_file_button)

        main_layout.addLayout(file_ocr_layout)
        # --- Fin Nuevos botones ---

        # --- Nuevo botón para Captura de Pantalla y OCR ---
        screen_capture_layout = QHBoxLayout()

        self.capture_screen_button = QPushButton("Capturar Pantalla y Traducir") # Nuevo botón
        screen_capture_layout.addWidget(self.capture_screen_button)
        self.capture_screen_button.setEnabled(True) # Habilitar botón de captura de pantalla

        main_layout.addLayout(screen_capture_layout)
        # --- Fin Nuevo botón ---


        self.input_text_edit = QTextEdit()
        self.input_text_edit.setPlaceholderText("Introduce el texto a traducir aquí o usa las opciones de OCR/Archivo...")
        main_layout.addWidget(self.input_text_edit)

        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        self.output_text_edit.setPlaceholderText("El texto traducido aparecerá aquí...")
        main_layout.addWidget(self.output_text_edit)

        # Conectar señales (eventos) a slots (métodos que responden a eventos)
        self.translate_button.clicked.connect(self.on_translate_button_clicked)
        self.translate_file_button.clicked.connect(self.on_translate_file_button_clicked)
        # Conectar los nuevos botones de OCR
        self.ocr_file_button.clicked.connect(self.on_ocr_file_button_clicked)
        self.ocr_clipboard_button.clicked.connect(self.on_ocr_clipboard_button_clicked)
        # Conectar el nuevo botón de captura de pantalla
        self.capture_screen_button.clicked.connect(self.on_capture_screen_button_clicked)


        # --- Conexión para Hotkeys ---
        # Asumimos que HotkeySignalEmitter es un QObject y vive en el hilo principal
        # o maneja la comunicación de hilos internamente si el listener está en otro hilo.
        self._hotkey_signal_emitter: HotkeySignalEmitter = self.translator_service.get_hotkey_signal_emitter()
        self._hotkey_signal_emitter.translation_finished.connect(self.on_hotkey_translation_finished)
        self._hotkey_signal_emitter.error_occurred.connect(self.on_hotkey_error_occurred)

        # --- Emisor de Señales para Hilo Estándar (Tareas de Traducción/OCR) ---
        # Creamos una instancia del emisor de señales para comunicar desde el hilo estándar
        self._translation_result_emitter = TranslationResultEmitter()
        self._translation_result_emitter.translation_finished.connect(self._on_translation_task_finished)
        self._translation_result_emitter.error_occurred.connect(self._on_translation_task_error)
        # Conectar las nuevas señales de inicio/fin de tarea
        self._translation_result_emitter.task_started.connect(self._on_translation_task_started)
        self._translation_result_emitter.task_finished.connect(self._on_translation_task_completed)


        # --- Conexión para la señal de finalización del selector Tkinter ---
        # Usaremos el evento _tkinter_selection_complete y un timer para verificarlo periódicamente
        self._selector_completion_timer = None


        self.load_languages()

        # Atributo para mantener referencia al hilo estándar
        self._current_translation_thread: Optional[threading.Thread] = None

        # Atributo para la ventana selectora (no necesitamos una referencia directa a la ventana Tkinter)
        # self._selector_window: Optional[ScreenSelectorWindow] = None # Ya no usamos ScreenSelectorWindow


    def _set_ui_busy_state(self, is_busy: bool, message: str = ""):
        """
        Establece el estado de ocupado de la UI, deshabilitando/habilitando botones
        y actualizando la barra de estado.
        """
        self.translate_button.setEnabled(not is_busy)
        self.ocr_file_button.setEnabled(not is_busy)
        self.ocr_clipboard_button.setEnabled(not is_busy)
        self.translate_file_button.setEnabled(not is_busy)
        self.capture_screen_button.setEnabled(not is_busy)
        self.source_lang_combo.setEnabled(not is_busy)
        self.target_lang_combo.setEnabled(not is_busy)

        if is_busy:
            # Mostrar mensaje de tarea en curso
            self.statusBar.showMessage(message, 0) # 0 significa mostrar indefinidamente
        else:
            # Mostrar mensaje de listo
            self.statusBar.showMessage(message if message else "Listo.", 3000) # Mostrar mensaje específico o "Listo." por 3 seg


    @Slot(str)
    def _on_translation_task_started(self, message: str):
        """
        Slot que se ejecuta cuando se recibe la señal de inicio de tarea desde el hilo estándar.
        Actualiza la UI para indicar que una tarea está en curso.
        """
        print(f"UI Layer: Tarea iniciada: {message}")
        self._set_ui_busy_state(True, message)
        # Opcional: Cambiar el cursor a "ocupado"
        QApplication.setOverrideCursor(Qt.WaitCursor)


    @Slot()
    def _on_translation_task_completed(self):
        """
        Slot que se ejecuta cuando se recibe la señal de fin de tarea desde el hilo estándar.
        Actualiza la UI para indicar que no hay tareas en curso.
        """
        print("UI Layer: Tarea completada.")
        self._set_ui_busy_state(False)
        # Opcional: Restaurar el cursor
        QApplication.restoreOverrideCursor()


    def load_languages(self):
        """
        Carga los idiomas disponibles en los ComboBoxes de origen y destino.
        """
        print("UI Layer: Loading languages...")
        self._set_ui_busy_state(True, "Cargando idiomas...")
        QApplication.processEvents() # Asegurar que el mensaje se muestre

        try:
            languages: List[Language] = self.translator_service.get_supported_languages()
            print(f"UI Layer: Loaded {len(languages)} languages.")

            self.source_lang_combo.clear()
            self.target_lang_combo.clear()

            for lang in languages:
                self.source_lang_combo.addItem(lang.name, lang)
                self.target_lang_combo.addItem(lang.name, lang)

            if len(languages) >= 2:
                 es_index = self.target_lang_combo.findData(Language(code="es", name="Spanish")) # Nota: El nombre exacto puede variar según argostranslate
                 if es_index == -1: # Fallback por si el nombre no es "Spanish"
                     es_index = self.target_lang_combo.findData(Language(code="es", name="Español"))
                 if es_index != -1:
                     self.target_lang_combo.setCurrentIndex(es_index)

                 en_index = self.source_lang_combo.findData(Language(code="en", name="English")) # Nota: El nombre exacto puede variar según argostranslate
                 if en_index == -1: # Fallback por si el nombre no es "English"
                      en_index = self.source_lang_combo.findData(Language(code="en", name="Inglés"))
                 if en_index != -1:
                      self.source_lang_combo.setCurrentIndex(en_index)


            self._set_ui_busy_state(False, "Idiomas cargados. Listo.")

        except Exception as e:
            print(f"UI Layer: Error loading languages: {e}")
            error_msg = f"Error al cargar idiomas: {e}"
            self.output_text_edit.setText(error_msg)
            self._set_ui_busy_state(False, error_msg) # Mostrar error en barra de estado


    def on_translate_button_clicked(self):
        """
        Slot para traducir texto manual.
        """
        print("UI Layer: Translate button clicked (manual).")

        input_text = self.input_text_edit.toPlainText()

        source_language: Language = self.source_lang_combo.currentData()
        target_language: Language = self.target_lang_combo.currentData()

        if not input_text:
            self.output_text_edit.setText("Por favor, introduce texto para traducir.")
            self.statusBar.showMessage("Por favor, introduce texto para traducir.", 3000)
            return

        if not source_language or not target_language:
             self.output_text_edit.setText("Por favor, selecciona idiomas de origen y destino válidos.")
             self.statusBar.showMessage("Por favor, selecciona idiomas.", 3000)
             return

        # Indicar inicio de tarea
        self._translation_result_emitter.task_started.emit("Traduciendo texto manual...")

        # Iniciar la tarea de traducción en un hilo estándar
        self._start_translation_task(
            self.translator_service.perform_translation,
            input_text,
            source_language.code,
            target_language.code
        )


    # --- Slots para Hotkeys (existente, modificado para usar pop-up) ---
    @Slot(TranslationResult)
    def on_hotkey_translation_finished(self, result: TranslationResult):
        """
        Slot que se ejecuta cuando se recibe la señal de traducción de portapapeles finalizada.
        Muestra el resultado en una ventana pop-up.
        """
        print("UI Layer: Señal de traducción de portapapeles recibida.")
        # Asegurarse de que el resultado es un TranslationResult
        if not isinstance(result, TranslationResult):
             print(f"UI Layer Error: Resultado de hotkey inesperado: {type(result).__name__}")
             self.statusBar.showMessage(f"Error hotkey: Resultado inesperado.", 5000)
             return

        if result.is_successful:
            pop_up = PopUpTranslationWindow(result.translated_text, self)
            pop_up.show()
            self.statusBar.showMessage("Traducción por hotkey completada.", 3000)
        else:
            error_message = f"Error (Hotkey): {result.error}"
            print(f"UI Layer: {error_message}")
            self.statusBar.showMessage(error_message, 5000)


    @Slot(str)
    def on_hotkey_error_occurred(self, error_message: str):
        """
        Slot que se ejecuta cuando se recibe una señal de error desde el hilo de hotkey.
        Muestra el error en la barra de estado.
        """
        print(f"UI Layer: Señal de error de hotkey recibida: {error_message}")
        self.statusBar.showMessage(f"Error hotkey: {error_message}", 5000)


    # --- Slots para OCR y Archivos ---

    @Slot()
    def on_ocr_file_button_clicked(self):
        """
        Slot para el botón 'OCR desde Archivo'.
        Abre un diálogo para seleccionar un archivo de imagen y realiza OCR + Traducción.
        """
        print("UI Layer: 'OCR desde Archivo' button clicked.")
        # Abrir diálogo de archivo para seleccionar una imagen
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Seleccionar archivo de imagen para OCR")
        # Filtrar por tipos de archivo de imagen comunes
        file_dialog.setNameFilter("Archivos de Imagen (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        file_dialog.setFileMode(QFileDialog.ExistingFile) # Solo permitir seleccionar un archivo existente

        if file_dialog.exec(): # Mostrar el diálogo y esperar a que el usuario seleccione un archivo
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                image_path = selected_files[0]
                print(f"UI Layer: Archivo de imagen seleccionado: {image_path}")

                # Obtener los idiomas seleccionados para la traducción
                source_language: Language = self.source_lang_combo.currentData()
                target_language: Language = self.target_lang_combo.currentData()

                if not source_language or not target_language:
                    self.statusBar.showMessage("Por favor, selecciona idiomas de origen y destino.", 3000)
                    return

                # Indicar inicio de tarea
                self._translation_result_emitter.task_started.emit("Realizando OCR y Traduciendo desde archivo...")

                try:
                    # Cargar la imagen usando PIL
                    image = Image.open(image_path)
                    # Llamar al servicio de aplicación para realizar OCR y traducción
                    # Ejecutamos en un hilo estándar para no bloquear la UI
                    self._start_translation_task( # Usamos el método genérico del hilo estándar
                        self.translator_service.perform_ocr_and_translate,
                        image, # Pasamos el objeto PIL Image
                        source_language.code,
                        target_language.code
                        # Los slots de resultado/error ya están conectados a _translation_result_emitter
                    )

                except FileNotFoundError:
                    error_msg = f"Error: Archivo no encontrado en {image_path}"
                    print(f"UI Layer: {error_msg}")
                    # Emitir error para que el slot lo maneje
                    self._translation_result_emitter.error_occurred.emit(error_msg)
                    # Asegurar que el estado de ocupado se desactive
                    self._translation_result_emitter.task_finished.emit()

                except Exception as e:
                    error_msg = f"Error al cargar o procesar imagen de archivo: {e}"
                    print(f"UI Layer: {error_msg}")
                    # Emitir error para que el slot lo maneje
                    self._translation_result_emitter.error_occurred.emit(error_msg)
                    # Asegurar que el estado de ocupado se desactive
                    self._translation_result_emitter.task_finished.emit()


    @Slot()
    def on_ocr_clipboard_button_clicked(self):
        """
        Slot para el botón 'OCR desde Portapapeles (Imagen)'.
        Obtiene la imagen del portapapeles, la guarda temporalmente y realiza OCR + Traducción.
        """
        print("UI Layer: 'OCR desde Portapapeles (Imagen)' button clicked.")
        clipboard = QGuiApplication.clipboard()

        # Verificar si el portapapeles contiene una imagen
        if clipboard.mimeData().hasImage():
            image = clipboard.image() # Obtener la imagen como QImage
            print("UI Layer: Imagen encontrada en el portapapeles.")

            # Obtener los idiomas seleccionados para la traducción
            source_language: Language = self.source_lang_combo.currentData()
            target_language: Language = self.target_lang_combo.currentData()

            if not source_language or not target_language:
                self.statusBar.showMessage("Por favor, selecciona idiomas de origen y destino.", 3000)
                return

            # Indicar inicio de tarea
            self._translation_result_emitter.task_started.emit("Realizando OCR y Traduciendo desde portapapeles...")

            # --- Guardar QImage a un archivo temporal ---
            temp_file = None # Inicializar a None
            temp_file_path = None
            try:
                # Crear un archivo temporal con extensión .png
                temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                temp_file_path = temp_file.name
                temp_file.close() # Cerrar el manejador de archivo inmediatamente

                # Guardar la QImage en el archivo temporal
                success = image.save(temp_file_path, "PNG") # Usar la ruta del archivo y formato string

                if not success:
                     error_msg = f"Error al guardar la imagen del portapapeles en archivo temporal: {temp_file_path}"
                     print(f"UI Layer: {error_msg}")
                     # Emitir error
                     self._translation_result_emitter.error_occurred.emit(error_msg)
                     # Asegurar que el estado de ocupado se desactive
                     self._translation_result_emitter.task_finished.emit()
                     # Intentar eliminar el archivo temporal si existía
                     if os.path.exists(temp_file_path):
                         os.remove(temp_file_path)
                     return

                print(f"UI Layer: Imagen del portapapeles guardada temporalmente en: {temp_file_path}")

                # Cargar la imagen desde el archivo temporal usando PIL
                pil_image = Image.open(temp_file_path)

                # Llamar al servicio de aplicación para realizar OCR y traducción
                self._start_translation_task( # Usamos el método genérico del hilo estándar
                    self.translator_service.perform_ocr_and_translate,
                    pil_image, # Pasamos el objeto PIL Image
                    source_language.code,
                    target_language.code,
                    temp_file_path=temp_file_path # Pasamos la ruta del archivo temporal como argumento
                )

            except Exception as e:
                error_msg = f"Error inesperado durante el procesamiento de imagen del portapapeles: {e}"
                print(f"UI Layer: {error_msg}")
                # Emitir error
                self._translation_result_emitter.error_occurred.emit(error_msg)
                # Asegurar que el estado de ocupado se desactive
                self._translation_result_emitter.task_finished.emit()
                # Asegurar que el archivo temporal se limpie en caso de error
                if temp_file_path is not None and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)


        else:
            print("UI Layer: No se encontró imagen en el portapapeles.")
            self.output_text_edit.setText("No se encontró imagen en el portapapeles.")
            self.statusBar.showMessage("No se encontró imagen en el portapapeles.", 3000)


    @Slot()
    def on_translate_file_button_clicked(self):
        """
        Slot para el botón 'Traducir Archivo (Texto)'.
        Abre un diálogo para seleccionar un archivo de texto (.txt, .doc, .docx) y lo traduce.
        """
        print("UI Layer: 'Traducir Archivo (Texto)' button clicked.")
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Seleccionar archivo de texto para traducir")
        file_dialog.setNameFilter("Archivos de Texto (*.txt *.doc *.docx);;Todos los archivos (*.*)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                print(f"UI Layer: Archivo de texto seleccionado: {file_path}")

                source_language: Language = self.source_lang_combo.currentData()
                target_language: Language = self.target_lang_combo.currentData()

                if not source_language or not target_language:
                    self.statusBar.showMessage("Por favor, selecciona idiomas de origen y destino.", 3000)
                    return

                # Indicar inicio de tarea
                self._translation_result_emitter.task_started.emit("Leyendo archivo y Traduciendo...")

                try:
                    # Leer el contenido del archivo - Esto puede ser bloqueante, pero lo hacemos antes del worker
                    # para validar el archivo y mostrar mensajes de error inmediatos si falla la lectura.
                    file_content = self._read_file_content(file_path)

                    if not file_content:
                         # Si _read_file_content mostró un QMessageBox, ya notificó al usuario.
                         # Solo necesitamos desactivar el estado de ocupado.
                         self._translation_result_emitter.task_finished.emit()
                         return

                    # Iniciar la tarea de traducción en un hilo estándar
                    self._start_translation_task( # Usamos el método genérico del hilo estándar
                         self.translator_service.perform_translation, # Usamos perform_translation
                         file_content,
                         source_language.code,
                         target_language.code
                         # Los slots de resultado/error ya están conectados a _translation_result_emitter
                    )

                except FileNotFoundError:
                    error_msg = f"Error: Archivo no encontrado en {file_path}"
                    print(f"UI Layer: {error_msg}")
                    # Emitir error
                    self._translation_result_emitter.error_occurred.emit(error_msg)
                    # Asegurar que el estado de ocupado se desactive
                    self._translation_result_emitter.task_finished.emit()
                except Exception as e:
                    error_msg = f"Error inesperado al procesar archivo de texto: {e}"
                    print(f"UI Layer: {error_msg}")
                    # Emitir error
                    self._translation_result_emitter.error_occurred.emit(error_msg)
                    # Asegurar que el estado de ocupado se desactive
                    self._translation_result_emitter.task_finished.emit()


    def _read_file_content(self, file_path: str) -> str:
        """
        Lee el contenido de un archivo de texto (.txt, .doc, .docx).
        Retorna el contenido como string, o cadena vacía si hay error o no soportado.
        Muestra QMessageBox en caso de error o formato no soportado.
        """
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower()

        if file_extension == ".txt":
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content:
                        QMessageBox.warning(self, "Archivo Vacío", "El archivo de texto seleccionado está vacío.")
                    return content
            except Exception as e:
                print(f"UI Layer: Error al leer archivo .txt: {e}")
                QMessageBox.warning(self, "Error al leer archivo", f"No se pudo leer el archivo .txt: {e}")
                return ""
        elif file_extension == ".docx":
            if Document:
                try:
                    document = Document(file_path)
                    content = "\n".join([paragraph.text for paragraph in document.paragraphs])
                    if not content:
                         QMessageBox.warning(self, "Archivo Vacío", "El archivo .docx seleccionado está vacío o no contiene texto.")
                    return content
                except Exception as e:
                    print(f"UI Layer: Error al leer archivo .docx: {e}")
                    QMessageBox.warning(self, "Error al leer archivo", f"No se pudo leer el archivo .docx: {e}")
                    return ""
            else:
                print("UI Layer: La biblioteca 'python-docx' no está instalada.")
                QMessageBox.warning(self, "Biblioteca faltante", "Para leer archivos .docx, instala la biblioteca 'python-docx' (`pip install python-docx`).")
                return ""
        elif file_extension == ".doc":
             print("UI Layer: La lectura de archivos .doc no está implementada.")
             QMessageBox.warning(self, "Formato no soportado", "Actualmente no se soporta la lectura de archivos .doc. Por favor, usa .docx o .txt.")
             return ""
        else:
            print(f"UI Layer: Extensión de archivo no soportada para lectura de texto: {file_extension}")
            QMessageBox.warning(self, "Formato no soportado", f"La extensión de archivo '{file_extension}' no está soportada para lectura de texto.")
            return ""


    # --- Función que se ejecutará en el hilo estándar (Tareas de Traducción/OCR) ---
    def _translation_task_function(self, func: Callable, *args, **kwargs):
        """
        Esta función se ejecuta en un hilo estándar.
        Llama a la función de traducción/OCR y emite señales al hilo principal.
        También maneja la limpieza del archivo temporal si se usó.
        """
        print(f"Standard Thread: _translation_task_function() iniciado. Llamando a {func.__name__}...")
        # Obtener la ruta del archivo temporal si existe (ahora puede ser "captura_pil.png")
        temp_file_path = kwargs.pop('temp_file_path', None)

        try:
            # Ejecutar la función (perform_translation o perform_ocr_and_translate)
            # Esperamos que la función retorne un TranslationResult
            translation_result: TranslationResult = func(*args, **kwargs)
            print("Standard Thread: La función de traducción/OCR ha regresado.")
            # Emitir el resultado al hilo principal usando la señal
            # Aseguramos que emitimos un TranslationResult válido
            if isinstance(translation_result, TranslationResult):
                 self._translation_result_emitter.translation_finished.emit(translation_result)
                 print("Standard Thread: Señal 'translation_finished' emitida.")
            else:
                 # Si la función no retornó un TranslationResult, emitimos un error
                 error_msg = f"La función {func.__name__} retornó un tipo inesperado: {type(translation_result).__name__}"
                 print(f"Standard Thread: {error_msg}")
                 self._translation_result_emitter.error_occurred.emit(error_msg)
                 print("Standard Thread: Señal 'error_occurred' emitida debido a tipo de retorno inesperado.")

        except Exception as e:
            # Capturar excepciones y emitir la señal de error al hilo principal
            print(f"Standard Thread: Error capturado: {e}")
            self._translation_result_emitter.error_occurred.emit(str(e))
            print("Standard Thread: Señal 'error_occurred' emitida.")
        finally:
             print("Standard Thread: _translation_task_function() finalizando.")
             # --- Limpieza del archivo temporal ---
             if temp_file_path and os.path.exists(temp_file_path):
                 try:
                     os.remove(temp_file_path)
                     print(f"Standard Thread: Archivo temporal eliminado: {temp_file_path}")
                 except Exception as cleanup_e:
                     print(f"Standard Thread Error: No se pudo eliminar el archivo temporal {temp_file_path}: {cleanup_e}")
             # --- Fin Limpieza ---
             # Indicar que la tarea ha terminado, independientemente del resultado
             self._translation_result_emitter.task_finished.emit()


    # --- Método genérico para iniciar tareas en el Hilo Estándar ---
    def _start_translation_task(self, func: Callable, *args, **kwargs):
        """
        Inicia una función dada (relacionada con traducción/OCR) en un hilo estándar.
        """
        # Si ya hay un hilo activo, no iniciar uno nuevo
        if self._current_translation_thread is not None and self._current_translation_thread.is_alive():
            print("UI Layer: Hilo de traducción ocupado. Espere a que termine la tarea actual.")
            self.statusBar.showMessage("Tarea anterior aún en proceso. Espere.", 3000)
            return

        print("UI Layer: Creando nuevo hilo estándar para tarea de traducción.")
        # Crear un nuevo hilo estándar
        # Pasamos la función _translation_task_function y sus argumentos
        self._current_translation_thread = threading.Thread(
            target=self._translation_task_function,
            args=(func, *args),
            kwargs=kwargs,
            daemon=True # Permite que el hilo se cierre automáticamente si la aplicación principal termina
        )

        # Iniciar el hilo
        self._current_translation_thread.start()
        print("UI Layer: Hilo estándar iniciado.")
        # La señal task_started se emite en los slots de los botones antes de llamar a este método


    # --- Slots para manejar resultados/errores del Hilo Estándar ---
    @Slot(TranslationResult)
    def _on_translation_task_finished(self, result: TranslationResult):
        """
        Slot que se ejecuta cuando se recibe la señal de traducción/OCR finalizada desde el hilo estándar.
        Muestra el resultado en el área de texto de salida.
        """
        print("UI Layer: Señal de traducción/OCR finalizada recibida desde hilo estándar.")
        # Ya verificamos que el resultado es TranslationResult en _translation_task_function
        if result.is_successful:
            self.output_text_edit.setText(result.translated_text)
            # El estado de "Listo" se establecerá en _on_translation_task_completed
        else:
            error_message = f"Error en tarea de traducción/OCR: {result.error}"
            print(f"UI Layer: {error_message}")
            self.output_text_edit.setText(error_message)
            # El error en la barra de estado se mostrará en _on_translation_task_error


        # Limpiar la referencia al hilo actual después de que la tarea termine
        self._current_translation_thread = None


    @Slot(str)
    def _on_translation_task_error(self, error_message: str):
        """
        Slot que se ejecuta cuando se recibe una señal de error desde el hilo estándar.
        Muestra el error en el área de texto de salida y la barra de estado.
        """
        print(f"UI Layer: Señal de error de tarea de traducción/OCR recibida desde hilo estándar: {error_message}")
        self.output_text_edit.setText(f"Error en tarea de traducción/OCR: {error_message}")
        # El estado de "Listo" con el mensaje de error se establecerá en _on_translation_task_completed
        # self.statusBar.showMessage(f"Error en tarea: {error_message}", 5000) # Ya se maneja en _on_translation_task_completed


        # Limpiar la referencia al hilo actual después de que la tarea termine
        self._current_translation_thread = None

    @Slot()
    def _on_translation_task_completed(self):
        """
        Slot que se ejecuta cuando se recibe la señal de fin de tarea desde el hilo estándar.
        Actualiza la UI para indicar que no hay tareas en curso y restaura el cursor.
        """
        print("UI Layer: Señal de fin de tarea recibida desde hilo estándar.")
        # Restaurar el estado de la UI a no ocupado
        # El mensaje de la barra de estado se establecerá a "Listo." por defecto
        self._set_ui_busy_state(False)
        # Restaurar el cursor
        QApplication.restoreOverrideCursor()


    def closeEvent(self, event):
        """
        Maneja el evento de cierre de la ventana.
        Asegura que el listener de hotkeys y el hilo de traducción estándar se detengan limpiamente.
        """
        print("UI Layer: Evento de cierre de ventana detectado.")
        self.statusBar.showMessage("Cerrando aplicación...", 0)
        QApplication.processEvents()

        # Detener el listener de hotkeys (ya conectado a aboutToQuit en main.py)
        # self.translator_service.stop_hotkey_listening() # Ya está conectado en main.py
        print("Application Layer: Solicitando detener monitoreo de hotkeys.")

        # No necesitamos detener explícitamente el hilo estándar aquí si es daemon=True.
        # Se cerrará automáticamente cuando el hilo principal (UI) termine.
        # Si no fuera daemon, necesitaríamos un mecanismo para solicitarle que termine.
        if self._current_translation_thread is not None and self._current_translation_thread.is_alive():
             print("UI Layer: Hilo de traducción estándar aún activo (daemon). Se cerrará con la aplicación principal.")
             # Opcional: Intentar un join() con timeout si no fuera daemon o si queremos esperar
             # self._current_translation_thread.join(1.0) # Esperar 1 segundo

        print("UI Layer: Aceptando evento de cierre.")
        event.accept()

    # --- Slot para Captura de Pantalla y OCR (Lanza el selector Tkinter en hilo) ---
    @Slot()
    def on_capture_screen_button_clicked(self):
        """
        Slot para el botón 'Capturar Pantalla y Traducir'.
        Oculta la ventana principal, obtiene la geometría del escritorio virtual,
        y lanza el selector de región de Tkinter en un hilo separado.
        Inicia un timer para verificar la finalización del selector.
        """
        print("UI Layer: 'Capturar Pantalla y Traducir' button clicked.")

        # Obtener los idiomas seleccionados para la traducción antes de ocultar la ventana
        source_language: Language = self.source_lang_combo.currentData()
        target_language: Language = self.target_lang_combo.currentData()

        if not source_language or not target_language:
            self.statusBar.showMessage("Por favor, selecciona idiomas de origen y destino.", 3000)
            return

        # Verificar si hay un hilo de traducción/OCR activo
        if self._current_translation_thread is not None and self._current_translation_thread.is_alive():
            print("UI Layer: Hilo de traducción/OCR ocupado. Espere a que termine la tarea actual.")
            self.statusBar.showMessage("Tarea anterior aún en proceso. Espere.", 3000)
            return

        # Verificar si el selector ya está activo (prevenir múltiples instancias)
        if self._selector_completion_timer is not None and self._selector_completion_timer.isActive():
             print("UI Layer: Selector de región ya activo. Espere a que termine.")
             self.statusBar.showMessage("Selector de región ya activo.", 3000)
             return

        # Indicar inicio de tarea (solo para el selector)
        self.statusBar.showMessage("Preparando selector de región...", 0)
        QApplication.processEvents() # Procesar eventos para actualizar la UI inmediatamente


        try:
            # Obtener la geometría física del escritorio virtual usando PySide
            desktop_geometry = _get_virtual_desktop_physical_geometry()

            if desktop_geometry is None:
                error_msg = "No se pudo obtener la geometría del escritorio virtual para el selector."
                print(f"UI Layer Error: {error_msg}")
                self.output_text_edit.setText(error_msg)
                self.statusBar.showMessage(error_msg, 5000)
                return

            # Ocultar la ventana principal antes de mostrar el selector
            self.hide()

            # Lanzar el selector de Tkinter en un hilo separado
            print("UI Layer: Lanzando selector Tkinter en hilo separado.")
            selector_thread = threading.Thread(
                target=_run_tkinter_selector,
                args=(desktop_geometry,),
                daemon=True # Permite que el hilo se cierre con la aplicación principal
            )
            selector_thread.start()

            # Iniciar un QTimer para verificar periódicamente si el selector Tkinter ha terminado
            # Usamos un timer porque no podemos hacer join() en el hilo de la UI
            self._selector_completion_timer = QTimer(self)
            self._selector_completion_timer.timeout.connect(self._check_selector_completion)
            self._selector_completion_timer.start(100) # Verificar cada 100 ms
            print("UI Layer: QTimer iniciado para verificar finalización del selector.")


        except Exception as e:
            error_msg = f"Error inesperado al lanzar el selector de región: {e}"
            print(f"UI Layer: {error_msg}")
            self.output_text_edit.setText(error_msg)
            self.statusBar.showMessage(error_msg, 5000)
            # Asegurarse de mostrar la ventana principal de nuevo si algo falla antes de mostrar el selector
            if not self.isVisible():
                self.show()

    @Slot()
    def _check_selector_completion(self):
        """
        Slot llamado por el QTimer para verificar si el selector Tkinter ha terminado.
        Si terminó, detiene el timer y procesa la captura.
        """
        global _tkinter_start_x, _tkinter_start_y, _tkinter_end_x, _tkinter_end_y
        global _tkinter_selection_complete, _tkinter_capture_error, _tkinter_captured_image_path

        # Verificar si el evento de finalización está seteado
        if _tkinter_selection_complete.is_set():
            # Detener el timer
            self._selector_completion_timer.stop()
            print("UI Layer: Selector Tkinter finalizado. QTimer detenido.")

            # Mostrar la ventana principal de nuevo
            self.show()
            self.activateWindow() # Asegurarse de que la ventana principal tenga el foco

            # Verificar si hubo un error en el hilo del selector Tkinter
            if _tkinter_capture_error:
                 error_msg = f"Error durante la selección/captura: {_tkinter_capture_error}"
                 print(f"UI Layer Error: {error_msg}")
                 self.output_text_edit.setText(error_msg)
                 self.statusBar.showMessage(error_msg, 5000)
                 # Limpiar coordenadas globales después de usarlas
                 _tkinter_start_x = _tkinter_start_y = _tkinter_end_x = _tkinter_end_y = None
                 return # Salir si hubo error

            # Verificar si la selección fue válida (start_x NO es None)
            if _tkinter_start_x is None or _tkinter_end_x is None or _tkinter_start_y is None or _tkinter_end_y is None:
                 print("UI Layer: Selección de región cancelada o inválida.")
                 self.statusBar.showMessage("Selección de región cancelada o inválida.", 3000)
                 # Limpiar coordenadas globales después de usarlas
                 _tkinter_start_x = _tkinter_start_y = _tkinter_end_x = _tkinter_end_y = None
                 return # Salir si se canceló o fue inválida


            # Verificar que el archivo de captura existe.
            image_path = _tkinter_captured_image_path
            if not os.path.exists(image_path):
                 error_msg = f"Error: No se encontró el archivo de imagen capturada: {image_path}"
                 print(f"UI Layer Error: {error_msg}")
                 self.output_text_edit.setText(error_msg)
                 self.statusBar.showMessage(error_msg, 5000)
                 # Limpiar coordenadas globales después de usarlas
                 _tkinter_start_x = _tkinter_start_y = _tkinter_end_x = _tkinter_end_y = None
                 # Intentar limpiar el archivo si existe (aunque no debería si no se creó)
                 if os.path.exists(image_path):
                     try: os.remove(image_path)
                     except Exception as e: print(f"UI Layer Error: Failed to clean up {image_path}: {e}")
                 return # Salir si no se encontró el archivo


            # --- Procesar la captura ---
            # Las coordenadas (_tkinter_start_x, _tkinter_start_y, _tkinter_end_x, _tkinter_end_y)
            # son las coordenadas de píxeles físicos obtenidas del hilo Tkinter.
            # mss ya guardó la imagen en "captura_pil.png".


            # Obtener los idiomas seleccionados para la traducción
            source_language: Language = self.source_lang_combo.currentData()
            target_language: Language = self.target_lang_combo.currentData()

            if not source_language or not target_language:
                self.statusBar.showMessage("Por favor, selecciona idiomas de origen y destino.", 3000)
                # Limpiar coordenadas globales después de usarlas
                _tkinter_start_x = _tkinter_start_y = _tkinter_end_x = _tkinter_end_y = None
                # Opcional: Eliminar el archivo de captura si no se va a procesar
                if os.path.exists(image_path):
                    try: os.remove(image_path)
                    except Exception as e: print(f"UI Layer Error: Failed to clean up {image_path}: {e}")
                return


            # Indicar inicio de tarea de OCR y traducción
            self._translation_result_emitter.task_started.emit("Cargando imagen capturada, realizando OCR y Traduciendo...")

            pil_image = None
            try:
                # Cargar la imagen capturada desde el archivo temporal (_tkinter_captured_image_path)
                pil_image = Image.open(image_path)
                print(f"UI Layer: Imagen capturada cargada con PIL desde {image_path}.")

            except Exception as e:
                error_msg = f"Error al cargar la imagen capturada con PIL: {e}"
                print(f"UI Layer Error: {error_msg}")
                # Emitir error
                self._translation_result_emitter.error_occurred.emit(error_msg)
                # Asegurar que el estado de ocupado se desactive
                self._translation_result_emitter.task_finished.emit()
                # Limpiar coordenadas globales después de usarlas
                _tkinter_start_x = _tkinter_start_y = _tkinter_end_x = _tkinter_end_y = None
                # Asegurarse de eliminar el archivo si no se pudo cargar
                if os.path.exists(image_path):
                    try: os.remove(image_path)
                    except Exception as e: print(f"UI Layer Error: Failed to clean up {image_path}: {e}")
                return # Salir si no se pudo cargar la imagen


            # Limpiar coordenadas globales después de usarlas
            _tkinter_start_x = _tkinter_start_y = _tkinter_end_x = _tkinter_end_y = None

            # Llamar al servicio de aplicación para realizar OCR y traducción
            # Ejecutamos en un hilo estándar para no bloquear la UI
            self._start_translation_task( # Usamos el método genérico del hilo estándar
                self.translator_service.perform_ocr_and_translate,
                pil_image, # Pasamos el objeto PIL Image
                source_language.code,
                target_language.code,
                # Pasar la ruta del archivo temporal para limpieza en el hilo de traducción
                temp_file_path=image_path
            )


    # --- Función que se ejecutará en el hilo estándar (Tareas de Traducción/OCR) ---
    # Mantenemos esta función para manejar la limpieza del archivo temporal
    def _translation_task_function(self, func: Callable, *args, **kwargs):
        """
        Esta función se ejecuta en un hilo estándar.
        Llama a la función de traducción/OCR y emite señales al hilo principal.
        También maneja la limpieza del archivo temporal si se usó.
        """
        print(f"Standard Thread: _translation_task_function() iniciado. Llamando a {func.__name__}...")
        # Obtener la ruta del archivo temporal si existe (ahora puede ser "captura_pil.png")
        temp_file_path = kwargs.pop('temp_file_path', None)

        try:
            # Ejecutar la función (perform_translation o perform_ocr_and_translate)
            # Esperamos que la función retorne un TranslationResult
            translation_result: TranslationResult = func(*args, **kwargs)
            print("Standard Thread: La función de traducción/OCR ha regresado.")
            # Emitir el resultado al hilo principal usando la señal
            # Aseguramos que emitimos un TranslationResult válido
            if isinstance(translation_result, TranslationResult):
                 self._translation_result_emitter.translation_finished.emit(translation_result)
                 print("Standard Thread: Señal 'translation_finished' emitida.")
            else:
                 # Si la función no retornó un TranslationResult, emitimos un error
                 error_msg = f"La función {func.__name__} retornó un tipo inesperado: {type(translation_result).__name__}"
                 print(f"Standard Thread: {error_msg}")
                 self._translation_result_emitter.error_occurred.emit(error_msg)
                 print("Standard Thread: Señal 'error_occurred' emitida debido a tipo de retorno inesperado.")

        except Exception as e:
            # Capturar excepciones y emitir la señal de error al hilo principal
            print(f"Standard Thread: Error capturado: {e}")
            self._translation_result_emitter.error_occurred.emit(str(e))
            print("Standard Thread: Señal 'error_occurred' emitida.")
        finally:
             print("Standard Thread: _translation_task_function() finalizando.")
             # --- Limpieza del archivo temporal ---
             if temp_file_path and os.path.exists(temp_file_path):
                 try:
                     os.remove(temp_file_path)
                     print(f"Standard Thread: Archivo temporal eliminado: {temp_file_path}")
                 except Exception as cleanup_e:
                     print(f"Standard Thread Error: No se pudo eliminar el archivo temporal {temp_file_path}: {cleanup_e}")
             # --- Fin Limpieza ---
             # Indicar que la tarea ha terminado, independientemente del resultado
             self._translation_result_emitter.task_finished.emit()


    # --- Método genérico para iniciar tareas en el Hilo Estándar ---
    def _start_translation_task(self, func: Callable, *args, **kwargs):
        """
        Inicia una función dada (relacionada con traducción/OCR) en un hilo estándar.
        """
        # Si ya hay un hilo activo, no iniciar uno nuevo
        if self._current_translation_thread is not None and self._current_translation_thread.is_alive():
            print("UI Layer: Hilo de traducción ocupado. Espere a que termine la tarea actual.")
            self.statusBar.showMessage("Tarea anterior aún en proceso. Espere.", 3000)
            return

        print("UI Layer: Creando nuevo hilo estándar para tarea de traducción.")
        # Crear un nuevo hilo estándar
        # Pasamos la función _translation_task_function y sus argumentos
        self._current_translation_thread = threading.Thread(
            target=self._translation_task_function,
            args=(func, *args),
            kwargs=kwargs,
            daemon=True # Permite que el hilo se cierre automáticamente si la aplicación principal termina
        )

        # Iniciar el hilo
        self._current_translation_thread.start()
        print("UI Layer: Hilo estándar iniciado.")
        # La señal task_started se emite en los slots de los botones antes de llamar a este método


    # --- Slots para manejar resultados/errores del Hilo Estándar ---
    @Slot(TranslationResult)
    def _on_translation_task_finished(self, result: TranslationResult):
        """
        Slot que se ejecuta cuando se recibe la señal de traducción/OCR finalizada desde el hilo estándar.
        Muestra el resultado en el área de texto de salida.
        """
        print("UI Layer: Señal de traducción/OCR finalizada recibida desde hilo estándar.")
        # Ya verificamos que el resultado es TranslationResult en _translation_task_function
        if result.is_successful:
            self.output_text_edit.setText(result.translated_text)
            # El estado de "Listo" se establecerá en _on_translation_task_completed
        else:
            # Si hubo un error, el mensaje ya se estableció en _on_translation_task_error
            pass # No hacemos nada aquí si hubo error, el otro slot ya manejó la UI


        # Limpiar la referencia al hilo actual después de que la tarea termine
        self._current_translation_thread = None


    @Slot(str)
    def _on_translation_task_error(self, error_message: str):
        """
        Slot que se ejecuta cuando se recibe una señal de error desde el hilo estándar.
        Muestra el error en el área de texto de salida y la barra de estado.
        """
        print(f"UI Layer: Señal de error de tarea de traducción/OCR recibida desde hilo estándar: {error_message}")
        self.output_text_edit.setText(f"Error en tarea de traducción/OCR: {error_message}")
        # El estado de "Listo" con el mensaje de error se establecerá en _on_translation_task_completed
        # self.statusBar.showMessage(f"Error en tarea: {error_message}", 5000) # Ya se maneja en _on_translation_task_completed


        # Limpiar la referencia al hilo actual después de que la tarea termine
        self._current_translation_thread = None

    @Slot()
    def _on_translation_task_completed(self):
        """
        Slot que se ejecuta cuando se recibe la señal de fin de tarea desde el hilo estándar.
        Actualiza la UI para indicar que no hay tareas en curso y restaura el cursor.
        """
        print("UI Layer: Señal de fin de tarea recibida desde hilo estándar.")
        # Restaurar el estado de la UI a no ocupado
        # El mensaje de la barra de estado se establecerá a "Listo." por defecto
        # Si hubo un error, el mensaje ya se mostró en _on_translation_task_error
        # Si la tarea fue exitosa, el mensaje de "Completada" se mostró en _on_translation_task_finished
        # Si no hubo errores y la tarea fue exitosa, mostramos "Tarea completada."
        if self.output_text_edit.toPlainText().startswith("Error en tarea:"):
             # Si el texto de salida es un error, mantenemos ese mensaje en la barra de estado por un tiempo
             current_error_msg = self.output_text_edit.toPlainText()
             self._set_ui_busy_state(False, current_error_msg) # Mostrar el error en la barra de estado
        else:
             # Si no hubo error, la tarea fue exitosa
             self._set_ui_busy_state(False, "Tarea completada.")

        # Restaurar el cursor
        QApplication.restoreOverrideCursor()


    def closeEvent(self, event):
        """
        Maneja el evento de cierre de la ventana.
        Asegura que el listener de hotkeys y el hilo de traducción estándar se detengan limpiamente.
        """
        print("UI Layer: Evento de cierre de ventana detectado.")
        self.statusBar.showMessage("Cerrando aplicación...", 0)
        QApplication.processEvents()

        # Detener el listener de hotkeys (ya conectado a aboutToQuit en main.py)
        # self.translator_service.stop_hotkey_listening() # Ya está conectado en main.py
        print("Application Layer: Solicitando detener monitoreo de hotkeys.")

        # No necesitamos detener explícitamente el hilo estándar aquí si es daemon=True.
        # Se cerrará automáticamente cuando el hilo principal (UI) termine.
        # Si no fuera daemon, necesitaríamos un mecanismo para solicitarle que termine.
        if self._current_translation_thread is not None and self._current_translation_thread.is_alive():
             print("UI Layer: Hilo de traducción estándar aún activo (daemon). Se cerrará con la aplicación principal.")
             # Opcional: Intentar un join() con timeout si no fuera daemon o si queremos esperar
             # self._current_translation_thread.join(1.0) # Esperar 1 segundo

        print("UI Layer: Aceptando evento de cierre.")
        event.accept()
