import re
import json
import pytesseract

_JSON_CACHE = {}

def load_json_cached(file_path: str) -> dict:
    """Carga JSON con caché para evitar lecturas repetidas de disco"""
    if file_path not in _JSON_CACHE:
        with open(file_path, 'r', encoding='utf-8') as f:
            _JSON_CACHE[file_path] = json.load(f)
    return _JSON_CACHE[file_path]

def search_in_coords(coord_list : list, coord_x : int , coord_y: int, item) -> str: 
    for coord in coord_list: 
        x = coord_x + coord['x']
        y = coord_y + coord['y']
        w = coord['w']
        h = coord['h']

        region = item.crop((x, y, x + w, y + h))
        status = pytesseract.image_to_string(region)
        status = status.replace("\n", "").replace("/", "")
        return status

#MODULO A MEJORAR
class Model():
    def __init__(self, data_ocr, item):
        self.data_ocr = data_ocr
        self.item = item

    def aproved_case(self, region_x, region_y, region_w, region_h, key_word) -> str:
        """
        Funcion para buscar la informacion dentro del documento PDF.
        Se busca la palabra clave, se recorta la region especifica y extraer el texto.

        PARAMETERS
        ----------
        region_x : int
            Coordenada x de la region a recortar.
        region_y : int
            Coordenada y de la region a recortar.
        region_w : int
            Ancho de la region a recortar.  
        region_h : int
            Alto de la region a recortar.
        key_word : str
            Palabra clave a buscar en el documento PDF.
        
        
        """
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

                    text = text.replace("-", " ")

                    # Reemplazar caracteres problemáticos
                    text = re.sub(r"[^A-Za-z0-9\s]", "", text)

                    # Dividir por líneas y eliminar espacios extra
                    text = [line.strip() for line in text.split("\n") if line.strip()]

                    # print(f"Text extract: {"".join(text)}", f"X: {region_x - x}", f"Y: {region_y - y}")
                    # print(f"Text extrac: {"".join(text)}")

                    # Filtrar posibles errores (puedes mejorar este criterio)
                    # if text:
                    return " ".join(text)  # Devolver como una sola línea de texto                
        except Exception as e:
            print(f"Error en OCR: {e}")
            return None

    def find_receipts(self) -> str:
        """Busca el tipo de documento utilizando coordenadas y palabras clave definidas en un JSON."""

        try:
            json_path = f"jsons/search_42BReceipts.json"
            doc_definitions = load_json_cached(json_path)  # Es una lista
            results = []

            for doc_config in doc_definitions:  # Iteramos sobre cada objeto del JSON
                def buscar_status(coord_x, coord_y) -> str | None:
                    # Buscar en coordenadas normales
                    status = search_in_coords(doc_config['second_coords'], coord_x, coord_y, self.item)
                    value = extraer_valor(status, doc_config.get("second_key_words", {}))
                    if value:
                        return value

                    # Luego buscar en coordenadas de excepción
                    status = search_in_coords(doc_config['except_coords'], coord_x, coord_y, self.item)
                    return extraer_valor(status, doc_config.get("except_key_words", {}))

                def extraer_valor(texto: str, key_words_dict: dict) -> str | None:
                    for key, value in key_words_dict.items():
                        if key in texto:
                            return value
                    return None

                for i, word in enumerate(self.data_ocr['text']):
                    if word != doc_config['anchor']:
                        continue

                    coord_x = self.data_ocr['left'][i]
                    coord_y = self.data_ocr['top'][i]
                    search_word = search_in_coords(doc_config['first_coords'], coord_x, coord_y, self.item)

                    for key_word in doc_config['first_key_word']:
                        if key_word not in search_word:
                            continue
                    
                    resultado = buscar_status(coord_x, coord_y)
                    if resultado:
                        results.append(resultado)
                        break  # Si ya encontró uno, no necesita seguir con las demás definiciones

            return results[0] if results else None
        except Exception as e:
            print(f"Error in 42B Receipts search module: {e}")
            return False

    def find_receipts_asylum(self) -> str:
        """Busca el tipo de documento utilizando coordenadas y palabras clave definidas en un JSON."""
        try:
            json_path = "jsons/search_Asylum.json"
            doc_definitions = load_json_cached(json_path)  # Es una lista
            results = []

            for doc_config in doc_definitions:  # Iteramos sobre cada objeto del JSON
                def buscar_status(coord_x, coord_y, anchor) -> str | None:
                    # Buscar en coordenadas normales
                    if anchor in doc_config['anchor']:
                        # print(doc_config['second_coords'], f"anchor: {anchor}")
                        status = search_in_coords(doc_config['second_coords'], coord_x, coord_y, self.item)
                        # print(f"status: {status}, anchor: {anchor}")
                        value = extraer_valor(status, doc_config.get("second_key_words", {}))
                        # print(f"value: {value}, anchor: {anchor}")
                        if value:
                            # print(f"value: {value}")
                            return value

                        # Luego buscar en coordenadas de excepción
                        status = search_in_coords(doc_config['except_coords'], coord_x, coord_y, self.item)
                        # print(f"status: {status}")
                        return extraer_valor(status, doc_config.get("except_key_words", {}))

                def extraer_valor(texto: str, key_words_dict: dict) -> str | None:
                    for key, value in key_words_dict.items():
                        if key in texto:
                            print(f"key: {key}, value: {value}, text: {texto}")
                            return value
                    return None

                for i, word in enumerate(self.data_ocr['text']):
                    if word != doc_config['anchor']:
                        continue
                    
                    # print(f"word: {word}, anchor: {doc_config['anchor']}")

                    coord_x = self.data_ocr['left'][i]
                    coord_y = self.data_ocr['top'][i]
                    search_word = search_in_coords(doc_config['first_coords'], coord_x, coord_y, self.item)

                    # print(f"search_word: {search_word}, first_key_word: {doc_config['first_key_word']}, and word: {word}")

                    for key_word in doc_config['first_key_word']:
                        # print(f"first_key_word: {search_word} search_word: {doc_config['first_key_word']} word: {word}")
                        if key_word not in search_word:
                            continue
                    
                    resultado = buscar_status(coord_x, coord_y, word)
                    # print(f"resultado: {resultado}")
                    if resultado:
                        results.append(resultado)
                        break  # Si ya encontró uno, no necesita seguir con las demás definiciones

            # print(f"Results: {results}")
            # print(f"Results: {results}")

            return results[0] if results else None
        except Exception as e:
            print(f"Error in asylum search module: {e}")
            return False