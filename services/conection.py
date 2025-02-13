import msal
import requests
import os
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
tenant_id = os.getenv('TENANT_ID')
drive_id = os.getenv('DRIVER_ID') 
authority = f"https://login.microsoftonline.com/{tenant_id}"
scope = ["https://graph.microsoft.com/.default"]

# Conexión con el SharePoint para obtener los Alien number
app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
result = app.acquire_token_for_client(scopes=scope)

# Autenticación de los tokens de acceso

def get_drive_id(): 
    if "access_token" in result:
        access_token = result["access_token"]
        site_url = "https://graph.microsoft.com/v1.0/sites/taylorleelaw.sharepoint.com:/sites/prueba"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        response = requests.get(site_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            print(data)
            print(f"Site title: {data['displayName']}")

            # Obtener documentos de una biblioteca de documentos
            drive_url = f"https://graph.microsoft.com/v1.0/sites/{data['id']}/pages"
            drive_response = requests.get(drive_url, headers=headers)
            if drive_response.status_code == 200:
                drives = drive_response.json()
                for drive in drives:
                    print(drive) 
                    return drive['id']
            else:
                print(f"Failed to get drives: {drive_response.status_code} - {drive_response.text}")
        else:
            print(f"Failed to connect: {response.status_code} - {response.text}")
    else:
        print("Failed to obtain access token")


def upload_file_to_sharepoint(local_file_path, file_name, alien_number):
    try: 
    
        if "access_token" in result:
            access_token = result["access_token"]
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            # URL de la biblioteca de documentos donde se creará el archivo
            items_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"

            # Datos del archivo a crear
            file_data = {
                "@microsoft.graph.conflictBehavior": "rename",  # Renombrar el archivo si ya existe
                "name": file_name, # Nombre del archivo
                "file": {}
            }
            # Crear el archivo
            create_response = requests.post(items_url, headers=headers, json=file_data)
            if create_response.status_code == 201:
                item_id = create_response.json().get("id")  # Obtener el ID del archivo creado
                upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"
                with open(local_file_path, 'rb') as file:
                    #Actualizar el archivo creado anteriormente 
                    file_content = file.read()
                    headers["Content-Type"] = "application/pdf"
                    upload_response = requests.put(upload_url, headers=headers, data=file_content)
                    if upload_response.status_code == 200 or upload_response.status_code == 201:
                        print(f"File '{file_name}' uploaded successfully.")
                    else:
                        print(f"Failed to upload file content: {upload_response.status_code} - {upload_response.text}")
            else:   
                print(f"Failed to create file: {create_response.status_code} - {create_response.text}")
        else:
            print("Failed to obtain access token")
    except Exception as e: 
        print(f"Error for upload file to sharepoint: {e}")


# Ruta del archivo local y nombre del archivo en SharePoint
local_file_path = "c:/Users/SimonMartinez/Documents/Simon/View Folder/OCR/Done/TORRES SUAREZ, ROXANA VANESSA.pdf" 
file_name = "simon.pdf"

if __name__=="__main__": 

    upload_file_to_sharepoint(local_file_path, file_name, "213135161") 
    # get_drive_id()