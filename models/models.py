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

    def aproved_case(self, region_x, region_y, region_w, region_h, key_word) -> str:
        try:

            words = self.data_ocr['text']

            for i, word in enumerate(words): 
                x,y = self.data_ocr['left'][i], self.data_ocr['top'][i]

                if key_word == word:

                    # print(region_x - x)
                    # print(region_y - y)

                    region_x = x + region_x
                    region_y = y + region_y

                    # print(region_x, region_y, x, y)


                    # Recortar la región específica
                    region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                    # Aplicar OCR para extraer el texto
                    text = pytesseract.image_to_string(region).strip()

                    text = text.replace("-", " ")

                    # Reemplazar caracteres problemáticos
                    text = re.sub(r"[^A-Za-z0-9\s]", "", text)

                    # Dividir por líneas y eliminar espacios extra
                    text = [line.strip() for line in text.split("\n") if line.strip()]

                    # print(f"Text extract: {"".join(text)}")

                    # Filtrar posibles errores (puedes mejorar este criterio)
                    # if text:
                    return " ".join(text)  # Devolver como una sola línea de texto
                        
        except Exception as e:
            print(f"Error en OCR: {e}")

        return None  # Retorna None si no encontr

    def find_receipts(self) -> str:
        try:

            result = []

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
                            result.append("Receipts")
                        else: 
                            region_x = x - 1
                            region_h = 141
                            region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h)) 
                            status = pytesseract.image_to_string(region)
                            status = status.replace("/","").replace("\n", "")

                            if "Page2" in status: 
                                result.append("Receipts" )
                            
                    case "APPLICANT":
                
                        region_x = x - 50
                        region_y = y - 80
                        region_w = 200
                        region_h = 100

                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("\n", "").replace("/","")

                        if "EOIR" in status:
                            result.append("Payment")
                        else:
                            region_x = x - 890
                            region_y = y - 200
                            region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h)) 
                            status = pytesseract.image_to_string(region)
                            status = status.replace("/","").replace("\n", "")

                            if "EOIR" in status: 
                                result.append("Payment") 
                            else: 
                                region_x = x + 100
                                region_y = y - 100
                                region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h)) 
                                status = pytesseract.image_to_string(region)
                                status = status.replace("/","").replace("\n", "")

                                if "EOIR" in status:
                                    result.append("Payment")
                            
                    case "ADJUST":
                        region_x = x + 380
                        region_y = y + 6
                        region_w = 110
                        region_h = 60

                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("\n", "").replace("/","")

                        status = f"{status}"
                        # print(status)

                        if "I485" in status or "1485" in status or "85" in status or "1765" in status or "765" in status or "EOIR42" in status or "89" in status:
                            result.append("Appointment")
                        else:
                            region_x = x + 20
                            region_y = y - 170
                            region_w = 350
                            region_h = 100
                            region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                            status = pytesseract.image_to_string(region)
                            status = status.replace("/","").replace("\n", "")

                            status = f"{status}"
                            print(status)

                            if "Appointment" in status:
                                result.append("Appointment")
                            
                            if "Applicants" in status:
                                result.append("Reused")
                
                    case "Applicants":
                        region_x = x + 150
                        region_y = y + 20
                        region_w = 160
                        region_h = 120

                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("\n", "").replace("/","")

                        if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or "589" in status:
                            result.append("Reused")
                        else:
                            region_x = x - 135
                            region_y = y + 45
                            region_w = 100
                            region_h = 120
                            region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h)) 
                            status = pytesseract.image_to_string(region)
                            status = status.replace("/","").replace("\n", "")

                            if "I485" in status or "1485" in status or "485" in status or "1765" in status or "765" in status or "589" in status: 
                                result.append("Reused") 
                            
                    case "Employment": 
                        region_x = x - 95
                        region_y = y - 8
                        region_w = 96
                        region_h = 33

                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("\n", "").replace("/", "")

                        if "765" in status or "766": 
                            result.append("Payment")

            return result[0]

        except Exception as e:
            print(f"Error in search model: {e}")
            return False
        
    def find_receipts_asylum(self) -> str: 
        try:
            result = []
            for i, word in enumerate(self.data_ocr['text']): 
                x,y,w,h = self.data_ocr['left'][i], self.data_ocr['top'][i], self.data_ocr['width'][i], self.data_ocr['height'][i]


                match word: 

                    case "Type": 
                        region_x = x - 600
                        region_y = y - 10
                        region_w = 280
                        region_h = 100

                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("\n", "").replace("/","")

                        # print(status)

                        if "Reject" in status: 
                            result.append("Reject_2020")
                    
                    case "Reference": 
                        region_x = x - 200
                        region_y = y 
                        region_w = 250
                        region_h = 50

                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("\n", "").replace("/","")

                        if "Reject" in status: 
                            result.append("Reject")
                        
                    case "Removal":
                        region_x = x - 390 
                        region_y = y - 14
                        region_w = 270
                        region_h = 95

                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("\n", "").replace("/","")

                        if "Asylu" in status or "Asvlu" in status:
                            
                            region_x = x + 340
                            region_y = y + 133
                            region_w = 341
                            region_h = 46

                            region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                            status = pytesseract.image_to_string(region)
                            status = status.replace("\n", "").replace("/","")
                            
                            if "PAYMENT" in status: 
                                result.append("Payment_receipt")
                            else: 
                                region_x = 1010
                                region_y = 451
                                region_w = 397
                                region_h = 75

                                region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                                status = pytesseract.image_to_string(region)
                                status = status.replace("\n", "").replace("/","")
                                
                                if "Receipt" in status: 
                                    result.append("Receipt")

                    case "REMOVAL":
                            
                            region_x = x - 380
                            region_y = y - 50
                            region_w = 248
                            region_h = 134
                            region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                            status = pytesseract.image_to_string(region)
                            status = status.replace("\n", "").replace("/","")

                            if "Applicants" in status: 
                                result.append("Reused")
                    
                    case "Defensive": 
                        # print(x, y)
                        region_x = x - 375
                        region_y = y -228
                        region_w = 233
                        region_h = 73
                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("\n", "").replace("/","")

                        if "1589" in status: 
                            result.append("Defensive_receipt")
                    
                    case "Applicant":

                        region_x = x - 3
                        region_y = y - 35
                        region_w = 440
                        region_h = 50

                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("\n", "").replace("/", "")

                        if "765" in status:

                            region_x = x + 524
                            region_y = y + 156
                            region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                            status = pytesseract.image_to_string(region)
                            status = status.replace("\n", "").replace("/", "")

                            if "Approval" in status:
                                result.append("Approved_receipts")

                    case "WITHHOLDING":
                        region_x = x - 405
                        region_y = y - 120
                        region_w = 280
                        region_h = 80
                        region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                        status = pytesseract.image_to_string(region)
                        status = status.replace("/","").replace("\n", "")


                        if "Appointment" in status: 
                            
                            region_x = x + 794
                            region_y = y - 83
                            region_w = 250
                            region_h = 180
                            region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                            status = pytesseract.image_to_string(region)
                            status = status.replace("/","").replace("\n", "")

                            # print(status)

                            if "2020" in status: 
                                result.append("Appointment_asylum_2020")
                            elif "2024" in status or "2025" in status: 
                                result.append("Appointment")
                            elif "2019" in status:
                                result.append("Appointment_asylum_2019")
                            else: 
                                region_x = x + 852
                                region_y = y - 94.5
                                region_w = 350
                                region_h = 250
                                region = self.item.crop((region_x, region_y, region_x + region_w, region_y + region_h))
                                status = pytesseract.image_to_string(region)
                                status = status.replace("/","").replace("\n", "")

                                status = re.sub(r'\D', "", status)

                                # print(status)

                                if "019" in status or "219" in status or "2059" in status: 
                                    result.append("Appointment_asylum_2019")
                                elif "2020" in status:
                                    result.append("Appointment_asylum_2020")

            # print(result)
            if result == []: 
                return None 
            return result[0]
        except Exception as e: 
            print(f"Error in asylum search module: {e}")
            return False