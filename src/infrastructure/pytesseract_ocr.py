# src/infrastructure/pytesseract_ocr.py

import pytesseract # La biblioteca concreta de infraestructura para OCR
from PIL import Image # pytesseract a menudo trabaja con objetos Image de PIL
import os # Para manejar rutas y verificar existencia de archivos
from typing import Any, Optional

# Importar la interfaz de la capa de Dominio
from src.domain.interfaces import IOCRService

class PytesseractOCRService(IOCRService):
    """
    Implementación de IOCRService que utiliza la biblioteca pytesseract.
    Esta clase reside en la capa de Infraestructura.
    """

    def __init__(self, tesseract_cmd_path: Optional[str] = None):
        """
        Constructor del servicio OCR.

        Args:
            tesseract_cmd_path: Ruta opcional al ejecutable de Tesseract OCR.
                                Si no se proporciona, pytesseract intentará encontrarlo en el PATH.
        """
        # Configurar la ruta al ejecutable de Tesseract si se proporciona
        if tesseract_cmd_path and os.path.exists(tesseract_cmd_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path
            print(f"Infrastructure Layer (PytesseractOCRService): Usando Tesseract desde: {tesseract_cmd_path}")
        elif tesseract_cmd_path:
             print(f"Infrastructure Layer (PytesseractOCRService): Advertencia: La ruta de Tesseract '{tesseract_cmd_path}' no existe.")
             print("Infrastructure Layer (PytesseractOCRService): pytesseract intentará encontrar Tesseract en el PATH.")
        else:
            print("Infrastructure Layer (PytesseractOCRService): No se proporcionó ruta de Tesseract. pytesseract intentará encontrarlo en el PATH.")

        # Verificar si Tesseract es accesible (opcional pero recomendable)
        try:
            pytesseract.get_tesseract_version()
            print("Infrastructure Layer (PytesseractOCRService): Tesseract encontrado y accesible.")
        except pytesseract.TesseractNotFoundError:
            print("Infrastructure Layer (PytesseractOCRService): Error: Tesseract OCR no encontrado.")
            print("Infrastructure Layer (PytesseractOCRService): Asegúrate de que Tesseract esté instalado y en el PATH, o proporciona la ruta correcta en la configuración.")
            # Considerar lanzar una excepción o manejar este error de forma más robusta
            # raise EnvironmentError("Tesseract OCR executable not found.")


    def extract_text_from_image_data(self, image_data: Any) -> str:
        """
        Extrae texto de datos de imagen utilizando pytesseract.

        Args:
            image_data: Los datos de la imagen. Se espera un objeto PIL.Image.Image.

        Returns:
            El texto extraído de la imagen.
        """
        if not isinstance(image_data, Image.Image):
            print("Infrastructure Layer (PytesseractOCRService): Error: Se esperaba un objeto PIL.Image.Image.")
            # Devolver cadena vacía o lanzar una excepción si el tipo de datos es incorrecto
            return ""

        try:
            # pytesseract.image_to_string() realiza el OCR
            text = pytesseract.image_to_string(image_data)
            print("Infrastructure Layer (PytesseractOCRService): Texto extraído de la imagen (primeros 50 chars):", text[:50])
            return text
        except Exception as e:
            print(f"Infrastructure Layer (PytesseractOCRService): Error durante el OCR: {e}")
            # Devolver cadena vacía o manejar el error según la necesidad
            return ""

    # Nota: La lógica para obtener la imagen (desde archivo, pantalla, etc.)
    # residirá en la capa de Aplicación, que llamará a este servicio
    # con los datos de la imagen ya obtenidos.

