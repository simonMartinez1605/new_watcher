import os
import uuid
import sys
import json
import shutil
import random
import traceback
import numpy as np
import pytesseract
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from models.models import Model  
from PIL import Image, ImageFilter
from pdf2image import convert_from_path
from PyPDF2 import PdfWriter, PdfReader
from services.deskewing import deskew_image  
from services.compare_keys import find_similar_key  
from errors.errors import regex_name, regex_alien_number
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor

# --- Configuration ---
def get_base_path() -> Path:
    """Determines the base path of the application, handling PyInstaller's _MEIPASS."""
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    else:
        return Path(os.path.abspath(os.path.dirname(__file__)))

BASE_PATH = get_base_path()
DOTENV_PATH = BASE_PATH / '.env'
load_dotenv(dotenv_path=DOTENV_PATH)

# Set Tesseract command path
# Make sure this path is correct for your environment
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Global Caches and Data (Manage carefully with ProcessPoolExecutor)
_JSON_CACHE = {} # Use a dictionary directly for cache

# Global for FamilyClosedCases merging (will be managed per PDF in main process)
pending_merges = {}
# 'data' variable seems to be used globally for 'FamilyClosedCases' but its specific usage isn't clear from provided code.
# If 'data' is meant to store collected results for FamilyClosedCases before final merge, it should be managed locally per PDF.
# For now, I'll keep it as a placeholder if it's used elsewhere.
data = {} 

# --- Utility Functions ---
def resource_path(relative_path: str) -> Path:
    """Obtiene la ruta absoluta de un recurso relativo."""
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(os.path.abspath("."))
    return base_path / relative_path

PROYECT_JSONS_PATH = resource_path("jsons") # Renamed for clarity and consistency

def load_json_cached(file_path: Path) -> dict:
    """Carga JSON con caché para evitar lecturas repetidas de disco."""
    if file_path not in _JSON_CACHE:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                _JSON_CACHE[file_path] = json.load(f)
        except FileNotFoundError:
            print(f"Error: JSON file not found at {file_path}")
            return {} # Return empty dict or raise specific error
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {file_path}")
            return {}
    return _JSON_CACHE.get(file_path, {}) # Return an empty dict if key not found (e.g., on error)

def preprocess_image(image: Image.Image) -> Image.Image:
    """Mejora la imagen para OCR. Already returns grayscale."""
    return image.filter(ImageFilter.SHARPEN).convert('L') # Convert to grayscale directly after sharpen

def needs_deskewing(image: np.ndarray) -> bool:
    """Determina si la imagen necesita corrección de inclinación.
    
    Implementación básica - puedes mejorarla con detección de bordes o un modelo de ML.
    """
    # Placeholder: You might want to implement a more robust check here.
    # For now, it always returns True as in your original code.
    return True
# --- Core Processing Functions ---
def process_page_optimized(page_image: Image.Image) -> Model | None:
    """Versión optimizada del procesamiento de página para OCR.
    
    Args:
        page_image (Image.Image): La imagen PIL de la página a procesar.

    Returns:
        Model | None: Un objeto Model con los datos del OCR o None si hay un error.
    """
    try:
        # Preprocesamiento
        pil_image = preprocess_image(page_image)

        # Convertir a numpy array for deskewing.
        # deskew_image typically expects a 3-channel image for OpenCV.
        # Convert 'L' (grayscale) to 'RGB' for consistent OpenCV input, then to BGR.
        open_cv_image = np.array(pil_image.convert('RGB'))
        open_cv_image = open_cv_image[:, :, ::-1].copy() # Convert from RGB to BGR (OpenCV's default color order)

        # Deskewing condicional
        if needs_deskewing(open_cv_image):
            open_cv_image = deskew_image(open_cv_image)
            open_cv_image = open_cv_image[:, :, ::-1] # Convert BGR back to RGB

        # Configuration optimized for Tesseract
        custom_config = r'--oem 3 --psm 6'

        # Convert back to PIL Image (grayscale) for Tesseract
        # If open_cv_image is 3D (RGB after deskewing), convert to 'L' (grayscale).
        if len(open_cv_image.shape) == 3 and open_cv_image.shape[2] == 3:
            ocr_image = Image.fromarray(open_cv_image).convert('L')
        else: # Assumes it's already grayscale or 2D
            ocr_image = Image.fromarray(open_cv_image)

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

