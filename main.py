import os
import io
import time
import datetime
import sqlite3
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template_string, Response
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaInMemoryUpload
from utils import get_services
from dateutil import parser as date_parser
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


# Función para gestionar reintentos exponenciales
def reintento_exponencial(request_func, *args, **kwargs):
    retries = 5
    backoff = 1  # Tiempo inicial de espera en segundos
    max_backoff = 64  # Máximo tiempo de espera entre reintentos

    for attempt in range(retries):
        try:
            return request_func(*args, **kwargs)
        except HttpError as err:
            if err.resp.status == 403 or err.resp.status == 429:  # Si hay un error por límite de solicitudes
                wait_time = min(backoff * (2 ** attempt), max_backoff)
                print(f"❌ Error {err.resp.status}: Intento {attempt + 1} - esperando {wait_time} segundos.")
                time.sleep(wait_time + random.randint(1, 5))  # Esperar tiempo exponencial más algo aleatorio
            else:
                raise
    raise Exception("Se alcanzó el número máximo de intentos")

def actualizar_link_en_hoja(sheet, row_index, link):
    """ Actualiza el link en la columna 'link' para el estudiante en la hoja base. """
    try:
        sheet.update_cell(row_index, 3, link)  # Columna 'C' es la 3
        print(f"✅ Enlace actualizado en la fila {row_index}: {link}")
    except Exception as e:
        print(f"❌ Error al actualizar el link en la fila {row_index}: {e}")


# Función para enviar correo electrónico con el enlace de la carpeta
def enviar_email(destinatario, nombre, link):
    try:
        # Configuración del servidor de correo
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login('tucorreo@gmail.com', 'tucontraseña')  # Cambiar por tus datos

        # Crear el mensaje
        mensaje = MIMEMultipart()
        mensaje['From'] = 'tucorreo@gmail.com'  # Cambiar por tu email
        mensaje['To'] = destinatario
        mensaje['Subject'] = f"Tu carpeta de {nombre} en Drive"
        cuerpo = f"Hola {nombre},\n\nAquí tienes el enlace a tu carpeta en Google Drive:\n{link}\n\nSaludos."
        mensaje.attach(MIMEText(cuerpo, 'plain'))

        # Enviar el correo
        servidor.sendmail('tucorreo@gmail.com', destinatario, mensaje.as_string())  # Cambiar por tu email
        servidor.quit()
        print(f"✅ Correo enviado a {destinatario}")
    except Exception as e:
        print(f"❌ Error al enviar correo a {destinatario}: {e}")


# Función para crear las carpetas y compartir el enlace
def crear_carpeta_y_compartir(nombre, mail, parent_folder_id):
    drive_service, _ = get_services()

    try:
        query = f"'{parent_folder_id}' in parents and name = '{nombre}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        resultados = drive_service.files().list(q=query, fields='files(id, name)').execute()
        archivos = resultados.get('files', [])

        if archivos:
            print(f"🔁 Carpeta ya existente: {nombre}. Se omite la creación e indexación.")
            return ""

        folder_metadata = {
            'name': nombre,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder.get('id')
        link = f"https://drive.google.com/drive/folders/{folder_id}"
        print(f"✅ Carpeta creada: {nombre} → {link}")
    except Exception as e:
        print(f"❌ Error al crear/verificar carpeta para {nombre}: {e}")
        return ""

    try:
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': mail
        }
        drive_service.permissions().create(fileId=folder_id, body=permission).execute()
        print(f"✅ Permisos asignados a {mail}")
    except Exception as e:
        print(f"❌Error al otorgar permisos. Procesa manualmente o intente nuevamente más tarde.{mail}: {e}")

    return link


@app.route('/')
def index():
    print("📡 Iniciando procesamiento de hoja...")
    try:
        _, gc = get_services()
        sheet = gc.open_by_url(SHEET_URL).sheet1
        data = sheet.get_all_records(expected_headers=["nombre", "mail", "link"])

        if not data:
            print("⚠️ No se encontraron datos en la hoja.")
            return "No se encontraron datos en la hoja."

        creados = 0

        for row_index, row in enumerate(data, start=2):
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
            if not link:
                continue

            actualizar_link_en_hoja(sheet, row_index, link)
            c.execute("INSERT INTO estudiantes (nombre, mail, carpeta) VALUES (?, ?, ?)", (nombre, mail, link))
            conn.commit()
            print(f"✅ Enlace indexado para {nombre}")

            creados += 1

        return f"Proceso finalizado. Carpetas nuevas: {creados}"

    except Exception as e:
        print(f"❌ Error: {e}")
        return f"Ocurrió un error: {e}"



@app.route('/enviar-emails')
def enviar_emails():
    try:
        conn = sqlite3.connect('database.db', check_same_thread=False)
        c = conn.cursor()
        registros = c.execute("SELECT nombre, mail, carpeta FROM estudiantes").fetchall()
        
        for nombre, mail, link in registros:
            enviar_email(mail, nombre, link)
        
        return "Correos enviados con éxito."

    except Exception as e:
        print(f"❌ Error al enviar correos: {e}")
        return f"❌ Error: {e}"


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
                resultado = reintento_exponencial(drive_service.files().list, q=query, fields="files(id, name, mimeType, modifiedTime)")

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



@app.route('/mostrar-datos')
def mostrar_datos():
    try:
        conn = sqlite3.connect('database.db', check_same_thread=False)
        c = conn.cursor()

        # Seleccionar todos los registros
        c.execute("SELECT nombre, mail, carpeta FROM estudiantes")
        registros = c.fetchall()

        # Renderizar HTML con numeración
        return render_template_string("""
            <h2>📋 Lista de Estudiantes</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Nombre</th>
                        <th>Correo</th>
                        <th>Carpeta</th>
                    </tr>
                </thead>
                <tbody>
                    {% for registro in registros %}
                        <tr>
                            <td>{{ loop.index }}</td>
                            <td>{{ registro[0] }}</td>
                            <td>{{ registro[1] }}</td>
                            <td><a href="{{ registro[2] }}" target="_blank">Ver carpeta</a></td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        """, registros=registros)
    
    except Exception as e:
        return f"<p>Error al mostrar los datos: {e}</p>"


# Función de purga de la base de datos
@app.route('/purgar-database')
def purgar_db():
    c.execute("DELETE FROM estudiantes")
    conn.commit()
    print("✅ Base de datos purgada")
    return "Base de datos purgada exitosamente."


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
