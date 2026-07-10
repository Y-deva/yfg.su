import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'

    # Если DATABASE_URL не задан — используем SQLite
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        # Создаём папку instance, если её нет
        os.makedirs('instance', exist_ok=True)
        # Используем абсолютный путь
        base_dir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(base_dir, 'instance', 'yfg.db')
        database_url = f'sqlite:///{db_path}'

    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('FLASK_DEBUG') == 'True'