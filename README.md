# PolarTranslate
Free and Open Source Translator. Works locally, offline, and requires no server.


**Polar Translate** es una aplicación de traducción local que utiliza los modelos de Argos Translate para ofrecer traducción offline, rápida y privada, sin depender de servidores externos.

## Características

- Traducción completamente offline
- Basado en modelos open source de Argos Translate
- Código open source con licencia AGPL-3.0
- Funcionalidades de OCR (Reconocimiento Óptico de Caracteres) desde imágenes y captura de pantalla.

## Tecnologías usadas

- Python 3.11.9 (Recomendado, no superior)
- Argos Translate
- Pytesseract (Biblioteca de Python para OCR)
- **Tesseract OCR Engine** (Software externo para OCR)

## ⚙️ Instalación

1. Clona o Descarga el repositorio:

```bash
git clone https://github.com/PolarCero/PolarTranslate.git
cd PolarTranslate
```

2. Instala los requisitos:

```bash
pip install -r requirements.txt
```

instala tesseract-ocr
https://github.com/tesseract-ocr/tesseract

3. Instala los modelos:

```bash
python install_models.py
```


Ejecuta la aplicación:

```bash
python main.py
```
|   Asegúrate de tener Python 3.8+ instalado.

## Licencia
Este proyecto está licenciado bajo la AGPL-3.0.

Los modelos de traducción son provistos por Argos Translate y están licenciados bajo MIT. Se agradece y reconoce su excelente trabajo.

Si usas este proyecto o haces algo derivado, por favor menciona el proyecto original. Toda contribución y fork debe mantenerse también open source, bajo los términos de la licencia AGPL.
