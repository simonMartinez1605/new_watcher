from pdf2image import convert_from_path
from PyPDF2 import PdfWriter
from models.models import Model
from services.ocr import ocr
from dotenv import load_dotenv
from services.conection import sharepoint
from io import BytesIO
from services.deskewing import deskew_image
from errors.errors import custom_errors, errors_folder, regex_name, regex_alien_number
from PIL import Image
import os
import pytesseract
import shutil
import traceback
import uuid
import json
import re
import numpy as np

load_dotenv()

def load_json(file_path : str) -> json:
    """Funcion para cargar el JSON de las coordenadas"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def process_page(page : list):
    """Procesa una sola página del PDF con OCR después de corregir la inclinación."""
    open_cv_image = np.array(page)
    open_cv_image = deskew_image(open_cv_image)  # Aplicar deskewing
    
    # Convertir el array de numpy de vuelta a PIL Image
    pil_image = Image.fromarray(open_cv_image)
    
    data_ocr_page = pytesseract.image_to_data(open_cv_image, output_type=pytesseract.Output.DICT)
    return Model(data_ocr_page, pil_image)

def search_in_doc(page, name_doc : str, type_data : str, json_type : str) -> bool:

    """Uso de coordenadas para buscar nombre y alien number en cada caso"""

    model = process_page(page)

    # Cargar el JSON
    json = fr"C:\Users\simon\OneDrive\Documents\Simon\Python\new_watcher\jsons\{json_type}.json"
    json_result = load_json(json)
    # Iterar sobre la lista de documentos
    for i, doc in enumerate(json_result):
        if doc["pdf"] == name_doc:  # Comprobar si el 'pdf' coincide con 'name_doc'
            # Verificar si el 'type_data' está presente en el documento
            key_word = doc['key_word']
            if type_data in doc:
                # Iterar sobre las coordenadas dentro del tipo de dato (por ejemplo, 'name' o 'a_number')
                for coord in doc[type_data]:
                    x = coord['x']
                    y = coord['y']
                    width = coord['width']
                    height = coord['height']
                    result = model.aproved_case(x, y, width, height, key_word)
                    if not result == None:
                        if len(result) > 15 and len(result) < 70:
                            return result
                return result
    # Si no se encuentra el documento o el tipo de dato, retorna None o alguna respuesta por defecto
    return None

def save_and_ocr(pdf_save : str, processed_path : str, result : list, doc_name : str, option : str) -> bool:
    """Guarda el PDF combinado en la carpeta de procesados, aplica OCR y lo sube a SharePoint."""

    # Asegurar que la carpeta de procesados existe
    os.makedirs(processed_path, exist_ok=True)

    #Validacion de datos y manejo de errores en carpetas individuales
    error = errors_folder(pdf_save, processed_path, result)
    if error == True: 
        return False
    else: 
        #Concatenar el path con el nombre encontrado para poder guardarlo
        output_pdf_path = os.path.join(processed_path, f"{result['name']}.pdf")

        name = regex_name(result['name'])
        # name = result["name"]
        alien_number = regex_alien_number(result['alien_number'])

        print(f"Name: {name} Alien Number: {alien_number}")
        #Combinar documentos !! Si aplica
        with open(output_pdf_path, "wb") as output_pdf:
            pdf_save.write(output_pdf)

        print(f"Combined PDF saved as {output_pdf_path}")
        
        ocr(output_pdf_path)
        print(f"OCR completed for {output_pdf_path}")

        #Funcion para subir el documento y los metadados al sharepoint
        sharepoint(output_pdf_path, f"{name}-{doc_name}.pdf", alien_number, option, doc_name)

    return True

def indexing(pdf : str, option: str, input_path: str, processed_path: str):
    """
    Convierte un PDF a imágenes, aplica OCR y clasifica documentos.
    
    Parametros: 
    -----------

    pdf: str
        Path de donde se encuentra el documento que deseas procesar
    option: str
        Nombre del sharepoint en donde se va a guardar el pdf (Este sharepoint debe de ser un sitio)
    input_path: str
        Path de la carpeta que constantemente se revisa
    processed_path: str
        Path de la carpeta en donde se almacenan todos los documentos procesados
    
    """
    #convertir cada una de las paginas del archivo PDF en independientes
    pages = convert_from_path(os.path.join(input_path, pdf))
    pdf_save = PdfWriter()

    # ocr(pdf)  

    #Funcion de ejecucion general para no generar codigo innecesario
    def exect_funct(type_name, doc_name, page, json_type, sheets_quantiy): 
        
        #Ejecucion de la funcion de busqueda, especificamente pasando la pagina, el tipo de documeto, el lo que se va a buscar, ya sea el nombre o el alien number y por ultimo el json en donde se almacenaron las coordenadas
        name = search_in_doc(page,type_name, "name",json_type)
        #Ejecucion de funcion para parametrizar el nombre 
        alien_number = search_in_doc(page,type_name, "a_number",json_type)

        error = custom_errors(pdf_save.pages, sheets_quantiy)

        if error == True: 
            result = None 
            errors_folder(pdf_save, processed_path, result)
        else: 
            result = {"name": name, "alien_number": alien_number}

            #Pasarle el resultado a la funcion que realizar el OCR y guarda los documentos en sharepoint
            save_and_ocr(pdf_save, processed_path, result, doc_name, option)
    try:
        #Iterar sobre las hojas del documento escaneado
        for page in pages:
            #Funcion para procesar imagenes
            model = process_page(page)
            image_stream = BytesIO()
            page.save(image_stream, format="PDF") #Agregar cada hoja en el PDF temporal
            pdf_save.append(image_stream)

            #validacion de datos utilizando la clase de modelos de busqueda
            match option:
                case "42BReceipts":
                    doc_type = model.find_receipts()

                    print(doc_type)

                    #Validacion de cada uno de los documentos que se pueden encontrar
                    match doc_type:
                        case "Payment":
                            exect_funct("Payment", doc_type, page,"42B",1)
                            pdf_save = PdfWriter()  # Reset para siguiente documento
                        case "Receipts":
                            
                            exect_funct("Receipts_42B", doc_type, page,"42B",2)
                            pdf_save = PdfWriter()
                        case "Appointment":
                            exect_funct("Appointment_42B", doc_type, page,"42B",1)
                            pdf_save = PdfWriter()
                        case "Reused":
                            exect_funct("Reused_42B", doc_type, page,"42B",1)
                            pdf_save = PdfWriter()

                case"Asylum":
                    doc_type = model.find_receipts_asylum()

                    # print(doc_type)

                    match doc_type:
                        case "Appointment":
                            exect_funct("Appointment_asylum", doc_type, page, "Asylum",1)
                            pdf_save = PdfWriter()
                        case "Appointment_asylum_2020":
                            exect_funct("Appointment_asylum_2020", "Appointment", page, "Asylum", 1)
                            pdf_save = PdfWriter()
                        case "Appointment_asylum_2019":
                            exect_funct("Appointment_asylum_2019", "Appointment" ,page, "Asylum",1)
                            pdf_save = PdfWriter()
                        case "Approved_receipts":
                            exect_funct("Approved_cases_asylum", doc_type, page, "Asylum",1)
                            pdf_save = PdfWriter()
                        case "Payment_receipt":
                            exect_funct("Asylum_receipt", doc_type, page, "Asylum",1)
                            pdf_save = PdfWriter()
                        case "Defensive_receipt":
                            exect_funct("Defensive_receipt", doc_type, page, "Asylum",1)
                            pdf_save = PdfWriter()
                        case "Application_to_asylum":
                            exect_funct("Application_to_asylum", doc_type, page, "Asylum",1)
                            pdf_save = PdfWriter()
                        case "Reused":
                            exect_funct("Reused_asylum", doc_type, page, "Asylum",1)
                            pdf_save = PdfWriter()
                        case "Reject":
                            exect_funct("Reject", doc_type, page, "Asylum", 1)
                            pdf_save = PdfWriter()
                        case "Reject_2020":
                            exect_funct("Reject_2020", "Reject", page, "Asylum", 1)
                            pdf_save = PdfWriter()
                        case "Receipt":
                            exect_funct("Receipt", doc_type, page, "Asylum", 1)
                            pdf_save = PdfWriter()
                        
                        case None: 
                            print(f"❌ Error in document type: {doc_type}")
                            errors_folder(pdf_save, processed_path, None)
                            pdf_save = PdfWriter()

                case"Criminal": 
                    
                    count = len(pdf_save.pages) 
                    total_pages = len(pages)

                    if total_pages == count: 
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