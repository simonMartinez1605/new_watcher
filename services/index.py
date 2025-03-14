from pdf2image import convert_from_path
from PyPDF2 import PdfWriter
from models.models import Model
from services.ocr import ocr
from dotenv import load_dotenv
from services.conection import sharepoint
import os
import pytesseract
import shutil
import traceback
from io import BytesIO

load_dotenv()

def process_page(page):
    """Procesa una sola página del PDF con OCR."""
    data_ocr_page = pytesseract.image_to_data(page, output_type=pytesseract.Output.DICT)
    return Model(data_ocr_page, page)

def save_and_ocr(pdf_save, processed_path, result, doc_name, option):
    """Guarda el PDF combinado en la carpeta de procesados, aplica OCR y lo sube a SharePoint."""
    
    # Asegurarse de que la carpeta de procesados exista
    os.makedirs(processed_path, exist_ok=True)
    
    output_pdf_path = os.path.join(processed_path, f"{result['name']}.pdf")

    with open(output_pdf_path, "wb") as output_pdf:
        pdf_save.write(output_pdf)

    print(f"Combined PDF saved as {output_pdf_path}")
    
    ocr(output_pdf_path)
    print(f"OCR completed for {output_pdf_path}")

    sharepoint(output_pdf_path, f"{result['name']}-{doc_name}.pdf", result['alien_number'], option, doc_name)

def indexing(pdf, option, input_path, processed_path):
    """Convierte un PDF a imágenes, aplica OCR y clasifica documentos."""
    
    pages = convert_from_path(os.path.join(input_path, pdf))
    pdf_save = PdfWriter()

    try:
        for page in pages:
            model = process_page(page)
            image_stream = BytesIO()
            page.save(image_stream, format="PDF")
            pdf_save.append(image_stream)

            if option == "42BReceipts":
                doc_type = model.find_42B()
                
                match doc_type:
                    case "Payment":
                        result = model.search_receipts()
                        save_and_ocr(pdf_save, processed_path, result, "Payment", option)
                        pdf_save = PdfWriter()  # Reset para siguiente documento
                    case "Receipts":
                        result = model.aproved_case()
                        save_and_ocr(pdf_save, processed_path, result, "Receipts", option)
                        pdf_save = PdfWriter()
                    case "Appointment":
                        result = model.appointment()
                        save_and_ocr(pdf_save, processed_path, result, "Appointment", option)
                        pdf_save = PdfWriter()
            elif option == "Criminal":
                print("Criminal case")
        
        # Mover el documento original a la carpeta de procesados para evitar duplicados
        shutil.move(os.path.join(input_path, pdf), os.path.join(processed_path, pdf))
    
    except Exception as e:
        print(f"Error in indexing module: {e}")
        print(traceback.format_exc())

        error_path = os.path.join(input_path, "Errors", os.path.basename(pdf))
        shutil.move(os.path.join(input_path, pdf), error_path)

if __name__ == "__main__":
    input_path = "incoming_docs"   # Carpeta donde se encuentran los PDFs sin procesar
    processed_path = "processed_docs"  # Carpeta donde se guardarán los PDFs procesados
    pdf = "document.pdf"  
    option = "42BReceipts"
    
    indexing(pdf, option, input_path, processed_path)
