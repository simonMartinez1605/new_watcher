import pytesseract
import re
import uuid

pattern_alien_number = r"^A\d{9}$"

def regex_alien_number(cadena): 
    alien_number = re.sub(r"\D", "", cadena)

    return f"A{alien_number}" 

def regex_name(text): 
    regex = r"[^A-ZÁÉÍÓÚáéíóúÑñÜü ]"

    return re.sub(regex, "", text) 

class Model():
    def __init__(self, data_ocr, item):
        self.data_ocr = data_ocr
        self.item = item

    def find_42B(self):
        try:

            for i, word in enumerate(self.data_ocr['text']):
                x,y,w,h = self.data_ocr['left'][i], self.data_ocr['top'][i], self.data_ocr['width'][i], self.data_ocr['height'][i]

                if word == "Priority" or word == "Page":
                    region_x = x
                    region_y = y
                    region_w = 140
                    region_h = 140

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                    status = pytesseract.image_to_string(region)
                    status = status.replace("\n", "").replace("/", "")

                    if "Page2" in status: 
                        return "Receipts"
                    else: 
                        region_x = x - 1
                        region_h = 141
                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h)) 
                        status = pytesseract.image_to_string(region)
                        status = status.replace("/","").replace("\n", "")

                        if "Page2" in status: 
                            return "Receipts" 
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
                        return "Payment"
                    else:
                        region_x = x - 890
                        region_y = y - 200
                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h)) 
                        status = pytesseract.image_to_string(region)
                        status = status.replace("/","").replace("\n", "")

                        if "EOIR" in status: 
                            return "Payment" 
                        else: 
                            region_x = x + 100
                            region_y = y - 100
                            region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h)) 
                            status = pytesseract.image_to_string(region)
                            status = status.replace("/","").replace("\n", "")

                            if "EOIR" in status:
                                return "Payment"
                            else:
                                return False
                            
                if word == "Appointment":
                    region_x = x + 380
                    region_y = y + 6
                    region_w = 110
                    region_h = 60

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                    status = pytesseract.image_to_string(region)
                    status = status.replace("\n", "").replace("/","")

                    # status = re.sub(r"\D", "", status)

                    status = f"{status}"

                    if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or "EOIR42" in status or "589" in status:
                        return "Appointment"
                    else:
                        region_x = x - 97
                        region_y = y + 25
                        region_w = 130
                        region_h = 85
                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("/","").replace("\n", "")

                        # status = re.sub(r"\D", "", status)

                        status = f"{status}"

                        if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or "EOIR42" in status or "589" in status:
                            return "Appointment"
                        else:
                            return False
                
                if word == "Applicants":
                    region_x = x + 350
                    region_y = y + 20
                    region_w = 160
                    region_h = 120

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                    status = pytesseract.image_to_string(region)
                    status = status.replace("\n", "").replace("/","")

                    print(status)

                    if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or 589 in status:
                        return "Reused"
                    else:
                        region_x = x - 135
                        region_y = y + 45
                        region_w = 100
                        region_h = 120
                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h)) 
                        status = pytesseract.image_to_string(region)
                        status = status.replace("/","").replace("\n", "")

                        print(status)
                        
                        if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or 589 in status: 
                            return "Reused" 
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

                    region_x = x + 15
                    region_y = y + 17
                    region_w = 800
                    region_h = 45

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    name = pytesseract.image_to_string(region)

                    name = regex_name(name) 

                    print(f"Document name: {name}")

                    region_x = x + 145
                    region_y = y - 1
                    region_w = 250
                    region_h = 35

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    alien_number = pytesseract.image_to_string(region)

                    alien_number = regex_alien_number(alien_number) 
                    
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
                if word == "Page" or word == "Priority":
                    x,y,w,h = self.data_ocr['left'][i], self.data_ocr['top'][i], self.data_ocr['width'][i], self.data_ocr['height'][i]
                    region_x = x + 350
                    region_y = y + 19
                    region_w = 800
                    region_h = 35

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    name = pytesseract.image_to_string(region)

                    name = name.split("\n")
                    
                    for i in name: 
                        if len(i) > 12: 
                            name = i 
                            
                    name = regex_name(name)

                    print(f"Document name: {name}")

                    region_x = x + 433
                    region_y = y - 6
                    region_w = 215
                    region_h = 38

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    alien_number = pytesseract.image_to_string(region)

                    alien_number = regex_alien_number(alien_number) 

                    print(f"Alien number: {alien_number}")

                    if name is None or alien_number is None:
                        return {
                            'name':fr"\Error{uuid.uuid4()}",
                            'alien_number':"Not found"
                        }
                    else:
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
                    region_y = y + 200
                    region_w = 800
                    region_h = 120

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    name = pytesseract.image_to_string(region)

                    name = regex_name(name)

                    text_module = "CHRISTOPHER C TAYLOR"

                    name = re.sub(text_module, "", name, flags=re.IGNORECASE)

                    print(f"Document name: {name}")

                    region_x = x + 920
                    region_y = y + 65
                    region_w = 215
                    region_h = 80

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    alien_number = pytesseract.image_to_string(region)

                    alien_number = regex_alien_number(alien_number) 

                    print(f"Alien number: {alien_number}")

                    return {
                        'name':name,
                        'alien_number':alien_number
                    }
        except Exception as e: 
            print(e)

    def reused(self):
        try: 
            for i, word in enumerate(self.data_ocr['text']):
                if word == "Applicants":
                    x,y,w,h = self.data_ocr['left'][i], self.data_ocr['top'][i], self.data_ocr['width'][i], self.data_ocr['height'][i]
                    region_x = x - 95
                    region_y = y + 200
                    region_w = 480
                    region_h = 80

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    name = pytesseract.image_to_string(region)

                    text_module = "CHRISTOPHER CASEY TAYT OR"

                    name = re.sub(text_module, "", name, flags=re.IGNORECASE)

                    text_module = "CHRISTOPHER CASEY TAYLOR"
                    name = re.sub(text_module, "", name, flags=re.IGNORECASE)

                    text_module = "CHRISTOPHER TAYLOR"
                    name = re.sub(text_module, "", name, flags=re.IGNORECASE)

                    name = regex_name(name)

                    print(f"Document name: {name}")

                    region_x = x + 760
                    region_y = y + 105
                    region_w = 350
                    region_h = 50

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    alien_number = pytesseract.image_to_string(region)
                    alien_number = regex_alien_number(alien_number)

                    if len(alien_number) < 9:
                        region_x = x + 780
                        region_y = y + 70
                        region_w = 350
                        region_h = 50

                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                        alien_number = pytesseract.image_to_string(region)

                        alien_number = regex_alien_number(alien_number)

                    print(f"Alien number: {alien_number}")

                    return {
                        'name':name,
                        'alien_number':alien_number
                    }
        except Exception as e:
            print(e)