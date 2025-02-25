from dotenv import load_dotenv 
from services.index import indexing 
import smbclient
import os
import time 
import random 

load_dotenv() 

smbclient.ClientConfig(username=os.getenv('SERVER_USER'), password=os.getenv('SERVER_PASSWORD')) 

share_folder = r"\\10.1.10.178\Scanning"  

def wait_doc(pdf_path, time_out, attempts): 
    for _ in range(attempts): 
        last_size = os.path.getsize(pdf_path)
        time.sleep(time_out)
        updated_size = os.path.getsize(pdf_path)
        if last_size == updated_size: 
            return True
    return False


def new_folder(): 

    global share_folder

    actual_folder = set(smbclient.listdir(share_folder))
    validate = wait_doc(share_folder, 2, 5)
    if validate == True:
        for doc in actual_folder: 
            if doc.lower().endswith(".pdf"): 
                share_folder = share_folder.replace("\\", "/") 
                doc = f"{share_folder}/{doc}" 
                print(f"New doc find: {doc}") 
                print("Indexing document") 
                indexing(doc) 
                os.rename(doc, rf"{share_folder}\Done\{random.randint(1,10000)}.pdf") 

try: 
    while True: 
        new_folder()
        time.sleep(2)
except KeyboardInterrupt:
        print("Stop Folder Monitoring")