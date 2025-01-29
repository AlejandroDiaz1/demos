import functions_framework
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import storage
import os
import csv
import uuid
from io import StringIO


# ------------------------------------------------------------------------ HELPER FUNCTIONs
def step1(bucket_name, file_name):
    # Crear cliente para Google Storage
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    # Descargar el contenido del archivo CSV
    csv_content = blob.download_as_text()
    csv_reader = csv.reader(StringIO(csv_content))

    # Convertir el contenido CSV a un formato adecuado para Google Sheets
    values = [row for row in csv_reader]
    return values


def step2(credentials, unique_id, values):
    # Crear cliente para la API de Google Sheets
    sheets_service = build('sheets', 'v4', credentials=credentials)

    # Crear una nueva hoja de cálculo
    spreadsheet = {
        "properties": {
            "title": f"GoogleSheet-{unique_id}"
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

    return sheet_id


def step3(credentials, email_address, folder_id, sheet_id):
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
            "emailAddress": email_address
        },
        fields="id"
    ).execute()

    doc_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    return doc_url


# ------------------------------------------------------------------------ MAIN FUNCTION
@functions_framework.http
def hello_http(request):
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_args and 'step' in request_args:
        step = request_args['step']
    else:
        return {"error": "step not defined"}, 400
    
    # Autenticación predeterminada de Google Cloud Function
    credentials, _ = google.auth.default(scopes=[
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets"
    ])

    if step == "storage":
        if request_json and 'bucket_name' in request_json and 'file_name' in request_json:
            bucket_name = request_json['bucket_name']
            file_name = request_json['file_name']
        else:
            return {"error": "missing arguments"}, 400

        values = step1(bucket_name, file_name)
        return {"values": values}, 200

    elif step == "sheets":
        if request_json and 'values' in request_json:
            values = request_json['values']
        else:
            return {"error": "missing arguments"}, 400
        sheet_id = step2(credentials, str(uuid.uuid4()), values)
        return {"sheet_id": sheet_id}, 200
    
    elif step == "drive":
        if request_json and 'email_address' in request_json and 'folder_id' in request_json and 'sheet_id' in request_json:
            email_address = request_json['email_address']
            folder_id = request_json['folder_id']
            sheet_id = request_json['sheet_id']
        else:
            return {"error": "missing arguments"}, 400

        doc_url = step3(credentials, email_address, folder_id, sheet_id)
        return {"doc_url": doc_url}, 200
    
    else:
        return {"error": "unknown step"}, 400