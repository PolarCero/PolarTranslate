# src/ui/pop_up_window.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QApplication
from PySide6.QtCore import Qt, QTimer # Importamos QTimer para auto-cerrar
from PySide6.QtGui import QGuiApplication # Importamos QGuiApplication para acceder al portapapeles

class PopUpTranslationWindow(QDialog):
    """
    Ventana pop-up para mostrar el resultado de la traducción por hotkey.
    """
    def __init__(self, translated_text: str, parent=None):
        """
        Constructor de la ventana pop-up.

        Args:
            translated_text: El texto traducido a mostrar.
            parent: El widget padre (opcional).
        """
        super().__init__(parent)

        self.setWindowTitle("Polar Translate Result")
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
        self.copy_button = QPushButton("Copiar al Portapapeles")
        main_layout.addWidget(self.copy_button)

        # Conectar señal del botón a un slot
        self.copy_button.clicked.connect(self.copy_to_clipboard)

        # Opcional: Auto-cerrar la ventana después de un tiempo
        # self.timer = QTimer(self)
        # self.timer.timeout.connect(self.close)
        # self.timer.start(5000) # Cerrar después de 5 segundos

        # Posicionar la ventana cerca del cursor del ratón (opcional, requiere lógica adicional)
        # current_cursor_pos = QGuiApplication.primaryScreen().cursor().pos()
        # self.move(current_cursor_pos)


    def copy_to_clipboard(self):
        """
        Copia el texto del área de resultado al portapapeles.
        """
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.result_text_edit.toPlainText())
        print("UI Layer (PopUp): Texto copiado al portapapeles.")
        # Podríamos añadir una pequeña indicación visual de que se copió

    # Si implementas auto-cerrar, también podrías querer detener el timer si el usuario interactúa
    # def mousePressEvent(self, event):
    #     self.timer.stop()
    #     super().mousePressEvent(event)

    # def keyPressEvent(self, event):
    #     self.timer.stop()
    #     super().keyPressEvent(event)

