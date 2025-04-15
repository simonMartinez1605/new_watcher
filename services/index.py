import os
import json
import shutil
import uuid
import traceback
import numpy as np
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pdf2image import convert_from_path
from PyPDF2 import PdfWriter
from PIL import Image, ImageFilter
import pytesseract
from dotenv import load_dotenv
from services.deskewing import deskew_image
from models.models import Model
from errors.errors import regex_name, regex_alien_number

# Cargar variables de entorno
load_dotenv()

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Configuración global
_JSON_CACHE = {}

def load_json_cached(file_path: str) -> dict:
    """Carga JSON con caché para evitar lecturas repetidas de disco"""
    if file_path not in _JSON_CACHE:
        with open(file_path, 'r', encoding='utf-8') as f:
            _JSON_CACHE[file_path] = json.load(f)
    return _JSON_CACHE[file_path]

def preprocess_image(image):
    """Mejora la imagen para OCR"""
    return image.filter(ImageFilter.SHARPEN).convert('L')

def needs_deskewing(image):
    """Determina si la imagen necesita corrección de inclinación"""
    # Implementación básica - puedes mejorarla con detección de bordes
    return True

def process_page_optimized(page):
    """Versión optimizada del procesamiento de página"""
    try:
        # Preprocesamiento
        pil_image = preprocess_image(page)
        
        # Convertir a numpy array manteniendo 3 canales si es necesario
        if pil_image.mode == 'L':
            # Si es escala de grises, convertir a RGB
            pil_image = pil_image.convert('RGB')
        
        open_cv_image = np.array(pil_image)
        
        # Convertir de RGB a BGR (que es lo que OpenCV espera)
        open_cv_image = open_cv_image[:, :, ::-1].copy()
        
        # Deskewing condicional
        if needs_deskewing(open_cv_image):
            open_cv_image = deskew_image(open_cv_image)
            
            # Convertir de vuelta a RGB para PIL
            open_cv_image = open_cv_image[:, :, ::-1]
        
        # Configuración optimizada para Tesseract
        custom_config = r'--oem 3 --psm 6'
        
        # Convertir a escala de grises para Tesseract si es necesario
        ocr_image = Image.fromarray(open_cv_image).convert('L') if open_cv_image.shape[2] == 3 else Image.fromarray(open_cv_image)
        
        data_ocr_page = pytesseract.image_to_data(
            ocr_image, 
            config=custom_config,
            output_type=pytesseract.Output.DICT
        )
        
        return Model(data_ocr_page, Image.fromarray(open_cv_image))
    except Exception as e:
        print(f"Error procesando página: {e}")
        traceback.print_exc()
        return None

def search_in_doc_optimized(page, name_doc: str, type_data: str, json_type: str):
    """Versión optimizada de búsqueda en documento"""
    model = process_page_optimized(page)
    if not model:
        return None
        
    json_path = f"jsons/{json_type}.json"  # Ajusta la ruta
    json_result = load_json_cached(json_path)
    
    # Búsqueda más eficiente
    matching_doc = next((doc for doc in json_result if doc["pdf"] == name_doc), None)
    if not matching_doc or type_data not in matching_doc:
        return None
    
    key_word = matching_doc['key_word']
    for coord in matching_doc[type_data]:
        result = model.aproved_case(
            coord['x'], coord['y'], 
            coord['width'], coord['height'], 
            key_word
        )
        if result and 8 < len(result) < 170:
            return result
    return None

def save_and_ocr_optimized(result, processed_path, option, pdf_save):
    try:
        os.makedirs(processed_path, exist_ok=True)
        output_pdf_path = os.path.join(processed_path, f"{result['name']}.pdf")

        # Guardar el PDF individual
        with open(output_pdf_path, "wb") as output_pdf:
            pdf_save.write(output_pdf)  # pdf_save contiene solo una página

        return {
            "name": regex_name(result['name']),
            "alien_number": regex_alien_number(result['alien_number']),
            "pdf": output_pdf_path,
            "doc_type": result.get('doc_type'),
            "folder_name": option
        }
    except Exception as e:
        print(f"❌ Error guardando PDF individual: {e}")
        return None

