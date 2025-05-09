# src/infrastructure/system_utils.py

import pyperclip # Biblioteca para acceder al portapapeles

# Nota: pyperclip es una biblioteca de infraestructura.
# No definimos una interfaz para ella en el Dominio a menos que
# anticipemos la necesidad de cambiar la implementación del portapapeles,
# lo cual es poco probable para esta funcionalidad.

def get_clipboard_text() -> str:
    """
    Obtiene el texto actual del portapapeles del sistema.

    Returns:
        El texto del portapapeles.
    """
    try:
        # pyperclip.paste() lee el contenido del portapapeles
        clipboard_content = pyperclip.paste()
        print(f"Infrastructure Layer (SystemUtils): Texto del portapapeles obtenido (primeros 50 chars): {clipboard_content[:50]}...")
        return clipboard_content
    except pyperclip.PyperclipException as e:
        print(f"Infrastructure Layer (SystemUtils): Error al obtener texto del portapapeles: {e}")
        # Dependiendo de cómo queramos manejar esto, podríamos devolver una cadena vacía
        # o lanzar una excepción específica del dominio si definimos una.
        return "" # Devolvemos cadena vacía en caso de error


def set_clipboard_text(text: str):
    """
    Establece el texto en el portapapeles del sistema.

    Args:
        text: El texto a colocar en el portapapeles.
    """
    try:
        # pyperclip.copy() escribe en el portapapeles
        pyperclip.copy(text)
        print(f"Infrastructure Layer (SystemUtils): Texto establecido en portapapeles (primeros 50 chars): {text[:50]}...")
    except pyperclip.PyperclipException as e:
        print(f"Infrastructure Layer (SystemUtils): Error al establecer texto en portapapeles: {e}")
        # Manejo de errores si no se puede escribir en el portapapeles.

# Podemos añadir otras utilidades del sistema aquí si son necesarias en el futuro
