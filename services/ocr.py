import ocrmypdf
#Funcion para realizar OCR a los documentos
def ocr(my_path):
    try:
        ocrmypdf.ocr(
            my_path,
            my_path,
            skip_text=True, 
            deskew=True
        )
    except Exception as e:
        print(f"Error in OCR services: {e}")