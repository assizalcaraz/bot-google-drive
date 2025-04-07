import os
import io
import time
import datetime
import sqlite3
import random

from flask import Flask, render_template_string, Response
from utils import crear_carpeta_y_compartir, get_services
from dateutil import parser as date_parser
from googleapiclient.http import MediaIoBaseDownload, MediaInMemoryUpload



from html_helpers.html_styles import render_head_html, render_html_close


app = Flask(__name__)

# 📁 Carpeta base de Drive donde se crean las subcarpetas
PARENT_FOLDER_ID = '14cPfGWwYmjsn-XJY4VteY5zwJqTKOcEc'

# 📄 URL de la hoja de cálculo con los datos de estudiantes
SHEET_URL = 'https://docs.google.com/spreadsheets/d/18QVgcXSCHbK1DrrojpCgUBoWVGlcUFhUYZvvk_6_bp8/edit#gid=0'

# 🗄️ Inicializar base de datos SQLite
conn = sqlite3.connect('database.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS estudiantes (
        nombre TEXT,
        mail TEXT,
        carpeta TEXT
    )
''')
conn.commit()

@app.route('/')
def index():
    print("📡 Iniciando procesamiento de hoja...")

    try:
        _, gc = get_services()
        sheet = gc.open_by_url(SHEET_URL).sheet1
        data = sheet.get_all_records(expected_headers=["nombre", "mail", "link"])

        creados = 0

        for row in data:
            nombre = row.get('nombre')
            mail = row.get('mail')

            if not nombre or not mail:
                print(f"⚠️ Fila inválida: {row}")
                continue

            c.execute("SELECT * FROM estudiantes WHERE mail = ?", (mail,))
            if c.fetchone():
                print(f"🔁 Ya procesado: {nombre} ({mail})")
                continue

            link = crear_carpeta_y_compartir(nombre, mail, PARENT_FOLDER_ID)
            c.execute("INSERT INTO estudiantes (nombre, mail, carpeta) VALUES (?, ?, ?)", (nombre, mail, link))
            conn.commit()
            print(f"✅ Carpeta creada: {nombre} → {link}")
            creados += 1

        return f"Proceso finalizado. Carpetas nuevas: {creados}"

    except Exception as e:
        print(f"❌ Error: {e}")
        return f"Ocurrió un error: {e}"

@app.route('/descargar')
def descargar_con_progreso():
    def generar():
        try:
            drive_service, _ = get_services()
            os.makedirs("DESCARGAS", exist_ok=True)

            yield render_head_html()

            conn = sqlite3.connect('database.db', check_same_thread=False)
            c = conn.cursor()
            registros = c.execute("SELECT nombre, carpeta FROM estudiantes").fetchall()
            archivos_pendientes = []

            def escanear(folder_id, ruta_local):
                query = f"'{folder_id}' in parents and trashed = false"
                resultado = drive_service.files().list(
                    q=query,
                    fields="files(id, name, mimeType, modifiedTime)",
                ).execute()

                for item in resultado.get("files", []):
                    nombre = item["name"]
                    tipo = item["mimeType"]
                    file_id = item["id"]

                    if tipo == "application/vnd.google-apps.folder":
                        nueva_ruta = os.path.join(ruta_local, nombre)
                        if os.path.exists(nueva_ruta) and os.path.isfile(nueva_ruta):
                            os.remove(nueva_ruta)
                        os.makedirs(nueva_ruta, exist_ok=True)
                        escanear(file_id, nueva_ruta)
                    else:
                        archivos_pendientes.append({
                            "id": file_id,
                            "name": nombre,
                            "path": os.path.join(ruta_local, nombre),
                            "modifiedTime": date_parser.parse(item["modifiedTime"]),
                        })

            for nombre_estudiante, link in registros:
                folder_id = link.split("/")[-1]
                ruta_local = os.path.join("DESCARGAS", nombre_estudiante)
                escanear(folder_id, ruta_local)

            total = len(archivos_pendientes)
            yield f"<div class='progreso'>🔍 Archivos detectados: <strong>{total}</strong></div>"
            yield """
            <div class='flex-header'>
                <h2>⬇️ Fase 2: sincronizando archivos...</h2>
                <div class='barra-externa'>
                    <div class='barra-interna' id='barra-interna'>0%</div>
                </div>
            </div>
            <ul id='archivo-lista' style='display: flex; flex-direction: column-reverse;'>
            """

            descargados = 0
            saltados = 0
            start_time = time.time()

            for idx, archivo in enumerate(archivos_pendientes, start=1):
                file_id = archivo["id"]
                nombre = archivo["name"]
                ruta = archivo["path"]
                os.makedirs(os.path.dirname(ruta), exist_ok=True)

                if os.path.exists(ruta):
                    modified_local = datetime.datetime.fromtimestamp(
                        os.path.getmtime(ruta), tz=datetime.timezone.utc
                    )
                    if modified_local > archivo["modifiedTime"]:
                        saltados += 1
                        yield f"<li class='saltado' style='opacity: 1; transform: none;'>🟡 [{idx}/{total}] {nombre} (saltado)</li>"
                        continue

                request = drive_service.files().get_media(fileId=file_id)
                with io.FileIO(ruta, "wb") as fh:
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()

                descargados += 1
                porcentaje = int((idx / total) * 100)
                tiempo_actual = time.time() - start_time
                tiempo_estimado = (tiempo_actual / idx) * (total - idx)
                mins, secs = divmod(int(tiempo_estimado), 60)

                barra_js = f"""
<script>
    const barra = document.getElementById('barra-interna');
    if (barra) {{
        barra.style.width = '{porcentaje}%';
        barra.innerText = '{porcentaje}%';
    }}
    const lista = document.getElementById('archivo-lista');
    if (lista) {{ lista.scrollTop = 0; }}
</script>
"""


                yield f"{barra_js}<li class='descargado' style='opacity: 1; transform: none;'>✅ [{idx}/{total}] {nombre} — ETA: {mins}m {secs}s</li>"

            yield f"""
                </ul>
                <div class='final'>
                    ✅ <strong>Sincronización completa.</strong><br>
                    Archivos descargados: <strong>{descargados}</strong><br>
                    Archivos saltados: <strong>{saltados}</strong>
                </div>
            """
            yield render_html_close()

        except Exception as e:
            yield f"<p class='error'>❌ Error: {e}</p>"

    return Response(generar(), mimetype='text/html')



import random  # asegurate de tener este import arriba

def generar_carpetas_de_prueba(base_dir="CARPETAS_PRUEBA"):
    nombres = [
        "Lucas", "Martina", "Agustín", "Camila", "Mateo", "Sofía", "Tomás", "Valentina",
        "Benjamín", "Juana", "Santiago", "Mía", "Joaquín", "Isabella", "Franco", "Renata",
        "Facundo", "Emma", "Thiago", "Catalina"
    ]
    extensiones = [".txt", ".jpg", ".mp4"]

    os.makedirs(base_dir, exist_ok=True)

    for nombre in nombres:
        carpeta_path = os.path.join(base_dir, nombre)
        os.makedirs(carpeta_path, exist_ok=True)

        cantidad_archivos = random.randint(1, 5)
        for i in range(cantidad_archivos):
            ext = random.choice(extensiones)
            nombre_archivo = f"{nombre.lower()}_{i+1}{ext}"
            archivo_path = os.path.join(carpeta_path, nombre_archivo)

            with open(archivo_path, "w") as f:
                if ext == ".txt":
                    f.write(f"Archivo de prueba {i+1} para {nombre}")
                else:
                    pass  # archivo vacío

    print(f"✅ Carpetas generadas en '{base_dir}'")


@app.route('/generar-prueba')
def vista_generar_carpetas():
    generar_carpetas_de_prueba()
    return "Carpetas de prueba generadas."

def crear_carpetas_prueba_en_drive(parent_id):
    drive_service, _ = get_services()

    nombres = [
        "Lucas", "Martina", "Agustín", "Camila", "Mateo", "Sofía", "Tomás", "Valentina",
        "Benjamín", "Juana", "Santiago", "Mía", "Joaquín", "Isabella", "Franco", "Renata",
        "Facundo", "Emma", "Thiago", "Catalina"
    ]
    extensiones = [".txt", ".jpg", ".mp4"]

    for nombre in nombres:
        # Crear carpeta
        folder_metadata = {
            'name': nombre,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder.get('id')

        # Crear archivos dentro
        for i in range(random.randint(1, 5)):
            ext = random.choice(extensiones)
            file_name = f"{nombre.lower()}_{i+1}{ext}"
            media = MediaInMemoryUpload(b"", mimetype="text/plain", resumable=False)  # archivo vacío

            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            drive_service.files().create(body=file_metadata, media_body=media).execute()

    print("✅ Carpetas y archivos creados en Google Drive.")    


@app.route('/generar-drive')
def generar_en_drive():
    crear_carpetas_prueba_en_drive(PARENT_FOLDER_ID)
    return "Carpetas y archivos creados en Drive."

@app.route('/sync-drive')
def registrar_todas_las_carpetas_en_drive():
    drive_service, _ = get_services()
    query = f"'{PARENT_FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    resultado = drive_service.files().list(q=query, fields="files(id, name)").execute()
    nuevas = 0

    for item in resultado.get("files", []):
        nombre = item["name"]
        file_id = item["id"]
        link = f"https://drive.google.com/drive/folders/{file_id}"

        c.execute("SELECT * FROM estudiantes WHERE nombre = ?", (nombre,))
        if not c.fetchone():
            c.execute("INSERT INTO estudiantes (nombre, mail, carpeta) VALUES (?, ?, ?)", (nombre, "", link))
            conn.commit()
            nuevas += 1

    return f"Carpetas agregadas: {nuevas}"






if __name__ == '__main__':
    print("🚀 Servidor Flask iniciado en http://127.0.0.1:5151")
    app.run(debug=True, host='0.0.0.0')
