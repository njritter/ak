import os

class Config:
    BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000/')
    SECRET_KEY = os.getenv('SECRET_KEY', 'super-secret-key')
    DATA = os.environ.get('DATA', '../data')