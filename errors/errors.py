from PyPDF2 import PdfWriter
import os 
import re
import uuid

def custom_errors(pages_pdf : list ,quantity:int) -> bool: 
    """Manejo de errores customizado por cada una de las hojas guardadas dentro del pdf"""
    pages_pdf = len(pages_pdf)
    print(pages_pdf)
    if pages_pdf != quantity:
        print(f"❌ Error in quantity sheets: {pages_pdf }")
        return True
    
    return False

def errors_folder(pdf_save : list ,procces_path : str , result : dict) -> bool: 
    """Funcion para validar informacion y guardar errores en caso de que alguno de los datos este vacio"""
    if result is None or result['name'] == None or result['alien_number'] == None or result['name'] == "" or result['alien_number'] == "": 
        error_folder = os.path.join(procces_path, "Errors")
        os.makedirs(error_folder, exist_ok=True)
        output_pdf_path = os.path.join(error_folder, f"{uuid.uuid4()}.pdf")

        with open(output_pdf_path, "wb") as output_pdf: 
            pdf_save.write(output_pdf) 
        
        print(f"❌ Error in result response: {result}")
        print(f" Doc save in errors folders: {output_pdf_path}")

        pdf_save = PdfWriter() 
        return True 

def regex_alien_number(cadena : str) -> str:
    """"Expresionr regular para el alien number encontrado"""
    alien_number = re.sub(r"\D", "", cadena)
    return f"A{alien_number}"

def regex_name(text : str) -> str:
    """"Expresion regular para el nombre econtrado"""
    regex = r"[^A-ZÁÉÍÓÚáéíóúÑñÜü ]"
    return re.sub(regex, "", text)