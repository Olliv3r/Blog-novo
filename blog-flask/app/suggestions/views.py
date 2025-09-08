from flask_login import login_required
from app.decorators import admin_required, permission_required
from app.models import Permission, Suggestion, User
from app.suggestions import bp
from flask import render_template, url_for, jsonify, request, current_app
import sqlalchemy as sa
from app import db
 
# 4: RENDERIZA PÁGINA QUE LISTA OS COMENTÀRIOS DE ARTIGOS
@bp.route("/dashboard/suggestions", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_suggestions():
  return render_template(
    "suggestions/suggestions.html",
    title="Sugestôes",
    use_admin_layout=True
  )
  
# RENDERIZA UMA LISTA DE SUGESTÔES JQUERY
@bp.route("/dashboard/suggestions/render", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_suggestions_render():
  query = sa.select(Suggestion).order_by(Suggestion.id.desc())
  page = request.args.get("page", 1, type=int)
  suggestions = db.paginate(query, page=page, per_page=current_app.config["PER_PAGE_SUGGESTIONS"], error_out=False)
  page_prev = url_for("suggestions.dashboard_suggestions_render", page=suggestions.prev_num) if suggestions.has_prev else None
  page_next = url_for("suggestions.dashboard_suggestions_render", page=suggestions.next_num) if suggestions.has_next else None
  
  return jsonify(
    render_template(
      "suggestions/_suggestion_list.html",
      suggestions=suggestions,
      page_prev=page_prev,
      page_next=page_next
    )
  )
"""
# RENDERIZA COMENTÁRIOS DE ARTIGO PESQUISADOS VIA JQUERY
@bp.route("/dashboard/articles/comments/search", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_articles_comments_search():
  word = request.args.get("word", "").strip()
  query =  sa.select(Comment).join(User, Comment.user_id == User.id).filter(User.username.ilike(f'%{word}%')).limit(10)

  if word:
    comments = db.session.scalars(query).all()
  else:
    comments = []
  
  return jsonify(
    render_template(
      "comments/_article_comment_search.html",
      comments=comments,
      total_result=len(comments)
    )
  )
"""