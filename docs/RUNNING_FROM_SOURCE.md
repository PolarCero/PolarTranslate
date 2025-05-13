# Guía para Ejecutar Polar Translate desde Código Fuente
Este documento detalla los pasos necesarios para configurar tu entorno de desarrollo, instalar las dependencias y ejecutar la aplicación Polar Translate directamente desde su código fuente.

## Requisitos Previos
Python 3.11.9: Se recomienda encarecidamente usar esta versión específica de Python. Puedes descargarla desde https://www.python.org/downloads/release/python-3119/.

Tesseract OCR Engine: Requerido para las funcionalidades de OCR. Consulta la sección de instalación a continuación.

## Pasos de Instalación y Ejecución
### 1. Clona o descarga el repositorio

```bash
git clone https://github.com/PolarCero/PolarTranslate.git
cd PolarTranslate
```

### 2. (Opcional pero recomendado) Usa un entorno virtual de Python

https://www.python.org/downloads/release/python-3119/

Esto es útil si no tienes Python 3.11.9 instalado globalmente o quieres mantener dependencias aisladas:

```bash
# Crear un entorno virtual
py -3.11 -m venv .venv


# Activar el entorno virtual
# En Windows:
.\.venv\Scripts\Activate.ps1


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

# En macOS/Linux:
source .venv/bin/activate
```

### 3. Instala las dependencias del proyecto

```bash
pip install -r requirements.txt
```

### 4. Instala Tesseract-OCR (requerido para funciones OCR)
(Release)
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

