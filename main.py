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

print(f"Path to share folder: {path_share_folder}")

console = Console()

# Configuración de la conexión a la carpeta compartida dentro del servidor
smbclient.ClientConfig(username=os.getenv('SERVER_USER'), password=os.getenv('SERVER_PASSWORD'))

# Carpetas a monitorear dentro del servidor
folders_to_monitor = [
    # rf"\\{path_share_folder}\Asylum",
    # rf"\\{path_share_folder}\42BReceipts",
    rf"\\{path_share_folder}\FamilyClosedCases",
]

class PDFMonitorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Folders monitor")
        self.setGeometry(100, 100, 1000, 800)
        
        self.pdf_data = []  # Almacenará los datos de los PDFs encontrados
        
        self.init_ui()
        self.start_monitoring_threads()
        
        # Timer para actualizar la tabla periódicamente
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_pdf_list)
        self.update_timer.start(3000)  # Actualizar cada 5 segundos
        
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
        self.table.setRowCount(0)
        
        for pdf_info in self.pdf_data:
            row_position = self.table.rowCount()
            # print(pdf_info)
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
                print(os.path.exists(fr"C:\Users\simon\OneDrive\Documents\Simon\Python\new_watcher\jsons\FamilyClosedCases.json"))
                # Ejecutar la función de indexing
                json_data = indexing(pdf_info['full_path'], pdf_info['option'], pdf_info['folder_path'], Path(pdf_info['folder_path']) / "Process", int(pdf_info['pages']))
                
                # Mostrar los resultados en una nueva ventana
                self.show_json_table(json_data)
                
                # Mover el archivo a la carpeta Done
                smbclient.rename(pdf_info['full_path'],Path(pdf_info['folder_path']) / "Done" / f"{uuid.uuid4()}.pdf")
                
                # Actualizar la lista
                self.pdf_data.pop(selected_row)
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
                last_size = os.path.getsize(pdf_path)
                time.sleep(timeout)
                updated_size = os.path.getsize(pdf_path)
                if last_size == updated_size:
                    return True
            except Exception as e:
                print(f"Error en wait_doc: {e}")
                time.sleep(timeout)
        return False
        
    def monitor_folder(self, folder: str) -> None:
        """Monitorea una carpeta en busca de nuevos PDFs"""
        print(f"Monitoring folder: {folder}")
        folder_name = Path(folder).name
        
        while True:
            try:
                # Obtener documentos en la carpeta
                actual_folder = set(smbclient.listdir(folder))
                
                for doc in actual_folder:
                    if doc.lower().endswith('.pdf'):
                        doc_path = "{}/{}".format(folder.replace("\\", "/"), doc)
                        
                        # Verificar si ya está en nuestra lista
                        if not any(p['full_path'] == doc_path for p in self.pdf_data):
                            if self.wait_doc(doc_path, 5, 5):
                                lector_pdf = PdfReader(doc_path)
                                length_pdf = len(lector_pdf.pages)
                                # Agregar a la lista de PDFs
                                pdf_info = {
                                    'name': doc,
                                    'folder': folder_name,
                                    'date_added': time.strftime("%Y-%m-%d %H:%M:%S"),
                                    'full_path': doc_path,
                                    'folder_path': folder,
                                    'option': folder_name,
                                    'pages': str(length_pdf)
                                }
                                self.pdf_data.append(pdf_info)
                                self.update_pdf_list()
                time.sleep(10)
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