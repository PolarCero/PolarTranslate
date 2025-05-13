# src/ui/config_window.py

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QStackedWidget, QLabel, QPushButton,
    QMessageBox, QListWidgetItem, QSizePolicy, QAbstractItemView,
    QApplication
)
from PySide6.QtCore import Qt, Signal, Slot, QObject, QThread, QTimer
import threading
from typing import List, Any, Callable, Optional
import os
import shutil

from src.application.translator_service import TranslatorService

import argostranslate.package
import argostranslate.translate


class PackageOperationEmitter(QObject):
    """Emite señales para comunicar resultados de operaciones de paquetes al hilo principal de la UI."""
    installed_packages_loaded = Signal(list)
    available_packages_loaded = Signal(list, list)
    operation_finished = Signal(bool, str)
    operation_started = Signal(str)
    operation_completed = Signal()
    # progress_updated = Signal(int)


class LanguagesConfigSection(QWidget):
    """Widget para la sección de configuración de Idiomas/Paquetes."""
    def __init__(self, translator_service: TranslatorService, parent: QWidget = None):
        super().__init__(parent)
        self.translator_service = translator_service
        self.layout = QVBoxLayout(self)

        # Usar self.tr() para el título de la sección
        title_label = QLabel(self.tr("<h2>Language and Package Configuration</h2>"))
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(title_label)

        # --- Sección de Idiomas Instalados ---
        installed_layout = QVBoxLayout()
        # Usar self.tr() para el subtítulo
        installed_layout.addWidget(QLabel(self.tr("<h3>Installed Packages</h3>")))
        self.installed_languages_list = QListWidget()
        self.installed_languages_list.setSelectionMode(QAbstractItemView.SingleSelection)
        installed_layout.addWidget(self.installed_languages_list)

        # Usar self.tr() para el texto del botón
        self.uninstall_button = QPushButton(self.tr("Uninstall Selected"))
        self.uninstall_button.setEnabled(False)
        installed_layout.addWidget(self.uninstall_button)

        # --- Sección de Paquetes Disponibles ---
        available_layout = QVBoxLayout()
        # Usar self.tr() para el subtítulo
        available_layout.addWidget(QLabel(self.tr("<h3>Available Packages for Installation</h3>")))
        self.available_packages_list = QListWidget()
        self.available_packages_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        available_layout.addWidget(self.available_packages_list)

        # Usar self.tr() para el texto del botón
        self.install_button = QPushButton(self.tr("Install Selected"))
        self.install_button.setEnabled(False)
        available_layout.addWidget(self.install_button)

        # Usar self.tr() para el texto del botón
        self.refresh_button = QPushButton(self.tr("Update Package List"))
        available_layout.addWidget(self.refresh_button)

        content_layout = QHBoxLayout()
        content_layout.addLayout(installed_layout)
        content_layout.addLayout(available_layout)

        self.layout.addLayout(content_layout)
        self.layout.addStretch()

        self._package_operation_emitter = PackageOperationEmitter()
        self._package_operation_emitter.installed_packages_loaded.connect(self._on_installed_packages_loaded)
        self._package_operation_emitter.available_packages_loaded.connect(self._on_available_packages_loaded)
        self._package_operation_emitter.operation_finished.connect(self._on_operation_finished)
        self._package_operation_emitter.operation_started.connect(self._on_operation_started)
        self._package_operation_emitter.operation_completed.connect(self._on_operation_completed)

        self.refresh_button.clicked.connect(self._on_refresh_button_clicked)
        self.install_button.clicked.connect(self.on_install_button_clicked) # Corregido: conectar a on_install_button_clicked
        self.uninstall_button.clicked.connect(self.on_uninstall_button_clicked) # Corregido: conectar a on_uninstall_button_clicked
        self.installed_languages_list.itemSelectionChanged.connect(self._on_installed_selection_changed)
        self.available_packages_list.itemSelectionChanged.connect(self._on_available_selection_changed)

        self._current_package_thread: Optional[threading.Thread] = None
        self._installed_packages: List[argostranslate.package.Package] = []
        self._available_packages: List[argostranslate.package.AvailablePackage] = []

        self._load_installed_packages()
        self._load_available_packages()

        print("UI Layer (LanguagesConfigSection): Inicializada.")

    def _set_ui_busy_state(self, is_busy: bool, message: str = ""):
        """
        Establece el estado de ocupado de los botones de la sección de idiomas.
        """
        self.refresh_button.setEnabled(not is_busy)
        self.install_button.setEnabled(not is_busy and len(self.available_packages_list.selectedItems()) > 0)
        self.uninstall_button.setEnabled(not is_busy and len(self.installed_languages_list.selectedItems()) == 1) # Habilitar solo si 1 seleccionado

        if is_busy:
            print(f"UI Layer (LanguagesConfigSection): Tarea en curso: {message}")
        else:
            # Usar self.tr() para el mensaje por defecto
            print(f"UI Layer (LanguagesConfigSection): {self.tr('Ready.')} {message}")


    # --- Funciones que se ejecutarán en el hilo estándar ---

    def _load_installed_packages_task(self):
        """Tarea para cargar paquetes instalados en un hilo separado."""
        print("Standard Thread (Packages): _load_installed_packages_task() iniciado.")
        try:
            installed_packages = argostranslate.package.get_installed_packages()
            print(f"Standard Thread (Packages): Cargados {len(installed_packages)} paquetes instalados.")
            self._package_operation_emitter.installed_packages_loaded.emit(installed_packages)
        except Exception as e:
            # Usar self.tr() para el mensaje de error
            error_msg = self.tr("Error loading installed packages: %s") % e
            print(f"Standard Thread (Packages) Error: {error_msg}")
            self._package_operation_emitter.operation_finished.emit(False, error_msg)
        finally:
            pass


    def _load_available_packages_task(self):
        """Tarea para cargar paquetes disponibles en un hilo separado."""
        print("Standard Thread (Packages): _load_available_packages_task() iniciado.")
        try:
            print("Standard Thread (Packages): Actualizando índice de paquetes remotos...")
            argostranslate.package.update_package_index()
            print("Standard Thread (Packages): Índice remoto actualizado.")

            print("Standard Thread (Packages): Obteniendo paquetes disponibles...")
            available_packages = argostranslate.package.get_available_packages()
            print(f"Standard Thread (Packages): Obtenidos {len(available_packages)} paquetes disponibles.")

            installed_packages = argostranslate.package.get_installed_packages()
            print(f"Standard Thread (Packages): Obtenidos {len(installed_packages)} paquetes instalados para comparación.")

            self._package_operation_emitter.available_packages_loaded.emit(available_packages, installed_packages)

        except Exception as e:
            # Usar self.tr() para el mensaje de error
            error_msg = self.tr("Error loading available packages: %s") % e
            print(f"Standard Thread (Packages) Error: {error_msg}")
            self._package_operation_emitter.operation_finished.emit(False, error_msg)
        finally:
            pass


    def _install_package_task(self, package_to_install: argostranslate.package.AvailablePackage):
        """Tarea para instalar un paquete en un hilo separado."""
        print(f"Standard Thread (Packages): _install_package_task() iniciado para {package_to_install.from_code} -> {package_to_install.to_code}.")
        try:
            print(f"Standard Thread (Packages): Descargando {package_to_install.from_code} -> {package_to_install.to_code}...")
            download_path = package_to_install.download()
            print(f"Standard Thread (Packages): Descarga completa. Instalando desde {download_path}...")

            argostranslate.package.install_from_path(download_path)
            print(f"Standard Thread (Packages): Instalación completa para {package_to_install.from_code} -> {package_to_install.to_code}.")

            if os.path.exists(download_path):
                 try:
                     os.remove(download_path)
                     print(f"Standard Thread (Packages): Archivo descargado temporal eliminado: {download_path}")
                 except Exception as cleanup_e:
                     print(f"Standard Thread (Packages) Error: No se pudo eliminar el archivo descargado temporal {download_path}: {cleanup_e}")

            self._load_installed_packages_task()
            self._load_available_packages_task()

            # Usar self.tr() para el mensaje de éxito
            self._package_operation_emitter.operation_finished.emit(True, self.tr("Package %s -> %s installed successfully.") % (package_to_install.from_code, package_to_install.to_code))

        except Exception as e:
            # Usar self.tr() para el mensaje de error
            error_msg = self.tr("Error installing package %s -> %s: %s") % (package_to_install.from_code, package_to_install.to_code, e)
            print(f"Standard Thread (Packages) Error: {error_msg}")
            self._package_operation_emitter.operation_finished.emit(False, error_msg)
        finally:
            pass


    def _uninstall_package_task(self, package_to_uninstall: argostranslate.package.Package):
        """
        Tarea para desinstalar un paquete buscando su directorio por códigos de idioma.
        """
        print(f"Standard Thread (Packages): _uninstall_package_task() iniciado para {package_to_uninstall.from_code} -> {package_to_uninstall.to_code}.")
        try:
            home_dir = os.path.expanduser("~")
            packages_dir = os.path.join(home_dir, ".local", "share", "argos-translate", "packages")

            print(f"Standard Thread (Packages): Buscando directorio del paquete en: {packages_dir}")

            from_code = package_to_uninstall.from_code
            to_code = package_to_uninstall.to_code

            package_path_to_remove = None

            if os.path.exists(packages_dir):
                for item_name in os.listdir(packages_dir):
                    item_path = os.path.join(packages_dir, item_name)
                    if os.path.isdir(item_path):
                        item_name_lower = item_name.lower()
                        from_to_lower = f"{from_code}_{to_code}".lower()
                        translate_from_to_lower = f"translate-{from_code}_{to_code}-".lower()

                        if from_to_lower in item_name_lower or item_name_lower.startswith(translate_from_to_lower):
                             package_path_to_remove = item_path
                             print(f"Standard Thread (Packages): Directorio encontrado: {package_path_to_remove}")
                             break

            if package_path_to_remove and os.path.exists(package_path_to_remove):
                print(f"Standard Thread (Packages): Eliminando directorio: {package_path_to_remove}")
                shutil.rmtree(package_path_to_remove)
                print("Standard Thread (Packages): Directorio del paquete eliminado correctamente.")

                self._load_installed_packages_task()
                self._load_available_packages_task()

                # Usar self.tr() para el mensaje de éxito
                self._package_operation_emitter.operation_finished.emit(True, self.tr("Package %s -> %s uninstalled successfully.") % (package_to_uninstall.from_code, package_to_uninstall.to_code))
            else:
                # Usar self.tr() para el mensaje de error
                error_msg = self.tr("Error uninstalling package %s -> %s: Could not find package directory at expected path (%s) with codes '%s_%s'.") % (package_to_uninstall.from_code, package_to_uninstall.to_code, packages_dir, from_code, to_code)
                print(f"Standard Thread (Packages) Error: {error_msg}")
                self._package_operation_emitter.operation_finished.emit(False, error_msg)

        except Exception as e:
            # Usar self.tr() para el mensaje de error
            error_msg = self.tr("Unexpected error uninstalling package %s -> %s: %s") % (package_to_uninstall.from_code, package_to_uninstall.to_code, e)
            print(f"Standard Thread (Packages) Error: {error_msg}")
            self._package_operation_emitter.operation_finished.emit(False, error_msg)
        finally:
            pass


    # --- Método genérico para iniciar tareas en el Hilo Estándar ---
    def _start_package_task(self, func: Callable, *args, message: str, **kwargs):
        """
        Inicia una función dada (relacionada con operaciones de paquetes) en un hilo estándar.
        """
        if self._current_package_thread is not None and self._current_package_thread.is_alive():
            # Usar self.tr() para el mensaje
            print("UI Layer (LanguagesConfigSection): Hilo de paquetes ocupado. Espere a que termine la tarea actual.")
            return

        print(f"UI Layer (LanguagesConfigSection): Creando nuevo hilo estándar para tarea: {message}")
        self._package_operation_emitter.operation_started.emit(message)

        def task_wrapper():
            try:
                func(*args, **kwargs)
            finally:
                self._package_operation_emitter.operation_completed.emit()
                print("Standard Thread (Packages): Señal 'operation_completed' emitida.")

        self._current_package_thread = threading.Thread(
            target=task_wrapper,
            daemon=True
        )

        self._current_package_thread.start()
        print("UI Layer (LanguagesConfigSection): Hilo estándar iniciado.")


    # --- Slots para manejar resultados/errores del Hilo Estándar ---

    @Slot(list)
    def _on_installed_packages_loaded(self, packages: List[argostranslate.package.Package]):
        """Slot para actualizar la lista de paquetes instalados en la UI."""
        print(f"UI Layer (LanguagesConfigSection): Señal installed_packages_loaded recibida con {len(packages)} paquetes.")
        self._installed_packages = packages
        self.installed_languages_list.clear()
        for pkg in packages:
            item = QListWidgetItem(f"{pkg.from_code} -> {pkg.to_code}")
            item.setData(Qt.UserRole, pkg)
            self.installed_languages_list.addItem(item)

        self.uninstall_button.setEnabled(False)


    @Slot(list, list)
    def _on_available_packages_loaded(self, available_packages: List[argostranslate.package.AvailablePackage], installed_packages: List[argostranslate.package.Package]):
        """Slot para actualizar la lista de paquetes disponibles en la UI."""
        print(f"UI Layer (LanguagesConfigSection): Señal available_packages_loaded recibida con {len(available_packages)} disponibles y {len(installed_packages)} instalados.")
        self._available_packages = available_packages

        installed_package_ids = {f"{pkg.from_code}->{pkg.to_code}" for pkg in installed_packages}

        self.available_packages_list.clear()
        for pkg in available_packages:
            item_text = f"{pkg.from_code} -> {pkg.to_code}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, pkg)

            if f"{pkg.from_code}->{pkg.to_code}" in installed_package_ids:
                 # Usar self.tr() para el texto "(Instalado)"
                 item.setText(f"{item_text} ({self.tr('Installed')})")
                 item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.available_packages_list.addItem(item)

        self.install_button.setEnabled(False)


    @Slot(bool, str)
    def _on_operation_finished(self, success: bool, message: str):
        """Slot para mostrar el resultado de una operación (instalación, etc.) y preguntar por reinicio."""
        print(f"UI Layer (LanguagesConfigSection): Señal operation_finished recibida. Éxito: {success}, Mensaje: {message}")

        if success:
            # Usar self.tr() para el título del MessageBox
            QMessageBox.information(self, self.tr("Operation Completed"), message)

            # --- Añadir la lógica de reinicio opcional aquí ---
            # Modificado el texto del mensaje según la sugerencia del usuario
            # Usar self.tr() para el título y el texto del MessageBox
            reply = QMessageBox.question(self, self.tr('Closing Application Required'),
                                         self.tr('Language package changes require the application to be reopened to take effect.\n\nClose Now?'),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                print("UI Layer (LanguagesConfigSection): Usuario eligió cerrar. Cerrando aplicación...")
                QApplication.quit()

        else:
            # Usar self.tr() para el título del MessageBox
            QMessageBox.warning(self, self.tr("Operation Error"), message)


    @Slot(str)
    def _on_operation_started(self, message: str):
        """Slot para indicar el inicio de una operación."""
        print(f"UI Layer (LanguagesConfigSection): Señal operation_started recibida: {message}")
        self._set_ui_busy_state(True, message)


    @Slot()
    def _on_operation_completed(self):
        """Slot para indicar la finalización de una operación."""
        print("UI Layer (LanguagesConfigSection): Señal operation_completed recibida.")
        # Usar self.tr() para el mensaje por defecto
        self._set_ui_busy_state(False, self.tr("Ready."))
        self._current_package_thread = None


    # --- Slots para acciones de botones ---

    @Slot()
    def _on_refresh_button_clicked(self):
        """Slot para el botón 'Actualizar Lista de Paquetes'."""
        print("UI Layer (LanguagesConfigSection): 'Actualizar Lista de Paquetes' clicked.")
        # Usar self.tr() para el mensaje
        self._start_package_task(
            self._load_available_packages_task,
            message=self.tr("Updating available package list...")
        )

    @Slot()
    def on_install_button_clicked(self): # Corregido: nombre del slot
        """Slot para el botón 'Instalar Seleccionados'."""
        print("UI Layer (LanguagesConfigSection): 'Instalar Seleccionados' clicked.")
        selected_items = self.available_packages_list.selectedItems()
        if not selected_items:
            # Usar self.tr() para el título y mensaje
            QMessageBox.information(self, self.tr("Nothing Selected"), self.tr("Please select at least one package to install."))
            return

        packages_to_install: List[argostranslate.package.AvailablePackage] = [item.data(Qt.UserRole) for item in selected_items]

        if packages_to_install:
            def install_multiple_task(packages: List[argostranslate.package.AvailablePackage]):
                 print(f"Standard Thread (Packages): Iniciando instalación secuencial de {len(packages)} paquete(s).")
                 success_count = 0
                 error_messages = []
                 for i, pkg in enumerate(packages):
                     try:
                         print(f"Standard Thread (Packages): Instalando paquete {i+1}/{len(packages)}: {pkg.from_code} -> {pkg.to_code}")
                         download_path = pkg.download()
                         argostranslate.package.install_from_path(download_path)
                         if os.path.exists(download_path):
                             try: os.remove(download_path)
                             except Exception as cleanup_e: print(f"Standard Thread (Packages) Error: No se pudo eliminar el archivo descargado temporal {download_path}: {cleanup_e}")

                         success_count += 1
                         print(f"Standard Thread (Packages): Paquete {pkg.from_code} -> {pkg.to_code} instalado correctamente.")

                     except Exception as e:
                         error_msg = f"Error al instalar paquete {pkg.from_code} -> {pkg.to_code}: {e}"
                         print(f"Standard Thread (Packages) Error: {error_msg}")
                         error_messages.append(error_msg)

                 try:
                     print("Standard Thread (Packages): Recargando listas después de instalación secuencial.")
                     installed_packages = argostranslate.package.get_installed_packages()
                     self._package_operation_emitter.installed_packages_loaded.emit(installed_packages)

                     argostranslate.package.load_available_packages()
                     available_packages = argostranslate.package.get_available_packages()
                     self._package_operation_emitter.available_packages_loaded.emit(available_packages, installed_packages)

                 except Exception as e:
                      error_messages.append(f"Error al recargar listas después de instalación: {e}")
                      print(f"Standard Thread (Packages) Error: Error al recargar listas: {e}")

                 if not error_messages:
                     # Usar self.tr() para el mensaje de éxito
                     final_message = self.tr("Successfully installed %n package(s).", "", success_count) % success_count # Uso de %n para pluralización
                     self._package_operation_emitter.operation_finished.emit(True, final_message)
                 else:
                     # Usar self.tr() para el mensaje de error
                     final_message = self.tr("Installed %n package(s) with errors in %m: \n%s", "", success_count).arg(len(error_messages)).arg("\n".join(error_messages)) % success_count # Uso de %n y %m
                     self._package_operation_emitter.operation_finished.emit(False, final_message)

            # Usar self.tr() para el mensaje
            self._start_package_task(
                install_multiple_task,
                packages_to_install,
                message=self.tr("Installing %n package(s)...", "", len(packages_to_install)) % len(packages_to_install)
            )


    @Slot()
    def on_uninstall_button_clicked(self): # Corregido: nombre del slot
        """Slot para el botón 'Desinstalar Seleccionado'."""
        print("UI Layer (LanguagesConfigSection): 'Desinstalar Seleccionado' clicked.")
        selected_item = self.installed_languages_list.selectedItems()
        if not selected_item:
            # Usar self.tr() para el título y mensaje
            QMessageBox.information(self, self.tr("Nothing Selected"), self.tr("Please select a package to uninstall."))
            return

        package_to_uninstall: argostranslate.package.Package = selected_item[0].data(Qt.UserRole)

        # Usar self.tr() para el título y mensaje de confirmación
        reply = QMessageBox.question(self, self.tr('Confirm Uninstall'),
                                     self.tr('Are you sure you want to uninstall the %s -> %s translation package?') % (package_to_uninstall.from_code, package_to_uninstall.to_code),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Usar self.tr() para el mensaje
            self._package_operation_emitter.operation_started.emit(self.tr("Uninstalling package %s -> %s...") % (package_to_uninstall.from_code, package_to_uninstall.to_code))

            self._start_package_task(
                self._uninstall_package_task,
                package_to_uninstall,
                message=self.tr("Uninstalling package %s -> %s...") % (package_to_uninstall.from_code, package_to_uninstall.to_code)
            )


    # --- Slots para manejar la selección en las listas ---

    @Slot()
    def _on_installed_selection_changed(self):
        """Slot que se ejecuta cuando cambia la selección en la lista de instalados."""
        print("UI Layer (LanguagesConfigSection): Selección en lista de instalados cambiada.")
        is_busy = self._current_package_thread is not None and self._current_package_thread.is_alive()
        self.uninstall_button.setEnabled(len(self.installed_languages_list.selectedItems()) == 1 and not is_busy)


    @Slot()
    def _on_available_selection_changed(self):
        """Slot que se ejecuta cuando cambia la selección en la lista de disponibles."""
        print("UI Layer (LanguagesConfigSection): Selección en lista de disponibles cambiada.")
        is_busy = self._current_package_thread is not None and self._current_package_thread.is_alive()
        self.install_button.setEnabled(len(self.available_packages_list.selectedItems()) > 0 and not is_busy)


    # --- Métodos para cargar las listas (llamados al iniciar la sección) ---

    def _load_installed_packages(self):
        """Carga la lista de paquetes instalados al iniciar la sección."""
        print("UI Layer (LanguagesConfigSection): Cargando paquetes instalados...")
        # Usar self.tr() para el mensaje
        self._start_package_task(
            self._load_installed_packages_task,
            message=self.tr("Loading installed packages...")
        )

    def _load_available_packages(self):
        """Carga la lista de paquetes disponibles al iniciar la sección."""
        print("UI Layer (LanguagesConfigSection): Cargando paquetes disponibles...")
        # Usar self.tr() para el mensaje
        self._start_package_task(
            self._load_available_packages_task,
            message=self.tr("Loading available packages...")
        )


class HotkeyConfigSection(QWidget):
    """Widget para la sección de configuración de Hotkeys."""
    def __init__(self, translator_service: TranslatorService, parent: QWidget = None):
        super().__init__(parent)
        self.translator_service = translator_service
        self.layout = QVBoxLayout(self)

        # Usar self.tr() para el título de la sección
        title_label = QLabel(self.tr("<h2>Hotkey Configuration</h2>"))
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(title_label)

        # Usar self.tr() para el placeholder
        placeholder_label = QLabel(self.tr("Hotkey configuration content (coming soon)"))
        placeholder_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(placeholder_label)

        self.layout.addStretch()


class TTSConfigSection(QWidget):
    """Widget para la sección de configuración de Text-to-Speech."""
    def __init__(self, translator_service: TranslatorService, parent: QWidget = None):
        super().__init__(parent)
        self.translator_service = translator_service
        self.layout = QVBoxLayout(self)

        # Usar self.tr() para el título de la sección
        title_label = QLabel(self.tr("<h2>Text-to-Speech Configuration</h2>"))
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(title_label)

        # Usar self.tr() para el placeholder
        placeholder_label = QLabel(self.tr("Text-to-Speech configuration content (coming soon)"))
        placeholder_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(placeholder_label)

        self.layout.addStretch()


class ConfigWindow(QMainWindow):
    """
    Ventana dedicada para la configuración de la aplicación (idiomas, hotkeys, TTS, etc.).
    """
    def __init__(self, translator_service: TranslatorService, parent: QWidget = None):
        """
        Constructor de la ventana de configuración.

        Args:
            translator_service: Instancia del servicio de aplicación para interactuar con la lógica.
            parent: Widget padre (opcional).
        """
        super().__init__(parent)
        self.translator_service = translator_service

        # Usar self.tr() para el título de la ventana
        self.setWindowTitle(self.tr("Polar Translate - Configuration"))
        self.setGeometry(200, 200, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        self.section_list_widget = QListWidget()
        self.section_list_widget.setFixedWidth(180)
        main_layout.addWidget(self.section_list_widget)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.languages_section = LanguagesConfigSection(self.translator_service)
        self.hotkey_section = HotkeyConfigSection(self.translator_service)
        self.tts_section = TTSConfigSection(self.translator_service)

        # Usar self.tr() para los nombres de las secciones en la lista
        self._add_section(self.tr("Languages and Packages"), self.languages_section)
        self._add_section(self.tr("Hotkeys"), self.hotkey_section)
        self._add_section(self.tr("Text-to-Speech"), self.tts_section)

        self.section_list_widget.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)
        self.section_list_widget.setCurrentRow(0)

        print("UI Layer (ConfigWindow): Ventana de Configuración inicializada.")


    def _add_section(self, name: str, widget: QWidget):
        """
        Añade una sección a la lista lateral y al stacked widget.
        """
        index = self.stacked_widget.addWidget(widget)
        item = QListWidgetItem(name)
        self.section_list_widget.addItem(item)
        print(f"UI Layer (ConfigWindow): Sección '{name}' añadida con índice {index}.")


    def closeEvent(self, event):
        """
        Maneja el evento de cierre de la ventana de configuración.
        """
        print("UI Layer (ConfigWindow): Evento de cierre detectado.")
        event.accept()
