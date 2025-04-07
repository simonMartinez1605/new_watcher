from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QComboBox, QMessageBox, QScrollArea
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from pdf2image import convert_from_path
import sys
import os
import shutil
# from services.conection import sharepoint

# CONFIGURA ESTAS RUTAS
CARPETA_DOCUMENTOS = r"Z:\Asylum\Process\Errors"
POPPLER_PATH = r"C:\Users\simon\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"
CARPETA_PROCESADOS = r"Z:\Asylum\Done"

class QAWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Review Documents")
        self.pdf_files = self.get_pdfs_from_folder(CARPETA_DOCUMENTOS)
        self.current_pdf_index = 0
        self.image_paths = []

        # Widgets
        self.image_label = QLabel("Load documents")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True)

        self.zoom_factor = 1.0

        self.zoom_in_button = QPushButton("Zoom +")
        self.zoom_in_button.clicked.connect(self.zoom_in)

        self.zoom_out_button = QPushButton("Zoom -")
        self.zoom_out_button.clicked.connect(self.zoom_out)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.image_label)

        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["Select type of document", "Appointment", "Payment", "Receipt", "Reject"])
        self.tipo_combo.currentIndexChanged.connect(self.on_tipo_selected)

        self.sharepoint_combo = QComboBox()
        self.sharepoint_combo.addItems(["Select type of sharepoint", "Asylum", "Criminal", "42BReceipts"])
        self.sharepoint_combo.currentIndexChanged.connect(self.on_tipo_selected)

        self.name_input = QLineEdit()
        self.id_input = QLineEdit()

        self.submit_button = QPushButton("Upload and Move")
        self.submit_button.clicked.connect(self.on_submit)

        self.path_label = QLabel()

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.path_label)
        layout.addWidget(self.scroll_area)
        layout.addWidget(QLabel("Document type:"))
        layout.addWidget(self.tipo_combo)
        layout.addWidget(QLabel("Sharepoint name:"))
        layout.addWidget(self.sharepoint_combo)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Alien number:"))
        layout.addWidget(self.id_input)
        # layout.addWidget(self.zoom_in_button)
        # layout.addWidget(self.zoom_out_button)
        layout.addWidget(self.submit_button)


        self.setLayout(layout)

        # Iniciar con el primer PDF
        self.load_next_pdf()

    def zoom_in(self):
        self.zoom_factor *= 1.2
        self.show_image()

    def zoom_out(self):
        self.zoom_factor /= 1.2
        self.show_image()


    def get_pdfs_from_folder(self, folder_path):
        return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

    def load_next_pdf(self):
        self.tipo_combo.setCurrentIndex(0)
        self.name_input.clear()
        self.id_input.clear()
        self.image_paths.clear()
        self.image_label.setText("")

        # self.path_label.setText(f"Proccessing: {self.current_pdf}")

        if self.current_pdf_index >= len(self.pdf_files):
            self.image_label.setText("All PDFs processed.")
            self.submit_button.setEnabled(False)
            return

        self.current_pdf = self.pdf_files[self.current_pdf_index]
        self.convert_pdf_to_images(self.current_pdf)

    def convert_pdf_to_images(self, pdf_path):
        try:
            output_dir = os.path.join(os.path.dirname(pdf_path), "temp_images")
            os.makedirs(output_dir, exist_ok=True)

            pages = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
            self.image_paths = []

            for i, page in enumerate(pages):
                image_path = os.path.join(output_dir, f"{os.path.basename(pdf_path)}_pagina_{i+1}.png")
                page.save(image_path, "PNG")
                self.image_paths.append(image_path)

            self.show_image()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al convertir el PDF: {str(e)}")

    def show_image(self):
        if self.image_paths:
            pixmap = QPixmap(self.image_paths[0])  # Por ahora solo muestra la primera página
            self.image_label.setPixmap(pixmap.scaled(800, 1000, Qt.KeepAspectRatio))

    def on_tipo_selected(self, index):
        pass  # Ya no es necesario hacer la conversión aquí

    def on_submit(self):
        name = self.name_input.text()
        doct_ype = self.tipo_combo.currentText()
        alien_number = self.id_input.text()
        sharepoint_name = self.tipo_combo.currentText()

        if not name or doct_ype == "Selecciona tipo" or not alien_number:
            QMessageBox.warning(self, "Data less", "Fill all fields")
            return

        print(f"Proccess doc:")
        print(f"  Path: {self.current_pdf}")
        print(f"  Name: {name}")
        print(f"  doct_ype: {doct_ype}")
        print(f"  Alien_number: {alien_number}")

        # 🟩 Mover el PDF a la carpeta de procesados
        try:
            # sharepoint(self.current_pdf, f"{name}-{doct_ype}.pdf", alien_number, sharepoint_name, doct_ype) 
            os.makedirs(CARPETA_PROCESADOS, exist_ok=True)
            archivo_nombre = os.path.basename(self.current_pdf)
            nuevo_path = os.path.join(CARPETA_PROCESADOS, archivo_nombre)
            shutil.move(self.current_pdf, nuevo_path)
            print(f"📁 PDF movido a: {nuevo_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error al mover archivo", str(e))
            return

        # 🟦 Continuar con el siguiente
        self.current_pdf_index += 1
        self.load_next_pdf()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QAWindow()
    window.show()
    sys.exit(app.exec_())
