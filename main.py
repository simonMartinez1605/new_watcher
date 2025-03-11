from dotenv import load_dotenv
from services.index import indexing
from rich.console import Console
import smbclient
import os
import time
import random
import threading

load_dotenv()

path_share_folder = os.getenv('PATH_SHARE_FOLDER')

console = Console()

# Configuración de la conexión a la carpeta compartida dentro del servidor
smbclient.ClientConfig(username=os.getenv('SERVER_USER'), password=os.getenv('SERVER_PASSWORD'))

# Carpetas a monitorear dentro del servidor
folders_to_monitor = [
    rf"\\{path_share_folder}\42BReceipts",
    rf"\\{path_share_folder}\Criminal",
]

# Función para esperar a que el documento se haya guardado completamente
def wait_doc(pdf_path, time_out, attempts):
    for _ in range(attempts):
        last_size = os.path.getsize(pdf_path)
        time.sleep(time_out)
        updated_size = os.path.getsize(pdf_path)
        if last_size == updated_size:
            return True

    return False

# Función para monitorear las carpetas
def monitor_folder(folder):
    print(f"Monitoring folder: {folder}")
    #Desglose de la ruta de la carpeta para obtener el nombre de la carpeta
    processed_path = f"{folder}\Process"
    option = folder.split("\\")[-1] #Con respecto a esta variable hay que tener en cuenta que el sharepoint en el que va a guardar la informacion debe tener el mismo nombre que la carpeta 
    while True:
        try:
            #Obtención de los documentos en la carpeta
            acutal_folder = set(smbclient.listdir(folder))
            #Iteración sobre los documentos en la carpeta
            for doc in acutal_folder:
                if doc.lower().endswith('.pdf'):
                    doc_path = "{}/{}".format(folder.replace("\\", "/"), doc)

                    if wait_doc(doc_path, 5, 5):
                        print(f"New doc found in: {folder}")
                        #Uso de spinner para simular proceso de indexado
                        with console.status("[bold green]Indexing document...[/bold green]", spinner="dots12"):
                            for _ in range(10):
                                time.sleep(0.5)
                        indexing(doc_path, option, folder, processed_path)
                        #Llamado a la función de indexacion
                        print("Document indexed!")
                        #Movimiento del documento a la carpeta Done dentro del servidor
                        os.rename(doc_path, fr"{folder}\Done\{random.randint(1,10000)}.pdf")
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")

#Manejo de hilos para monitorear las carpetas
threads = []

#Iteración sobre las carpetas a monitorear
for folder in folders_to_monitor:
    thread = threading.Thread(target=monitor_folder, args=(folder,))
    thread.daemon = True
    thread.start()
    threads.append(thread)


if __name__=="__main__":
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")