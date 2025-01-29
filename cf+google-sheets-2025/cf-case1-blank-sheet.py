"""
* IAM roles
Cloud Run Invoker

* Env var:
EMAIL - EMAIL

requirements.txt
functions-framework==3.*
google-api-python-client 
google-auth-httplib2 
google-auth-oauthlib
google-auth
    
HTTPS trigger

Service account creates a new blank Google Sheets file and shares it with EMAIL
"""

import functions_framework
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import uuid

@functions_framework.http
def hello_http(request):
    emailAddress = os.getenv('EMAIL')
    print(emailAddress)

    try:
        # Autenticación predeterminada de Google Cloud Function
        credentials, _ = google.auth.default(scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
        ])

        # Crear cliente para la API de Google Sheets
        sheets_service = build('sheets', 'v4', credentials=credentials)

        # Crear hoja en blanco
        spreadsheet = {
            "properties": {
                "title": f"GoogleSheet-{str(uuid.uuid4())}"
            }
        }
        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet).execute()

        # Obtener el ID del archivo
        sheet_id = spreadsheet.get('spreadsheetId')

        # Crear cliente para la API de Google Drive
        drive_service = build('drive', 'v3', credentials=credentials)

        # Mover el archivo a tu espacio de Google Drive
        drive_service.permissions().create(
            fileId=sheet_id,
            body={
                "type": "user",
                "role": "writer",
                "emailAddress": emailAddress
            },
            fields="id"
        ).execute()

        return f"Google Sheet creado exitosamente: https://docs.google.com/spreadsheets/d/{sheet_id}"

    except HttpError as error:
        return f"Se produjo un error al crear el Google Sheet: {error}"