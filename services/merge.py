def merge_pages(images, result, processed_path, option, pages_number=None):
    try:
        # Si se proporciona pages_number, ordenar las imágenes en base a ese orden
        if pages_number:
            # Emparejar páginas con sus números
            paired = list(zip(pages_number, images))
            # Extraer número como entero de strings tipo "page2"
            def extract_page_num(p): return int(p.replace("page", "").strip())
            paired.sort(key=lambda x: extract_page_num(x[0]))
            # Obtener imágenes ordenadas
            ordered_images = [img.convert('RGB') for _, img in paired]
        else:
            # Si no hay pages_number, convertir directamente todas las imágenes a RGB
            ordered_images = [img.convert('RGB') for img in images]

        # Guardar el PDF
        ordered_images[0].save(processed_path, save_all=True, append_images=ordered_images[1:])
        data = {}
        for key, value in result.items(): 
            data.update({key:value})

        data.update({"folder_name":option})
        data.update({"pdf":processed_path})
        return data
    except Exception as e:
        print(f"❌ Error guardando PDF combinado (imágenes): {e}")
        return None