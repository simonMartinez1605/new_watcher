import os
import sys
import platform
import ocrmypdf
from pypdf import PdfReader, PdfWriter
from concurrent.futures import ProcessPoolExecutor, as_completed
import tempfile
import shutil # Para manejar directorios temporales

# Tu función OCR existente
def ocr_single_document(input_path: str, output_path: str) -> str:
    """
    Procesa un solo documento PDF con OCR y guarda el resultado.
    input_path: Ruta al archivo PDF de entrada.
    output_path: Ruta donde se guardará el archivo PDF con OCR aplicado.
    Retorna la ruta del archivo de salida si tiene éxito, None en caso de error.
    """
    try:
        ocrmypdf.ocr(
            input_path,
            output_path,
            skip_text=True,  # Ya lo tenías, bueno para evitar reprocesar texto existente
            deskew=True,     # Para corregir la inclinación de las páginas
            # --- Opciones adicionales para acelerar el OCR ---
            optimize=0,      # Deshabilita la optimización del tamaño del archivo para mayor velocidad
            output_type='pdf', # Genera un PDF estándar en lugar de PDF/A
            # skip_big=10,     # Opcional: Salta OCR en páginas > 10 megapíxeles (ajústalo según necesidad)
        )
        print(f"[{os.getpid()}] Successfully OCRed: {input_path} -> {output_path}")
        return output_path
    except Exception as e:
        print(f"[{os.getpid()}] Error in OCR services for {input_path}: {e}")
        import traceback
        traceback.print_exc()
        return None

def split_pdf(input_pdf_path: str, pages_per_chunk: int = 100) -> list:
    """
    Divide un PDF grande en múltiples PDFs más pequeños.
    Retorna una lista de rutas a los PDFs pequeños generados.
    """
    output_paths = []
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    num_chunks = (total_pages + pages_per_chunk - 1) // pages_per_chunk

    print(f"Split '{input_pdf_path}' ({total_pages} pages) in {num_chunks} parts of ~{pages_per_chunk} each pages.")

    # Crear un directorio temporal para las partes divididas
    temp_dir = tempfile.mkdtemp(prefix="pdf_chunks_")
    print(f"Temporal docs: {temp_dir}")

    for i in range(num_chunks):
        writer = PdfWriter()
        start_page = i * pages_per_chunk
        end_page = min((i + 1) * pages_per_chunk, total_pages)

        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])

        chunk_path = os.path.join(temp_dir, f"chunk_{i+1:03d}.pdf")
        with open(chunk_path, "wb") as output_pdf:
            writer.write(output_pdf)
        output_paths.append(chunk_path)
        print(f"  - Created: {os.path.basename(chunk_path)} ({start_page+1}-{end_page} of {total_pages} pages)")

    return output_paths, temp_dir

def merge_pdfs(input_pdf_paths: list, output_pdf_path: str) -> bool:
    """
    Une múltiples PDFs en un solo PDF.
    """
    writer = PdfWriter()
    print(f"Merge {len(input_pdf_paths)} PDFs in '{output_pdf_path}'...")
    for pdf_path in input_pdf_paths:
        try:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                writer.add_page(page)
        except Exception as e:
            print(f"Error to read the PDF '{pdf_path}': {e}")
            return False

    with open(output_pdf_path, "wb") as output_pdf:
        writer.write(output_pdf)
    print(f"Merge complet: '{output_pdf_path}'")
    return True

def process_large_pdf_with_ocr(input_large_pdf: str, output_final_pdf: str, pages_per_chunk: int = 100):
    """
    Función principal para dividir, procesar con OCR en paralelo y unir un PDF grande.
    """
    if not os.path.exists(input_large_pdf):
        print(f"Error: input file '{input_large_pdf}' does not exit.")
        return

    # 1. Dividir el PDF
    chunk_input_paths, temp_dir_chunks = split_pdf(input_large_pdf, pages_per_chunk)
    if not chunk_input_paths:
        print("PDF parts don't exits.")
        if os.path.exists(temp_dir_chunks):
            shutil.rmtree(temp_dir_chunks) # Limpiar dir temporal si no hay chunks
        return

    # Crear un directorio temporal para los chunks procesados (con OCR)
    temp_dir_ocr_chunks = tempfile.mkdtemp(prefix="pdf_ocr_chunks_")
    print(f"Parts on temporal file with OCR in: {temp_dir_ocr_chunks}")

    chunk_output_paths = []
    
    # 2. Procesar cada parte con OCR en paralelo
    # Usamos ProcessPoolExecutor para tareas intensivas en CPU como OCR
    num_processes = os.cpu_count() # Usar el número de núcleos de la CPU
    print(f"Init OCR proccess {num_processes} proccess...")

    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        # Mapear las tareas: (input_path_chunk, output_path_ocr_chunk)
        futures = {}
        for i, input_chunk_path in enumerate(chunk_input_paths):
            output_chunk_ocr_path = os.path.join(temp_dir_ocr_chunks, f"ocr_chunk_{i+1:03d}.pdf")
            future = executor.submit(ocr_single_document, input_chunk_path, output_chunk_ocr_path)
            futures[future] = input_chunk_path # Almacenar la ruta de entrada para referencia

        for future in as_completed(futures):
            original_input_path = futures[future]
            ocr_output_path = future.result()
            if ocr_output_path:
                chunk_output_paths.append(ocr_output_path)
            else:
                print(f"Warning: OCR Failed '{original_input_path}'. Does not include in the final document")
    
    # Asegurarse de que los chunks se unan en el orden correcto
    # (Los nombres de archivo "ocr_chunk_001.pdf", "ocr_chunk_002.pdf" aseguran esto)
    chunk_output_paths.sort() 

    if not chunk_output_paths:
        print("Any OCR part was succefully. The program can't complete the merge proccess")
        return

    # 3. Unir los PDFs procesados con OCR
    success = merge_pdfs(chunk_output_paths, output_final_pdf)

    # Limpiar los directorios temporales
    print("Cleaning temporal files...")
    if os.path.exists(temp_dir_chunks):
        shutil.rmtree(temp_dir_chunks)
    if os.path.exists(temp_dir_ocr_chunks):
        shutil.rmtree(temp_dir_ocr_chunks)
    print("Temporal files cleaned.")

    if success:
        print(f"OCR proccess complete: '{input_large_pdf}'. Results in '{output_final_pdf}'")
    else:
        print(f"OCR proccess failed: '{input_large_pdf}'.")

