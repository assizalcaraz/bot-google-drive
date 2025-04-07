import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
]

def get_services():
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    gc = gspread.authorize(creds)
    return drive_service, gc

def crear_carpeta_y_compartir(nombre, mail, parent_folder_id):
    drive_service, _ = get_services()

    # Crear subcarpeta
    folder_metadata = {
        'name': nombre,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
    folder_id = folder.get('id')

    # Compartir con permisos de escritura
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': mail
    }
    drive_service.permissions().create(
        fileId=folder_id,
        body=permission,
        fields='id',
        sendNotificationEmail=False
    ).execute()

    # Devolver el link
    return f"https://drive.google.com/drive/folders/{folder_id}"
