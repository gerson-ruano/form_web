import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


class Config:
    """Configuración base (por defecto)."""
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "clave_por_defecto")
    ADMIN_USER = os.getenv("ADMIN_USER", "admin")
    ADMIN_PASS = os.getenv("ADMIN_PASS", "12345")
    FORMS_DIR = os.getenv("FORMS_DIR", "forms")
    DATA_DIR = os.getenv("DATA_DIR", "data")


class DevelopmentConfig(Config):
    """Configuración para desarrollo."""
    DEBUG = True
    ENV = "development"


class ProductionConfig(Config):
    """Configuración para producción."""
    DEBUG = False
    ENV = "production"
