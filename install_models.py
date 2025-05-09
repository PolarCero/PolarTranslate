import os
import argostranslate.package
import argostranslate.translate

def verificar_idiomas_instalados():
    try:
        installed_languages = argostranslate.translate.get_installed_languages()
        if installed_languages:
            print(f"🌐 Idiomas instalados: {len(installed_languages)}")
            for language in installed_languages:
                print(f"🌎 {language.name} ({language.code}):")
                print(f"{language.translations_to}")
        else:
            print("❌ No hay idiomas instalados.")
    except Exception as e:
        print(f"❌ Error al verificar idiomas instalados: {e}")

def obtener_modelos_disponibles():
    try:
        # Obtenemos la lista de paquetes disponibles
        available_packages = argostranslate.package.get_available_packages()
        return available_packages
    except Exception as e:
        print(f"❌ Error al obtener modelos disponibles: {e}")
        return []

def instalar_modelo(pkg):
    try:
        print(f"⬇️ Descargando: {pkg.from_code} ➜ {pkg.to_code}")
        path = pkg.download()
        print("Ruta de descarga:", path)  # Muestra la ruta donde se descarga el modelo
        # Verificar si la ruta de instalación es correcta
        print("Instalando desde:", path)
        argostranslate.package.install_from_path(path)
        print("✅ Modelo instalado correctamente.")
    except Exception as e:
        print(f"❌ Error al instalar modelo: {e}")

def menu():
    argostranslate.translate.load_installed_languages()

    while True:
        print("\n=== 🌍 MENÚ ARGOS TRANSLATE ===")
        print("1. Verificar idiomas instalados")
        print("2. Instalar todos los modelos disponibles")
        print("3. Instalar modelo específico")
        print("q. Salir")

        opcion = input("Selecciona una opción: ").strip().lower()

        if opcion == '1':
            verificar_idiomas_instalados()
        elif opcion == '2':
            paquetes = obtener_modelos_disponibles()
            for pkg in paquetes:
                instalar_modelo(pkg)
        elif opcion == '3':
            paquetes = obtener_modelos_disponibles()
            for i, pkg in enumerate(paquetes):
                print(f"{i + 1}. {pkg.from_code} ➜ {pkg.to_code}")
            seleccion = input("Número del modelo a instalar: ").strip()
            if seleccion.isdigit() and 1 <= int(seleccion) <= len(paquetes):
                instalar_modelo(paquetes[int(seleccion) - 1])
            else:
                print("❌ Opción inválida.")
        elif opcion == 'q':
            print("👋 Saliendo del programa...")
            break
        else:
            print("❌ Opción no reconocida.")

if __name__ == "__main__":
    menu()
