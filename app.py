import tkinter as tk
from tkinter import messagebox
import configparser
import threading
import paramiko
import ftplib
import schedule
import pyodbc
import pandas as pd
from datetime import datetime
import time
import logger as J

config = configparser.ConfigParser()
config.read('config.ini') 

J.Logger("logs") 

# Funcion para leer el archivo de configuracion
def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

# Funcion para obtener los datos desde la base de datos
def get_info(config):
    db_conf = config['DATABASE']  # Obtenemos la configuracion de la base de datos
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={db_conf["SERVER"]};DATABASE={db_conf["DATABASE_NAME"]};UID={db_conf["USER"]};PWD={db_conf["PASSWORD"]}'
    query = db_conf['QUERY']  # Obtenemos la consulta SQL a ejecutar
    J.info('Conectando a la base de datos...')  # Registramos el inicio de la conexion
    with pyodbc.connect(conn_str) as conn:
        df = pd.read_sql(query, conn)  # Ejecutamos la consulta y almacenamos los resultados en un DataFrame
    J.info(f'{len(df)} registros recuperados de la base de datos.')  # Registramos el numero de registros recuperados
    return df

# Funcion para generar el archivo (CSV o Excel)
def generate(df, config):
    csv_conf = config['CSVDATA']  # Obtenemos la configuracion para la generacion de archivos
    file_name = f"{csv_conf['FICHERO_NOMBRE']}_{datetime.now().strftime('%Y%m%d')}"  # Nombre del archivo con fecha
    file_format = csv_conf['FORMATO'].lower()  # Obtenemos el formato del archivo (CSV o XLSX)

    if file_format == 'csv':
        file = f'{file_name}.csv'
        df.to_csv(file, index=False)  # Guardamos el DataFrame como archivo CSV
    elif file_format == 'xlsx':
        file = f'{file_name}.xlsx'
        df.to_excel(file, index=False)  # Guardamos el DataFrame como archivo Excel
    else:
        raise ValueError('Formato de fichero no soportado')  # Si el formato no es valido, lanzamos un error
    
    J.info(f'Fichero generado: {file}')  # Registramos el nombre del archivo generado
    return file

# Funcion para subir el archivo a un servidor FTP o SFTP
def upload(file, config):
    ftp_conf = config['FTP']  # Obtenemos la configuracion para FTP/SFTP
    server_type = ftp_conf['TIPO_SERVER'].upper()  # Tipo de servidor (FTP o SFTP)
    host = ftp_conf['HOST_FTP']
    user = ftp_conf['USER_FTP']
    password = ftp_conf['PASSWORD_FTP']
    port = int(ftp_conf['PORT_FTP'])

    # Conexion a servidor SFTP
    if server_type == 'SFTP':
        J.info(f'Conectando via SFTP a {host}...')
        transport = paramiko.Transport((host, port))
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(file, f'./{file}')  # Subimos el archivo
        sftp.close()
        transport.close()
        J.info(f'Archivo subido via SFTP correctamente')

    # Conexion a servidor FTP
    elif server_type == 'FTP':
        J.info(f'Conectando via FTP a {host}...')
        with ftplib.FTP() as ftp:
            ftp.connect(host, port)
            ftp.login(user, password)
            with open(file, 'rb') as f:
                ftp.storbinary(f'STOR {file}', f)  # Subimos el archivo
                J.info(f'Archivo subido via FTP correctamente')
    else:
        raise ValueError('Tipo de servidor no soportado')  # Si el tipo de servidor no es valido, lanzamos un error
    
    J.info(f'Archivo {file} subido correctamente.')  # Registramos la subida exitosa del archivo

