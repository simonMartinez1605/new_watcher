import os
import uuid
import json
import shutil
import random
import traceback
import pytesseract
import numpy as np
from io import BytesIO
from dotenv import load_dotenv
from models.models import Model
from PIL import Image, ImageFilter
from PyPDF2 import PdfWriter, PdfReader
from pdf2image import convert_from_path
from services.deskewing import deskew_image
from services.compare_keys import find_similar_key
from errors.errors import regex_name, regex_alien_number
from concurrent.futures import ThreadPoolExecutor, as_completed

# Cargar variables de entorno
load_dotenv(override=True)

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Configuración global
_JSON_CACHE = {}

pending_merges = {}

def load_json_cached(file_path: str) -> dict:
    """Carga JSON con caché para evitar lecturas repetidas de disco"""
    print(file_path)
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
        
    json_path = fr"C:\Users\simon\OneDrive\Documents\Simon\Python\new_watcher\jsons\{json_type}.json"
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
        if result and 1 < len(result) < 170:
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
    
def copy_pdf(input_path, output_path):
    """Copia un PDF de input_path a output_path"""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        with open(output_path, "wb") as output_file: 
            writer.write(output_file)

        return output_file

    except Exception as e:
        print(f"❌ Error al copiar el PDF: {e}")
        return False
    

def merge_pages(images, result, processed_path, option, pages_number=None):
    try:
        output_pdf_path = os.path.join(processed_path, f"{result['name']}.pdf")

        # Si se proporciona pages_number, ordenar las imágenes en base a ese orden
        if pages_number:
            # Emparejar páginas con sus números
            paired = list(zip(pages_number, images))

            # Extraer número como entero de strings tipo "page2"
            def extract_page_num(p): return int(p.replace("page", "").strip())
            paired.sort(key=lambda x: extract_page_num(x[0]))

            # Obtener imágenes ordenadas
            ordered_images = [img.convert('RGB') for _, img in paired]
        else:
            # Si no hay pages_number, convertir directamente todas las imágenes a RGB
            ordered_images = [img.convert('RGB') for img in images]

        # Guardar el PDF
        ordered_images[0].save(output_pdf_path, save_all=True, append_images=ordered_images[1:])

        return {
            "name": regex_name(result['name']),
            "pl": result['pl'],
            "pdf": output_pdf_path,
            "case_type": result['case_type'],
            "folder_name": option
        }
        return {
            "name": regex_name(result['name']),
            "alien_number": regex_alien_number(result['alien_number']),
            "pdf": output_pdf_path,
            "doc_type": result['doc_type'],
            "folder_name": option
        }
    except Exception as e:
        print(f"❌ Error guardando PDF combinado (imágenes): {e}")
        return None

