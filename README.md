# New_watcher
En una primera instacia este proyecto va enfocado en la recopilacion de informacion dentro de documentos escaneados, por medio de OCR.
Especificamente en la version V1.01.00 los documentos a los que se les puede realizar la extraccion de informacion es a las aprobaciones de las 42B, las cuales se manejan en conjunto (2 documentos) 

# Pasos a seguir

# Configurar Sharepoint 
En el sharepoint creado se tiene que tener 2 campos
1. Name: Nombre del documento a guardar 
2. Alien Number: Numero que se extrae de los documentos 

# CREACION DE ENV 
Se crea un archivo de .env en el cual van 8 variables 

1. MY_PATH: En esta variable va el PATH de la cartpeta que se quiere monitorear
Se tiene que tener en cuenta que los documentos a los que se pretenden extraer la informacion tienen que llegar a esta carpeta en especifico

2. SAVE_PDF: El PATH de donde se quiere guardar los archivos 

3. SHARE_POINT_URL: El dominio del sharepoint en donde se quiere guardar la informacion 

    Ejemplo: "https://tudominio.sharepoint.com" 

4. USER_NAME: Correo para logearse en sharepoint 

    Ejemplo: "nombre@ejemplo.com" 

5. PASSWORD: Esta es una clave que se genero automaticamente en el sharepoint para desactivar la autenticacion de dos factores

6. SITE_URL: Path del sitio creado para guardar los documentos y la informacion extraida 

    Ejemplo: /sites/Corte

7. LIBRARY_NAME: Nombre del documento compartido 
    (Por lo general esta variable se llama: Shared Documents)

8. LIST_NAME: Nombre de la carpeta en sharepoint 

    Ejemplo: Documents 


# Recomendaciones 

* Usar python 3.13.2
* Usar VENV (Virtual Environment)  
python -m venv nombre_del_proyecto


# Instalacion de dependecias 

    pip install -r requirements.txt 