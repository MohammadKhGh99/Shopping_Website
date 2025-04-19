import io, json

from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Path to your JSON key file
SERVICE_ACCOUNT_FILE = "irtekaa-website-73f9eb120957.json"

# Define the required scopes
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Authenticate using the service account
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Build the Drive API client
service = build("drive", "v3", credentials=credentials)

# def list_drive_files():
#     results = service.files().list(
#         pageSize=100, fields="files(id, name, mimeType)"
#     ).execute()
    
#     files = results.get("files", [])
#     if not files:
#         print("No files found.")
#     else:
#         print("Files and Folders in Drive:")
#         for file in files:
#             file_type = "Folder" if file["mimeType"] == "application/vnd.google-apps.folder" else "File"
#             print(f"{file['name']} ({file_type}) - ID: {file['id']}")

# def get_file_by_path(path, root_folder_id="root"):
#     """
#     Get a file or folder in Google Drive by its path.

#     Args:
#         path (str): The file path (e.g., "folder1/subfolder2/file.txt").
#         root_folder_id (str): The ID of the root folder to start from (default is "root").

#     Returns:
#         dict: The file metadata if found, or None if not found.
#     """
#     # Split the path into components
#     path_parts = path.strip("/").split("/")
#     current_folder_id = root_folder_id

#     try:
#         for part in path_parts:
#             # Query for the current part (folder or file) in the current folder
#             query = f"'{current_folder_id}' in parents and name = '{part}' and trashed = false"
#             results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
#             files = results.get("files", [])

#             if not files:
#                 print(f"'{part}' not found in folder ID: {current_folder_id}")
#                 return None

#             # Assume the first match is the correct one (Google Drive allows duplicate names)
#             current_file = files[0]
#             current_folder_id = current_file["id"]

#         return current_file  # Return the final file or folder metadata
#     except Exception as e:
#         print(f"Error while retrieving file by path: {e}")
#         return None


# Example usage
# file_path = "images/books/9/product1.png"  # Replace with your file path
# irtekaa_website_folder_id = "1xoAmZPgTGkacrCdpa4_gFaON-h6rfqKG"  # Replace with your folder ID
# file_metadata = get_file_by_path(file_path, irtekaa_website_folder_id)

# if file_metadata:
#     print(f"{file_metadata['name']}")
# else:
#     print("File not found.")



# # Function to download a file from Google Drive
# def download_file(file_id, destination_path):
#     """
#     Download a file from Google Drive.

#     Args:
#         file_id (str): The ID of the file to download.
#         destination_path (str): The local path where the file will be saved.

#     Returns:
#         None
#     """
#     try:
#         request = service.files().get_media(fileId=file_id)
#         with io.FileIO(destination_path, 'wb') as file:
#             downloader = MediaIoBaseDownload(file, request)
#             done = False
#             while not done:
#                 status, done = downloader.next_chunk()
#                 print(f"Download progress: {int(status.progress() * 100)}%")
#         print(f"File downloaded successfully to {destination_path}")
#     except Exception as e:
#         print(f"Error downloading file: {e}")

# # Example usage
# file_path = "images/books/9/product1.png"  # Replace with your file path
# root_folder_id = "1xoAmZPgTGkacrCdpa4_gFaON-h6rfqKG"  # Replace with your root folder ID

# # Get the file metadata
# file_metadata = get_file_by_path(file_path, root_folder_id)

# if file_metadata:
#     print(f"File found: {file_metadata['name']} (ID: {file_metadata['id']})")
#     # Download the file
#     destination = f"./{file_metadata['name']}"  # Save the file in the current directory
#     download_file(file_metadata['id'], destination)
# else:
#     print("File not found.")


# def get_file_link(file_id):
#     """
#     Get the shareable link of a file in Google Drive.

#     Args:
#         file_id (str): The ID of the file.

#     Returns:
#         str: The webViewLink (viewable link) or webContentLink (downloadable link).
#     """
#     try:
#         # Retrieve the file metadata, including the webViewLink and webContentLink
#         file = service.files().get(fileId=file_id, fields="webViewLink, webContentLink").execute()
#         web_view_link = file.get("webViewLink")  # Link to view the file in Google Drive
#         web_content_link = file.get("webContentLink")  # Direct download link

#         if web_view_link:
#             print(f"Web View Link: {web_view_link}")
#             return web_view_link
#         elif web_content_link:
#             print(f"Web Content Link: {web_content_link}")
#             return web_content_link
#         else:
#             print("No link available for this file.")
#             return None
#     except Exception as e:
#         print(f"Error retrieving file link: {e}")
#         return None


