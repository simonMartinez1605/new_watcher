from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QTableWidget, QAbstractItemView, 
                            QLabel, QPushButton, QTableWidgetItem, QVBoxLayout, QProgressDialog, QApplication, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from pdf2image import convert_from_path
from services.conection import sharepoint
from services.ocr import ocr
from io import BytesIO
import subprocess
import os
import sys

class Json_table(QWidget):
    def __init__(self, data_list):
        super().__init__()
        self.setWindowTitle("Tabla con Vista Previa de PDF")
        self.resize(1600, 800)
        self.setWindowFlags(self.windowFlags() | Qt.Window)  # Para asegurar que es una ventana independiente

        self.data = data_list
        
        # Layout principal (vertical)
        self.main_layout = QVBoxLayout(self)
        
        # Layout horizontal para tabla y vista previa (como antes)
        self.content_layout = QHBoxLayout()
        
        # Tabla (40% del espacio)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemSelectionChanged.connect(self.show_pdf_preview)
        self.content_layout.addWidget(self.table, 4)  # 40% del espacio

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
        self.button = QPushButton("Export")
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

        # Ajustar el tamaño de las columnas
        # self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.resizeColumnsToContents()

    def update_json_from_table(self, item):
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
        """Carga y muestra el PDF con tamaño inicial adaptado"""
        selected = self.table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        pdf_path = self.data[row]["pdf"]

        if not os.path.exists(pdf_path):
            self.preview_label.setText("PDF document don't found")
            return

        try:
            # Convertir PDF a imagen (solo primera página)
            images = convert_from_path(
                pdf_path,
                first_page=1,
                last_page=1,
                dpi=300,  # Alta resolución para mejor calidad
                fmt='jpeg'
            )
            
            if images:
                # Guardar imagen original
                buffer = BytesIO()
                images[0].save(buffer, format='JPEG', quality=95)
                buffer.seek(0)
                self.original_pixmap = QPixmap()
                self.original_pixmap.loadFromData(buffer.getvalue(), "JPEG")
                
                # Escalar solo al cargar por primera vez
                self.scale_on_first_load()
                
        except Exception as e:
            self.preview_label.setText(f"Error to upload preview:\n{str(e)}")

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

