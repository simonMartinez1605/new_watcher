import os
from dotenv import load_dotenv
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential
from office365.runtime.client_request_exception import ClientRequestException

load_dotenv(override=True)

sharepoint_url = os.getenv('SHARE_POINT_URL')
username = os.getenv('USER_NAME')
password = os.getenv('PASSWORD')
library_name = os.getenv('LIBRARY_NAME')
list_name = os.getenv('LIST_NAME')

def sharepoint(file_path, file_name, site_name, folder_name:None, metadata_dict):
    """Function to upload file in the new folder"""
    try:
        site_full_url = f"{sharepoint_url}/sites/{site_name}"
        user_credentials = UserCredential(username, password)
        ctx = ClientContext(site_full_url).with_credentials(user_credentials)
        target_list = ctx.web.lists.get_by_title(list_name)
        
        # 1. Verificar o crear la carpeta de destino
        # La forma más robusta es obtener la URL relativa de la carpeta
        target_folder_relative_url = f"/sites/{site_name}/{list_name}/{folder_name}"

        original_folder_name = folder_name
        counter = 0
        unique_folder_name = original_folder_name
        
        try:
            target_folder = ctx.web.get_folder_by_server_relative_url(target_folder_relative_url)
            ctx.load(target_folder)
            ctx.execute_query()
            print(f"✅ Folder '{folder_name}' found.")
        except ClientRequestException as e:
            if "404 Client Error" in str(e):
                while True:
                    # Intentar obtener la carpeta. Si no existe, lanzará una ClientRequestException (404 Not Found).
                    try:
                        # Comprobar si la carpeta ya existe dentro de la root_folder
                        existing_folder = target_list.root_folder.folders.get_by_url(unique_folder_name)
                        ctx.load(existing_folder)
                        ctx.execute_query()
                        
                        # Si llegamos aquí, la carpeta existe, así que incrementamos el contador
                        # y generamos un nuevo nombre.
                        counter += 1
                        unique_folder_name = f"{original_folder_name}_{counter}"
                        print(f"⚠️ Folder '{original_folder_name}' already exists. Trying with '{unique_folder_name}'.")

                    except ClientRequestException as e:
                        # Capturamos específicamente ClientRequestException, que es la que se lanza para 404
                        if "404 Not Found" in str(e):
                            # Si el error es 404, significa que el nombre actual es único.
                            break 
                        else:
                            # Si es otro tipo de ClientRequestException, relanzamos el error.
                            break
                    except Exception as e:
                        # Capturamos cualquier otra excepción inesperada.
                        print(f"Unspect error, review folder: {e}")
                        # raise e # Relanzar para no ocultar el problema
                        
                target_folder = target_list.root_folder.folders.add(unique_folder_name)
                ctx.load(target_folder)
                ctx.execute_query()
                print(f"✅ Folder '{unique_folder_name}' succefully created.")

                # Subir metadatos
                folder_item = target_folder.list_item_all_fields
                ctx.load(folder_item)
                ctx.execute_query()

                for key, value in metadata_dict.items():
                    folder_item.set_property(key, value)
                folder_item.update()
                ctx.execute_query()
                print(f"✅ Metadata succefully update in'{unique_folder_name}' folder")
            else:
                raise e

        # 2. Subir el archivo a la carpeta
        with open(file_path, 'rb') as file_obj:
            file_content = file_obj.read()
        
        uploaded_file = target_folder.upload_file(file_name, file_content)
        ctx.execute_query()
        print(f"✅ File '{file_name}' succefully upload in '{folder_name}'.")

        # 3. Actualizar metadatos del archivo
        # Para evitar el error, primero cargamos el objeto list_item_all_fields
        file_item = uploaded_file.listItemAllFields
        ctx.load(file_item)
        ctx.execute_query()
        
        for key, value in metadata_dict.items():
            if value is not None:
                file_item.set_property(key, value)
        
        file_item.update()
        ctx.execute_query()
        print(f"✅ File metadata '{file_name}' succefully update.")
        
    except FileNotFoundError:
        print(f"❌ Error: File '{file_path}' didn't find.")
    except ClientRequestException as e:
        print(f"❌ Error with SharePoint: {e}")
    except Exception as e:
        print(f"❌ Unspect error: {e}")