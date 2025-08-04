from flask_login import login_required
from app.decorators import admin_required, permission_required
from app.models import Permission, Comment, User
from app.comments import bp
from flask import render_template, url_for, jsonify, request, current_app
import sqlalchemy as sa
from app import db
 
# 4: RENDERIZA PÁGINA QUE LISTA OS COMENTÀRIOS DE ARTIGOS
@bp.route("/dashboard/articles/comments", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_articles_comments():
  return render_template(
    "comments/articles_comments.html",
    title="Comentários de artigos",
    use_admin_layout=True
  )
  
# RENDERIZA UMA LISTA DE COMENTÁRIOS DE ARTIGO VIA JQUERY
@bp.route("/dashboard/articles/comments/render", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_articles_comments_render():
  query = sa.select(Comment).order_by(Comment.id.desc())
  page = request.args.get("page", 1, type=int)
  comments = db.paginate(query, page=page, per_page=current_app.config["PER_PAGE_COMMENTS"], error_out=False)
  page_prev = url_for("comments.dashboard_articles_comments_render", page=comments.prev_num) if comments.has_prev else None
  page_next = url_for("comments.dashboard_articles_comments_render", page=comments.next_num) if comments.has_next else None
  
  return jsonify(
    render_template(
      "comments/_article_comment_list.html",
      comments=comments,
      page_prev=page_prev,
      page_next=page_next
    )
  )
  
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