import configparser
import os
import logger as J

J.Logger("logs")

def create_ini():
    if os.path.isfile("config.ini"):
        J.info("Archivo config existente, comprobando formato")
        update_ini()
        return
    
    config = configparser.ConfigParser()
    config.add_section('DATABASE')
    config.set('DATABASE', 'SERVER', 'ip')
    config.set('DATABASE', 'USER', 'usr')
    config.set('DATABASE', 'PASSWORD', 'pass')
    config.set('DATABASE', 'DATABASE_NAME', 'db')
    config.set('DATABASE', 'QUERY', 'spam')
    
    config.add_section('CSVDATA')
    config.set('CSVDATA', 'FORMAT', 'ip')
    config.set('CSVDATA', 'FILE_NAME', 'usr')
    
    config.add_section('FTP')
    config.set('FTP', 'SERVER_TYPE', 'SFTP')
    config.set('FTP', 'HOST_FTP', 'usr')
    config.set('FTP', 'USER_FTP', 'psw')
    config.set('FTP', 'PASSWORD_FTP', 'pass')
    config.set('FTP', 'PORT_FTP', '22')
    
    config.add_section('TIMER')
    config.set('TIMER', 'HOUR', '17:00')
    config.set('TIMER', 'DAYS', '1-5, 7')

    with open('config.ini', 'w') as configfile:
        config.write(configfile)
        J.info("Se ha creado el archivo config")

DEFAULT_CONFIG = {
    'DATABASE': {
        'SERVER': 'ip',
        'USER': 'usr',
        'PASSWORD': 'pass',
        'DATABASE_NAME': 'db',
        'QUERY': 'spam',
    },
    'CSVDATA': {
        'FORMAT': 'ip',
        'FILE_NAME': 'usr',
    },
    'FTP': {
        'SERVER_TYPE': 'SFTP',
        'HOST_FTP': 'usr',
        'USER_FTP': 'psw',
        'PASSWORD_FTP': 'pass',
        'PORT_FTP': '22',
    },
    'TIMER': {
        'HOUR': '17:00',
        'DAYS': '1-5, 7',
    }
}

SECTIONS = ['DATABASE', 'CSVDATA', 'FTP', 'TIMER']
OPTIONS = ['SERVER', 'USER', 'PASSWORD', 'DATABASE_NAME', 'QUERY', 'FORMAT', 'FILE_NAME', 'SERVER_TYPE', 'HOST_FTP', 'USER_FTP', 'PASSWORD_FTP', 'PORT_FTP', 'HOUR', 'DAYS']

def update_ini():
    config_path = "config.ini"
    config = configparser.ConfigParser()

    if os.path.isfile(config_path):
        config.read(config_path)

    modified = False

    for section, options in DEFAULT_CONFIG.items():
        if not config.has_section(section):
            config.add_section(section)
            modified = True
            J.info(f"Se añadio seccion: [{section}]")

        for option, default_value in options.items():
            if not config.has_option(section, option):
                config.set(section, option, default_value)
                modified = True
                J.info(f"  Se añadio opcion: {section}.{option} = {default_value}")

    # Solo escribe si se hicieron cambios
    if modified:
        with open(config_path, 'w') as configfile:
            config.write(configfile)
        J.info("Archivo 'config.ini' actualizado.")
    else:
        J.info("No hubo cambios: todos los campos existen.")