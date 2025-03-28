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

    def aproved_case(self, region_x, region_y, region_w, region_h, key_word):
        try:

            words = self.data_ocr['text']

            for i, word in enumerate(words): 
                x,y = self.data_ocr['left'][i], self.data_ocr['top'][i]

                if key_word == word:

                    region_x = x + region_x 
                    region_y = y + region_y 


                    # Recortar la región específica
                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    # Aplicar OCR para extraer el texto
                    text = pytesseract.image_to_string(region).strip()

                    # Reemplazar caracteres problemáticos
                    text = text.replace("-", " ").replace(".","").replace("\\","").replace("/","").replace(":","")

                    # Dividir por líneas y eliminar espacios extra
                    text = [line.strip() for line in text.split("\n") if line.strip()]

                    # Filtrar posibles errores (puedes mejorar este criterio)
                    # if text:
                    return " ".join(text)  # Devolver como una sola línea de texto
                        
        except Exception as e:
            print(f"Error en OCR: {e}")

        return None  # Retorna None si no encontr

    def find_receipts(self):
        try:

            for i, word in enumerate(self.data_ocr['text']):
                x,y,w,h = self.data_ocr['left'][i], self.data_ocr['top'][i], self.data_ocr['width'][i], self.data_ocr['height'][i]
                
                match word: 
                    #42B
                    case "Priority":

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

                    case "APPLICANT":
                
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
                            
                    case "Appointment":
                        region_x = x + 380
                        region_y = y + 6
                        region_w = 110
                        region_h = 60

                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("\n", "").replace("/","")

                        # status = re.sub(r"\D", "", status)

                        status = f"{status}"
                        print(status)

                        if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or "EOIR42" in status or "89" in status:
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

                            print(status)

                            status = f"{status}"

                            if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or "EOIR42" in status or "89" in status:
                                return "Appointment"
                            else:
                                return False
                
                    case "Applicants":
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

                            if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or "589" in status: 
                                return "Reused" 
                            else: 
                                return False

                    case "Employment": 
                        region_x = x - 95
                        region_y = y - 8
                        region_w = 96
                        region_h = 33

                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("\n", "").replace("/", "")

                        if "765" in status or "766": 
                            return "Payment"
                        else: 
                            return False

        except Exception as e:
            print(f"Error in search model: {e}")
            return False
        
    def find_receipts_asylum(self): 
        try:
            for i, word in enumerate(self.data_ocr['text']): 
                x,y,w,h = self.data_ocr['left'][i], self.data_ocr['top'][i], self.data_ocr['width'][i], self.data_ocr['height'][i]

                # print(i)

                match word: 
                    case "Removal":
                        region_x = x - 390 
                        region_y = y - 14
                        region_w = 270
                        region_h = 95

                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("\n", "").replace("/","")

                        if "Asylu" in status or "Asvlu" in status:
                            return "Payment_receipt"

                    case "REMOVAL": 
                            region_x = x - 380
                            region_y = y - 50
                            region_w = 248
                            region_h = 134
                            region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                            status = pytesseract.image_to_string(region)
                            status = status.replace("\n", "").replace("/","")

                            if "Applicants" in status: 
                                return "Reused"
                            else:
                                region_x = x - 10
                                region_y = y - 50
                                region_w = 248
                                region_h = 134
                                region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                                status = pytesseract.image_to_string(region)
                                status = status.replace("\n", "").replace("/","")

                                if "589" in status: 
                                    return "Defensive_receipt"
                    
                    case "Applicant":
                        
                        region_x = x - 3
                        region_y = y - 35
                        region_w = 440
                        region_h = 50

                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("\n", "").replace("/", "")

                        if "765" in status: 
                            return "Receipts"

                    case "Appointment":                   
                        region_x = x - 65
                        region_y = y + 22
                        region_w = 160
                        region_h = 110
                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("/","").replace("\n", "")

                        status = f"{status}"

                        if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or "EOIR42" in status or "89" in status:
                            return "Appointment"
                        else:
                            region_x = x - 5
                            region_y = y + 22
                            region_w = 160
                            region_h = 150
                            region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                            status = pytesseract.image_to_string(region)
                            status = status.replace("/","").replace("\n", "")

                            if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or "EOIR42" in status or "89" in status:
                                return "Appointment"
                            else: 
                                return False

                    case "ASC": 
                            region_x = x - 5
                            region_y = y + 22
                            region_w = 160
                            region_h = 150
                            region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                            status = pytesseract.image_to_string(region)
                            status = status.replace("/","").replace("\n", "")

                            if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or "EOIR42" in status or "89" in status:
                                return "Appointment"
                            else: 
                                region_x = 129
                                region_y = 359

                                region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                                status = pytesseract.image_to_string(region)
                                status = status.replace("/","").replace("\n", "")

                                if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or "EOIR42" in status or "89" in status:
                                    return "Appointment"
                                else: 
                                    return False


        except Exception as e: 
            print(f"Error in asylum search module: {e}")
            return False