from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

# Path to your service account key file
SERVICE_ACCOUNT_FILE = 'irtekaa-website-73f9eb120957.json'

# Scopes required for Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

# Authenticate with service account
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Build the Google Drive API client
drive_service = build('drive', 'v3', credentials=credentials)

def upload_file_to_drive(file_path, folder_id):
    # Specify the file metadata
    file_metadata = {
        'name': file_path.split('/')[-1],  # File name
        'parents': [folder_id]            # Folder ID
    }
    
    # Specify the media to upload
    media = MediaFileUpload(file_path, resumable=True)
    
    # Upload the file
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"File uploaded with ID: {file.get('id')}")

# Example usage
upload_file_to_drive('path/to/your/file.jpg', 'your-folder-id')
