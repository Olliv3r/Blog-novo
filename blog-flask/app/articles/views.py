from flask_login import login_required
from app.decorators import admin_required, permission_required
from app.models import Permission, Article, User, ArticleBlock, BlockType
from app.articles import bp
from flask import render_template, url_for, jsonify, request, current_app
from app import db
import sqlalchemy as sa
  
# 5: RENDERIZA PÁGINA QUE LISTA OS ARTIGOS DE ARTIGOS
@bp.route("/dashboard/articles", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_articles():
  return render_template(
    "articles/articles.html",
    title="Artigos",
    use_admin_layout=True
  )
  
# RENDERIZA UMA LISTA DE ARTIGOS VIA JQUERY
@bp.route("/dashboard/articles/render", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_articles_render():
  query = sa.select(Article).order_by(Article.id.desc())
  page = request.args.get("page", 1, type=int)
  articles = db.paginate(query, page=page, per_page=current_app.config["PER_PAGE_ARTICLES"], error_out=False)
  page_prev = url_for("articles.dashboard_articles_render", page=articles.prev_num) if articles.has_prev else None
  page_next = url_for("articles.dashboard_articles_render", page=articles.next_num) if articles.has_next else None
  
  return jsonify(
    render_template(
      "articles/_article_list.html",
      articles=articles,
      page_prev=page_prev,
      page_next=page_next
    )
  )
  
# RENDERIZA ARTIGOS PESQUISADOS VIA JQUERY
@bp.route("/dashboard/articles/search", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_articles_search():
  word = request.args.get("word", "").strip()
  query = sa.select(Article).join(User, Article.user_id == User.id).filter(User.username.ilike(f'%{word}%')).limit(10)
  
  if word:
    articles = db.session.scalars(query).all()
  else:
    articles = []
    
  return jsonify(
    render_template(
      "articles/_article_search.html",
      articles=articles,
      total_result=len(articles)
    )
  )
  
@bp.route("/blog/article/<slug>", methods=["GET"])
def article(slug):
  query = sa.select(Article).filter_by(slug=slug)
  article = db.session.scalar(query)
  
  blocks = db.session.scalars(
    sa.select(ArticleBlock).where(ArticleBlock.article_id == article.id)
  ).all()
  
  return render_template(
    "articles/_article.html",
    title=article.title,
    article=article,
    blocks=blocks
  )
  
@bp.route("/dashboard/block_types", methods=["GET"])
def get_block_types():
  block_types = BlockType.query.all()
  return jsonify([{"id": block.id, "name": block.name} for block in block_types])
  
  