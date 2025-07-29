import os
import json
import requests
from shareplum import Site
from dotenv import load_dotenv
from shareplum import Office365
from shareplum.site import Version
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential

load_dotenv(override=True)

sharepoint_url = os.getenv('SHARE_POINT_URL')
username = os.getenv('USER_NAME')
password = os.getenv('PASSWORD')
library_name = os.getenv('LIBRARY_NAME')
list_name = os.getenv('LIST_NAME')

def get_request_digest(site_name, authcookie) -> str:
    """Función para obtener el X-RequestDigest"""
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
    return None

def get_list_item_type(list_name, site_name,authcookie)-> str:
    """Function to get the sharepoint list type"""
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
    return None

def get_file_id(list_name, file_name, site_name, folder_name:None, authcookie) -> str:
    """
    Get ID of the recently doc upload.
    """
    # Consulta la lista/biblioteca para obtener el ID del archivo dentro de la carpeta
    # The FileDirRef includes the library name, e.g., '/sites/mysite/Shared Documents/MyFolder'
    relative_folder_path = f"/{library_name}/{folder_name}" #Cuando se cree una carpeta
    # relative_folder_path = f"/{library_name}"
    url = f"{sharepoint_url}/sites/{site_name}/_api/web/lists/getbytitle('{list_name}')/items"
    params = {
        "$filter": f"FileLeafRef eq '{file_name}' and FileDirRef eq '/sites/{site_name}{relative_folder_path}'",
        "$select": "Id"
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
                return data["d"]["results"][0]["Id"]
            else:
                print(f"❌ No se encontró el archivo '{file_name}' en la carpeta '{folder_name}'.")
                return None
        else:
            print(f"❌ Error al obtener el ID del archivo: {response.text}")
            return None
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    return None

def create_sharepoint_folder(site_name, folder_name, metadata) -> bool:
    """
    Create folder in sharepoint and upload metadata
    """
    try:
        site_sharepoint_url = f"{sharepoint_url}/sites/{site_name}"
        user_credentials = UserCredential(username, password)
        ctx = ClientContext(site_sharepoint_url).with_credentials(user_credentials)

        target_list = ctx.web.lists.get_by_title(list_name)
        ctx.load(target_list)
        ctx.execute_query()

        target_folder = target_list.root_folder.folders.add(folder_name)
        ctx.load(target_folder)
        ctx.execute_query()
        print(f"✅ Folder '{folder_name}' succefully created.")

        folder_item = target_folder.list_item_all_fields
        ctx.load(folder_item)
        ctx.execute_query()

        for key, value in metadata.items():
            folder_item.set_property(key, value)
        folder_item.update()
        ctx.execute_query()
        print(f"✅ Metadata succefully update in'{folder_name}' folder")
        return True
    except Exception as e: 
        print(f"Error to create or upload metadata in folder: {folder_name}: {e}")
        return False

def sharepoint(file_path, file_name, site_name, folder_name:None, metadata_dict):
    """Function to upload file in the new folder"""
    # Authentificacion a SharePoint
    authcookie = Office365(sharepoint_url, username=username, password=password).GetCookies()
    site = Site(f"{sharepoint_url}/sites/{site_name}", version=Version.v365, authcookie=authcookie)

    #📂 1. Crear el folder (usando la nueva función)
    folder_created_or_exists = create_sharepoint_folder(site_name, folder_name, metadata_dict)
    if not folder_created_or_exists:
        print(f"❌ Didn't create '{folder_name}' folder.")
        return

    # 📂 2. Subir el archivo dentro del nuevo folder
    # The target folder path for upload needs to include the library and the subfolder
    target_folder_path_for_upload = f"{library_name}/{folder_name}" #Cuando se cree una carpeta
    # target_folder_path_for_upload = f"{library_name}"

    target_folder = site.Folder(target_folder_path_for_upload)

    try:
        with open(file_path, "rb") as file:
            target_folder.upload_file(file.read(), file_name)
        print(f"✅ Document '{file_name}' uploaded successfully to '{target_folder_path_for_upload}'.")
    except Exception as e:
        print(f"❌ Error uploading file '{file_name}' to '{target_folder_path_for_upload}': {e}")
        return

    # 📄 3. Obtener el Request Digest (ya se hizo en create_sharepoint_folder, pero lo necesitamos para update)
    digest = get_request_digest(site_name, authcookie)
    if not digest:
        print(f"❌ Didn't get the RequestDigest to upload metadata folder ")
        return

    # 🛠️ 4. Obtener el tipo de entidad de la lista
    item_type = get_list_item_type(list_name, site_name, authcookie)
    if not item_type:
        print("❌ Didn't get entity type.")
        return

    # 🔍 5. Obtener el file_id dinámicamente, buscando dentro del folder
    file_id = get_file_id(list_name, file_name, site_name, folder_name, authcookie)
    if not file_id:
        print("❌ Didn't get ID to upload metadata.")
        return

    # 6. Actualizar metadatos del archivo
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
    }

    for key, value in metadata_dict.items():
        if value is not None:
            metadata.update({key: value})
    
    try:
        response = requests.post(update_url, data=json.dumps(metadata), cookies=authcookie, headers=headers)
        response.raise_for_status()
        if response.status_code in [200, 204]:
            print(f"✅ Succefully upload metadata '{file_name}'.")
        else:
            print(f"❌ Error to upload metadata: {response.text}")


    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as e:
        print(f"An unexpected error occurred during metadata update: {e}")