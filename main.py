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
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread
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

class PDFProcessWorker(QObject):
    # Señal que emite el resultado JSON (usamos 'object' para pasar el diccionario)
    processing_finished = pyqtSignal(list)
    # Señal para emitir cualquier error que ocurra
    processing_error = pyqtSignal(str)

    def __init__(self, pdf_path, option, folder_path, pages):
        super().__init__()
        self.pdf_path = pdf_path
        self.option = option
        self.folder_path = folder_path
        self.pages = pages

    def run(self):
        """Ejecuta la tarea de indexación en segundo plano."""
        try:
            # Tu lógica de procesamiento pesado va aquí
            json_data = indexing(self.pdf_path, self.option, self.folder_path, Path(self.folder_path) / "Process", self.pages)
            self.processing_finished.emit(json_data)
        except Exception as e:
            self.processing_error.emit(str(e))

class PDFMonitorWorker(QObject):
    pdf_found = pyqtSignal(dict)
    # Señal que emitirá un diccionario con la info del PDF encontrado
    # Señal para indicar que el monitoreo ha terminado (opcional)
    finished = pyqtSignal()

    def __init__(self, folders):
        super().__init__()
        self.folders = folders
        self.found_paths = set() # Mantiene un registro de los PDFs ya procesados

    def run(self):
        """
        Esta función se ejecutará en el hilo secundario.
        Monitorea las carpetas en un bucle infinito.
        """
        while True:
            try:
                for folder in self.folders:
                    for entry in smbclient.scandir(folder):
                        if entry.is_file() and entry.name.lower().endswith('.pdf'):
                            pdf_path = os.path.join(folder, entry.name)
                            
                            # Procesar solo si es un archivo nuevo
                            if pdf_path not in self.found_paths:
                                self.found_paths.add(pdf_path) # Marcar como procesado
                                
                                try:
                                    # Extraer metadatos UNA SOLA VEZ
                                    with smbclient.open_file(pdf_path, mode='rb') as f:
                                        reader = PdfReader(f)
                                        page_count = len(reader.pages)
                                    
                                    pdf_info = {
                                        'name': entry.name,
                                        'folder': Path(folder).name,
                                        'date_added': time.strftime("%Y-%m-%d %H:%M:%S"),
                                        'full_path': pdf_path,
                                        'pages': str(page_count)
                                    }
                                    
                                    # Emitir la señal con los datos
                                    self.pdf_found.emit(pdf_info)
                                    
                                except Exception as e:
                                    print(f"Error procesando {pdf_path}: {e}")
                                    
            except Exception as e:
                print(f"Error monitoreando carpetas: {e}")
            
            # Esperar un tiempo antes de volver a escanear para no saturar la red
            time.sleep(5) 

            self.finished.emit()

class PDFMonitorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Folders monitor")
        self.setGeometry(100, 100, 1000, 800)
        
        # Almacenaremos los datos directamente en la tabla, ya no necesitamos self.pdf_data
        self.init_ui()
        self.start_monitoring()

    def init_ui(self):
        # ... (tu código de init_ui es casi el mismo, solo quitamos el botón de refresco)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        title_label = QLabel("PDF documents found")
        title_label.setFont(QFont('Arial', 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        self.status_label = QLabel("Status: Monitoring folders...")
        layout.addWidget(self.status_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Document", "Folder", "Date Added", "Pages"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self.process_selected_pdf) # Mantienes tu lógica aquí
        layout.addWidget(self.table)
        
    def start_monitoring(self):
        """Prepara y ejecuta el worker en un hilo secundario."""
        # 1. Crear una instancia del hilo
        self.thread = QThread()
        # 2. Crear una instancia de nuestro worker
        self.worker = PDFMonitorWorker(folders_to_monitor)
        # 3. Mover el worker al hilo
        self.worker.moveToThread(self.thread)

        # 4. Conectar señales y slots
        # Cuando el hilo empiece, ejecuta el método 'run' del worker
        self.thread.started.connect(self.worker.run)
        # Conecta la señal 'pdf_found' del worker a la función 'add_pdf_to_table' de la GUI
        self.worker.pdf_found.connect(self.add_pdf_to_table)
        # Limpieza cuando el worker termine
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        # 5. Iniciar el hilo
        self.thread.start()

    def add_pdf_to_table(self, pdf_info):
        """
        Agrega una fila a la tabla y almacena los datos completos en el primer item.
        """
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        
        # Creamos el primer item con el nombre del documento
        item_name = QTableWidgetItem(pdf_info['name'])
        
        # Almacenamos TODO el diccionario de información en este item
        item_name.setData(Qt.UserRole, pdf_info) 
        
        self.table.setItem(row_position, 0, item_name)
        self.table.setItem(row_position, 1, QTableWidgetItem(pdf_info['folder']))
        self.table.setItem(row_position, 2, QTableWidgetItem(pdf_info['date_added']))
        self.table.setItem(row_position, 3, QTableWidgetItem(pdf_info['pages']))
        self.status_label.setText(f"Status: Found {self.table.rowCount()} documents.")
        
    def closeEvent(self, event):
        """Asegurarse de que TODOS los hilos se cierren correctamente."""
        print("Cerrando la aplicación...")

        # Detener el hilo de monitoreo de forma segura
        if hasattr(self, 'worker') and self.thread.isRunning():
            print("Deteniendo el hilo de monitoreo...")
            self.worker.stop()  # 1. Decirle al worker que pare su bucle
            self.thread.quit()  # 2. Pedir al hilo que termine
            self.thread.wait()  # 3. Esperar a que realmente termine
            print("Hilo de monitoreo detenido.")

        # Detener el hilo de procesamiento si está activo
        if hasattr(self, 'processing_thread') and self.processing_thread.isRunning():
            print("Deteniendo el hilo de procesamiento...")
            # Nota: El hilo de procesamiento no tiene bucle, así que quit() suele ser suficiente
            self.processing_thread.quit()
            self.processing_thread.wait()
            print("Hilo de procesamiento detenido.")

        event.accept()

    def process_selected_pdf(self):
        """Inicia el proceso de indexación de un PDF en un hilo separado."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return

        # Extraer la información almacenada en el item de la fila seleccionada
        item = self.table.item(selected_row, 0)
        pdf_info = item.data(Qt.UserRole)
        
        self.status_label.setText(f"Processing: {pdf_info['name']}...")
        # Opcional: Deshabilitar la tabla para evitar múltiples clics
        self.table.setEnabled(False) 

        # Crear hilo y worker para esta tarea específica
        self.processing_thread = QThread()
        self.processing_worker = PDFProcessWorker(
            pdf_path=pdf_info['full_path'],
            option=pdf_info['folder'], # o la opción que necesites
            folder_path=os.path.dirname(pdf_info['full_path']),
            pages=int(pdf_info['pages'])
        )
        self.processing_worker.moveToThread(self.processing_thread)

        # Conectar señales
        self.processing_thread.started.connect(self.processing_worker.run)
        self.processing_worker.processing_finished.connect(self.on_processing_complete)
        self.processing_worker.processing_error.connect(self.on_processing_error)

        # Limpieza
        self.processing_worker.processing_finished.connect(self.processing_thread.quit)
        self.processing_worker.processing_error.connect(self.processing_thread.quit)
        self.processing_thread.finished.connect(self.processing_thread.deleteLater)
        # self.processing_worker.finished.connect(self.processing_worker.deleteLater)
        
        self.processing_thread.start()

    def on_processing_complete(self, json_data):
        """
        Slot que se ejecuta cuando el procesamiento es exitoso.
        Recibe los datos JSON del worker.
        """
        selected_row = self.table.currentRow()
        item = self.table.item(selected_row, 0)
        pdf_info = item.data(Qt.UserRole)

        # 1. Mostrar la nueva ventana con los resultados
        self.show_json_table(json_data)
        
        # 2. Eliminar la fila de la tabla principal
        self.table.removeRow(selected_row)
        
        # 3. Notificar al monitor principal que este archivo ya no debe ser listado
        # (Si el worker de monitoreo tiene acceso al set de archivos procesados)
        # Esto requiere una comunicación más avanzada (señales al worker) o simplemente
        # dejar que el worker de monitoreo intente añadirlo de nuevo (pero ya no estará en el disco).
        # La forma más simple es que tu función `indexing` mueva o elimine el archivo procesado.

        self.status_label.setText(f"Successfully processed: {pdf_info['name']}")
        self.table.setEnabled(True) # Volver a habilitar la tabla

    def on_processing_error(self, error_message):
        """Slot que se ejecuta si hay un error en el procesamiento."""
        self.status_label.setText(f"Error processing document: {error_message}")
        self.table.setEnabled(True) # Volver a habilitar la tabla

    def show_json_table(self, json_data):
        """Esta función no necesita cambios."""
        self.json_window = Json_table(json_data)
        self.json_window.setWindowModality(Qt.WindowModal)
        self.json_window.show()


def main():
    app = QApplication([])
    app.setStyle('Fusion')
    window = PDFMonitorGUI()
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()