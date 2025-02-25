import pytesseract 

class Model(): 
    def __init__(self, data_ocr, item): 
        self.data_ocr = data_ocr 
        self.item = item 

    def find_42B(self): 
        try: 
            for i, word in enumerate(self.data_ocr['text']): 

                if word == "APPLICANT":
                    x,y,w,h = self.data_ocr['left'][i], self.data_ocr['top'][i], self.data_ocr['width'][i], self.data_ocr['height'][i]
                    region_x = x - 50
                    region_y = y - 80
                    region_w = 200 
                    region_h = 100

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                    status = pytesseract.image_to_string(region)
                    status = status.replace("\n", "")
                    status = status.replace("/", "")

                    if "EOIR" in status: 
                        return True
                    else: 
                        return False 
        except Exception as e: 
            print(f"Error in search model: {e}")
            return False 
        
    def search(self): 
        try: 
            for i, word in enumerate(self.data_ocr['text']): 
                if word == "APPLICANT":
                    x,y,w,h = self.data_ocr['left'][i], self.data_ocr['top'][i], self.data_ocr['width'][i], self.data_ocr['height'][i]

                    region_x = x - 20
                    region_y = y + 15
                    region_w = 800 
                    region_h = 45 

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    name = pytesseract.image_to_string(region)

                    name = name.replace("\n", "")
                    name = name.replace("/", "")
                    name = name.replace("|", "")

                    print(f"Document name: {name}") 

                    region_x = x + 145
                    region_y = y - 1 
                    region_w = 250 
                    region_h = 35 

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    alien_number = pytesseract.image_to_string(region)

                    alien_number = alien_number.replace("\n", "")
                    alien_number = alien_number.replace("/", "")
                    alien_number = alien_number.replace(" ", "")

                    print(f"Alien number: {alien_number}") 

                    return {
                        'name':name, 
                        'alien_number':alien_number 
                    }   
        except Exception as e: 
            print(f"Error in search model: {e}")
            return False