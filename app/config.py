from dotenv import load_dotenv
import os

load_dotenv() 

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') 
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')  
    print("Database URL:", os.getenv('DATABASE_URL'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

