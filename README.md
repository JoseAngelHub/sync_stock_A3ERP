# Sincronizador de Datos (FTP/SFTP)

Este proyecto es un script en Python que automatiza la sincronización de datos desde una base de datos SQL Server hacia un servidor FTP o SFTP. El script:

1. **Lee la configuración** desde un archivo `config.ini`.
2. **Obtiene datos** desde la base de datos mediante una consulta SQL.
3. **Genera un archivo** (CSV o Excel) con los datos recuperados.
4. **Sube el archivo** generado a un servidor FTP o SFTP.
5. **Ejecuta automáticamente** la tarea a una hora y en unos días definidos.

---

## 🚀 Tecnologías y librerías utilizadas

- `configparser`
- `pandas`
- `pyodbc`
- `paramiko`
- `ftplib`
- `schedule`
- `datetime`
- `time`
- `logger` (módulo propio)

---

## 📁 Estructura de archivos
```yaml
├── main.py
├── config.ini
├── logs/
│ └── ...
├── requirements.txt
└── README.md
```
---

## ⚙️ Configuración (`config.ini`)

### Sección `[DATABASE]`

| Clave            | Descripción                                                   |
|------------------|---------------------------------------------------------------|
| SERVER           | Dirección del servidor SQL Server.                            |
| DATABASE_NAME    | Nombre de la base de datos.                                   |
| USER             | Usuario de la base de datos.                                  |
| PASSWORD         | Contraseña de la base de datos.                               |
| QUERY            | Consulta SQL para recuperar los datos.                        |

### Sección `[CSVDATA]`

| Clave            | Descripción                                                   |
|------------------|---------------------------------------------------------------|
| FICHERO_NOMBRE   | Nombre base del fichero generado.                             |
| FORMATO          | Formato del fichero: `csv` o `xlsx`.                          |

### Sección `[FTP]`

| Clave            | Descripción                                                   |
|------------------|---------------------------------------------------------------|
| TIPO_SERVER      | Tipo de servidor: `FTP` o `SFTP`.                             |
| HOST_FTP         | Dirección del servidor FTP/SFTP.                              |
| USER_FTP         | Usuario para la conexión FTP/SFTP.                            |
| PASSWORD_FTP     | Contraseña para la conexión FTP/SFTP.                         |
| PORT_FTP         | Puerto para la conexión.                                      |

### Sección `[TIMER]`

| Clave            | Descripción                                                   |
|------------------|---------------------------------------------------------------|
| HOUR             | Hora de ejecución en formato `HH:MM` (24h).                   |
| DAYS             | Días de ejecución (ejemplo: `1-5` para lunes a viernes).      |

---

## 🛠️ Instalación

1️⃣ Clona este repositorio:

```bash
git clone https://github.com/tuusuario/sincronizador-datos.git
cd sincronizador-datos
pip install -r requirements.txt
```
Nota: Las principales dependencias son:

    pandas
    
    pyodbc
    
    paramiko
    
    schedule

▶️ Uso
Configura el archivo config.ini con los valores correctos.

Ejecuta el script principal:

```bash
python main.py
```

El script permanecerá en ejecución y esperará la hora programada para ejecutar la tarea automáticamente, verificando también si el día actual está permitido según la configuración.

📝 Funcionalidades
✅ Conexión a SQL Server usando pyodbc.

✅ Exportación de datos a CSV o Excel usando pandas.

✅ Carga de archivos a servidores FTP o SFTP.

✅ Ejecución automática a una hora y días específicos usando schedule.

✅ Logs detallados del proceso (ubicados en la carpeta logs).

🔒 Seguridad
Usa config.ini para manejar las credenciales de manera centralizada y sencilla.

Asegúrate de proteger este archivo y la carpeta de logs para evitar la exposición de datos sensibles.

```markefile
INFO: Conectando a la base de datos...
INFO: 150 registros recuperados de la base de datos.
INFO: Fichero generado: export_20250509.csv
INFO: Conectando via SFTP a sftp.ejemplo.com...
INFO: Archivo subido via SFTP correctamente
INFO: --- Sincronizacion completada correctamente ---
```

## 🤝 Colaboradores
Este proyecto ha sido desarrollado en colaboración con:

- [JoseAngelHub](https://github.com/JoseAngelHub)
- [JoseAngelHub](https://github.com/DaniAndries)

## 📄 **Licencia**

Este proyecto está licenciado bajo la **Licencia GNU** - consulta el archivo [LICENSE](LICENSE) para más detalles.

---
