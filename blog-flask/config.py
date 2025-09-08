import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Config:
  SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///' + os.path.join(BASE_DIR, 'dev.db')
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  SECRET_KEY = os.getenv("SECRET_KEY")
  
  PAGE=10
  
  # USERS:
  PER_PAGE_USERS = PAGE
  PER_PAGE_SITUATIONS_USERS = PAGE
  PER_PAGE_ROLES = PAGE
  PER_PAGE_PROFILES = PAGE
  
  # COMMENTS:
  PER_PAGE_COMMENTS = PAGE
  # ARTICLES:
  PER_PAGE_ARTICLES = PAGE
  
  # EMAIL:
  BLOG_ADMIN = os.getenv("BLOG_ADMIN")
  ADMINS = [BLOG_ADMIN]
  MAIL_SERVER = os.getenv("MAIL_SERVER")
  MAIL_PORT = os.getenv("MAIL_PORT")
  MAIL_USE_TLS = os.getenv("MAIL_USE_TLS")
  MAIL_USERNAME = os.getenv("MAIL_USERNAME")
  MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
  
  # IMAGENS - Configurações de upload
  # UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'images', 'uploads', 'profiles')
  ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
  MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB