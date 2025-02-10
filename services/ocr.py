import ocrmypdf

def ocr(my_path): 
    ocrmypdf.ocr(
        my_path, 
        my_path, 
        skip_text=True 
    )