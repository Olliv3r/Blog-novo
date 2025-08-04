from app.main import bp
from flask import render_template

@bp.route("/")
@bp.route("/index")
@bp.route("/home")
def index():
  return render_template("main/index.html", title="Página Inicial")