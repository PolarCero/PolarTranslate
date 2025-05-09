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

### 1. Clona o descarga el repositorio

```bash
git clone https://github.com/PolarCero/PolarTranslate.git
cd PolarTranslate
```

### 2. (Opcional pero recomendado) Usa un entorno virtual de Python

https://www.python.org/downloads/release/python-3119/

Esto es útil si no tienes Python 3.11.9 instalado globalmente o quieres mantener dependencias aisladas:

```bash
# Crear un entorno virtual (requiere tener Python 3.11.9 instalado)
python -m venv .venv_p311

py -3.11 -m venv .venv


# Activar el entorno virtual
# En Windows:
.\.venv\Scripts\Activate.ps1
# En macOS/Linux:
source .venv/bin/activate
```

### 3. Instala las dependencias del proyecto

```bash
pip install -r requirements.txt
```

### 4. Instala Tesseract-OCR (requerido para funciones OCR)

🔗 https://github.com/tesseract-ocr/tesseract

Asegúrate de que el ejecutable `tesseract` esté en tu variable de entorno `PATH`.

### 5. Instala los modelos de traducción

```bash
python install_models.py
```

### 6. Ejecuta la aplicación

```bash
python main.py
```

> ✅ Asegúrate de tener **Python 3.11.9** instalado o usar un entorno virtual con esa versión.

### ℹ️ Activación del entorno virtual en Windows

Si estás en Windows y usas PowerShell, activa el entorno virtual con:

```powershell
.\.venv\Scripts\Activate.ps1
```

#### ⚠️ ¿Ves un error como este?

```text
.\.venv\Scripts\Activate.ps1 : File ... is not digitally signed. 
You cannot run this script on the current system.
```

Significa que tu política de ejecución de scripts está deshabilitada. Puedes permitirlo temporalmente con este comando:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

Esto cambiará la política **solo durante la sesión actual**, sin afectar la seguridad general del sistema. Luego intenta de nuevo:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Licencia
Este proyecto está licenciado bajo la AGPL-3.0.

Los modelos de traducción son provistos por Argos Translate y están licenciados bajo MIT. Se agradece y reconoce su excelente trabajo.

Si usas este proyecto o haces algo derivado, por favor menciona el proyecto original. Toda contribución y fork debe mantenerse también open source, bajo los términos de la licencia AGPL.
