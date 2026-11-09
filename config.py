import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

# Lee el archivo .env (variables de entorno del proyecto)
load_dotenv()

# Base de datos: SQLite (un archivo, sin instalar nada) o MySQL (producción, ej: Aiven)
DB_CONNECTION = os.getenv('DB_CONNECTION', 'sqlite')
if DB_CONNECTION == 'mysql':
    # URL.create codifica bien los símbolos de la contraseña
    DATABASE_URL = URL.create(
        'mysql+pymysql',
        username=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD') or None,
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        database=os.getenv('DB_NAME', 'dropx'),
        query={'charset': 'utf8mb4'},
    )
else:
    DATABASE_URL = 'sqlite:///' + str(Path(__file__).parent / 'instance' / 'dropx.db')


class Config:
    # Clave para firmar la sesión del panel web y los tokens JWT de la API
    SECRET_KEY = os.getenv('SECRET_KEY')

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    # Certificado SSL (archivo .pem) que exigen algunos servicios en la nube, como Aiven
    _ssl_ca = os.getenv('DB_SSL_CA')
    SQLALCHEMY_ENGINE_OPTIONS = {'connect_args': {'ssl': {'ca': _ssl_ca}}} if _ssl_ca and DB_CONNECTION == 'mysql' else {}

    # Duración del token JWT de la API (por defecto 168 horas = 7 días, para que
    # el repartidor no tenga que iniciar sesión en la app todos los días)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_EXPIRES_HOURS', 168)))

    # Número del asesor para el formulario de contacto (con indicativo y sin "+")
    WHATSAPP_ADVISOR_NUMBER = os.getenv('WHATSAPP_ADVISOR_NUMBER', '')
