import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "insyte_secret_key_oracle23ai_academic_2026")
    
    # Oracle Database 23ai Free Connection
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "1521"))
    DB_SERVICE = os.getenv("DB_SERVICE", "FREEPDB1")
    DB_USER = os.getenv("APP_ADMIN_USER", "INSYTE_ADMIN")
    DB_PASSWORD = os.getenv("APP_ADMIN_PASSWORD", "AdminSecurePassword2026!")
    DB_SYS_USER = os.getenv("DB_SYS_USER", "SYS")
    
    # Pool sizing
    DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "2"))
    DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "10"))
    DB_POOL_INCREMENT = int(os.getenv("DB_POOL_INCREMENT", "1"))
    
    # AI Vector Settings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))
    
    # Flask settings
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"
    PORT = int(os.getenv("FLASK_PORT", "5000"))
