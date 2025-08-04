from config import Config
from app import create_app
from flask_migrate import Migrate
from app import db
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models import insert_all

app = create_app(Config)
migrate = Migrate(app, db)

@app.context_processor
def inject_layout_flags():
  return dict(use_admin_layout=False, sa=sa, so=so, insert_all=insert_all)