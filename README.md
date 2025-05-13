# PolarTranslate
Free and Open Source Translator. Works locally, offline, and requires no server.

**Polar Translate** es una aplicación de traducción local que utiliza los modelos de Argos Translate para ofrecer traducción offline, rápida y privada, sin depender de servidores externos.

---

## Características

- Traducción completamente offline utilizando modelos de Argos Translate.
- Basado en modelos *open source*.
- Código *open source* con licencia **AGPL-3.0**.
- Funcionalidades de OCR (Reconocimiento Óptico de Caracteres) desde imágenes y captura de pantalla.
- Gestión de paquetes de idioma de Argos Translate (instalación/desinstalación) desde la interfaz de usuario.

---

## Requisitos

- Python 3.11.9 (Recomendado, no superior)
- **Tesseract OCR Engine** (Software externo para OCR)

---

## 🚀 Ejecutar desde Código Fuente

Sigue estos pasos si deseas clonar el repositorio y ejecutar la aplicación directamente desde el código fuente en tu máquina.

👉 Para obtener instrucciones detalladas sobre cómo configurar tu entorno, instalar dependencias y ejecutar la aplicación desde el código fuente, consulta nuestra [**Guía Completa para Ejecutar desde Código Fuente**](docs/RUNNING_FROM_SOURCE.md).

---

## 📦 Usar el Ejecutable (Release)

Si solo quieres usar la aplicación sin instalar Python ni gestionar dependencias, **descarga el ejecutable precompilado** desde las *Releases* de GitHub.

### 1. Descarga el Ejecutable

- Ve a la página de Releases del repositorio:  
  [https://github.com/PolarCero/PolarTranslate/releases](https://github.com/PolarCero/PolarTranslate/releases)  
  *(Reemplaza PolarCero/PolarTranslate con la ruta real de tu repositorio si es diferente).*
- Busca la última Release (por ejemplo, `v0.1.0`).
- En la sección **"Assets"** de la Release, descarga el archivo `PolarTranslate.exe`.

### 2. Guarda el Ejecutable

Guarda el archivo `PolarTranslate.exe` en una carpeta de tu elección en tu computadora (por ejemplo, en tu carpeta de Descargas o crea una carpeta específica para la aplicación).

### 3. Instala Tesseract-OCR (requerido para funciones OCR)

Este paso es el mismo que para ejecutar desde código fuente y es **OBLIGATORIO** para las funciones de OCR.

- Descarga el instalador de Tesseract OCR desde el sitio web oficial:  
  [https://tesseract-ocr.github.io/](https://tesseract-ocr.github.io/)
- Sigue las instrucciones de instalación para tu sistema operativo.
- Asegúrate de que el ejecutable `tesseract` esté en el **PATH** de tu sistema.

### 4. Ejecuta la Aplicación

Simplemente haz doble clic en el archivo `PolarTranslate.exe` que descargaste.

> **Nota sobre Paquetes de Idioma:**  
> Los paquetes de idioma de Argos Translate se gestionan directamente desde la ventana de **Configuración** dentro de la aplicación.  
> La primera vez que la ejecutes, es posible que solo tengas los idiomas base instalados.  
> Ve a `Configuración -> Idiomas y Paquetes` para instalar los idiomas que necesites.  
> La aplicación te pedirá que la cierres y vuelvas a abrir después de instalar/desinstalar paquetes para que los cambios surtan efecto.

---

## Licencia
Este proyecto está licenciado bajo la **AGPL-3.0**.

Los modelos de traducción son provistos por **Argos Translate** y están licenciados bajo **MIT**. Se agradece y reconoce su gran trabajo.

> Si usas este proyecto o haces algo derivado, por favor menciona el proyecto original.  
> Toda contribución y fork debe mantenerse también open source, bajo los términos de la licencia AGPL.