def search_in_doc_optimized(page_model: Model, name_doc: str, type_data: str, json_type: str) -> str | None:
    """Versión optimizada de búsqueda en documento.
    
    Args:
        page_model (Model): El objeto Model con los datos del OCR de la página.
        name_doc (str): El nombre del documento a buscar en el JSON.
        type_data (str): El tipo de dato a extraer (e.g., "name", "a_number").
        json_type (str): El nombre del archivo JSON a cargar (e.g., "42BReceipts").

    Returns:
        str | None: El resultado de la búsqueda o None si no se encuentra.
    """
    if not page_model:
        return None

    json_file_path = PROYECT_JSONS_PATH / f"{json_type}.json"

    # Check if the file exists directly using pathlib
    if not json_file_path.exists():
        print(f"JSON file not found at expected path: {json_file_path}")
        return None

    json_result = load_json_cached(json_file_path)

    # Búsqueda más eficiente usando una comprensión de generador
    matching_doc = next((doc for doc in json_result if doc.get("pdf") == name_doc), None)
    
    if not matching_doc or type_data not in matching_doc:
        return None

    key_word = matching_doc.get('key_word')
    if not key_word: # Ensure key_word exists
        return None

    for coord in matching_doc[type_data]:
        result = page_model.aproved_case(
            coord['x'], coord['y'],
            coord['width'], coord['height'],
            key_word
        )
        # Check if result is valid and within expected length
        if result and 1 < len(str(result)) < 170: # Convert result to string for length check
            return str(result) # Ensure result is a string
    return None

def save_single_page_pdf(image: Image.Image, result_meta: dict, processed_path: Path, option: str) -> dict | None:
    """Guarda una sola imagen PIL como un PDF individual y retorna sus metadatos.
    
    Args:
        image (Image.Image): La imagen PIL de la página a guardar.
        result_meta (dict): Diccionario con los resultados (nombre, número de extranjero, tipo de documento).
        processed_path (Path): La ruta donde se guardarán los PDFs procesados.
        option (str): El tipo de carpeta (e.g., "42BReceipts").

    Returns:
        dict | None: Diccionario con los metadatos del PDF guardado o None si hay un error.
    """
    try:
        processed_path.mkdir(parents=True, exist_ok=True)
        output_pdf_name = f"{result_meta.get('name', 'unknown')}.pdf"
        output_pdf_path = processed_path / output_pdf_name

        image.convert('RGB').save(output_pdf_path, save_all=True)

        return {
            "name": regex_name(result_meta.get('name', '')),
            "alien_number": regex_alien_number(result_meta.get('alien_number', '')),
            "pdf": str(output_pdf_path),
            "doc_type": result_meta.get('doc_type'),
            "folder_name": option
        }
    except Exception as e:
        print(f"❌ Error guardando PDF individual desde imagen: {e}")
        traceback.print_exc()
        return None

def merge_pages_to_pdf(images: list[Image.Image], result_meta: dict, processed_path: Path, option: str, pages_number: list[str] = None) -> dict | None:
    """Fusiona múltiples imágenes en un solo PDF.
    
    Args:
        images (list[Image.Image]): Lista de imágenes PIL a fusionar.
        result_meta (dict): Metadatos del documento fusionado.
        processed_path (Path): La ruta donde se guardará el PDF combinado.
        option (str): El tipo de carpeta.
        pages_number (list[str], optional): Lista de cadenas de números de página para ordenar.

    Returns:
        dict | None: Metadatos del PDF fusionado o None si hay un error.
    """
    try:
        processed_path.mkdir(parents=True, exist_ok=True)
        output_pdf_name = f"{result_meta.get('name', 'unknown')}.pdf"
        output_pdf_path = processed_path / output_pdf_name

        if pages_number:
            paired = list(zip(pages_number, images))
            def extract_page_num(p_str):
                try:
                    # Extracts number from "pageX" or "page_X"
                    return int(''.join(filter(str.isdigit, p_str)))
                except ValueError:
                    return float('inf') 

            paired.sort(key=lambda x: extract_page_num(x[0]))
            ordered_images = [img.convert('RGB') for _, img in paired]
        else:
            ordered_images = [img.convert('RGB') for img in images]

        if not ordered_images:
            print("No images to merge.")
            return None

        # Save the PDF
        ordered_images[0].save(output_pdf_path, save_all=True, append_images=ordered_images[1:])

        return {
            "name": regex_name(result_meta.get('name', '')),
            "pl": result_meta.get('pl', ''),
            "pdf": str(output_pdf_path),
            "case_type": result_meta.get('case_type', ''),
            "folder_name": option
        }
    except Exception as e:
        print(f"❌ Error guardando PDF combinado (imágenes): {e}")
        traceback.print_exc()
        return None

