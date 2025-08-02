import os
import sys
import uuid
import time
import threading
import smbclient
from pathlib import Path
from pypdf import PdfReader
from PyQt5.QtGui import QFont
from dotenv import load_dotenv
from rich.console import Console
from PyQt5.QtCore import Qt, QTimer
from QA.quality_assurance import Json_table
from services.index import optimized_indexing as indexing
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView, QLabel, QPushButton)

def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    else:
        return os.path.abspath(os.path.dirname(__file__))

dotenv_path = os.path.join(get_base_path(), '.env')

load_dotenv(dotenv_path=dotenv_path)

path_share_folder = os.getenv('PATH_SHARE_FOLDER')

console = Console()

# Configuración de la conexión a la carpeta compartida dentro del servidor
smbclient.ClientConfig(username=os.getenv('SERVER_USER'), password=os.getenv('SERVER_PASSWORD'))

# Carpetas a monitorear dentro del servidor
folders_to_monitor = [
    # rf"\\{path_share_folder}\Asylum",
    # rf"\\{path_share_folder}\42BReceipts",
    rf"\\{path_share_folder}\FamilyClosedCases",
    rf"\\{path_share_folder}\CourtPending",
    # rf"\\{path_share_folder}\ClientDocs",
    rf"\\{path_share_folder}\USCISClosedCases",
    # rf"\\{path_share_folder}\Testing",
]

class PDFMonitorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Folders monitor")
        self.setGeometry(100, 100, 1000, 800)

        self.pdf_data = []  # Almacenará los datos de los PDFs encontrados
        self.found_pdfs = set() # Nueva variable para llevar un control de los PDF encontrados
        self.lock = threading.Lock() # Añadimos un Lock para evitar conflictos de hilos

        self.init_ui()
        self.start_monitoring_threads()

        # Timer para actualizar la tabla periódicamente
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_pdf_list)
        self.update_timer.start(3000)  # Actualizar cada 3 segundos

    def init_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Título
        title_label = QLabel("PDF documents found")
        title_label.setFont(QFont('Arial', 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Instrucciones
        instructions = QLabel("Double click on a document to process it")
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)

        # Botón para actualizar manualmente
        refresh_btn = QPushButton("Update List")
        refresh_btn.clicked.connect(self.update_pdf_list)
        layout.addWidget(refresh_btn)

        # Tabla para mostrar los PDFs
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Document", "Folder", "Date", "Pages"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self.process_selected_pdf)

        layout.addWidget(self.table)

        # Estado
        self.status_label = QLabel("Status: Review documents...")
        layout.addWidget(self.status_label)

    def start_monitoring_threads(self):
        """Inicia los hilos para monitorear las carpetas"""
        self.threads = []

        for folder in folders_to_monitor:
            thread = threading.Thread(target=self.monitor_folder, args=(folder,))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

    def update_pdf_list(self):
        """Actualiza la lista de PDFs en la interfaz"""
        # Crear una nueva lista de PDFs para la interfaz
        new_pdf_data = []
        with self.lock:
            # Iterar sobre los PDFs encontrados por los hilos y preparar la información para la tabla
            for pdf_path in self.found_pdfs:
                try:
                    folder_path = os.path.dirname(pdf_path)
                    folder_name = Path(folder_path).name
                    doc = os.path.basename(pdf_path)
                    
                    # Usar smbclient para leer las propiedades del archivo
                    with smbclient.open_file(pdf_path, mode='rb') as f:
                        lector_pdf = PdfReader(f)
                        length_pdf = len(lector_pdf.pages)
                        
                    pdf_info = {
                        'name': doc,
                        'folder': folder_name,
                        'date_added': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'full_path': pdf_path,
                        'folder_path': folder_path,
                        'option': folder_name,
                        'pages': str(length_pdf)
                    }
                    new_pdf_data.append(pdf_info)

                except Exception as e:
                    return None
            
            # Reemplazar la lista anterior con la nueva
            self.pdf_data = new_pdf_data

        # Limpiar la tabla y llenarla con los datos actualizados
        self.table.setRowCount(0)
        for pdf_info in self.pdf_data:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(pdf_info['name']))
            self.table.setItem(row_position, 1, QTableWidgetItem(pdf_info['folder']))
            self.table.setItem(row_position, 2, QTableWidgetItem(pdf_info['date_added']))
            self.table.setItem(row_position, 3, QTableWidgetItem(pdf_info['pages']))


    def process_selected_pdf(self):
        """Procesa el PDF seleccionado al hacer doble click"""
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            pdf_info = self.pdf_data[selected_row]
            self.status_label.setText(f"Proccesing: {pdf_info['name']}...")
            QApplication.processEvents()  # Actualiza la UI inmediatamente

            try:
                # Ejecutar la función de indexing
                json_data = indexing(pdf_info['full_path'], pdf_info['option'], pdf_info['folder_path'], Path(pdf_info['folder_path']) / "Process", int(pdf_info['pages']))
                # Mostrar los resultados en una nueva ventana
                self.show_json_table(json_data)

                # Eliminar el PDF de la lista 'found_pdfs' del hilo para que no se vuelva a añadir
                with self.lock:
                    self.found_pdfs.discard(pdf_info['full_path'])
                
                # Ya no es necesario eliminarlo de self.pdf_data, la función update_pdf_list() se encargará de ello
                self.update_pdf_list()
                self.status_label.setText(f"Proccess document: {pdf_info['name']}")

            except Exception as e:
                self.status_label.setText(f"Error al procesar: {str(e)}")

    def show_json_table(self, json_data):
        """Muestra los datos JSON en una nueva ventana"""
        self.json_window = Json_table(json_data)
        self.json_window.setWindowModality(Qt.WindowModal)  # Modal respecto a la ventana principal
        self.json_window.show()

    def wait_doc(self, pdf_path: str, timeout: int, attempts: int) -> bool:
        """Función para esperar a que el documento se haya guardado completamente"""
        for _ in range(attempts):
            try:
                # Usar smbclient para obtener el tamaño del archivo
                last_size = smbclient.stat(pdf_path).st_size
                time.sleep(timeout)
                updated_size = smbclient.stat(pdf_path).st_size
                if last_size == updated_size:
                    return True
            except Exception as e:
                # print(f"Error en wait_doc: {e}")
                time.sleep(timeout)
        return False
        
    def monitor_folder(self, folder: str) -> None:
        """Monitorea una carpeta en busca de nuevos PDFs"""
        print(f"Monitoring folder: {folder}")
        
        while True:
            try:
                actual_folder = set(smbclient.listdir(folder))
                
                with self.lock:
                    current_pdfs = {p for p in self.found_pdfs if os.path.dirname(p) == folder}
                    new_pdfs = actual_folder.difference({os.path.basename(p) for p in current_pdfs})
                
                for doc in new_pdfs:
                    if doc.lower().endswith('.pdf'):
                        doc_path = "{}/{}".format(folder.replace("\\", "/"), doc)
                        
                        if self.wait_doc(doc_path, 2, 5):
                            with self.lock:
                                # Añadir a la lista de PDFs encontrados
                                self.found_pdfs.add(doc_path)
                
                # Eliminar de la lista interna los archivos que ya no existen en la carpeta
                files_in_folder = set(smbclient.listdir(folder))
                # with self.lock:
                #     to_remove = {p for p in self.found_pdfs if os.path.basename(p) not in files_in_folder}
                #     self.found_pdfs.difference_update(to_remove)

                # time.sleep(50)
            except Exception as e:
                print(f"Error en monitor_folder: {e}")
                time.sleep(30)

def main():
    app = QApplication([])
    app.setStyle('Fusion')
    window = PDFMonitorGUI()
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()