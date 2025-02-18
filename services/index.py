from pdf2image import convert_from_path
from PyPDF2 import PdfWriter
from models.models import Model
from services.ocr import ocr 
from dotenv import load_dotenv
from services.conection import sharepoint 
import os
import pytesseract

load_dotenv()

save_pdf = os.getenv('SAVE_PDF')

save_pdf = save_pdf.replace("\\", "/") 
#Funcion para poder obtener el nombre y numero de Alien 
def indexing(pdf):
    pages = convert_from_path(pdf)
    print(f"Review documents")

    try: 
        for i in range(0, len(pages), 2):
            page1 = pages[i]
            page2 = pages[i + 1] if i + 1 < len(pages) else None

            data_ocr_page1 = pytesseract.image_to_data(page1, output_type=pytesseract.Output.DICT)
            doc_type = Model(data_ocr_page1, page1).search_form() 

            if doc_type == True:
                result = Model(data_ocr_page1, page1).search_I_485() 
                print(f"Page {i+1}: Indexed")

            # Crea un nuevo PdfWriter para cada par de páginas
            pdf_writer = PdfWriter()

            # Guarda la primera página en el PDF
            page1_path = f"{save_pdf}{result['name']}.pdf" 
            page1.save(page1_path, "PDF")
            pdf_writer.append(page1_path)

            if page2:
                # Guarda la segunda página en el PDF
                page2_path = f"{save_pdf}{result['name']}.pdf" 
                page2.save(page2_path, "PDF")
                pdf_writer.append(page2_path)
                print(f"Page {i+2}: Saved")
    
            # Guarda el PDF combinado para este par de páginas
            output_pdf_path = f"{save_pdf}{result['name']}.pdf"
            with open(output_pdf_path, "wb") as output_pdf:
                pdf_writer.write(output_pdf)

            ocr(output_pdf_path) 

            sharepoint(output_pdf_path ,f"{result['name']}.pdf", result['alien_number']) 

            print(f"Combined PDF saved as {output_pdf_path}")
    except Exception as e: 
        print(f"Error in indexing module : {e}")


if __name__ == "__main__":
    if not os.path.exists(save_pdf):
        os.makedirs(save_pdf)
    indexing("c:/Users/SimonMartinez/Documents/Simon/View Folder/OCR/Done/simon.pdf")