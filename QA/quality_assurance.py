import os
import sys
import traceback
import subprocess
from PIL import Image
from io import BytesIO
from PyQt5.QtCore import Qt
from services.ocr import ocr
from PyQt5.QtGui import QPixmap, QImage
from pdf2image import convert_from_path
from services.conection import sharepoint
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QTableWidget, QAbstractItemView, QLabel, QPushButton, QTableWidgetItem, QVBoxLayout, QProgressDialog, QApplication, QMessageBox, QScrollArea, QFrame)

class Json_table(QWidget):
    def __init__(self, data_list):
        super().__init__()
        self.setWindowTitle("Tabla con Vista Previa de PDF")
        self.resize(1600, 800)
        self.setWindowFlags(self.windowFlags() | Qt.Window)

        self.data = data_list
        self.current_page = 0  # Página actual
        self.total_pages = len(data_list)  # Total de páginas (ajustar según el PDF)
        self.images = []  # Lista para almacenar las imágenes del PDF

        # Layout principal (vertical)
        self.main_layout = QVBoxLayout(self)

        # Layout horizontal para tabla y vista previa (como antes)
        self.content_layout = QHBoxLayout()

        # Tabla (40% del espacio)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemSelectionChanged.connect(self.show_pdf_preview)
        self.content_layout.addWidget(self.table, 4)  # 40% del espacio

        self.navigation_layout = QHBoxLayout()

        self.page_counter_label = QLabel("Página 0 de 0")
        self.navigation_layout.addWidget(self.page_counter_label)
        
        # Vista previa (60% del espacio)
        self.preview_label = QLabel("Seleccione un documento para ver la vista previa")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        self.content_layout.addWidget(self.preview_label, 6)  # 60% del espacio
        

        # Añadir el layout horizontal al layout principal
        self.main_layout.addLayout(self.content_layout)

        # Crear y añadir el botón en la parte inferior
        self.button = QPushButton("Exportar")
        self.button.setStyleSheet("""
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
        # Botones de navegación (anterior y siguiente)
        self.prev_button = QPushButton("Anterior")
        self.prev_button.clicked.connect(self.show_previous_page)
        self.next_button = QPushButton("Siguiente")
        self.next_button.clicked.connect(self.show_next_page)

        self.navigation_layout.addWidget(self.prev_button)
        self.navigation_layout.addWidget(self.next_button)
        self.main_layout.addLayout(self.navigation_layout)

        self.button.clicked.connect(self.upload)
        self.main_layout.addWidget(self.button, alignment=Qt.AlignRight)

        self.load_data(self.data)
        self.table.itemChanged.connect(self.update_json_from_table)

        self.progress_label = QLabel(self)
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.hide()

    def load_data(self, data_list):
            if not data_list:
                return

            self.headers = list(data_list[0].keys())
            self.headers.append("open_pdf")

            self.table.setColumnCount(len(self.headers))
            self.table.setRowCount(len(data_list))
            self.table.setHorizontalHeaderLabels(self.headers)

            for row_idx, item in enumerate(data_list):
                for col_idx, key in enumerate(self.headers):
                    if key == "open_pdf":
                        btn = QPushButton("Abrir PDF")
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
                        btn.clicked.connect(lambda _, r=row_idx: self.open_pdf(r))
                        self.table.setCellWidget(row_idx, col_idx, btn)
                    else:
                        table_item = QTableWidgetItem((item[key]))
                        table_item.setFlags(table_item.flags() | Qt.ItemIsEditable)
                        self.table.setItem(row_idx, col_idx, table_item)

            self.table.resizeColumnsToContents()

    def update_json_from_table(self, item):
        """Actualiza el JSON a partir de la tabla cuando se edita un valor"""
        row = item.row()
        column = item.column()
        key = self.headers[column]
        if key == "open_pdf":
            return

        new_value = item.text()
        try:
            new_value = int(new_value)
        except ValueError:
            try:
                new_value = float(new_value)
            except ValueError:
                pass

        self.data[row][key] = new_value
        print(f"Update: Row {row + 1}, Column '{key}' => {new_value}")

    def open_pdf(self, row):
        """Abre el PDF correspondiente a la fila seleccionada"""
        pdf_path = self.data[row]["pdf"]
        try:
            if sys.platform == "win32":
                os.startfile(pdf_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", pdf_path])
            else:
                subprocess.run(["xdg-open", pdf_path])
        except Exception as e:
            print(f"The system can't open the file: {e}")

    def show_pdf_preview(self):
        selected = self.table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        pdf_path = self.data[row]["pdf"]

        if not os.path.exists(pdf_path):
            self.preview_label.setText("Documento PDF no encontrado.")
            return

        try:
            # Convertir PDF a imagen (todas las páginas)
            images = convert_from_path(pdf_path, dpi=300, fmt='jpeg')

            if images:
                self.images = images  # Guardar todas las imágenes generadas
                self.total_pages = len(images)  # Total de páginas
                self.show_page(self.current_page)  # Mostrar la página actual

        except Exception as e:
            self.preview_label.setText(f"Error al cargar la vista previa:\n{str(e)}")

    def show_page(self, page_num):
        """Muestra la página correspondiente"""
        if page_num < 0 or page_num >= self.total_pages:
            print(f"Página inválida: {page_num}")
            return

        image = self.images[page_num]

        if image is None:
            print(f"Error: la imagen de la página {page_num} no se pudo generar.")
            return

        # Convertir a QPixmap
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())

        if pixmap.isNull():
            print(f"Error al cargar la imagen de la página {page_num} en QPixmap.")
            return

        # Escalar la imagen al tamaño del QLabel
        available_size = self.preview_label.size()
        scaled_pixmap = pixmap.scaled(available_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled_pixmap)

        # Actualizar el contador de páginas
        self.page_counter_label.setText(f"Página {self.current_page + 1} de {self.total_pages}")

        # Desactivar botones si estamos en la primera o última página
        self.update_navigation_buttons()

    def show_previous_page(self):
        """Muestra la página anterior"""
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)

    def show_next_page(self):
        """Muestra la siguiente página"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.show_page(self.current_page)

    def update_navigation_buttons(self):
        """Desactiva los botones de navegación si estamos en los extremos"""
        if self.current_page == 0:
            self.prev_button.setEnabled(False)  # Desactivar botón 'Anterior'
        else:
            self.prev_button.setEnabled(True)

        if self.current_page == self.total_pages - 1:
            self.next_button.setEnabled(False)  # Desactivar botón 'Siguiente'
        else:
            self.next_button.setEnabled(True)

    def scale_on_first_load(self):
        """Escala la imagen solo al cargar inicialmente"""
        if hasattr(self, 'original_pixmap') and not self.original_pixmap.isNull():
            # Obtener tamaño disponible en el QLabel
            available_size = self.preview_label.size()
            
            # Escalar manteniendo relación de aspecto
            scaled_pixmap = self.original_pixmap.scaled(
                available_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Guardar el pixmap escalado para no volver a escalar
            self.current_pixmap = scaled_pixmap
            self.preview_label.setPixmap(self.current_pixmap)

    def resizeEvent(self, event):
        """Maneja el redimensionamiento de la ventana SIN reescalar la imagen"""
        super().resizeEvent(event)
        # Solo mostramos el pixmap actual sin volver a escalar
        if hasattr(self, 'current_pixmap'):
            self.preview_label.setPixmap(self.current_pixmap)

    def upload(self):
        """Sube los documentos a SharePoint y aplica OCR"""
        try: 
            progress = QProgressDialog("Upload data to sharepoint...", "Cancel", 0, len(self.data), self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            for i, data in enumerate(self.data, 1):
                if progress.wasCanceled(): 
                    break

                progress.setValue(i)
                progress.setLabelText(f"Procesing {data['name']}...")
                QApplication.processEvents()

                try: 

                    ocr(data['pdf'])
                    sharepoint(data['pdf'], f"{data['name']}-{data['doc_type']}.pdf", data['alien_number'], data['folder_name'], data['doc_type'])
                except Exception as e: 
                    print(f"Error to process data: {e}")

            progress.close()
            self.close()

        except Exception as e:
            print(f"Error to upload documents: {e}")
            QMessageBox.critical(self, "Error", f"Upload documents: \n{str(e)}")