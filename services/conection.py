from shareplum import Site
from shareplum import Office365
from shareplum.site import Version
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Variables de entorno
sharepoint_url = os.getenv('SHARE_POINT_URL')
username = os.getenv('USER_NAME')
password =  os.getenv('PASSWORD')
library_name = os.getenv('LIBRARY_NAME')
list_name = os.getenv('LIST_NAME')

# Función para obtener el X-RequestDigest
def get_request_digest(site_name, authcookie) -> str:
    url = f"{sharepoint_url}/sites/{site_name}/_api/contextinfo"
    headers = {
        "Accept": "application/json;odata=verbose",
        "Content-Type": "application/json;odata=verbose"
    }
    try:
        response = requests.post(url, cookies=authcookie, headers=headers)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()["d"]["GetContextWebInformation"]["FormDigestValue"]
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    
# Función para obtener el tipo de entidad de una lista de SharePoint
def get_list_item_type(list_name, site_name,authcookie)-> str:
    url = f"{sharepoint_url}/sites/{site_name}/_api/web/lists/getbytitle('{list_name}')"
    headers = {
        "Accept": "application/json;odata=verbose",
        "Content-Type": "application/json;odata=verbose"
    }
    try :
        response = requests.get(url, cookies=authcookie, headers=headers)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()["d"]["ListItemEntityTypeFullName"]
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")

# Función para obtener el ID de un archivo recién subido
def get_file_id(list_name, file_name, site_name,authcookie) -> str:
    """
    Obtiene el ID del archivo recién subido.
    """
    # Consulta la lista/biblioteca para obtener el ID del archivo
    url = f"{sharepoint_url}/sites/{site_name}/_api/web/lists/getbytitle('{list_name}')/items"
    params = {
        "$filter": f"FileLeafRef eq '{file_name}'",  # Filtra por el nombre del archivo
        "$select": "Id"  # Solo obtén el campo ID
    }
    headers = {
        "Accept": "application/json;odata=verbose",
        "Content-Type": "application/json;odata=verbose"
    }
    try: 
        response = requests.get(url, params=params, cookies=authcookie, headers=headers)
        response.raise_for_status()
        if response.status_code == 200:
            data = response.json()
            if data["d"]["results"]:
                return data["d"]["results"][0]["Id"]  # Devuelve el ID del primer resultado
            else:
                print("❌ No se encontró el archivo en la lista/biblioteca.")
                return None
        else:
            print(f"❌ Error al obtener el ID del archivo: {response.text}")
            return None
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    
# Función para subir archivo y actualizar metadatos
def sharepoint(file_path, file_name, alien_number, site_name, case_type):

    # Authentificacion a SharePoint
    authcookie = Office365(sharepoint_url, username=username, password=password).GetCookies()
    site = Site(f"{sharepoint_url}/sites/{site_name}", version=Version.v365, authcookie=authcookie)

    # 📂 1. Subir el archivo
    folder = site.Folder(library_name)
    with open(file_path, "rb") as file:
        folder.upload_file(file.read(), file_name)
    print("✅ Documents uploaded successfully.")

    # 📄 2. Obtener el Request Digest
    digest = get_request_digest(site_name,authcookie)
    if not digest:
        print("❌Cant get RequestDigest.")
        return

    # 🛠️ 3. Obtener el tipo de entidad de la lista
    item_type = get_list_item_type(list_name, site_name,authcookie)
    if not item_type:
        print("❌ cant get the entity type.")
        return

    # 🔍 4. Obtener el file_id dinámicamente
    file_id = get_file_id(list_name, file_name, site_name, authcookie)
    if not file_id:
        print("❌ No se pudo obtener el ID del archivo.")
        return

    update_url = f"{sharepoint_url}/sites/{site_name}/_api/web/lists/getbytitle('{list_name}')/items({file_id})"

    headers = {
        "Accept": "application/json;odata=verbose",
        "Content-Type": "application/json;odata=verbose",
        "X-RequestDigest": digest,
        "IF-MATCH": "*",
        "X-HTTP-Method": "MERGE"
    }

    metadata = {
        "__metadata": {"type": item_type},
        "AlienNumber": alien_number, 
        "CaseType":case_type
    }
    try: 
        response = requests.post(update_url, data=json.dumps(metadata), cookies=authcookie, headers=headers)
        response.raise_for_status()
        if response.status_code in [200, 204]:
            print(f"✅ Metadata upload successfully.")
        else:
            print(f"❌ Error to upload metadata: {response.text}")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")

if __name__ == "__main__":
    doc = "c:/Users/SimonMartinez/Documents/Simon/View Folder/OCR/Done/review.pdf"
    sharepoint(doc, "archivo.pdf", "245-282-251")
    get_request_digest("Shared Documents")
    get_list_item_type("Documents", "Shared Documents")
    get_file_id("Documents", "archivo.pdf", "Shared Documents")