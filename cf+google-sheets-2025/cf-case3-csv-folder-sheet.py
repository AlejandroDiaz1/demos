"""
* IAM roles
Cloud Run Invoker
Eventarc Event Receiver
Storage Admin

* Env var:
EMAIL - EMAIL
FOLDER_ID - FOLDER_ID

* requirements.txt
functions-framework==3.*
google-api-python-client 
google-auth-httplib2 
google-auth-oauthlib
google-auth
google-cloud-storage
    
Cloud storage trigger

Service account creates a new Google Sheets file (from uploaded CSV) and uploads it at the FOLDER_ID location
"""

import functions_framework
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import storage
import os
import csv
import uuid
from io import StringIO

# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def hello_gcs(cloud_event):
    data = cloud_event.data

    event_id = cloud_event["id"]
    event_type = cloud_event["type"]

    bucket_name = data["bucket"]
    file_name = data["name"]

    print(f"Event ID: {event_id}")
    print(f"Event type: {event_type}")
    print(f"Bucket: {bucket_name}")
    print(f"File: {file_name}")

    emailAddress = os.getenv('EMAIL')
    folder_id = os.getenv('FOLDER_ID')  # ID del folder en Google Drive

    try:
        # Autenticación predeterminada de Google Cloud Function
        credentials, _ = google.auth.default(scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
        ])

        # Crear cliente para Google Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)

        # Descargar el contenido del archivo CSV
        csv_content = blob.download_as_text()
        csv_reader = csv.reader(StringIO(csv_content))

        # Convertir el contenido CSV a un formato adecuado para Google Sheets
        values = [row for row in csv_reader]

        # Crear cliente para la API de Google Sheets
        sheets_service = build('sheets', 'v4', credentials=credentials)

        # Crear una nueva hoja de cálculo
        spreadsheet = {
            "properties": {
                "title": f"GoogleSheet-{str(uuid.uuid4())}"
            }
        }
        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet).execute()

        # Obtener el ID del archivo
        sheet_id = spreadsheet.get('spreadsheetId')

        # Agregar datos al Google Sheet
        sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range="Sheet1",  # Nombre de la hoja predeterminada
            valueInputOption="RAW",
            body={"values": values}
        ).execute()

        # Crear cliente para la API de Google Drive
        drive_service = build('drive', 'v3', credentials=credentials)

        # Mover el archivo al folder especificado
        drive_service.files().update(
            fileId=sheet_id,
            addParents=folder_id,
            removeParents="root",  # Quita el archivo de la raíz de Drive
            fields="id, parents"
        ).execute()

        # Compartir el archivo con un usuario específico
        drive_service.permissions().create(
            fileId=sheet_id,
            body={
                "type": "user",
                "role": "writer",
                "emailAddress": emailAddress
            },
            fields="id"
        ).execute()

        doc_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        print(doc_url)
        return f"Google Sheet creado exitosamente con datos del archivo CSV y movido al folder: {doc_url}"

    except HttpError as error:
        return f"Se produjo un error al crear o mover el Google Sheet: {error}"

    except Exception as e:
        return f"Se produjo un error inesperado: {e}"
