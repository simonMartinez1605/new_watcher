import os
import sys
import platform
import ocrmypdf

# --- START PYINSTALLER PATH ADJUSTMENTS ---
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

tesseract_exe_name = 'tesseract.exe'
tesseract_exe_path = os.path.join(bundle_dir, tesseract_exe_name)

tessdata_path = os.path.join(bundle_dir, 'tessdata')

# os.environ['TESSDATA_PREFIX'] = tessdata_path
# print(f"DEBUG: TESSDATA_PREFIX set to: {os.environ['TESSDATA_PREFIX']}")

# if platform.system() == "Windows":
#     os.environ['PATH'] += os.pathsep + bundle_dir
# else:
#     os.environ['PATH'] += os.pathsep + bundle_dir

# print(f"DEBUG: Tesseract executable path determined: {tesseract_exe_path}")
# --- END PYINSTALLER PATH ADJUSTMENTS ---

# Your ocr function definition goes here, after tesseract_exe_path is defined
def ocr(my_path: str) -> str:
    # ... (rest of your ocr function code as above, using tesseract_exe_path) ...
    try:
        ocrmypdf.ocr(
            my_path,
            my_path,
            skip_text=True,
            deskew=True,
            jobs=os.cpu_count(), 
            optimize=0
        )
    except Exception as e:
        print(f"Error in OCR services: {e}")
        import traceback
        traceback.print_exc()