import pytesseract
import re

pattern = r"^A\d{9}$"

def regex(cadena): 
    alien_number = re.sub(r"\D", "", cadena)

    return f"A{alien_number}" 

class Model():
    def __init__(self, data_ocr, item):
        self.data_ocr = data_ocr
        self.item = item

    def find_42B(self):
        try:

            for i, word in enumerate(self.data_ocr['text']):
                x,y,w,h = self.data_ocr['left'][i], self.data_ocr['top'][i], self.data_ocr['width'][i], self.data_ocr['height'][i]

                if word == "Page":
                    region_x = x
                    region_y = y
                    region_w = 210
                    region_h = 110

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                    status = pytesseract.image_to_string(region)
                    status = status.replace("\n", "").replace("/", "")

                    if "Page2" in status: 
                        return "Aproved"
                    else: 
                        return False
                    

                if word == "APPLICANT":
                    region_x = x - 50
                    region_y = y - 80
                    region_w = 200
                    region_h = 100

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                    status = pytesseract.image_to_string(region)
                    status = status.replace("\n", "").replace("/","")

                    if "EOIR" in status:
                        return "Receipt"
                    else:
                        region_x = x - 890
                        region_y = y - 200
                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h)) 
                        status = pytesseract.image_to_string(region)
                        status = status.replace("/","").replace("\n", "")

                        if "EOIR" in status: 
                            return "Receipt" 
                        else: return False

                if word == "Appointment": 
                    region_x = x + 380
                    region_y = y + 6
                    region_w = 110
                    region_h = 60

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                    status = pytesseract.image_to_string(region)
                    status = status.replace("\n", "").replace("/","")

                    status = re.sub(r"\D", "", status)

                    status = f"{status}" 

                    if "I485" in status or "1485" in status:
                        return "Appointment"
                    else:
                         
                        return False
                        
        except Exception as e:
            print(f"Error in search model: {e}")
            return False
        
    def search_receipts(self):
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

                    name = name.replace("\n", "").replace("/", "").replace("|", "")

                    print(f"Document name: {name}")

                    region_x = x + 145
                    region_y = y - 1
                    region_w = 250
                    region_h = 35

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    alien_number = pytesseract.image_to_string(region)

                    alien_number = regex(alien_number) 
                    
                    print(f"Alien number: {alien_number}")

                    return {
                        'name':name,
                        'alien_number':alien_number
                    }
        except Exception as e:
            print(f"Error in search model: {e}")
            return False
        
    def aproved_case(self): 
        try: 
            for i, word in enumerate(self.data_ocr['text']): 
                if word == "Page": 
                    x,y,w,h = self.data_ocr['left'][i], self.data_ocr['top'][i], self.data_ocr['width'][i], self.data_ocr['height'][i]
                    region_x = x + 300
                    region_y = y + 20
                    region_w = 800
                    region_h = 50

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    name = pytesseract.image_to_string(region)

                    name = name.replace("\n", "").replace("|", "").replace("/", "")

                    print(f"Document name: {name}")

                    region_x = x + 433
                    region_y = y + 4
                    region_w = 215
                    region_h = 35

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    alien_number = pytesseract.image_to_string(region)

                    alien_number = regex(alien_number) 

                    print(f"Alien number: {alien_number}")

                    return {
                        'name':name,
                        'alien_number':alien_number
                    }
        except Exception as e: 
            print(e)

    def appointment(self): 
        try: 
            for i, word in enumerate(self.data_ocr['text']): 
                if word == "Appointment": 
                    x,y,w,h = self.data_ocr['left'][i], self.data_ocr['top'][i], self.data_ocr['width'][i], self.data_ocr['height'][i]
                    region_x = x - 50
                    region_y = y + 250
                    region_w = 800
                    region_h = 50

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    name = pytesseract.image_to_string(region)

                    name = name.replace("\n", "").replace("|", "").replace("/", "")

                    print(f"Document name: {name}")

                    region_x = x + 920
                    region_y = y + 65
                    region_w = 215
                    region_h = 80

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    alien_number = pytesseract.image_to_string(region)

                    alien_number = regex(alien_number) 

                    print(f"Alien number: {alien_number}")

                    return {
                        'name':name,
                        'alien_number':alien_number
                    }
        except Exception as e: 
            print(e)