def exect_funct_optimized_single_page(doc_type: str, page_image: Image.Image, option: str, processed_path: Path, json_type: str) -> dict | None:
    """Función ejecutora optimizada para clasificar y procesar páginas (para documentos de una sola página).
    
    Args:
        doc_type (str): El tipo de documento clasificado.
        page_image (Image.Image): La imagen PIL de la página a procesar.
        option (str): La opción de carpeta (e.g., "42BReceipts", "Asylum").
        processed_path (Path): La ruta donde se guardarán los PDFs.
        json_type (str): El nombre del archivo JSON de configuración.

    Returns:
        dict | None: Los metadatos del documento procesado o None si hay un error.
    """
    doc_config = {
        "42BReceipts": {
            "Payment": ("Payment", 1, "Payment", "page1"),
            "Receipts1": ("Receipts_42B", 2, "Receipts", "page1"), # sheets_quantity 2 implies multi-page, but here it's processed as single
            "Receipts2": ("Receipts_42B", 2, "Receipts", "page2"), # sheets_quantity 2 implies multi-page, but here it's processed as single
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
            "Receipt_2023": ("Receipt_2023", 1, "Receipt", "page1"),
            "Receipt": ("Receipt", 1, "Receipts", "page1"),
            "Receipts1": ("Receipts_Asylum", 2, "Receipts", "page1"),
            "Receipts2": ("Receipts_Asylum", 2, "Receipts", "page2"),
            "Appointment": ("Appointment_asylum", 1, "Appointment", "page1"),
            "Appointment_asylum_2020": ("Appointment_asylum_2020", 1, "Appointment", "page1"),
            "Appointment_asylum_2019": ("Appointment_asylum_2019", 1, "Appointment", "page1"),
            "Appointment_asylum_2021": ("Appointment_asylum_2021", 1, "Appointment", "page1"),
            "Appointment_asylum_2022": ("Appointment_asylum_2022", 1, "Appointment", "page1"),
            "Approved_receipts": ("Approved_cases_asylum", 1, "Approved_receipts", "page1"),
            "Payment_receipt": ("Asylum_receipt", 1, "Payment_receipt", "page1"),
            "Defensive_receipt_2024": ("Defensive_receipt_2024", 1, "Defensive_receipt", "page1"),
            "Defensive_receipt_2023": ("Defensive_receipt_2023", 1, "Defensive_receipt", "page1"),
            "Defensive_receipt_2020": ("Defensive_receipt_2020", 1, "Defensive_receipt", "page1"),
            "Defensive_receipt_2019": ("Defensive_receipt_2019", 1, "Defensive_receipt", "page1"),
            "Application_to_asylum": ("Application_to_asylum", 1, "Application_to_asylum", "page1"),
            "Reused": ("Reused_asylum", 1, "Reused", "page1"),
            "Reused_2018": ("Reused_2018", 1, "Reused", "page1"),
            "Reject": ("Reject", 1, "Reject", "page1"),
            "Reject_2020": ("Reject_2020", 1, "Reject", "page1")
        }
        # FamilyClosedCases is handled separately for merging logic
    }

    try:
        config = doc_config.get(option, {}).get(doc_type)

        model = process_page_optimized(page_image)
        if not model:
            return None

        if not config:
            print(f"❌ Tipo de documento no reconocido: {doc_type} for option {option}. Assigning random metadata.")
            result = {
                "name": str(uuid.uuid4()),
                "alien_number": f"A{random.randint(1, 10000)}",
                "doc_type": doc_type,
                "folder_name": option
            }
            return save_single_page_pdf(page_image, result, processed_path, option)

        type_name, sheets_quantity, kind_of_doc, page_number_str = config # page_number_str is not used for saving single page

        name = search_in_doc_optimized(model, type_name, "name", option) or str(uuid.uuid4())
        alien_number = search_in_doc_optimized(model, type_name, "a_number", option) or f"A{random.randint(1, 10000)}"

        result = {
            "name": name,
            "alien_number": alien_number,
            "doc_type": kind_of_doc,
            "folder_name": option
        }
        return save_single_page_pdf(page_image, result, processed_path, option)

    except Exception as e:
        print(f"❌ Error en exect_funct_optimized_single_page: {e}")
        traceback.print_exc()
        return None

