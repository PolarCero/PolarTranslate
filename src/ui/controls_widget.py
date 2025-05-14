from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QPushButton
)
from PySide6.QtGui import QIcon


class ControlsWidget(QWidget):
    """
    Widget que contiene los controles principales de la aplicación.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Layout principal
        layout = QVBoxLayout(self)

        # --- Idiomas ---
        languages_layout = QHBoxLayout()
        self.source_lang_combo = QComboBox()
        self.target_lang_combo = QComboBox()

        languages_layout.addWidget(QLabel("Source:"))
        languages_layout.addWidget(self.source_lang_combo)
        languages_layout.addWidget(QLabel("Target:"))
        languages_layout.addWidget(self.target_lang_combo)

        layout.addLayout(languages_layout)

        # --- Botones principales ---
        buttons_layout = QHBoxLayout()

        # Botón de traducción
        self.translate_button = QPushButton("Translate")
        buttons_layout.addWidget(self.translate_button)

        # Botón de configuración (con icono de tuerca)
        self.settings_button = QPushButton()
        self.settings_button.setIcon(QIcon("icons/settings.png"))
        self.settings_button.setToolTip("Settings")
        buttons_layout.addWidget(self.settings_button)

        layout.addLayout(buttons_layout)