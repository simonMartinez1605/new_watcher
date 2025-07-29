import os
import sys
import subprocess
from io import BytesIO
from PyQt5.QtCore import Qt, QSize
from services.ocr import process_large_pdf_with_ocr as ocr
from PyQt5.QtGui import QPixmap
from pdf2image import convert_from_path
from PyPDF2 import PdfReader # Import PdfReader
from services.conection import sharepoint
from QA.upperCaseDelegate import UpperCaseDelegate
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QTableWidget, QAbstractItemView,
                             QLabel, QPushButton, QTableWidgetItem, QVBoxLayout,
                             QProgressDialog, QApplication, QMessageBox, QSizePolicy)

class Json_table(QWidget):
    def __init__(self, data_list):
        super().__init__()
        self.setWindowTitle("QA")
        self.resize(1600, 800)
        self.setWindowFlags(self.windowFlags() | Qt.Window)

        self.data = data_list
        self.current_pdf_first_page_image = None  # Stores the first page image of the currently selected PDF
        self.current_pdf_path = None # Store the path of the currently loaded PDF
        self.current_page_display = 0 # This will always be 0 for the preview
        self.total_pages = 0

        self.init_ui()
        self.load_data(self.data)

        # Connect signals after initial setup
        self.table.itemSelectionChanged.connect(self.show_pdf_preview)
        self.table.itemChanged.connect(self.update_json_from_table)
        self.prev_button.clicked.connect(self.show_previous_page)
        self.next_button.clicked.connect(self.show_next_page)
        self.upload_button.clicked.connect(self.upload)

        # Set delegate for uppercase column
        self.table.setItemDelegateForColumn(0, UpperCaseDelegate())

    def init_ui(self):
        """Initializes the user interface."""
        self.main_layout = QVBoxLayout(self)

        # Content layout for table and preview
        self.content_layout = QHBoxLayout()

        # Table (50% of space for better visibility of data)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.AnyKeyPressed)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_layout.addWidget(self.table, 1)  # Use stretch factor 1 (equal to preview)

        # PDF Preview section
        pdf_preview_layout = QVBoxLayout()
        self.preview_label = QLabel("Select document to show preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        self.preview_label.setMinimumSize(400, 300) # Set a minimum size for the preview
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        pdf_preview_layout.addWidget(self.preview_label)

        # Navigation controls for PDF (buttons will be disabled as only first page is shown)
        self.navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.page_counter_label = QLabel("Page 0 of 0")
        self.page_counter_label.setAlignment(Qt.AlignCenter)

        self.navigation_layout.addWidget(self.prev_button)
        self.navigation_layout.addWidget(self.page_counter_label)
        self.navigation_layout.addWidget(self.next_button)
        pdf_preview_layout.addLayout(self.navigation_layout)

        self.content_layout.addLayout(pdf_preview_layout, 1) # Use stretch factor 1 (equal to table)

        self.main_layout.addLayout(self.content_layout)

        # Export Button
        self.upload_button = QPushButton("Export")
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.main_layout.addWidget(self.upload_button, alignment=Qt.AlignRight)

    def load_data(self, data_list):
        """Populates the QTableWidget with data."""
        if not data_list:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        self.headers = list(data_list[0].keys())
        self.headers.append("open_pdf")

        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setRowCount(len(data_list))

        for row_idx, item in enumerate(data_list):
            for col_idx, key in enumerate(self.headers):
                if key == "open_pdf":
                    btn = QPushButton("Open PDF")
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #4CAF50;
                            color: white;
                            border: none;
                            padding: 5px;
                            border-radius: 3px;
                        }
                        QPushButton:hover {
                            background-color: #45a049;
                        }
                    """)
                    # Using functools.partial for cleaner signal connection if needed,
                    # but lambda is fine here as well for simple cases.
                    btn.clicked.connect(lambda _, r=row_idx: self.open_pdf(r))
                    self.table.setCellWidget(row_idx, col_idx, btn)
                else:
                    table_item = QTableWidgetItem(str(item.get(key, ''))) # Use .get with default for robustness
                    table_item.setFlags(table_item.flags() | Qt.ItemIsEditable)
                    self.table.setItem(row_idx, col_idx, table_item)

        self.table.resizeColumnsToContents()

    def update_json_from_table(self, item):
        """Updates the internal data (JSON) when a table item is edited."""
        row = item.row()
        column = item.column()
        key = self.headers[column]

        if key == "open_pdf":
            return

        new_value = item.text()
        # Attempt to convert to int or float if possible
        try:
            if '.' in new_value: # Check for decimal point to assume float
                new_value = float(new_value)
            else:
                new_value = int(new_value)
        except ValueError:
            pass # Keep as string if conversion fails

        self.data[row][key] = new_value
        print(f"Update: Fila {row + 1}, Columna '{key}' => {new_value}")

    def open_pdf(self, row):
        """Opens the PDF file associated with the selected row."""
        pdf_path = self.data[row]["pdf"]
        if not os.path.exists(pdf_path):
            QMessageBox.warning(self, "Error al abrir PDF", f"El archivo PDF no se encontró en: {pdf_path}")
            return

        try:
            if sys.platform == "win32":
                os.startfile(pdf_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", pdf_path])
            else:
                subprocess.run(["xdg-open", pdf_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo PDF: {e}")

    def show_pdf_preview(self):
        """Displays the first page of the PDF preview for the selected row and shows total pages."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.preview_label.setText("Select document to show preview.")
            self.current_pdf_first_page_image = None
            self.current_pdf_path = None
            self.current_page_display = 0
            self.total_pages = 0
            self.update_page_counter()
            self.update_navigation_buttons()
            return

        row = selected_items[0].row()
        pdf_path = self.data[row]["pdf"]

        if not os.path.exists(pdf_path):
            self.preview_label.setText("Document PDF not found.")
            self.current_pdf_first_page_image = None
            self.current_pdf_path = None
            self.current_page_display = 0
            self.total_pages = 0
            self.update_page_counter()
            self.update_navigation_buttons()
            return

        # Optimization: Only process PDF if a different one is selected
        if self.current_pdf_path != pdf_path:
            self.preview_label.setText("Loading preview...")
            QApplication.processEvents() # Update UI while loading

            try:
                # Get total pages first (efficiently)
                reader = PdfReader(pdf_path)
                self.total_pages = len(reader.pages)

                # Convert only the first page to image
                # Lower DPI for faster loading if high resolution isn't strictly necessary for preview
                images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=150, fmt='jpeg', thread_count=os.cpu_count())

                if images:
                    self.current_pdf_first_page_image = images[0]
                    self.current_pdf_path = pdf_path
                    self.current_page_display = 0 # Always display the first page (index 0)
                    self.show_first_page_image()
                else:
                    self.preview_label.setText("No se pudo cargar la primera página del PDF.")
                    self.current_pdf_first_page_image = None
                    self.current_pdf_path = None
                    self.total_pages = 0
            except Exception as e:
                self.preview_label.setText(f"Error al cargar la vista previa:\n{str(e)}")
                self.current_pdf_first_page_image = None
                self.current_pdf_path = None
                self.total_pages = 0
        else:
            # If the same PDF is selected, just ensure the first page is shown
            self.show_first_page_image()

        self.update_page_counter()
        self.update_navigation_buttons()

    def show_first_page_image(self):
        """Displays the stored first page image of the current PDF preview."""
        if not self.current_pdf_first_page_image:
            self.preview_label.setText("No hay página para mostrar.")
            return

        try:
            buffer = BytesIO()
            self.current_pdf_first_page_image.save(buffer, format="JPEG")
            buffer.seek(0)

            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())

            if pixmap.isNull():
                self.preview_label.setText("Error al cargar la imagen de la primera página.")
                return

            # Store the original pixmap to re-scale on resize
            self.original_pixmap = pixmap
            self._scale_and_set_pixmap()

        except Exception as e:
            self.preview_label.setText(f"Error al procesar la imagen de la primera página:\n{str(e)}")

    def show_previous_page(self):
        """
        These buttons are now effectively disabled as only the first page is shown.
        You might want to hide them or remove them entirely if they serve no purpose.
        """
        pass # No action as only the first page is displayed

    def show_next_page(self):
        """
        These buttons are now effectively disabled as only the first page is shown.
        You might want to hide them or remove them entirely if they serve no purpose.
        """
        pass # No action as only the first page is displayed

    def update_page_counter(self):
        """Updates the page counter label."""
        # For preview, it will always show "Page 1 of X"
        self.page_counter_label.setText(f"Página {self.current_page_display + 1} de {self.total_pages}")

    def update_navigation_buttons(self):
        """Disables navigation buttons as only the first page is shown."""
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)

    def _scale_and_set_pixmap(self):
        """Helper to scale the pixmap to fit the preview label."""
        if hasattr(self, 'original_pixmap') and not self.original_pixmap.isNull():
            available_size = self.preview_label.size()
            scaled_pixmap = self.original_pixmap.scaled(
                available_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)
            self.current_scaled_pixmap = scaled_pixmap # Store the currently displayed scaled pixmap

    def resizeEvent(self, event):
        """Handles window resizing to re-scale the PDF preview."""
        super().resizeEvent(event)
        self._scale_and_set_pixmap()

    def upload(self):
        """Uploads documents to SharePoint and applies OCR."""
        # This function remains unchanged as per your request
        try:
            progress = QProgressDialog("Upload data to SharePoint...", "Cancel", 0, len(self.data), self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            for i, data in enumerate(self.data, 1):
                if progress.wasCanceled():
                    QMessageBox.warning(self, "Carga cancelada", "La carga de documentos ha sido cancelada por el usuario.")
                    break

                progress.setValue(i)
                progress.setLabelText(f"Processing {data.get('name', 'documento')}...")
                QApplication.processEvents() # Ensure UI updates

                try:
                    ocr(data['pdf'], data['pdf'], 50)
                    metadata_dict = {}
                    for key, value in data.items():
                        if key != "name" and key != "pdf" and key != "folder_name":
                            metadata_dict.update({key: value})
                    sharepoint(data['pdf'], f"{data['name']}.pdf", data['folder_name'], data['name'], metadata_dict)
                except Exception as e:
                    # Log the error and notify the user without stopping the whole process
                    QMessageBox.warning(self, "Error de procesamiento",f"Error al procesar el documento {data.get('name', 'desconocido')}: {e}")
                    print(f"Error al procesar el documento {data.get('name', 'desconocido')}: {e}")
                    # Optionally, you might want to mark this item as failed in self.data or a separate list
            progress.close()
            # Only close the window if the upload wasn't cancelled or had critical errors
            if not progress.wasCanceled():
                QMessageBox.information(self, "Carga completa", "Todos los documentos han sido procesados y subidos.")
                self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error de carga global", f"Ocurrió un error inesperado durante la carga: \n{str(e)}")
            print(f"Error al cargar documentos: {e}")