# This function is designed to be run by ProcessPoolExecutor
def process_single_page_for_pool(page_data: tuple[bytes, int], option: str, processed_path_str: str, json_type: str) -> dict | None:
    """Processes a single page received as bytes, suitable for ProcessPoolExecutor.
    
    Args:
        page_data (tuple[bytes, int]): A tuple containing the page image as bytes and its original index.
        option (str): The folder option.
        processed_path_str (str): The string representation of the processed path.
        json_type (str): The type of JSON to use.

    Returns:
        dict | None: The metadata of the processed document or None.
    """
    page_bytes, page_index = page_data
    processed_path = Path(processed_path_str) # Reconstruct Path object in child process

    try:
        # Recreate PIL Image from bytes
        page_image = Image.open(BytesIO(page_bytes))

        model = process_page_optimized(page_image)
        if not model:
            return None

        classification_functions = {
            "42BReceipts": model.find_receipts,
            "Asylum": model.find_receipts_asylum,
            # FamilyClosedCases classification is handled in the main process
        }

        classify_func = classification_functions.get(option)
        if not classify_func:
            print(f"⚠️ Folder type '{option}' not found in classification functions. Assigning to 'Error' type.")
            return exect_funct_optimized_single_page("Error", page_image, option, processed_path, json_type)

        doc_type = classify_func()

        if not doc_type:
            print(f"⚠️ The system can't index document in the {option} folder. Assigning to 'Error' type.")
            return exect_funct_optimized_single_page("Error", page_image, option, processed_path, json_type)

        return exect_funct_optimized_single_page(doc_type, page_image, option, processed_path, json_type)

    except Exception as e:
        print(f"❌ Error in process_single_page_for_pool for page index {page_index}: {e}")
        traceback.print_exc()
        return None

