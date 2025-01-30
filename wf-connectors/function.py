import functions_framework
from google.cloud import storage
import pandas as pd
from googleapiclient.discovery import build
import google.auth
from io import StringIO

@functions_framework.http
def process_csv_to_sheets(request):
    """
    HTTP Cloud Function that processes a CSV file from Cloud Storage 
    and updates a Google Sheet with its contents.
    
    Args:
        request (flask.Request): Contains the request data including:
            - bucket: The name of the Cloud Storage bucket
            - file: The name of the CSV file
            - sheet_id: The ID of the Google Sheet to update
            
    Returns:
        dict: A response indicating success or failure
    """
    # Get request data
    request_json = request.get_json(silent=True)
    
    # Validate required parameters
    if not request_json or 'bucket' not in request_json or 'file' not in request_json or 'sheet_id' not in request_json:
        return {'error': 'Missing required parameters'}, 400
    
    try:
        # Extract parameters from request
        bucket_name = request_json['bucket']
        file_name = request_json['file']
        sheet_id = request_json['sheet_id']
        
        # Initialize Cloud Storage client and get the file
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        
        # Download and read the CSV content
        content = blob.download_as_text()
        
        # Use pandas to parse the CSV
        df = pd.read_csv(StringIO(content))
        
        # Convert DataFrame to list of lists for Google Sheets
        values = [df.columns.values.tolist()] + df.values.tolist()
        
        # Use default authentication instead of service account key
        credentials, project = google.auth.default(scopes=[
            "https://www.googleapis.com/auth/spreadsheets"
        ])
        
        # Initialize Sheets API with default credentials
        sheets_service = build('sheets', 'v4', credentials=credentials)
        
        # Update the spreadsheet
        result = sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='Sheet1',
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        
        return {
            'success': True,
            'message': f'Updated {result.get("updatedCells")} cells in the spreadsheet',
            'details': result
        }
        
    except Exception as e:
        print(f'Error processing file: {str(e)}')
        return {
            'success': False,
            'error': str(e)
        }, 500
