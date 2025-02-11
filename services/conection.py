import msal
import requests
import os
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
tenant_id = os.getenv('TENANT_ID')
authority = f"https://login.microsoftonline.com/{tenant_id}"
scope = ["https://graph.microsoft.com/.default"]

print(client_id, client_secret, tenant_id)  

#Conexion con el sharepoint para obtener los Alien number 
app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
result = app.acquire_token_for_client(scopes=scope)
#Autentificacion de los tokens de acceso 
if "access_token" in result:
    access_token = result["access_token"]
    print(access_token) 
    # print("Access token:", access_token)
    site_url = "https://graph.microsoft.com/v1.0/sites/taylorleelaw.sharepoint.com:/sites/prueba"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    response = requests.get(site_url, headers=headers)
    print(response)
    if response.status_code == 200:
        data = response.json()
        print(f"Site title: {data['displayName']}")
        
        # Example: Get list items
        list_title = "Your List Name"
        list_url = f"{site_url}/lists/{list_title}/items"
        list_response = requests.get(list_url, headers=headers)
        if list_response.status_code == 200:
            list_data = list_response.json()
            for item in list_data['value']:
                print(f"Item ID: {item['id']}, Title: {item['fields']['Title']}")
        else:
            print(f"Failed to get list items: {list_response.status_code} - {list_response.text}")
    else:
        print(f"Failed to connect: {response.status_code} - {response.text}")
else:
    print("Failed to obtain access token")

