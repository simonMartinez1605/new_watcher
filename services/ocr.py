import os
import ocrmypdf
#Funcion para realizar OCR a los documentos
def ocr(my_path : str) -> str:
    """
    Funcion para realizar OCR a los documentos

    Parametros: 
    ------------

    my_path: str 
        Recibe el path del documento al que se le desea aplicar OCR, a la vez lo reemplaza y corrigue los defectos de escaneo que tengan
        Para optimizar el proceso, se utiliza la cantidad de nucleos del CPU disponibles para realizar el OCR en paralelo.
    
    """
    try:
        ocrmypdf.ocr(
            my_path,
            my_path,
            skip_text=True, 
            deskew=True, 
            jobs=os.cpu_count(), 
            optimize=0, 
        )
    except Exception as e:
        print(f"Error in OCR services: {e}")