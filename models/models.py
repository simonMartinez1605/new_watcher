import pytesseract
import re

pattern_alien_number = r"^A\d{9}$"

def regex_alien_number(cadena):
    alien_number = re.sub(r"\D", "", cadena)

    return f"A{alien_number}"

def regex_name(text):
    regex = r"[^A-ZÁÉÍÓÚáéíóúÑñÜü ]"

    return re.sub(regex, "", text)


#MODULO A MEJORAR
class Model():
    def __init__(self, data_ocr, item):
        self.data_ocr = data_ocr
        self.item = item

    def find_receipts(self):
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
                        region_x = x - 65
                        region_y = y + 22
                        region_w = 130
                        region_h = 110
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
                    region_x = x + 150
                    region_y = y + 20
                    region_w = 160
                    region_h = 120

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                    status = pytesseract.image_to_string(region)
                    status = status.replace("\n", "").replace("/","")

                    if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or "589" in status:
                        return "Reused"
                    else:
                        region_x = x - 135
                        region_y = y + 45
                        region_w = 100
                        region_h = 120
                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h)) 
                        status = pytesseract.image_to_string(region)
                        status = status.replace("/","").replace("\n", "")

                        
                        if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or 589 in status: 
                            return "Reused" 
                        else: 
                            return False

                if word == "Receipt":
                    region_x = 337
                    region_y = 337
                    region_w = 91
                    region_h = 30

                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                    status = pytesseract.image_to_string(region)
                    status = status.replace("\n", "").replace("/","")

                    if "Asylum" in status:
                        return "Payment_receipt"
        except Exception as e:
            print(f"Error in search model: {e}")
            return False
        
    def aproved_case(self, region_x, region_y, region_w, region_h):
        try: 
           
            region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

            name = pytesseract.image_to_string(region)

            name = name.replace("-"," ")

            name = name.split("\n")
            
            return name 
        except Exception as e:
            print(e)