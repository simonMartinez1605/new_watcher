import ocrmypdf
#Funcion para realizar OCR a los documentos
def ocr(my_path : str) -> str:
    """
    Funcion para realizar OCR a los documentos

    Parametros: 
    ------------

    my_path: str 
        Recibe el path del documento al que se le desea aplicar OCR, a la vez lo reemplaza y corrigue los defectos de escaneo que tengan
    
    """
    try:
        ocrmypdf.ocr(
            my_path,
            my_path,
            skip_text=True, 
            deskew=True
        )
    except Exception as e:
        print(f"Error in OCR services: {e}")