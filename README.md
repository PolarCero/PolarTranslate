# PolarTranslate

Free and Open Source Translator. Works locally, offline, and requires no server.

[English](README.md) | [Español](README.es.md)

**Polar Translate** is a local desktop translation application that uses Argos Translate models to provide offline, fast, and private translation, without relying on external servers.

---

## Features

* Completely offline translation using Argos Translate models.
* Based on *open source* models.
* *Open source* code under the **AGPL-3.0** license.
* OCR (Optical Character Recognition) functionalities from images and screen capture.
* Management of Argos Translate language packages (installation/uninstallation) from the user interface.

---

## Requirements

* Python 3.11.9 (Recommended, not higher)
* **Tesseract OCR Engine** (External software for OCR)

---

## 🚀 Run from Source Code

Follow these steps if you want to clone the repository and run the application directly from the source code on your machine.

👉 For detailed instructions on how to set up your environment, install dependencies, and run the application from source code, check out our [**Complete Guide to Running from Source Code**](docs/RUNNING_FROM_SOURCE.md).

---

## 📦 Use the Executable (Release)

If you just want to use the application without installing Python or managing dependencies, **download the pre-compiled executable** from the GitHub *Releases*.

### 1. Download the Executable

- Go to the repository's Releases page:
  [https://github.com/PolarCero/PolarTranslate/releases](https://github.com/PolarCero/PolarTranslate/releases)
  *(Replace PolarCero/PolarTranslate with your actual repository path if different).*
- Find the latest Release (e.g., `v0.1.0`).
- In the **"Assets"** section of the Release, download the `PolarTranslate.exe` file.

### 2. Save the Executable

Save the `PolarTranslate.exe` file to a folder of your choice on your computer (e.g., in your Downloads folder or create a specific folder for the application).

### 3. Install Tesseract-OCR (required for OCR features)

This step is the same as for running from source code and is **MANDATORY** for OCR features.

- Download the Tesseract OCR installer from the official website:
  [https://tesseract-ocr.github.io/](https://tesseract-ocr.github.io/)
- Follow the installation instructions for your operating system.
- Make sure the `tesseract` executable is in your system's **PATH**.

### 4. Run the Application

Simply double-click the `PolarTranslate.exe` file you downloaded.

> **Note on Language Packages:**
> Argos Translate language packages are managed directly from the **Configuration** window within the application.
> The first time you run it, you might only have the base languages installed.
> Go to `Configuration -> Languages and Packages` to install the languages you need.
> The application will ask you to close and reopen it after installing/uninstalling packages for the changes to take effect.

---

## 🔜 Upcoming Features

We are working on improving Polar Translate and adding new functionalities. Some of the planned features include:

* **Advanced Configuration:** Complete interface to manage Tesseract path, custom hotkeys, and other application options.

* **Text-to-Speech (TTS):** Functionality to read translated text aloud.

* **OCR Improvements:** Ability to select more precise text areas in screen capture, support for more image formats.

* **Improved Clipboard Integration:** Optional automatic detection of clipboard changes.

* **Multi-platform Support:** Packaging and testing for macOS and Linux.

* **Full Installer:** An installer (e.g., .msi for Windows) that can automatically manage the installation of Tesseract OCR (optionally).

* **UI/UX Improvements:** Refinements to the user interface for a smoother experience.

---

## License
This project is licensed under the **AGPL-3.0**.

Translation models are provided by **Argos Translate** and are licensed under **MIT**. Their great work is appreciated and acknowledged.

> If you use this project or create a derivative work, please mention the original project.
> All contributions and forks must also remain open source, under the terms of the AGPL license.

## Report Bugs and Suggestions
If you find any bugs, have suggestions for improvement, or want to request a new feature, please open an issue in the repository's Issues section.
[Report Bugs and Suggestions](https://github.com/PolarCero/PolarTranslate/issues)