# Funcion que coordina todo el proceso de sincronizacion
def sync_job():
    try:
        J.info('--- Inicio del proceso de sincronizacion ---')
        config = read_config()  # Leemos la configuracion
        df = get_info(config)  # Obtenemos los datos de la base de datos
        file = generate(df, config)  # Generamos el archivo
        upload(file, config)  # Subimos el archivo al servidor
        J.info('--- Sincronizacion completada correctamente ---')
    except Exception as e:
        J.error(f'Error en el proceso: {e}')  # En caso de error, registramos el mensaje de error

# Funcion para validar los dias de sincronizacion
def valid(days_config):
    valid_days = set()
    # Parseamos los dias de la semana desde la configuracion
    for part in days_config.split(','):
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))  # Rango de dias
            if start <= end:
                valid_days.update(range(start, end + 1))
            else:
                return False  # Si el rango es invalido (start > end), lo rechazamos
        else:
            try:
                valid_days.add(int(part))  # Dia individual
            except ValueError:
                return False  # Si no es un numero valido, lo rechazamos
    current_day = datetime.today().isoweekday()  # Obtenemos el dia actual de la semana (Lunes=1, Domingo=7)
    return current_day in valid_days  # Verificamos si el dia actual es valido

# Funcion para guardar la configuracion desde la interfaz grafica
def save_config():
    # Obtener los valores de la interfaz grafica
    file_format = file_format_var.get()
    server_type = server_type_var.get()
    sync_days = sync_days_entry.get()

    # Validamos los dias antes de guardar la configuracion
    if not valid(sync_days):
        messagebox.showerror("Error de configuracion", "Los dias de sincronizacion no son validos.")
        return

    # Actualizamos el archivo de configuracion
    config['CSVDATA']['FORMATO'] = file_format
    config['FTP']['TIPO_SERVER'] = server_type
    config['TIMER']['DAYS'] = sync_days

    # Guardamos la configuracion en el archivo .ini
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

    messagebox.showinfo("Configuracion guardada", "La configuracion se ha guardado correctamente.")  # Mostramos mensaje de exito

# Funcion para lanzar la sincronizacion en un hilo separado
def launch_sync():
    threading.Thread(target=sync_job).start()  # Ejecutamos la sincronizacion en un hilo para no bloquear la interfaz

# Crear la ventana principal de la interfaz grafica
root = tk.Tk()
root.title("Configuracion de Sincronizacion")

# Configuracion de la opcion para seleccionar el formato de archivo
file_format_var = tk.StringVar(value=config['CSVDATA']['FORMATO'])
file_format_label = tk.Label(root, text="Formato de archivo (CSV o XLSX):")
file_format_label.grid(row=0, column=0, sticky="w")
file_format_option = tk.OptionMenu(root, file_format_var, "csv", "xlsx")
file_format_option.grid(row=0, column=1)

# Configuracion de la opcion para seleccionar el tipo de servidor FTP o SFTP
server_type_var = tk.StringVar(value=config['FTP']['TIPO_SERVER'])
server_type_label = tk.Label(root, text="Tipo de servidor (FTP o SFTP):")
server_type_label.grid(row=1, column=0, sticky="w")
server_type_option = tk.OptionMenu(root, server_type_var, "FTP", "SFTP")
server_type_option.grid(row=1, column=1)

# Entrada para configurar los dias de sincronizacion
sync_days_label = tk.Label(root, text="Dias de sincronizacion (Formato valido: 1-3, 6):")
sync_days_label.grid(row=2, column=0, sticky="w")
sync_days_entry = tk.Entry(root)
sync_days_entry.insert(0, config['TIMER']['DAYS'])  # Valor por defecto
sync_days_entry.grid(row=2, column=1)

# Boton para guardar la configuracion
save_button = tk.Button(root, text="Guardar configuracion", command=save_config)
save_button.grid(row=3, columnspan=2, pady=10)

# Boton para lanzar la sincronizacion
launch_button = tk.Button(root, text="Lanzar sincronizacion", command=launch_sync)
launch_button.grid(row=4, columnspan=2, pady=10)

# Ejecutamos la interfaz grafica
root.mainloop()
