# src/domain/models.py
from typing import Optional

class Language:
    """Representa un idioma soportado."""
    def __init__(self, code: str, name: str):
        self.code = code  # e.g., "en", "es"
        self.name = name  # e.g., "English", "Español"

    def __repr__(self):
        return f"Language(code='{self.code}', name='{self.name}')"

    def __eq__(self, other):
        if not isinstance(other, Language):
            return NotImplemented
        return self.code == other.code

    def __hash__(self):
        return hash(self.code)


class TranslationRequest:
    """Representa una solicitud para traducir texto."""
    def __init__(self, text: str, source_language: Language, target_language: Language):
        self.text = text
        self.source_language = source_language
        self.target_language = target_language

    def __repr__(self):
        return (f"TranslationRequest(text='{self.text[:50]}...', "
                f"source='{self.source_language.code}', "
                f"target='{self.target_language.code}')")

class TranslationResult:
    """Representa el resultado de una operación de traducción."""
    def __init__(self, translated_text: Optional[str] = None, error: Optional[str] = None):
        self.translated_text = translated_text
        self.error = error
        self.is_successful = translated_text is not None and error is None

    def __repr__(self):
        if self.is_successful:
            return f"TranslationResult(translated_text='{self.translated_text[:50]}...')"
        else:
            return f"TranslationResult(error='{self.error}')"

# Podemos añadir modelos para la configuración, resultados de OCR, etc. más adelante