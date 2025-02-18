from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer 
from dotenv import load_dotenv 
from services.ocr import ocr 
from services.index import indexing 
import os
import time 

load_dotenv() 

class Event_manager(FileSystemEventHandler): 
    def on_created(self, event):
        if event.src_path.endswith(".pdf"): 
            print(f"New doc find")

            path_pdf = event.src_path.replace("\\", "/")

            ocr(path_pdf)

            print("OCR Done") 

            indexing(path_pdf) 

            os.rename(path_pdf, f"C:/Users/SimonMartinez/Documents/Simon/View Folder/OCR/Done/review.pdf")    

def monitor_folder(path): 
    manage = Event_manager()
    watcher = Observer()
    watcher.schedule(manage, path, recursive=False)
    watcher.start() 
    try: 
        while True: 
            time.sleep(2)
    except KeyboardInterrupt:
        watcher.stop()
    watcher.join() 

path = os.getenv('MY_PATH')

if __name__ == "__main__":
    monitor_folder(path) 