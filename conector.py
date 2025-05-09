import configparser
import pandas as pd
import pyodbc
import paramiko
import ftplib
import schedule
import logger as J
import time
from datetime import datetime

J.Logger("logs")


# Funcion para leer el archivo de configuracion
def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

# Funcion para obtener los datos desde la base de datos segun la configuracion
def get_info(config):
    db_conf = config['DATABASE']
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={db_conf["SERVER"]};DATABASE={db_conf["DATABASE_NAME"]};UID={db_conf["USER"]};PWD={db_conf["PASSWORD"]}'
    query = db_conf['QUERY']
    J.info('Conectando a la base de datos...')
    with pyodbc.connect(conn_str) as conn:
        df = pd.read_sql(query, conn)
    J.info(f'{len(df)} registros recuperados de la base de datos.')
    return df

# Funcion para generar el fichero (CSV o Excel) a partir de los datos recuperados
def generate(df, config):
    csv_conf = config['CSVDATA']
    file_name = f"{csv_conf['FICHERO_NOMBRE']}_{datetime.now().strftime('%Y%m%d')}"
    file_format = csv_conf['FORMATO'].lower()

    if file_format == 'csv':
        file = f'{file_name}.csv'
        df.to_csv(file, index=False)
    elif file_format == 'xlsx':
        file = f'{file_name}.xlsx'
        df.to_excel(file, index=False)
    else:
        raise ValueError('Formato de fichero no soportado')
    
    J.info(f'Fichero generado: {file}')
    return file

# Funcion para subir el archivo generado a un servidor FTP o SFTP
def upload(file, config):
    ftp_conf = config['FTP']
    server_type = ftp_conf['TIPO_SERVER'].upper()
    host = ftp_conf['HOST_FTP']
    user = ftp_conf['USER_FTP']
    password = ftp_conf['PASSWORD_FTP']
    port = int(ftp_conf['PORT_FTP'])

    if server_type == 'SFTP':
        J.info(f'Conectando via SFTP a {host}...')
        transport = paramiko.Transport((host, port))
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(file, f'./{file}')
        sftp.close()
        transport.close()
        J.info(f'Archivo subido via SFTP correctamente')
    elif server_type == 'FTP':
        J.info(f'Conectando via FTP a {host}...')
        with ftplib.FTP() as ftp:
            ftp.connect(host, port)
            ftp.login(user, password)
            with open(file, 'rb') as f:
                ftp.storbinary(f'STOR {file}', f)
                J.info(f'Archivo subido via FTP correctamente')
    else:
        raise ValueError('Tipo de servidor no soportado')
    
    J.info(f'Archivo {file} subido correctamente.')

# Funcion que coordina todo el proceso: 
# 1) leer configuracion, 
# 2) obtener datos, 
# 3) generar fichero, 
# 4) subir fichero
def sync_job():
    try:
        J.info('--- Inicio del proceso de sincronizacion ---')
        config = read_config()
        df = get_info(config)
        file = generate(df, config)
        upload(file, config)
        J.info('--- Sincronizacion completada correctamente ---')
    except Exception as e:
        J.error(f'Error en el proceso: {e}')

# Funcion para validar si hoy es un dia habilitado segun la configuracion
def valid(days_config):
    valid_days = set()
    for part in days_config.split(','):
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))
            valid_days.update(range(start, end + 1))
        else:
            valid_days.add(int(part))
    current_day = datetime.today().isoweekday()  # Lunes=1 ... Domingo=7
    return current_day in valid_days

# Funcion principal que programa la tarea segun la hora y los dias definidos
def main():
 # Bucle infinito para mantener el proceso corriendo
    while True:
        config = read_config()
        timer_conf = config['TIMER']
        hour = timer_conf['HOUR'].strip()
        J.info(f'Esperando la hora programada ({hour})...')
        days = timer_conf['DAYS']
        # Programa la tarea para que se ejecute cada dia a la hora especificada
        schedule.every().day.at(hour).do(
            lambda: sync_job() if valid(days) else J.info('Hoy no es un dia programado.')
        )
        schedule.run_pending()  # Ejecuta las tareas pendientes
        time.sleep(60)          # Espera 30 segundos antes de revisar de nuevo
        J.info(f'Conector iniciado y esperando la hora programada ({hour})...')

if __name__ == '__main__':
    main()
