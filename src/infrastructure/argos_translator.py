# src/infrastructure/argos_translator.py

import argostranslate.package
import argostranslate.translate
import argostranslate.settings # Mantenemos settings por si se necesita para configuración futura
from typing import List, Optional

# Importar la interfaz de la capa de Dominio y los modelos
from src.domain.interfaces import ITranslator
from src.domain.models import Language, TranslationRequest, TranslationResult

class ArgosTranslator(ITranslator):
    """
    Implementación de ITranslator que utiliza la biblioteca argostranslate.
    Esta clase reside en la capa de Infraestructura.
    """

    def __init__(self):
        """
        Constructor del traductor Argos.
        Intenta actualizar y cargar los paquetes de idioma instalados.
        """
        print("Infrastructure Layer (ArgosTranslator): Inicializando...")
        try:
            # Intenta actualizar la base de datos de paquetes remotos
            print("Infrastructure Layer (ArgosTranslator): Intentando actualizar paquetes remotos...")
            argostranslate.package.update_package_index()
            print("Infrastructure Layer (ArgosTranslator): Paquetes remotos actualizados.")
        except Exception as e:
            print(f"Infrastructure Layer (ArgosTranslator): Advertencia: No se pudo actualizar el índice de paquetes remotos: {e}")
            print("Infrastructure Layer (ArgosTranslator): Continuará con los paquetes locales instalados.")

        try:
            # Carga los paquetes de idioma instalados localmente
            print("Infrastructure Layer (ArgosTranslator): Cargando paquetes locales instalados...")
            # Es importante cargar los paquetes disponibles para que get_installed_languages funcione correctamente
            argostranslate.package.load_available_packages()
            print("Infrastructure Layer (ArgosTranslator): Paquetes locales cargados.")
        except Exception as e:
            print(f"Infrastructure Layer (ArgosTranslator): Error al cargar paquetes locales: {e}")
            print("Infrastructure Layer (ArgosTranslator): La traducción podría no funcionar si no hay paquetes instalados.")

        print("Infrastructure Layer (ArgosTranslator): Inicialización completa.")


    def get_available_languages(self) -> List[Language]:
        """
        Obtiene la lista de idiomas disponibles para la traducción desde argostranslate.
        Utiliza get_installed_languages() para obtener solo los idiomas de paquetes instalados.

        Returns:
            Una lista de objetos Language.
        """
        print("Infrastructure Layer (ArgosTranslator): Obteniendo idiomas disponibles (instalados)...")
        try:
            # CORREGIDO: Usar get_installed_languages() en lugar de get_available_languages()
            argos_languages = argostranslate.translate.get_installed_languages()
            print(f"Infrastructure Layer (ArgosTranslator): argostranslate.translate.get_installed_languages() retornó {len(argos_languages)} idiomas.")

            # Convertir los objetos Language de argostranslate a nuestros objetos Language del Dominio
            domain_languages: List[Language] = [
                Language(code=lang.code, name=lang.name) for lang in argos_languages
            ]
            print(f"Infrastructure Layer (ArgosTranslator): Convertidos a {len(domain_languages)} objetos Language del Dominio.")
            return domain_languages
        except Exception as e:
            print(f"Infrastructure Layer (ArgosTranslator): Error al obtener idiomas disponibles: {e}")
            # Retornar una lista vacía en caso de error
            return []


    def translate(self, request: TranslationRequest) -> TranslationResult:
        """
        Realiza una solicitud de traducción utilizando argostranslate.

        Args:
            request: Un objeto TranslationRequest con el texto, idioma de origen y destino.

        Returns:
            Un objeto TranslationResult con el texto traducido o posibles errores.
        """
        print(f"Infrastructure Layer (ArgosTranslator): translate() llamado para texto='{request.text[:50]}...' de {request.source_language.code} a {request.target_language.code}")
        translated_text = ""
        error_message: Optional[str] = None

        try:
            # argostranslate.translate.translate() realiza la traducción.
            # Requiere los códigos de idioma como strings.
            print("Infrastructure Layer (ArgosTranslator): Llamando a argostranslate.translate.translate()...")
            translated_text = argostranslate.translate.translate(
                request.text,
                request.source_language.code,
                request.target_language.code
            )
            print("Infrastructure Layer (ArgosTranslator): argostranslate.translate.translate() regresó.")
            print(f"Infrastructure Layer (ArgosTranslator): Texto traducido (primeros 50 chars): {translated_text[:50]}...")

        except Exception as e:
            error_message = f"Error en argostranslate.translate.translate(): {e}"
            print(f"Infrastructure Layer (ArgosTranslator): {error_message}")
            # Si ocurre un error, argostranslate.translate.translate() puede lanzar una excepción.
            # Capturamos la excepción y la reportamos en el TranslationResult.

        # Crear y retornar el objeto TranslationResult
        if error_message:
            return TranslationResult(error=error_message)
        else:
            return TranslationResult(translated_text=translated_text)