def exect_funct_optimized(doc_type, page, option, processed_path, json_type, save_pdf, pages_length=None):
    try:
        doc_config = {
            "42BReceipts": {
                "Payment": ("Payment", 1, "Payment", "page1"),
                "Receipts1": ("Receipts_42B", 2, "Receipts", "page1"),
                "Receipts2": ("Receipts_42B", 2, "Receipts", "page2"),
                "Appointment": ("Appointment_42B", 1, "Appointment", "page1"),
                "Reused": ("Reused_42B", 1, "Reused", "page1"),
            },
            "Asylum": {
                "Lack_notice": ("Lack_notice", 1, "Lack_notice", "page1"),
                "Notice1": ("Notice1", 1, "Notice", "page2"),
                "Evidence_notice_1": ("Evidence_notice_1", 2, "Evidence_notice", "page1"),
                "Evidence_notice_2": ("Evidence_notice_2", 2, "Evidence_notice", "page2"),
                "Interview_Waiver_1": ("Interview_Waiver_1", 2, "Interview_Waiver", "page1"),
                "Interview_Waiver_2": ("Interview_Waiver_2", 2, "Interview_Waiver", "page2"),
                "Receipt_2023":("Receipt_2023", 1, "Receipt", "page1"),
                "Receipt": ("Receipt", 1, "Receipts", "page1"),
                "Receipts1": ("Receipts_Asylum", 2, "Receipts", "page1"),
                "Receipts2": ("Receipts_Asylum", 2, "Receipts", "page2"),
                "Appointment": ("Appointment_asylum", 1, "Appointment", "page1"),
                "Appointment_asylum_2020": ("Appointment_asylum_2020", 1, "Appointment", "page1"),
                "Appointment_asylum_2019": ("Appointment_asylum_2019", 1, "Appointment", "page1"),
                "Appointment_asylum_2021":("Appointment_asylum_2021", 1, "Appointment", "page1"),
                "Appointment_asylum_2022":("Appointment_asylum_2022", 1, "Appointment", "page1"),
                "Approved_receipts": ("Approved_cases_asylum", 1, "Approved_receipts", "page1"),
                "Payment_receipt": ("Asylum_receipt", 1, "Payment_receipt", "page1"),
                "Defensive_receipt_2024": ("Defensive_receipt_2024", 1, "Defensive_receipt", "page1"),
                "Defensive_receipt_2023": ("Defensive_receipt_2023", 1, "Defensive_receipt", "page1"),
                "Defensive_receipt_2020": ("Defensive_receipt_2020", 1, "Defensive_receipt", "page1"),
                "Defensive_receipt_2019":("Defensive_receipt_2019", 1, "Defensive_receipt", "page1"),
                "Application_to_asylum": ("Application_to_asylum", 1, "Application_to_asylum", "page1"),
                "Reused": ("Reused_asylum", 1, "Reused", "page1"),
                "Reused_2018":("Reused_2018", 1, "Reused", "page1"),
                "Reject": ("Reject", 1, "Reject", "page1"),
                "Reject_2020": ("Reject_2020", 1, "Reject", "page1")
            }, 
            "FamilyClosedCases": {
                "Family":("Family", 3, "Family", "page1"),
            }
        }

        config = doc_config.get(option, {}).get(doc_type)
        if not config:
            print(f"❌ Tipo de documento no reconocido: {doc_type}")
            result = {"name": f"{uuid.uuid4()}", "alien_number": f"{random.randint(1,10000)}", "doc_type": f"{uuid.uuid4()}", "folder_name":option}
            # return save_and_ocr_optimized(result, processed_path, option, save_pdf)

        if option == "FamilyClosedCases":
            
            name = search_in_doc_optimized(page, "Family", "name", option) or str(uuid.uuid4())
            case_type = search_in_doc_optimized(page, "Family", "case_type", option) or f"{uuid.uuid4()}"
            pysical_location = search_in_doc_optimized(page, "Family", "pl", option) or f"{uuid.uuid4()}"

            print(pysical_location)

            key = "FamlyClosedCases"

            pending_merges.setdefault(key, {
                "pages": [], 
                "meta":{"name": name, "case_type": case_type, "pl": pysical_location},
                "pages_number": []
            })

            pending_merges[key]["pages"].append(page)

            if len(pending_merges[key]['pages']) == pages_length:
                merged = merge_pages(
                    pending_merges[key]["pages"],
                    pending_merges[key]["meta"],
                    processed_path,
                    option,
                    pending_merges[key]["pages_number"]
                )

                del pending_merges[key]
                return merged

        type_name, sheets_quantity, kind_of_doc, page_number = config

        name = search_in_doc_optimized(page, type_name, "name", option) or str(uuid.uuid4())

        alien_number = search_in_doc_optimized(page, type_name, "a_number", option) or f"A{random.randint(1, 10000)}"
        
        key = f"{name}_{sheets_quantity}_{kind_of_doc}"

        if sheets_quantity > 1:
            # Buscar si ya hay una key similar
            similar_key = find_similar_key(key, pending_merges)

            # Usar la key similar o la original
            used_key = similar_key if similar_key else key

            # Si no existe, inicializamos
            pending_merges.setdefault(used_key, {
                "pages": [],
                "meta": {"name": name, "alien_number": alien_number, "doc_type": kind_of_doc}, 
                "pages_number": []
            })

            # Añadimos la página
            pending_merges[used_key]["pages"].append(page)
            if pending_merges[used_key]['pages_number'] != []:
                for page_info in pending_merges[used_key]['pages_number']:
                    if page_info != page_number:
                        pending_merges[used_key]["pages_number"].append(page_number)

            else: 
                pending_merges[used_key]["pages_number"].append(page_number)

            if len(pending_merges[used_key]['pages']) == sheets_quantity:
                # print(f"Name: {pending_merges[used_key]['name']}")
                merged = merge_pages(
                    pending_merges[used_key]["pages"],
                    pending_merges[used_key]["meta"],
                    processed_path,
                    option, 
                    pending_merges[used_key]["pages_number"]
                )
                del pending_merges[used_key]
                return merged
            
        else: 
            result = {
                "name": name,
                "alien_number": alien_number,
                "doc_type": kind_of_doc,
                "folder_name": option
            }
            return save_and_ocr_optimized(result, processed_path, option, save_pdf)
        
    except Exception as e:
        print(f"❌ Error en exect_funct_optimized: {e}")
        traceback.print_exc()
        return None
    except Exception as e:
        print(f"❌ Error en exect_funct_optimized: {e}")
        traceback.print_exc()
        return None

def process_single_page(page, pages_length, option, processed_path, json_type):
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
            "FamilyClosedCases": model.find_family_closed_cases
        }
        
        classify_func = classification_functions.get(option)
        if not classify_func:
            print(f"⚠️ Folder type did't found: {option}")
            return None
        
        doc_type = classify_func()

        if not doc_type:
            print(f"⚠️ The system can't index document in the {option} folder")
            return exect_funct_optimized("Error", page, option, processed_path, json_type, pdf_save, pages_length)

        return exect_funct_optimized(doc_type, page, option, processed_path, json_type, pdf_save, pages_length)
        
    except Exception as e:
        print(f"❌ Error to page process: {e}")
        traceback.print_exc()
        return None

def process_pages_parallel(pages, pages_length, option, processed_path, json_type):
    """Procesa páginas en paralelo, cada una con su propio PDF"""
    results = []
    with ThreadPoolExecutor(max_workers=os.cpu_count() - 2) as executor:
        futures = [executor.submit(
            process_single_page, 
            page, pages_length, option, processed_path, json_type
        ) for page in pages]
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    return results

def optimized_indexing(pdf: str, option: str, input_path: str, processed_path: str, pages_length: int = None):
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
        
        results = process_pages_parallel(pages, pages_length, option, processed_path, option)
        
        shutil.move(pdf_path, os.path.join(processed_path, pdf))
        return [r for r in results if r is not None]
        
    except Exception as e:
        print(f"Error en indexing: {e}")
        error_path = os.path.join(input_path, "Errors", os.path.basename(pdf))
        shutil.move(pdf_path, error_path)
        return []