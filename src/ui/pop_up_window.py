# src/ui/pop_up_window.py

from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QApplication
from PySide6.QtCore import Qt, QTimer, QPoint # Importamos QPoint
from PySide6.QtGui import QGuiApplication # Importamos QGuiApplication para obtener el cursor

class PopUpTranslationWindow(QMainWindow):
    """
    Ventana pop-up para mostrar el resultado de la traducción de portapapeles.
    Aparece cerca del cursor del ratón y se cierra automáticamente.
    """
    def __init__(self, translated_text: str, parent: QWidget = None):
        super().__init__(parent)

        # Configurar la ventana
        # Usar self.tr() para el título de la ventana
        self.setWindowTitle(self.tr("Translated Text"))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool) # Sin bordes, siempre encima, no aparece en la barra de tareas
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose) # Asegurar que se elimine al cerrar

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Etiqueta para mostrar el texto traducido
        self.translation_label = QLabel(translated_text)
        self.translation_label.setWordWrap(True) # Permite que el texto se ajuste automáticamente
        self.translation_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop) # Alineación
        # Opcional: Añadir un poco de padding
        self.translation_label.setStyleSheet("padding: 5px;")
        layout.addWidget(self.translation_label)

        # Botón para cerrar manualmente (opcional, ya que se cierra automáticamente)
        # self.close_button = QPushButton("Cerrar")
        # self.close_button.clicked.connect(self.close)
        # layout.addWidget(self.close_button)

        self.adjustSize() # Ajustar el tamaño de la ventana al contenido

        # Posicionar la ventana cerca del cursor del ratón
        cursor_pos = QGuiApplication.cursor().pos()
        # Intentar posicionar debajo y a la derecha del cursor
        # Ajustar según el tamaño de la ventana para que no quede fuera de pantalla
        screen = QGuiApplication.screenAt(cursor_pos)
        if screen:
            screen_geometry = screen.geometry()
            # Calcular la posición X: si la ventana se sale por la derecha, ajustarla a la izquierda del cursor
            x = cursor_pos.x()
            if x + self.width() > screen_geometry.right():
                x = cursor_pos.x() - self.width()
            # Calcular la posición Y: si la ventana se sale por abajo, ajustarla encima del cursor
            y = cursor_pos.y()
            if y + self.height() > screen_geometry.bottom():
                y = cursor_pos.y() - self.height()
            # Asegurarse de que no se salga por la izquierda o arriba (si el cursor está cerca del borde)
            x = max(screen_geometry.left(), x)
            y = max(screen_geometry.top(), y)

            self.move(x, y)
        else:
            # Si no se pudo obtener la pantalla, simplemente centrarla o usar una posición por defecto
            self.move(cursor_pos + QPoint(20, 20)) # Posición por defecto relativa al cursor


        # Configurar un temporizador para cerrar la ventana automáticamente después de unos segundos
        # Usar self.tr() para el mensaje en la barra de estado (si tuvieras una) o para un tooltip (opcional)
        self._close_timer = QTimer(self)
        self._close_timer.singleShot(7000, self.close) # Cerrar después de 7 segundos (7000 ms)


    # Opcional: Permitir cerrar haciendo clic en la ventana
    def mousePressEvent(self, event):
        # Usar self.tr() si se añade algún mensaje aquí
        # print(self.tr("Window clicked, closing."))
        self.close()
