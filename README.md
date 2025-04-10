# DriveBot

**DriveBot** es una aplicación automatizada construida con Flask que permite gestionar archivos y carpetas en Google Drive usando Google Sheets como base de datos. Diseñada para funcionar fácilmente con Docker, es ideal para entornos educativos o colaborativos que requieren organizar materiales por estudiante.

## 🚀 Características principales

- 📁 Crea carpetas en Google Drive desde una tabla de Google Sheets.
- 🔗 Comparte las carpetas automáticamente con permisos de edición.
- 🧠 Guarda y reutiliza los enlaces creados.
- 📊 Interfaz simple basada en Flask.
- 🐳 Compatible con Docker y lista para producción.
- 🧰 Instalador para Windows en desarrollo (ver sección 👇).

## 📦 Requisitos

- Python 3.10+
- Credenciales de una cuenta de Google con permisos en Drive y Sheets
- Docker y Git (si usás el instalador)

## ⚙️ Instalación

### Opción 1: Clonar y ejecutar manualmente

```bash
git clone https://github.com/tuusuario/DriveBot.git
cd DriveBot
pip install -r requirements.txt
python app.py
```

Accedé a `http://localhost:5000`.

---

### Opción 2: Usar Docker

```bash
docker-compose up --build
```

El servidor quedará accesible en `http://localhost:5000`.

---

## 🔐 Configuración de credenciales

1. Crea un proyecto en [Google Cloud Console](https://console.cloud.google.com/).
2. Habilitá las APIs:
   - Google Drive API
   - Google Sheets API
3. Descargá tu archivo `credentials.json` y colocalo en la raíz del proyecto.
4. El primer inicio generará un archivo `token.json` tras la autorización.

> ⚠️ Asegurate de agregar `credentials.json` y `token.json` al `.gitignore`.

---

## 🧪 En desarrollo

- 🪟 Instalador minimalista para Windows (con GUI Tkinter):
  - Instala Docker y Git si no están presentes.
  - Clona este repositorio.
  - Ejecuta `docker-compose up`.
  - Abre el navegador automáticamente en `localhost`.

---

## 📝 Licencia

MIT License

---

_Creado por José Assiz - 2025-04-10_
