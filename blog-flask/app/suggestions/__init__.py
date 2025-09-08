from flask import Blueprint

bp = Blueprint("suggestions", __name__)

from app.suggestions import views