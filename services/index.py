from pdf2image import convert_from_path
from PyPDF2 import PdfWriter
from models.models import Model
from services.ocr import ocr 
from dotenv import load_dotenv
from services.conection import sharepoint 
import os
import pytesseract
import shutil

load_dotenv()

#funcion para indexar los documentos
def indexing(pdf, option, path): 
    #Convertir pdf en hojas 
    pages = convert_from_path(pdf)

    #Uso de la libreria PdfWriter la cual puede almacenar contenido pdf en una lista 
    pdf_save = PdfWriter() 

    try: 
        #Iterar sobre las hojas del pdf 
        for i in range(0, len(pages)): 
            
            page1 = pages[i]
            #Uso de pytesseract para el reconocimento optico y convertir las hojas en un diccionario de palabras 
            data_ocr_page = pytesseract.image_to_data(page1, output_type=pytesseract.Output.DICT) 
            
            #Manejo de casos para los diferentes tipos de archivos que llegan 
            match option: 
                case "42BReceipts":

                    #Implementacion del modelo de busqueda 
                    doc_type = Model(data_ocr_page, page1).find_42B()

                    #Guardar cada una de las hojas en formato pdf 
                    page_path = fr"{path}.pdf"
                    page1.save(page_path, "PDF") 
                    #Añadir la pagina convertida a pdf en la libreria de PdfWriter 
                    pdf_save.append(page_path) 

                    #Validacion del tipo de documento que entra
                    if doc_type == True: 
                        #Uso de la funcion search para encontrar el ancla, la cual nos indica que es el ultimo documento ligado a la misma persona 
                        result = Model(data_ocr_page, page1).search()

                        #Combinacion de los documentos guardados 
                        output_pdf_path = f"{path}{result['name']}.pdf"
                        with open(output_pdf_path, "wb") as output_pdf:
                            pdf_save.write(output_pdf)  
                        print(f"Combined PDF saved as {output_pdf_path}") 

                        #Aplicamiento de OCR (Optical Character Recognition)
                        ocr(output_pdf_path)

                        print(f"OCR completed for {output_pdf_path}") 

                        #Guardar la informacion extraida y el documento pdf en sharepoint 
                        sharepoint(output_pdf_path, f"{result['name']}.pdf", result['alien_number'],option) 

                        #Vaciar libreria de guardado para otra posible iteracion 
                        pdf_save = PdfWriter()
                case "Criminal": 
                    print("Criminal case") 
    except Exception as e: 
        print(f"Error in indexing module : {e}")
        shutil.move(pdf, f"{path}\Errors\{os.path.basename(pdf)}")

if __name__ == "__main__":
    indexing("save_pdf")   