def exect_funct_optimized(doc_type, page, option, processed_path, json_type, save_pdf):
    """Versión optimizada de la función de ejecución"""
    try:
        # Mapeo de tipos de documento a sus parámetros
        doc_config = {
            "42BReceipts": {
                "Payment": ("Payment", "42B", 1),
                "Receipts": ("Receipts_42B", "42B", 2),
                "Appointment": ("Appointment_42B", "42B", 1),
                "Reused": ("Reused_42B", "42B", 1)
            },
            "Asylum": {
                "Appointment": ("Appointment_asylum", 1, "Appointment"),
                "Appointment_asylum_2020": ("Appointment_asylum_2020", 1, "Appointment"),
                "Appointment_asylum_2019": ("Appointment_asylum_2019", 1, "Appointment"),
                "Appointment_asylum_2021":("Appointment_asylum_2021", 1, "Appointment"),
                "Approved_receipts": ("Approved_cases_asylum", 1, "Approved_receipts"),
                "Payment_receipt": ("Asylum_receipt", 1, "Payment_receipt"),
                "Defensive_receipt_2024": ("Defensive_receipt_2024", 1, "Defensive_receipt"),
                "Defensive_receipt_2020": ("Defensive_receipt_2020", 1, "Defensive_receipt"),
                "Defensive_receipt_2019":("Defensive_receipt_2019", 1, "Defensive_receipt"),
                "Application_to_asylum": ("Application_to_asylum", 1, "Application_to_asylum"),
                "Reused": ("Reused_asylum", 1, "Reused"),
                "Reused_2018":("Reused_2018", 1, "Reused"),
                "Reject": ("Reject", 1, "Reject"),
                "Reject_2020": ("Reject_2020", 1, "Reject"),
                "Receipt": ("Receipt", 1, "Receipts")
            }
        }

        # Obtener configuración según el tipo de documento
        config = doc_config.get(option, {}).get(doc_type)
        if not config:
            print(f"❌ Tipo de documento no reconocido: {doc_type}")
            result = {"name": f"{uuid.uuid4()}", "alien_number": f"{random.randint(1,10000)}", "doc_type": f"{uuid.uuid4()}", "folder_name":option}
            return save_and_ocr_optimized(result, processed_path, option, save_pdf)

        type_name, sheets_quantity, kind_of_doc = config

        # Búsqueda optimizada
        name = search_in_doc_optimized(page, type_name, "name", option)
        alien_number = search_in_doc_optimized(page, type_name, "a_number", option)

        if not name:
            print(f"❌ The system can't find Name: {name}")
            name = f"{uuid.uuid4()}" 

        if not alien_number: 
            print(f"❌ The system can't find Alien Number: {alien_number}")
            alien_number = f"A{random.randint(1, 10000)}"


        result = {"name": name, "alien_number": alien_number, "doc_type": kind_of_doc, "folder_name":option}
        return save_and_ocr_optimized(result, processed_path, option, save_pdf)

    except Exception as e:
        print(f"❌ Error en exect_funct_optimized: {e}")
        traceback.print_exc()
        return None

def process_single_page(page, option, processed_path, json_type):
    """Procesa una página individual con su propio PdfWriter"""
    try:
        pdf_save = PdfWriter()  # Nuevo PdfWriter para cada página
        model = process_page_optimized(page)
        if not model:
            return None
            
        # Guardar página en PDF
        image_stream = BytesIO()
        page.save(image_stream, format="PDF")
        pdf_save.append(image_stream)
        
        classification_functions = {
            "42BReceipts": model.find_receipts,
            "Asylum": model.find_receipts_asylum,
        }
        
        classify_func = classification_functions.get(option)
        if not classify_func:
            print(f"⚠️ Folder type did't found: {option}")
            return None
        
        doc_type = classify_func()
        
        if not doc_type:
            print(f"⚠️ The system can't index document in the {option} folder")
            return exect_funct_optimized("Error", page, option, processed_path, json_type, pdf_save)

        return exect_funct_optimized(doc_type, page, option, processed_path, json_type, pdf_save)
        
    except Exception as e:
        print(f"❌ Error to page process: {e}")
        traceback.print_exc()
        return None

def process_pages_parallel(pages, option, processed_path, json_type):
    """Procesa páginas en paralelo, cada una con su propio PDF"""
    results = []
    with ThreadPoolExecutor(max_workers=os.cpu_count() - 2) as executor:
        futures = [executor.submit(
            process_single_page, 
            page, option, processed_path, json_type
        ) for page in pages]
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    return results

def optimized_indexing(pdf: str, option: str, input_path: str, processed_path: str):
    """Versión optimizada de la función principal"""
    try:
        pdf_path = os.path.join(input_path, pdf)
        
        pages = convert_from_path(
            pdf_path,
            thread_count=6,
            dpi=200,
            grayscale=True,
            poppler_path=r'C:\Users\simon\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin'
        )
        
        json_type = "42B" if option == "42BReceipts" else "Asylum"
        results = process_pages_parallel(pages, option, processed_path, json_type)
        
        shutil.move(pdf_path, os.path.join(processed_path, pdf))
        return [r for r in results if r is not None]
        
    except Exception as e:
        print(f"Error en indexing: {e}")
        error_path = os.path.join(input_path, "Errors", os.path.basename(pdf))
        shutil.move(pdf_path, error_path)
        return []