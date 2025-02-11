import pytesseract 
import re 

def form(data_ocr, item): 

    try: 
    
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
    except Exception as e: 
        print(f"Error in search model: {e}")

def I_485(data_ocr, item): 

    try: 
    
        for i, word in enumerate(data_ocr['text']): 
            if word == "Applicant":
                print(word) 
                x,y,w,h = data_ocr['left'][i], data_ocr['top'][i], data_ocr['width'][i], data_ocr['height'][i]

                region_x = x - 15
                region_y = y + 7
                region_w = 470 
                region_h = 50 

                region = item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                name = pytesseract.image_to_string(region)

                name = name.replace("\n", "")
                name = name.replace("/", "")

                region_x = x - 50
                region_y = y + 50
                region_w = 470 
                region_h = 50 

                alien_number_region = item.crop((region_x, region_y, region_x + region_w, region_y + region_h))

                alien_number = pytesseract.image_to_string(alien_number_region)

                alien_number_pattern = r"A(\d\s?){8,9}"

                alien_number = re.search(alien_number_pattern, alien_number) 

                if alien_number: 
                    alien_number = alien_number.group().replace("\n", "").replace(" ", "-") 

                return {
                        'name':name, 
                        'alien_number':alien_number
                    } 
    except Exception as e:
        print(f"Error in search models {e}")