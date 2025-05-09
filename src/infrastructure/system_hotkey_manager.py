# src/infrastructure/system_hotkey_manager.py

import keyboard # La biblioteca concreta de infraestructura para hotkeys
import threading # Necesario para ejecutar el listener en un hilo separado
from typing import Callable, Dict, Optional

# Importar la interfaz de la capa de Dominio
from src.domain.interfaces import IHotkeyManager

class SystemHotkeyManager(IHotkeyManager):
    """
    Implementación de IHotkeyManager que utiliza la biblioteca keyboard.
    Esta clase reside en la capa de Infraestructura.
    """

    def __init__(self):
        # Diccionario para almacenar las hotkeys registradas y sus callbacks
        # La clave es la combinación de teclas (string), el valor es el objeto Hook de keyboard
        self._hotkey_hooks: Dict[str, keyboard.Hook] = {}
        # Hilo para ejecutar el listener de hotkeys
        self._listener_thread: Optional[threading.Thread] = None
        # Evento para detener el hilo del listener
        self._stop_event = threading.Event()

    def register_hotkey(self, hotkey: str, callback: Callable[[], None]):
        """
        Registra una hotkey global y asocia una función de callback a ella.
        Si la hotkey ya está registrada, primero la desregistra.

        Args:
            hotkey: La combinación de teclas a registrar (ej: "ctrl+shift+t").
                    El formato debe ser compatible con la biblioteca 'keyboard'.
            callback: La función a ejecutar cuando la hotkey es presionada.
        """
        if hotkey in self._hotkey_hooks:
            self.unregister_hotkey(hotkey)
            print(f"Infrastructure Layer: Desregistrada hotkey existente: {hotkey}")

        try:
            # keyboard.add_hotkey registra la hotkey y devuelve un objeto Hook
            # El parametro 'suppress=False' significa que el evento de la hotkey no será bloqueado
            hook = keyboard.add_hotkey(hotkey, callback, suppress=False)
            self._hotkey_hooks[hotkey] = hook
            print(f"Infrastructure Layer: Registrada hotkey: {hotkey}")
        except Exception as e:
            print(f"Infrastructure Layer: Error al registrar hotkey {hotkey}: {e}")
            # Considerar relanzar la excepción o manejarla según la necesidad de la aplicación

    def unregister_hotkey(self, hotkey: str):
        """
        Elimina el registro de una hotkey global previamente registrada.

        Args:
            hotkey: La combinación de teclas a eliminar.
        """
        if hotkey in self._hotkey_hooks:
            try:
                # keyboard.remove_hotkey elimina el registro usando el objeto Hook o la combinación de teclas
                keyboard.remove_hotkey(self._hotkey_hooks[hotkey])
                del self._hotkey_hooks[hotkey]
                print(f"Infrastructure Layer: Desregistrada hotkey: {hotkey}")
            except Exception as e:
                 print(f"Infrastructure Layer: Error al desregistrar hotkey {hotkey}: {e}")
        else:
            print(f"Infrastructure Layer: Intento de desregistrar hotkey no registrada: {hotkey}")


    def start_listening(self):
        """
        Inicia el monitoreo global de hotkeys en un hilo separado.
        Esto es necesario porque keyboard.wait() es bloqueante.
        """
        if self._listener_thread is None or not self._listener_thread.is_alive():
            self._stop_event.clear() # Asegurarse de que el evento de parada esté limpio
            # Creamos un nuevo hilo que ejecutará el método _listen
            self._listener_thread = threading.Thread(target=self._listen, daemon=True)
            self._listener_thread.start()
            print("Infrastructure Layer: Iniciado monitoreo de hotkeys en hilo separado.")
        else:
            print("Infrastructure Layer: El monitoreo de hotkeys ya está en ejecución.")


    def stop_listening(self):
        """
        Detiene el monitoreo global de hotkeys.
        """
        if self._listener_thread is not None and self._listener_thread.is_alive():
            # Establecemos el evento de parada para indicarle al hilo que termine
            self._stop_event.set()
            # Esperamos a que el hilo termine (con un timeout opcional)
            self._listener_thread.join(timeout=1.0)
            if self._listener_thread.is_alive():
                 print("Infrastructure Layer: Advertencia: El hilo del listener de hotkeys no se detuvo a tiempo.")
            self._listener_thread = None
            print("Infrastructure Layer: Detenido monitoreo de hotkeys.")
        else:
            print("Infrastructure Layer: El monitoreo de hotkeys no estaba en ejecución.")

    def _listen(self):
        """
        Método interno que se ejecuta en el hilo separado para escuchar hotkeys.
        Bloquea hasta que se establece el evento de parada.
        """
        print("Infrastructure Layer: Hilo de listener de hotkeys iniciado.")
        # keyboard.wait() bloquea hasta que se presiona una tecla o se detiene externamente.
        # En este caso, se detendrá cuando se establezca self._stop_event.
        # Nota: keyboard.wait() puede no ser ideal para detenerse limpiamente con un evento.
        # Una alternativa más robusta podría ser usar keyboard.hook() y monitorear el evento manualmente,
        # o depender de keyboard.unhook_all() o sys.exit() si la aplicación se cierra.
        # Para este ejemplo, usaremos wait() por simplicidad, pero ten en cuenta esta limitación.
        try:
            keyboard.wait(suppress=True) # suppress=True para evitar que la hotkey llegue a otras aplicaciones
        except Exception as e:
            print(f"Infrastructure Layer: Error en el hilo del listener de hotkeys: {e}")
        finally:
             print("Infrastructure Layer: Hilo de listener de hotkeys finalizado.")
             # Limpiar hotkeys registradas al finalizar el hilo
             self._hotkey_hooks.clear() # Esto no desregistra del sistema, solo limpia el diccionario interno


    def __del__(self):
        """
        Método llamado cuando el objeto es recolectado como basura.
        Intenta detener el listener para liberar recursos del sistema.
        """
        self.stop_listening()
        print("Infrastructure Layer: Instancia de SystemHotkeyManager eliminada.")

