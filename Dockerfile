FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    poppler-utils \ 
    tesseract-ocr \ 
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

WORKDIR / app 

COPY . .

RUN pip install --no-cache-dir -r requirements.txt 

CMD ["python", "main.py"] 