from app.error import bp
from flask import render_template, url_for

# Contrói o caminho da imagem de erros
def build_url_img(img):
  url_img = url_for("static", filename=f"images/{img}.png")
  return url_img

@bp.app_errorhandler(404)
def not_found(error):
  return render_template(
    "error/error.html",
    title="Página não encontrada",
    title_error="Erro 404",
    text_error="Procuramos esta página em todos os lugares. Tem certeza de que o URL do site está correto? entre em contato com o proprietário do site.",
    url_image=build_url_img("404")
  ), 404
  
@bp.app_errorhandler(403)
def forbidden(error):
  return render_template(
    "error/error.html",
    title="Sem permisão pra acessar a página",
    title_error="Erro 403",
    text_error="Parece que você não tem permissão para acessar este conteúdo. Seu usuário pode ter uma função com permissôes insuficientes.",
    url_image=build_url_img("403")
  ), 403

@bp.app_errorhandler(500)
def internal(error):
  return render_template(
    "error/error.html",
    title="Problema com o servidor",
    title_error="Erro 500",
    text_error="Ops! algo estar errado. Tente atualizar esta página ou entre em contato conosco se o problema persistir.",
    url_image=build_url_img("500")
  ), 500