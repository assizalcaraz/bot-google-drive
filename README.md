# 📁 Google_Drive_Bot

**DriveBot** es una aplicación automatizada construida con Flask que permite gestionar archivos y carpetas en Google Drive usando Google Sheets como base de datos. Diseñada para funcionar fácilmente con Docker, es ideal para entornos educativos o colaborativos que requieren organizar materiales por estudiante.

---

## 🚀 Características principales

- 📁 Crea carpetas en Google Drive desde una tabla de Google Sheets.
- 🔗 Comparte las carpetas automáticamente con permisos de edición.
- 🧠 Guarda y reutiliza los enlaces creados.
- 📊 Interfaz simple basada en Flask.
- 🐳 Compatible con Docker y lista para producción.
- 🧰 Instalador para Windows en desarrollo.

---

## 📸 Capturas de pantalla

### 🔧 Configuración inicial del proyecto

Primero, ingresá el enlace de tu carpeta base en Google Drive y compartila con el bot:

<img src="/screenshots/configuracion.png" width="800"/>

---

### 📤 Compartir archivos con estudiantes

Copiá carpetas completas o creá accesos directos dentro de las carpetas personales:

<img src="/screenshots/compartir.png" width="800"/>

---

### 📂 Visualización de lotes generados

Explorá la estructura de carpetas generadas automáticamente para cada lote:

<img src="/screenshots/lotes.png" width="800"/>

---

### 👨‍🎓 Vista del estudiante

Así se ve para un estudiante dentro de su Google Drive:

<img src="/screenshots/drive.png" width="600"/>

---

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

Creado por Assiz Alcaraz Baxter - 2025-04-10
