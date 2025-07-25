# New_watcher
En una primera instacia este proyecto va enfocado en la recopilacion de informacion dentro de documentos escaneados, por medio de OCR.

# Versiones
V1.01.01: Extraccion para 2 departamentos (Asylum - 42B)
En la version del codigo 04/22/2025 se pueden procesar aproximadamanete 17 tipos de documentos diferentes para Asylum y 5 para los casos de 42B

# Pasos a seguir

# Configuracion del Share Folder
Especificamente en esta carpeta compartida se usa una coneccion SMB (Security Message Block), ya que, actualmente todo se esta desarrollando dentro de un econsistema de windows, pero esto puede variar dependiendo del OS

# Para tener en cuenta: 

    * Te recomiendo probar la coneccion a tu carpeta compartida para validar los accesos
    * Puedes cambiar las rutas que quieres monitorear dependiendo de tus necesidades en .\main.py,  especificamente en la variable de folders_to_monitor. Tambien ten en cuenta que para poder que funcione debes de agregar dichas rutas en el path principal de la carpeta compartida 

# !IMPORTANTE
Hay algo fundamental en este punto y es que las rutas subyacentes a la raiz de la carpeta van a ser tomados para guardar la informacion dentro del sharepoint, por lo, tanto te recomiendo crear los sites del sharepoint con el mismo nombre que las rutas 

# Configurar Sharepoint 
Como lo mencione en el punto anterior el nombre del sitio debe de coincidir con las rutas en donde se desea enviar la informacion 
En el sharepoint creado se tiene que tener 2 campos: 
    1. Name: Nombre del documento a guardar 
    2. Alien Number: Numero que se extrae de los documentos 

# CREACION DE ENV 
Se crea un archivo de .env en el cual van 8 variables. De esas variables 5 son para la coneccion existosa en sharepoint y las otras 3 son para acceder a una carpeta compartida dentro de un servidor. 


1. SHARE_POINT_URL: El dominio del sharepoint en donde se quiere guardar la informacion 

    Ejemplo: "https://tudominio.sharepoint.com" 

2. USER_NAME: Correo para logearse en sharepoint 

    Ejemplo: "nombre@ejemplo.com" 

3. PASSWORD: Esta es una clave que se genero automaticamente en el sharepoint para desactivar la autenticacion de dos factores


4. LIBRARY_NAME: Nombre del documento compartido 
    (Por lo general esta variable se llama: Shared Documents)

5. LIST_NAME: Nombre de la carpeta en sharepoint 

    Ejemplo: Documents 

6. SERVER_USER: Nombre del usuario que se creo para administrar la carpeta compartida 
    Ejemplo: admin

7. SERVER_PASSWORD: Contraseña que se usa para ingresar a la carpeta compartida 

8. PATH_SHARE_FOLDER: La ruta raiz de la carpeta compartida 
    Ejemplo: 10.2.20.187\Scanning

# Recomendaciones 

* Usar python 3.13.2
* Usar VENV (Virtual Environment)  
    python -m venv nombre_del_proyecto


# Instalacion de dependecias y otros motores 
    pip install -r requirements.txt 

Tesseract: https://github.com/UB-Mannheim/tesseract/wiki

Poppler: https://github.com/oschwartz10612/poppler-windows/releases/

ghostscript: https://ghostscript.com/releases/gsdnld.html

# Pasos para configurar los motores de reconocimiento 

*  Descargar y seguir los pasos de instalacion 

* Buscar la ruta en donde se instalo el paquete, copiarla y dirigirse a las variables de entorno del sistema 
    - Ctrl + R
    - Copiar: control 
    - Buscar variables o enviroment 
    - Seleccionar la edicion de variables de entorno 
    - Seleccionar Variables de entorno 
    - Buscar PATH en las variables del sistema o del usuario y editarlo 
    - Una vez adentro agregas una nueva ruta 
    - Por ultimo, guarda todas las ediciones realizadas 