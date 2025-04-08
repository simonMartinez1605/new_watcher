from dotenv import load_dotenv
from services.index import indexing
from rich.console import Console
from pathlib import Path
from testing.test_QA import QAWindow, QApplication
import smbclient
import os
import time
import uuid
import threading
import logging
import sys

load_dotenv()

path_share_folder = os.getenv('PATH_SHARE_FOLDER')

console = Console()

# Configuración de la conexión a la carpeta compartida dentro del servidor
smbclient.ClientConfig(username=os.getenv('SERVER_USER'), password=os.getenv('SERVER_PASSWORD'))

# Carpetas a monitorear dentro del servidor
folders_to_monitor = [
    rf"\\{path_share_folder}\42BReceipts",
    rf"\\{path_share_folder}\Criminal",
    rf"\\{path_share_folder}\Asylum"
]

def wait_doc(pdf_path : str, timeout : int, attempts : int) -> bool:
    """Función para esperar a que el documento se haya guardado completamente"""

    for _ in range(attempts):
        last_size = os.path.getsize(pdf_path)
        time.sleep(timeout)
        updated_size = os.path.getsize(pdf_path)
        if last_size == updated_size:
            return True

    return False

def monitor_folder(folder : str) -> None:
    """

    Funcion para monitorear Paths de carpetas en especificio. Por lo general a dichas carpetas deben de entrar PDFs para realizar indexing
    y guardarlos en sharepoint

    Parametros
    -----------

    folder: str
        * Path de la ruta que se desea monitorear

    Funciones y variables de importacia
    ------------------------------------

    option: str 
        * Hay que tener en cuenta que el sharepoint en el que va a guardar la informacion debe tener el mismo nombre que la carpeta 

    indexing: 
        * Esta es la funcion principal para realizar el indexing de los documentos que entran a la carpeta que se esta monitoreando
    
    """
    print(f"Monitoring folder: {folder}")
    #Desglose de la ruta de la carpeta para obtener el nombre de la carpeta
    processed_path = Path(folder) / "Process"
    option = Path(folder).name 
    while True:
        try:
            #Obtención de los documentos en la carpeta
            actual_folder = set(smbclient.listdir(folder))
            #Iteración sobre los documentos en la carpeta
            for doc in actual_folder:
                if doc.lower().endswith('.pdf'):
                    doc_path = "{}/{}".format(folder.replace("\\", "/"), doc)

                    if wait_doc(doc_path, 5, 5):
                        print(f"New doc found in: {folder}")
                        print("----------------------------------------------------------------------------------")
                        indexing(doc_path, option, folder, processed_path)
                        #Llamado a la función de indexacion
                        logging.info("Document indexed!")
                        #Movimiento del documento a la carpeta Done dentro del servidor
                        smbclient.rename(doc_path, Path(folder) / "Done" / f"{uuid.uuid4()}.pdf")
            time.sleep(12)
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
            time.sleep(15)
    except KeyboardInterrupt:
        print("Exiting...")