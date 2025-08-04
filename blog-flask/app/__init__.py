from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap4
from flask_mail import Mail
from flask_moment import Moment
from logging.handlers import SMTPHandler, RotatingFileHandler
import logging
import os

db = SQLAlchemy()
login = LoginManager()
login.login_view = "auth.signin"
login.login_message = u"Página restrita, faça login para ter acesso!"
bootstrap = Bootstrap4()
moment = Moment()
mail = Mail()

def get_upload_folder():
  return os.path.join(current_app.root_path, "static", "images", "uploads", "profile")

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config_name)
    
    with app.app_context():
      app.config["UPLOAD_FOLDER"] = get_upload_folder()
    
    db.init_app(app)
    login.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    mail.init_app(app)
    
    from app.error import bp as error_bp
    app.register_blueprint(error_bp, url_prefix="/error")

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    
    from app.profile import bp as profile_bp
    app.register_blueprint(profile_bp)
    
    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    from app.users import bp as users_bp
    app.register_blueprint(users_bp)
    
    from app.articles import bp as articles_bp
    app.register_blueprint(articles_bp)
    
    from app.comments import bp as comments_bp
    app.register_blueprint(comments_bp)
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    if not app.debug:
      if app.config["MAIL_SERVER"]:
        auth = None
        
        if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
          auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
         
        secure = None 
        if app.config["MAIL_USE_TLS"]:
          secure = ()
          
        mail_handler = SMTPHandler(
          mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
          fromaddr="no-reply@" + app.config["MAIL_SERVER"],
          toaddrs=app.config["ADMINS"],
          subject="Tio oliver falha",
          credentials=auth, secure=secure
        )
        
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
        
        if not os.path.exists("logs"):
          os.mkdir("logs")
          
        file_handler = RotatingFileHandler("logs/tio_oliver.log", maxBytes=10240, backupCount=10)
        file_handler.setFormatter(
          logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
        )
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("Tio oliver startup")
    return app

from app import models
