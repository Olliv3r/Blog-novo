from flask import Blueprint

bp = Blueprint("admin", __name__)

# Filtro de url
@bp.app_template_filter('check_url_type')
def check_url_type(url):
  if not url:
    return None
  if url.startswith(('http://', 'https://')):
    return 'external'
  else:
    return 'local'
  

from app.admin import views