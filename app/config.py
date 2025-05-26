from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv() 

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') 
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "sslmode": "require"
        }
    }
    JWT_SECRET_KEY = "### seu segredo ###"
    JWT_COOKIE_SECURE = False
    JWT_TOKEN_LOCATION = ["cookies"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_COOKIE_SAMESITE = "Lax"
    SENHA_EMAIL = os.getenv("EMAIL_SENHA")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
