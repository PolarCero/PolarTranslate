# src/ui/pop_up_window.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QApplication
# Importamos QTimer para auto-cerrar y QPoint para posicionar
from PySide6.QtCore import Qt, QTimer, QPoint
# Importamos QGuiApplication para acceder a la pantalla y QCursor para acceder al cursor
from PySide6.QtGui import QGuiApplication, QCursor # Importamos QCursor

class PopUpTranslationWindow(QDialog):
    """
    Ventana pop-up para mostrar el resultado de la traducción por hotkey.
    Será independiente de la ventana principal y siempre visible.
    """
    # Eliminamos el parámetro parent=None del constructor para que sea independiente
    def __init__(self, translated_text: str):
        """
        Constructor de la ventana pop-up.

        Args:
            translated_text: El texto traducido a mostrar.
            # Ya no necesitamos el parámetro parent aquí
        """
        # No pasamos parent a super() para hacerla independiente
        super().__init__()

        # Configuramos la ventana
        self.setWindowTitle("Polar Translate Result")
        # Añadimos las banderas para hacerla independiente, siempre visible y sin bordes
        self.setWindowFlags(
            Qt.WindowType.Window
        )

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose) # Aseguramos que se elimine al cerrarse

        # Establecemos el tamaño inicial y políticas de tamaño
        self.resize(400, 150) # Tamaño inicial
        self.setSizeGripEnabled(True) # Permite redimensionar con un "agarre" en la esquina

        # Layout principal
        main_layout = QVBoxLayout(self)

        # Área de texto para mostrar el resultado
        self.result_text_edit = QTextEdit()
        self.result_text_edit.setReadOnly(True) # Solo lectura
        self.result_text_edit.setText(translated_text)
        # Ajustar el tamaño del texto automáticamente si es necesario (opcional)
        # self.result_text_edit.setWordWrapMode(QTextOption.WordWrap) # Asegura que el texto se envuelva
        main_layout.addWidget(self.result_text_edit)

        # Botón para copiar al portapapeles
        self.copy_button = QPushButton("Copy to clipboard")
        main_layout.addWidget(self.copy_button)
        # Conectar señal del botón a un slot
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        
        # Estado de fijación
        self.is_pinned = False

        self.pin_button = QPushButton("Unpin")
        main_layout.addWidget(self.pin_button)
        self.pin_button.clicked.connect(self.toggle_pin)  # Usamos nueva función toggle_pin

        self.toggle_pin()

        #self.close_button = QPushButton("Cerrar")
        #main_layout.addWidget(self.close_button)
        #self.close_button.clicked.connect(self.close)

        # --- Auto-cerrar la ventana después de un tiempo ---
        #self.timer = QTimer(self)
        #self.timer.timeout.connect(self.close)
        #self.timer.start(7000) # Cerrar después de 7 segundos (7000 ms)
        # --- Fin Auto-cerrar ---

        # --- Posicionar la ventana cerca del cursor del ratón ---
        # Obtenemos la posición actual del cursor usando QCursor.pos()
        current_cursor_pos = QCursor.pos()
        # Obtenemos la pantalla donde se encuentra el cursor
        screen = QGuiApplication.screenAt(current_cursor_pos)

        if screen:
            screen_geometry = screen.geometry()
            # Calcular la posición X: si la ventana se sale por la derecha, ajustarla a la izquierda del cursor
            x = current_cursor_pos.x()
            if x + self.width() > screen_geometry.right():
                x = current_cursor_pos.x() - self.width()
            # Calcular la posición Y: si la ventana se sale por abajo, ajustarla encima del cursor
            y = current_cursor_pos.y()
            if y + self.height() > screen_geometry.bottom():
                y = current_cursor_pos.y() - self.height()
            # Asegurarse de que no se salga por la izquierda o arriba (si el cursor está cerca del borde)
            x = max(screen_geometry.left(), x)
            y = max(screen_geometry.top(), y)

            self.move(x, y)
        else:
            # Si no se pudo obtener la pantalla (caso raro), simplemente la centramos o usamos una posición por defecto
            self.move(current_cursor_pos + QPoint(20, 20)) # Posición por defecto relativa al cursor
        # --- Fin Posicionar ---


    def copy_to_clipboard(self):
        """
        Copia el texto del área de resultado al portapapeles.
        """
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.result_text_edit.toPlainText())
        print("UI Layer (PopUp): Texto copiado al portapapeles.")
        # Podríamos añadir una pequeña indicación visual de que se copió

    # Si implementas auto-cerrar, también podrías querer detener el timer si el usuario interactúa
    def mousePressEvent(self, event):
        # Detener el timer si el usuario hace clic en la ventana
        #self.timer.stop()
        # Llamar al método base para que el evento se propague (si es necesario)
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        # Detener el timer si el usuario presiona una tecla en la ventana
        #self.timer.stop()
        # Llamar al método base
        super().keyPressEvent(event)

    def set_always_on_top(self, always_on_top: bool):
        # Siempre partimos de Qt.Window, para que la ventana tenga su marco y botón de cerrar
        base_flags = Qt.Window
        # flags = Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint
        if always_on_top:
            base_flags |= Qt.WindowStaysOnTopHint

        self.setWindowFlags(base_flags)
        self.show()

    def toggle_pin(self):
        """
        Alterna el estado de 'siempre visible' de la ventana.
        """
        self.is_pinned = not self.is_pinned  # Cambiar el estado
        self.set_always_on_top(self.is_pinned)  # Aplicar estado
        self.pin_button.setText("Unpin" if self.is_pinned else "Pin")  # Cambiar texto del botón
