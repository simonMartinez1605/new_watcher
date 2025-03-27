from pdf2image import convert_from_path
from PyPDF2 import PdfWriter
from models.models import Model
from services.ocr import ocr
from dotenv import load_dotenv
from services.conection import sharepoint
from io import BytesIO
from services.deskewing import deskew_image
from PIL import Image
import os
import pytesseract
import shutil
import traceback
import uuid
import json
import re
import numpy as np
import cv2

load_dotenv()

#Funciones para validar datos extraidos
def regex_alien_number(cadena):
    alien_number = re.sub(r"\D", "", cadena)
    return f"A{alien_number}"

def regex_name(text):
    regex = r"[^A-ZÁÉÍÓÚáéíóúÑñÜü ]"
    return re.sub(regex, "", text)

#funcion para cargar el arhivo JSON
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def search_in_doc(model, name_doc, type_data):
    # Cargar el JSON
    json = r"\Users\simon\OneDrive\Documents\Simon\Python\new_watcher\data.json"
    json_result = load_json(json)
    # Iterar sobre la lista de documentos
    for i, doc in enumerate(json_result):
        if doc["pdf"] == name_doc:  # Comprobar si el 'pdf' coincide con 'name_doc'
            # Verificar si el 'type_data' está presente en el documento
            if type_data in doc:
                # Iterar sobre las coordenadas dentro del tipo de dato (por ejemplo, 'name' o 'a_number')
                for coord in doc[type_data]:
                    x = coord['x']
                    y = coord['y']
                    width = coord['width']
                    height = coord['height']

                    result = model.aproved_case(x, y, width, height)
                    if not result == None:
                        if len(result) > 15 and len(result) < 70:
                            return result
                return result
    # Si no se encuentra el documento o el tipo de dato, retorna None o alguna respuesta por defecto
    return None

def process_page(page):
    """Procesa una sola página del PDF con OCR después de corregir la inclinación."""
    open_cv_image = np.array(page)
    open_cv_image = deskew_image(open_cv_image)  # Aplicar deskewing
    
    # Convertir el array de numpy de vuelta a PIL Image
    pil_image = Image.fromarray(open_cv_image)
    
    data_ocr_page = pytesseract.image_to_data(open_cv_image, output_type=pytesseract.Output.DICT)
    return Model(data_ocr_page, pil_image)

#Funcion para guardar y realizar OCR a cada uno de los documentos encontrados
def save_and_ocr(pdf_save, processed_path, result, doc_name, option):
    """Guarda el PDF combinado en la carpeta de procesados, aplica OCR y lo sube a SharePoint."""

    # Asegurar que la carpeta de procesados existe
    os.makedirs(processed_path, exist_ok=True)

    #Validacion de datos y manejo de errores en carpetas individuales
    if result is None or result['name'] == '' or result['alien_number'] == '' or result['name'] == None:
        error_folder = os.path.join(processed_path, "Errors")
        os.makedirs(error_folder, exist_ok=True)  # Asegurar que la carpeta de errores existe
        output_pdf_path = os.path.join(error_folder, f"{uuid.uuid4()}.pdf")

        with open(output_pdf_path, "wb") as output_pdf:
            pdf_save.write(output_pdf)

        print(f"❌ Doc save in errors folders: {output_pdf_path}")

        pdf_save = PdfWriter()  # Reset para siguiente documento
        return False
    
    #Concatenar el path con el nombre encontrado para poder guardarlo
    output_pdf_path = os.path.join(processed_path, f"{result['name']}.pdf")

    #Combinar documentos !! Si aplica
    with open(output_pdf_path, "wb") as output_pdf:
        pdf_save.write(output_pdf)

    print(f"Combined PDF saved as {output_pdf_path}")
    
    # ocr(output_pdf_path)
    print(f"OCR completed for {output_pdf_path}")

    #Funcion para subir el documento y los metadados al sharepoint
    # sharepoint(output_pdf_path, f"{result['name']}-{doc_name}.pdf", result['alien_number'], option, doc_name)

    return True

#Funcion principal para realizar la indexacion de los documentos
def indexing(pdf, option, input_path, processed_path):
    """Convierte un PDF a imágenes, aplica OCR y clasifica documentos."""
    #convertir cada una de las paginas del archivo PDF en independientes
    pages = convert_from_path(os.path.join(input_path, pdf))
    pdf_save = PdfWriter()

    # ocr(pdf)

    #Funcion de ejecucion general para no generar codigo innecesario
    def exect_funct(type_name, doc_name): 
        name = search_in_doc(model,type_name, "name")
        # name = regex_name(name)
        alien_number = search_in_doc(model,type_name, "a_number")
        # alien_number = regex_alien_number(alien_number)
        result = {"name": name, "alien_number": alien_number}
        print(result)
        save_and_ocr(pdf_save, processed_path, result, doc_name, option)
    try:
        #Iterar sobre las hojas del documento escaneado
        for page in pages:
            model = process_page(page)
            image_stream = BytesIO()
            page.save(image_stream, format="PDF") #Agregar cada hoja en el PDF temporal
            pdf_save.append(image_stream)

            #validacion de datos utilizando la clase de modelos de busqueda
            if option == "42BReceipts":
                doc_type = model.find_receipts()

                #Validacion de cada uno de los documentos que se pueden encontrar
                match doc_type:
                    case "Payment":
                       exect_funct("Payment", doc_type)
                       pdf_save = PdfWriter()  # Reset para siguiente documento
                    case "Receipts":
                        exect_funct("Receipts_42B", doc_type)
                        pdf_save = PdfWriter()
                    case "Appointment":
                        exect_funct("Appointment_42B", doc_type)
                        pdf_save = PdfWriter()
                    case "Reused": 
                        exect_funct("Reused_42B", doc_type)
                        pdf_save = PdfWriter()
            elif option == "Asylum":

                doc_type = model.find_receipts_asylum()

                print(doc_type)
                match doc_type:
                    case "Appointment":
                        # exect_funct("Appointment_asylum", doc_type)
                        exect_funct("Test", doc_type)
                        pdf_save = PdfWriter()
                    case "Receipts": 
                        exect_funct("Approved_cases_asylum", doc_type)
                        pdf_save = PdfWriter()
                    case "Payment_receipt": 
                        exect_funct("Asylum_receipt", doc_type)
                        pdf_save = PdfWriter()
                    case "Defensive_receipt": 
                        exect_funct("Defensive_receipt", doc_type)
                        pdf_save = PdfWriter()
            elif option == "Criminal": 
                result = {"name":f"{uuid.uuid4()}", "alien_number":" "}
                save_and_ocr(pdf_save, processed_path,result," ", option)

        # Mover el documento original a la carpeta de procesados para evitar duplicados
        shutil.move(os.path.join(input_path, pdf), os.path.join(processed_path, pdf))
    
    except Exception as e:
        print(f"Error in indexing module: {e}")
        print(traceback.format_exc())
        #Movimiento de los documentos cuando se presente un error general
        error_path = os.path.join(input_path, "Errors", os.path.basename(pdf))
        shutil.move(os.path.join(input_path, pdf), error_path)

if __name__ == "__main__":
    input_path = "incoming_docs"   # Carpeta donde se encuentran los PDFs sin procesar
    processed_path = "processed_docs"  # Carpeta donde se guardarán los PDFs procesados
    pdf = "document.pdf"  
    option = "42BReceipts"
    
    indexing(pdf, option, input_path, processed_path)