# --- Main Indexing Function ---
def optimized_indexing(pdf_filename, option, input_path, processed_path, pages: None):
    """Versión optimizada de la función principal de indexación.
    
    Args:
        pdf_filename (str): El nombre del archivo PDF a indexar.
        option (str): La opción de carpeta para clasificar el documento.
        input_path (Path): La ruta de entrada donde se encuentra el PDF.
        processed_path (Path): La ruta de salida donde se guardarán los PDFs procesados.

    Returns:
        list[dict]: Una lista de diccionarios con los metadatos de los documentos indexados.
    """
    # pdf_path = fr"{input_path}\{pdf_filename}"
    
    if not os.path.exists(pdf_filename):
        print(f"Error: PDF file not found at {pdf_filename}")
        return []

    results = []
    
    try:
        # Convert PDF pages to images using threads (efficient for I/O bound)
        # Ensure poppler_path is correctly configured for your system
        pages_pil_images = convert_from_path(
            str(pdf_filename),
            thread_count=os.cpu_count(), # Use all CPU cores for conversion
            dpi=150,
            grayscale=True,
            poppler_path=r'C:\Users\simon\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin' # IMPORTANT: Update this path!
        )
        
        # pages_length = len(pages_pil_images)

        if option == "FamilyClosedCases":
            # For FamilyClosedCases, process sequentially in the main process to handle merging logic
            # This ensures pending_merges is managed correctly for a single multi-page PDF.
            current_pdf_family_pages = []
            current_pdf_family_meta = {"name": "unknown", "pl": "", "case_type": str(uuid.uuid4())}
            current_pdf_page_numbers = []

            for i, page_image in enumerate(pages_pil_images):
                # if not model:
                #     continue

                # Classify (should always be "Family" if option is "FamilyClosedCases")
                # doc_type = model.find_family_closed_cases()
                # if not doc_type:
                #     print(f"⚠️ Page {i+1} of {pdf_filename}: Could not classify as FamilyClosedCases. Skipping for merge.")
                #     continue

                # Search for metadata on each page
                if i == 0:  # Only set metadata on the first page
                    print(f"Processing FamilyClosedCases PDF: {pdf_filename}")
                    model = process_page_optimized(page_image)
                    current_pdf_family_meta["name"] = search_in_doc_optimized(model, "Family", "name", option)
                    current_pdf_family_meta["case_type"] = search_in_doc_optimized(model, "Family", "case_type", option)
                    current_pdf_family_meta["pl"] = search_in_doc_optimized(model, "Family", "pl", option)
                    current_pdf_family_pages.append(page_image)
                    current_pdf_page_numbers.append(f"page{i+1}")
                    print(f"Processing page {i+1} - {pages} of {pdf_filename} for FamilyClosedCases.")
                    if current_pdf_family_meta["name"] is None:
                        current_pdf_family_meta["name"] = str(uuid.uuid4())
                        print(f"⚠️ No name found for FamilyClosedCases PDF. Using UUID: {current_pdf_family_meta['name']}")
                else: 
                    current_pdf_family_pages.append(page_image)
                    current_pdf_page_numbers.append(f"page{i+1}")
                    print(f"Processing page {i+1} - {pages} of {pdf_filename} for FamilyClosedCases.")

            if current_pdf_family_pages:
                # After processing all pages for this FamilyClosedCases PDF, merge them
                merged_result = merge_pages_to_pdf(
                    current_pdf_family_pages,
                    current_pdf_family_meta,
                    processed_path,
                    option,
                    current_pdf_page_numbers
                )
                if merged_result:
                    results.append(merged_result)
            else:
                print(f"No pages collected for merging for {pdf_filename} in FamilyClosedCases.")

        # else:
        #     # For other document types, process pages in parallel using ProcessPoolExecutor
        #     # Each page will result in a separate PDF.
            
        #     # Serialize PIL Images to bytes to pass to child processes
        #     # This avoids issues with pickling PIL Image objects directly
        #     pages_as_bytes = []
        #     for i, page_image in enumerate(pages_pil_images):
        #         img_byte_arr = BytesIO()
        #         page_image.save(img_byte_arr, format="PNG") # Use PNG for lossless serialization
        #         pages_as_bytes.append((img_byte_arr.getvalue(), i))

        #     # Using os.cpu_count() for max_workers to leverage all cores for CPU-bound tasks.
        #     # You can adjust this (e.g., max(1, os.cpu_count() - 1)) if you need to reserve a core.
        #     max_workers = os.cpu_count()
            
        #     with ProcessPoolExecutor(max_workers=max_workers) as executor:
        #         futures = [executor.submit(
        #             process_single_page_for_pool,
        #             page_byte_data, option, str(processed_path), option
        #         ) for page_byte_data in pages_as_bytes]

        #         for future in as_completed(futures):
        #             try:
        #                 result = future.result()
        #                 if result:
        #                     results.append(result)
        #             except Exception as e:
        #                 print(f"Error in parallel page processing for {pdf_filename}: {e}")
        #                 traceback.print_exc()

        # Move the original PDF to the processed path after all its pages have been handled
        # processed_path.mkdir(parents=True, exist_ok=True)
        # shutil.move(pdf_filename, processed_path / pdf_filename)
        
        # Filter out None results and return the list
        return [r for r in results if r is not None]

    except Exception as e:
        print(f"Error en indexing para {pdf_filename}: {e}")
        traceback.print_exc()
        
        # Move the problematic PDF to an "Errors" folder
        error_dir = input_path / "Errors"
        error_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(pdf_filename, error_dir / pdf_filename)
        return []