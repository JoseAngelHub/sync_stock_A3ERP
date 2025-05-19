import configparser
import os
import pandas as pd
import paramiko
import ftplib
import time
from datetime import datetime
import sched
import pyodbc
import schedule
from setup_ini import create_ini
import logger as J

J.Logger("logs")

scheduler = sched.scheduler(time.time, time.sleep)
last_mtime = 0
last_hour = None
job_ref = None


# Leer archivo de configuracion
def read_config():
    create_ini()
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config


# Obtener datos desde base de datos
def get_info(config):
    db_conf = config["DATABASE"]
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={db_conf["SERVER"]};DATABASE={db_conf["DATABASE_NAME"]};UID={db_conf["USER"]};PWD={db_conf["PASSWORD"]}'
    query = db_conf["QUERY"]
    J.info("Conectando a la base de datos...")
    with pyodbc.connect(conn_str) as conn:
        df = pd.read_sql(query, conn)
    J.info(f"{len(df)} registros recuperados de la base de datos.")
    return df


# Generar fichero CSV o Excel
def generate(df, config):
    csv_conf = config["CSVDATA"]
    file_name = f"{csv_conf['file_name']}_{datetime.now().strftime('%Y%m%d')}"
    file_format = csv_conf["FORMAT"].lower()

    if file_format == "csv":
        file = f"{file_name}.csv"
        df.to_csv(file, index=False)
    elif file_format == "xlsx":
        file = f"{file_name}.xlsx"
        df.to_excel(file, index=False)
    else:
        raise ValueError("Formato de fichero no soportado")

    J.info(f"Fichero generado: {file}")
    return file


# Subir archivo por FTP o SFTP
def upload(file, config):
    ftp_conf = config["FTP"]
    server_type = ftp_conf["server_type"].upper()
    path = ftp_conf["PATH"]
    host = ftp_conf["HOST_FTP"]
    user = ftp_conf["USER_FTP"]
    password = ftp_conf["PASSWORD_FTP"]
    port = int(ftp_conf["PORT_FTP"])

    if not path:
        path = "./"

    if path.endswith("/"):
        path = path[:-1]

    if server_type == "SFTP":
        J.info(f"Conectando via SFTP a {host}...")
        transport = paramiko.Transport((host, port))
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        try:
            remote_file = f"{path}/{os.path.basename(file)}"
            J.info(f"Intentando subir archivo a: {remote_file}")

            try:
                sftp.chdir(path)
            except IOError:
                J.warning(
                    f"La ruta remota '{path}' no existe. Intentando subir a la raiz '/'"
                )
                remote_file = os.path.basename(file)

            sftp.put(file, remote_file)
            J.info("Archivo subido via SFTP correctamente")
        except Exception as e:
            J.error(f"Error al subir archivo por SFTP: {e}")
        finally:
            sftp.close()
            transport.close()
    elif server_type == "FTP":
        J.info(f"Conectando via FTP a {host}...")
        with ftplib.FTP() as ftp:
            ftp.connect(host, port)
            ftp.login(user, password)
            try:
                ftp.cwd(path)
            except ftplib.error_perm:
                J.warning(
                    f"La ruta remota '{path}' no existe. Se subira en el directorio raiz."
                )

            with open(file, "rb") as f:
                remote_file = os.path.basename(file)
                ftp.storbinary(f"STOR {remote_file}", f)

            J.info("Archivo subido via FTP correctamente")
    else:
        raise ValueError("Tipo de servidor no soportado")


# Ejecutar proceso completo
def sync_job():
    try:
        config = read_config()
        df = get_info(config)
        file = generate(df, config)
        upload(file, config)
    except ftplib.error_perm:
        J.error(f"Error en la ruta especificada por el usuario")
    except ValueError as e:
        J.error(f"{e}")
    except Exception as e:
        J.error(f"Error en el proceso: {e}")


# Validar dias configurados
def is_valid_day(days_config):
    valid_days = set()
    for part in days_config.split(","):
        part = part.strip()
        if "-" in part:
            start, end = map(int, part.split("-"))
            valid_days.update(range(start, end + 1))
        else:
            valid_days.add(int(part))
    current_day = datetime.today().isoweekday()
    return current_day in valid_days


# Ejecutar tarea programada
def scheduled_task():
    config = read_config()
    days = config["TIMER"]["DAYS"]
    if is_valid_day(days):
        sync_job()
    else:
        J.info("Hoy no es un dia programado.")


# Verificar y programar tareas
def check_config(sc):
    global last_mtime, last_hour, job_ref

    try:
        config = read_config()
        current_mtime = os.path.getmtime("config.ini")

        if current_mtime != last_mtime:
            last_mtime = current_mtime
            hour = config["TIMER"]["HOUR"].strip()

            if hour != last_hour:
                if job_ref:
                    schedule.cancel_job(job_ref)
                job_ref = schedule.every().day.at(hour).do(scheduled_task)
                last_hour = hour
                J.info(f"Tarea programada para las {hour}")
    except Exception as e:
        J.error(f"Error al manejar cambios en config.ini: {e}")

    schedule.run_pending()
    scheduler.enter(30, 1, check_config, (scheduler,))
    J.info(f"Checking... {last_hour}")


# Punto de entrada
def main():
    scheduler.enter(0, 1, check_config, (scheduler,))
    scheduler.run()


if __name__ == "__main__":
    main()
