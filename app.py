import configparser
import os
import pandas as pd
import pyodbc
import paramiko
import ftplib
import schedule
import logger as J
import time
from datetime import datetime
from setup_ini import create_ini

J.Logger("logs")


# Funcion para leer el archivo de configuracion
def read_config():
    create_ini()
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

# Funcion para obtener los datos desde la base de datos segun la configuracion
def get_info(config):
    db_conf = config['DATABASE']
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={db_conf["SERVER"]};DATABASE={db_conf["DATABASE_NAME"]};UID={db_conf["USER"]};PWD={db_conf["PASSWORD"]}'
    query = db_conf['QUERY']
    J.info('Conectando a la base de datos...')
    # Conexion y consulta a la base de datos
    with pyodbc.connect(conn_str) as conn:
        df = pd.read_sql(query, conn)
    J.info(f'{len(df)} registros recuperados de la base de datos.')
    return df

# Funcion para generar el fichero (CSV o Excel) a partir de los datos recuperados
def generate(df, config):
    csv_conf = config['CSVDATA']
    file_name = f"{csv_conf['file_name']}_{datetime.now().strftime('%Y%m%d')}"
    file_format = csv_conf['FORMAT'].lower()
    
    # Generar fichero en el formato indicado
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
    server_type = ftp_conf['server_type'].upper()
    host = ftp_conf['HOST_FTP']
    user = ftp_conf['USER_FTP']
    password = ftp_conf['PASSWORD_FTP']
    port = int(ftp_conf['PORT_FTP'])

    if 'SFTP' in server_type:
        J.info(f'Conectando via SFTP a {host}...')
        transport = paramiko.Transport((host, port))
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        if '/' in server_type:
            ruta = server_type[4:len(server_type)]
            J.info(f'Buscando la ruta {ruta}')
            sftp.put(file, f'{ruta}./{file}')
        else:
            sftp.put(file, f'./{file}')
        sftp.close()
        transport.close()
        J.info(f'Archivo subido via SFTP correctamente')
    elif 'FTP' in server_type:
        J.info(f'Conectando via FTP a {host}...')
        with ftplib.FTP() as ftp:
            with open(file, 'rb') as f:
                ftp.connect(host, port)
                ftp.login(user, password)
                if '/' in server_type:
                    ruta = server_type[3:len(server_type)]
                    J.info(f'Buscando la ruta {ruta}')
                    ftp_file = ruta+'/'+file
                    ftp.storbinary(f'STOR {ftp_file}', f)
                else:
                        ftp.storbinary(f'STOR {file}', f)
                J.info(f'Archivo subido via FTP correctamente')
    else:
        raise ValueError('Tipo de servidor no soportado')


# Funcion que coordina todo el proceso: 
# 1) leer configuracion, 
# 2) obtener datos, 
# 3) generar fichero, 
# 4) subir fichero
def sync_job():
    try:
        # J.info('--- Inicio del proceso de sincronizacion ---')
        config = read_config()
        df = get_info(config)
        file = generate(df, config)
        upload(file, config)
        # J.info('--- Sincronizacion completada correctamente ---')
    except ftplib.error_perm as e:
        J.error(f'Error en la ruta especificada por el usuario')
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

# Funcion para cancelar una tarea programada
def cancel_job():
    return schedule.CancelJob

# Funcion ejecutada por la tarea programada, valida si se debe ejecutar el proceso
def scheduled_task():
    config = read_config()
    days = config['TIMER']['DAYS']
    if valid(days):
        sync_job()
    else:
        J.info('Hoy no es un dia programado.')

# Funcion principal que programa la tarea segun la hora y los dias definidos
def main():
    last_mtime = 0
    last_hour = None
    job_ref = None

    while True:
        try:
            # Verifica si config.ini fue modificado
            config = read_config()
            current_mtime = os.path.getmtime('config.ini')
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                hour = config['TIMER']['HOUR'].strip()

                # Solo reprograma si la hora cambio
                if hour != last_hour:
                    if job_ref:
                        schedule.cancel_job(job_ref)

                    job_ref = schedule.every().day.at(hour).do(scheduled_task)
                    last_hour = hour
        except Exception as e:
            J.error(f'Error al manejar cambios en config.ini: {e}')

        schedule.run_pending()
        time.sleep(30)
        J.info(f'Checking... {hour}')

if __name__ == '__main__':
    main()