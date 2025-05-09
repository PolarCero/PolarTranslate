# src/infrastructure/tts_service.py

import pyttsx3
import threading # Importamos threading para ejecutar la reproducción en segundo plano

class TTSService:
    """
    Interfaz (clase base abstracta) para los servicios de Text-to-Speech.
    Define el contrato que deben seguir los servicios TTS.
    """
    def speak(self, text: str):
        """
        Convierte el texto proporcionado en voz.
        """
        raise NotImplementedError("Subclass must implement abstract method")

    def stop(self):
        """
        Detiene cualquier reproducción de voz en curso.
        """
        raise NotImplementedError("Subclass must implement abstract method")

    def get_available_voices(self) -> list[dict]:
        """
        Obtiene una lista de las voces disponibles en el sistema.
        Cada voz se representa como un diccionario con detalles (ej: id, name).
        """
        raise NotImplementedError("Subclass must implement abstract method")

    def set_voice(self, voice_id: str):
        """
        Establece la voz a utilizar para la reproducción.
        """
        raise NotImplementedError("Subclass must implement abstract method")

    def set_rate(self, rate: int):
        """
        Establece la velocidad de reproducción (palabras por minuto).
        """
        raise NotImplementedError("Subclass must implement abstract method")

    def set_volume(self, volume: float):
        """
        Establece el volumen de reproducción (0.0 a 1.0).
        """
        raise NotImplementedError("Subclass must implement abstract method")


class Pyttsx3TTSService(TTSService):
    """
    Implementación del servicio de Text-to-Speech utilizando la biblioteca pyttsx3.
    Interactúa con los motores de síntesis de voz del sistema operativo.
    """
    def __init__(self):
        """
        Inicializa el motor pyttsx3.
        """
        try:
            # Inicializar el motor TTS
            self._engine = pyttsx3.init()
            print("Infrastructure Layer (Pyttsx3TTSService): Motor pyttsx3 inicializado.")

            # Atributo para mantener la referencia al hilo de reproducción
            self._speak_thread = None

        except Exception as e:
            print(f"Infrastructure Layer (Pyttsx3TTSService): Error al inicializar pyttsx3: {e}")
            self._engine = None # Asegurarse de que el motor sea None si falla la inicialización


    def speak(self, text: str):
        """
        Convierte el texto proporcionado en voz.
        Ejecuta la reproducción en un hilo separado para no bloquear la aplicación.
        """
        if not self._engine:
            print("Infrastructure Layer (Pyttsx3TTSService): Motor TTS no inicializado. No se puede hablar.")
            return

        # Detener cualquier reproducción anterior antes de iniciar una nueva
        self.stop()

        # Crear y iniciar un nuevo hilo para la reproducción
        # Usamos una función interna para la tarea del hilo
        def _speak_task():
            try:
                print(f"Infrastructure Layer (Pyttsx3TTSService): Iniciando reproducción de voz para: {text[:50]}...")
                self._engine.say(text)
                self._engine.runAndWait() # Bloquea el hilo hasta que termine la reproducción
                print("Infrastructure Layer (Pyttsx3TTSService): Reproducción de voz finalizada.")
            except Exception as e:
                print(f"Infrastructure Layer (Pyttsx3TTSService): Error durante la reproducción de voz: {e}")

        self._speak_thread = threading.Thread(target=_speak_task, daemon=True)
        self._speak_thread.start()


    def stop(self):
        """
        Detiene cualquier reproducción de voz en curso.
        """
        if self._engine:
            print("Infrastructure Layer (Pyttsx3TTSService): Solicitando detener reproducción de voz...")
            self._engine.stop()
            # Opcional: Esperar a que el hilo termine si no es daemon, pero con daemon no es estrictamente necesario
            # if self._speak_thread and self._speak_thread.is_alive():
            #     self._speak_thread.join(1.0) # Esperar un máximo de 1 segundo

    def get_available_voices(self) -> list[dict]:
        """
        Obtiene una lista de las voces disponibles en el sistema.
        """
        if not self._engine:
            print("Infrastructure Layer (Pyttsx3TTSService): Motor TTS no inicializado. No se pueden obtener voces.")
            return []
        try:
            voices = self._engine.getProperty('voices')
            # Convertir los objetos de voz a diccionarios simples para el Dominio/Aplicación
            voice_list = [{"id": voice.id, "name": voice.name, "lang": voice.languages[0] if voice.languages else "unknown"} for voice in voices]
            print(f"Infrastructure Layer (Pyttsx3TTSService): Voces disponibles obtenidas: {len(voice_list)}")
            return voice_list
        except Exception as e:
            print(f"Infrastructure Layer (Pyttsx3TTSService): Error al obtener voces: {e}")
            return []

    def set_voice(self, voice_id: str):
        """
        Establece la voz a utilizar para la reproducción.
        """
        if not self._engine:
            print("Infrastructure Layer (Pyttsx3TTSService): Motor TTS no inicializado. No se puede establecer la voz.")
            return
        try:
            self._engine.setProperty('voice', voice_id)
            print(f"Infrastructure Layer (Pyttsx3TTSService): Voz establecida a: {voice_id}")
        except Exception as e:
            print(f"Infrastructure Layer (Pyttsx3TTSService): Error al establecer la voz {voice_id}: {e}")

    def set_rate(self, rate: int):
        """
        Establece la velocidad de reproducción (palabras por minuto).
        """
        if not self._engine:
            print("Infrastructure Layer (Pyttsx3TTSService): Motor TTS no inicializado. No se puede establecer la velocidad.")
            return
        try:
            self._engine.setProperty('rate', rate)
            print(f"Infrastructure Layer (Pyttsx3TTSService): Velocidad establecida a: {rate}")
        except Exception as e:
            print(f"Infrastructure Layer (Pyttts3TTSService): Error al establecer la velocidad {rate}: {e}")

    def set_volume(self, volume: float):
        """
        Establece el volumen de reproducción (0.0 a 1.0).
        """
        if not self._engine:
            print("Infrastructure Layer (Pyttsx3TTSService): Motor TTS no inicializado. No se puede establecer el volumen.")
            return
        try:
            # Asegurarse de que el volumen esté en el rango [0.0, 1.0]
            volume = max(0.0, min(1.0, volume))
            self._engine.setProperty('volume', volume)
            print(f"Infrastructure Layer (Pyttsx3TTSService): Volumen establecido a: {volume}")
        except Exception as e:
            print(f"Infrastructure Layer (Pyttsx3TTSService): Error al establecer el volumen {volume}: {e}")

    def __del__(self):
        """
        Destructor para asegurar que el motor pyttsx3 se detenga al cerrar la aplicación.
        """
        if self._engine:
            print("Infrastructure Layer (Pyttsx3TTSService): Deteniendo motor pyttsx3 en destructor.")
            self._engine.stop()
            # No llamamos a engine.quit() aquí porque puede causar problemas al salir de la aplicación PySide.
            # pyttsx3.init() y .runAndWait() manejan la inicialización y el bucle de eventos interno,
            # y engine.stop() es suficiente para detener la reproducción activa.
            # La limpieza final del motor a menudo ocurre automáticamente al terminar el proceso.