# Example usage
# file_path = "images/books/9/product1.png"  # Replace with your file path
# root_folder_id = "1xoAmZPgTGkacrCdpa4_gFaON-h6rfqKG"  # Replace with your root folder ID

# # Get the file metadata
# file_metadata = get_file_by_path(file_path, root_folder_id)

# if file_metadata:
#     print(f"File found: {file_metadata['name']} (ID: {file_metadata['id']})")
#     # Get the file's link
#     file_link = get_file_link(file_metadata['id'])
#     if file_link:
#         print(f"File Link: {file_link}")
# else:
#     print("File not found.")

# Run the function
# list_drive_files()


def get_file_link(file_id):
    """
    Get the shareable link of a file in Google Drive.

    Args:
        file_id (str): The ID of the file.

    Returns:
        str: The webViewLink (viewable link) or webContentLink (downloadable link).
    """
    try:
        file = service.files().get(fileId=file_id, fields="webViewLink, webContentLink").execute()
        return file.get("webViewLink") or file.get("webContentLink")
    except Exception as e:
        print(f"Error retrieving file link for file ID {file_id}: {e}")
        return None
    

def traverse_drive(folder_id, parent_path=""):
    """
    Recursively traverse Google Drive folders and retrieve image links.

    Args:
        folder_id (str): The ID of the folder to start from.
        parent_path (str): The path of the current folder (used for recursion).

    Returns:
        dict: A dictionary containing folder structure and image links.
    """
    result = {}
    try:
        # List all files and folders in the current folder
        query = f"'{folder_id}' in parents and trashed = false"
        items = service.files().list(q=query, fields="files(id, name, mimeType)").execute().get("files", [])

        for item in items:
            if item["mimeType"] == "application/vnd.google-apps.folder":
                # If the item is a folder, recursively traverse it
                subfolder_path = item["name"]  # f"{parent_path}/{item['name']}" if parent_path else 
                result[subfolder_path] = traverse_drive(item["id"], subfolder_path)
            elif item["mimeType"].startswith("image/"):
                # If the item is an image, get its link
                file_link = get_file_link(item["id"])
                if parent_path not in result:
                    result[parent_path] = []
                result[parent_path].append({"name": item["name"], "link": file_link})
    except Exception as e:
        print(f"Error traversing folder ID {folder_id}: {e}")
    return result


def save_to_json(data, output_file):
    """
    Save the data to a JSON file.

    Args:
        data (dict): The data to save.
        output_file (str): The path to the output JSON file.
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Data saved to {output_file}")
    except Exception as e:
        print(f"Error saving data to JSON file: {e}")


def upload_file_to_drive(file_path, product_folder_name, root_folder_id, product_id):
    """
    Upload a file to a specific folder in Google Drive. Create a folder for the product if it doesn't exist.

    Args:
        file_path (str): The local path to the file to upload.
        product_folder_name (str): The name of the parent folder (e.g., "books", "clothes").
        root_folder_id (str): The ID of the root folder in Google Drive.
        product_id (str): The ID of the product (used as the folder name for the product).

    Returns:
        dict: The metadata of the uploaded file, including its webViewLink.
    """
    try:
        # Check if the parent folder (e.g., "books") exists
        query = f"'{root_folder_id}' in parents and name = '{product_folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(q=query, fields="files(id)").execute()
        parent_folder = results.get("files", [])

        if not parent_folder:
            raise Exception(f"Parent folder '{product_folder_name}' does not exist in Google Drive.")

        parent_folder_id = parent_folder[0]["id"]

        # Check if the product folder exists
        query = f"'{parent_folder_id}' in parents and name = '{product_id}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(q=query, fields="files(id)").execute()
        product_folder = results.get("files", [])

        # If the product folder does not exist, create it
        if not product_folder:
            folder_metadata = {
                "name": product_id,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_folder_id]
            }
            product_folder = service.files().create(body=folder_metadata, fields="id").execute()
            product_folder_id = product_folder["id"]
        else:
            product_folder_id = product_folder[0]["id"]

        # Upload the file to the product folder
        file_name = file_path.split("/")[-1]
        file_metadata = {
            "name": file_name,
            "parents": [product_folder_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink"
        ).execute()

        print(f"File '{uploaded_file['name']}' uploaded successfully to folder '{product_id}'.")
        return uploaded_file
    except Exception as e:
        print(f"Error uploading file to Google Drive: {e}")
        return None


# if __name__ == "__main__":
#     root_folder_id = "1k5rB_WljD_v9ExgMx4ASvy4o7VNvnm6R"
#     output_json_file = "drive_image_links.json"

#     # Traverse the Google Drive folder structure
#     drive_data = traverse_drive(root_folder_id)

#     # Save the results to a JSON file
#     save_to_json(drive_data, output_json_file)