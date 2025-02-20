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

def indexing(pdf): 
    pages = convert_from_path(pdf)

    pdf_save = PdfWriter() 

    try: 
        for i in range(0, len(pages)): 
            
            page1 = pages[i]
            data_ocr_page = pytesseract.image_to_data(page1, output_type=pytesseract.Output.DICT) 

            doc_type = Model(data_ocr_page, page1).find() 

            
            page_path = f"{save_pdf}{doc_type}.pdf"  
            page1.save(page_path, "PDF") 
            pdf_save.append(page_path) 

            if doc_type == True: 
                result = Model(data_ocr_page, page1).search()
                output_pdf_path = f"{save_pdf}{result['name']}.pdf"
                with open(output_pdf_path, "wb") as output_pdf:
                    pdf_save.write(output_pdf)  
                print(f"Combined PDF saved as {output_pdf_path}") 

                ocr(output_pdf_path)

                sharepoint(output_pdf_path, f"{result['name']}.pdf", result['alien_number']) 

                pdf_save = PdfWriter() 

    except Exception as e: 
        print(f"Error in indexing module : {e}")

if __name__ == "__main__":
    indexing(save_pdf)   