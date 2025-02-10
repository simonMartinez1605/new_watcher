import pytesseract 

def form(data_ocr, item): 
    for i, word in enumerate(data_ocr['text']): 
        if word == "Applicant":
            print(word) 
            x,y,w,h = data_ocr['left'][i], data_ocr['top'][i], data_ocr['width'][i], data_ocr['height'][i]

            region_x = x - 60
            region_y = y - 75
            region_w = 100 
            region_h = 37 

            region = item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

            text = pytesseract.image_to_string(region)

            text = text.replace("\n", "")

            text = text.replace("/", "")

            print(f"Document type {text}")

            if "1485" in text: 
                return True 
            else: 
                return False 
            

def I_485(data_ocr, item): 
    for i, word in enumerate(data_ocr['text']): 
        if word == "Applicant":
            print(word) 
            x,y,w,h = data_ocr['left'][i], data_ocr['top'][i], data_ocr['width'][i], data_ocr['height'][i]

            region_x = x - 15
            region_y = y + 7
            region_w = 470 
            region_h = 50 

            region = item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

            text = pytesseract.image_to_string(region)

            text = text.replace("\n", "")
            text = text.replace("/", "")

            return text 

           