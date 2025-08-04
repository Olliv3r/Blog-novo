from app.dashboard import bp
from flask import render_template, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.decorators import admin_required, permission_required
from app.models import Permission, User, Role, Comment, Situation, Article
from app import db
import sqlalchemy as sa

# retorna o numero de registros de uma tabela
def count_table(table):
  return db.session.scalar(
    sa.select(sa.func.count()).select_from(table)
  )

#RENDERIZA PÆÁGINA PADRÃO DO PAINEL
@bp.route("/dashboard", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard():
  models = {
    "total_users": User,
    "total_roles": Role,
    "total_comments": Comment,
    "total_situations": Situation,
    "total_articles": Article
  }
  
  counts = {key: count_table(model) for key, model in models.items()}
  
  return render_template(
    "dashboard/dashboard.html", 
    **counts,
    title="Painel Administrativo", 
    use_admin_layout=True
  )

