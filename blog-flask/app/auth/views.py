from app.auth import bp
from app import db
import sqlalchemy as sa
from flask import redirect, url_for, render_template, jsonify, g, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from app.auth.forms import SignupForm, SigninForm, ResetPasswordEmailForm, ResetPasswordForm
from app.models import User
from app.email import send_email_confirm_account, send_email_confirm_email, send_email_reset_password
from datetime import datetime

# RETORNA O ID DO USUARIO LOGADO
def get_current_user_id():
  if current_user.is_authenticated:
    return current_user.id

# REDIRECIONA PRA PAGINA DE DETALHES DE CONFIRMAÇÃO DA CONTA ENQUANTO NÃO CONFIRMOU
@bp.before_app_request
def before_request():
  if current_user.is_authenticated and not current_user.confirmed and request.blueprint != "auth" and request.endpoint != "static":
    return redirect(url_for("auth.unconfirmed"))
    
  g.user_id = get_current_user_id()
  
# PÁGINA DE DETALHES DE CONFIRMAÇÃO DA CONTA
@bp.route("/unconfirmed", methods=["GET",])
def unconfirmed():
  if current_user.is_anonymous or current_user.confirmed:
    return redirect(url_for("main.index"))
    
  return render_template("auth/unconfirmed.html", title="A conta ainda não foi confirmada")

# CONFIRMA A CONTA DE USUARIO
@bp.route("/confirm-account/<token>", methods=["GET"])
@login_required
def confirm_account(token):
  if not current_user.is_authenticated:
    flash("Antes de confirmar a sua conta, faça login")
    return redirect(url_for("auth.signin"))
    
  if current_user.confirmed:
    return redirect(url_for("main.index"))
  else:
    if current_user.check_token_confirm_account(token):
      db.session.commit()
      flash("Você confirmou a sua conta. Obrigado!", "success")
    else:
      flash("O link de confirmação é inválido ou expirou!")
  return redirect(url_for("main.index"))

# REENVIA CONFIRMAR A CONTA DE USUARIO NO EMAIL
@bp.route("/resend-confirm-account", methods=["GET"])
def resend_confirm_account():
  user = current_user
  
  send_email_confirm_account(user)
  flash("Um novo e-mail de confirmação foi enviado a você por e-mail.")
  return redirect(url_for("main.index"))

# ATUALIZA O EMAIL
@bp.route("/confirm-email/<token>", methods=["GET"])
def confirm_email(token):
  user = current_user.check_token_confirm_email(token)
  
  if user:
    user.email = user.new_email
    user.new_email = None
    user.email_change_token = None
    user.email_confirmed = True
    db.session.commit()
    flash("Seu e-mail foi confirmado", "success")
    return redirect(url_for("main.index"))
  else:
    flash("O token expirou, solicite um novo!")
    return redirect(url_for("main.index"))
  
# ENVIA REDEFINIÇÃO DE SENHA POR EMAIL
@bp.route("/reset-password-request", methods=["GET", "POST"])
def reset_password_request():
  if current_user.is_authenticated:
    return redirect(url_for("main.index"))

  form = ResetPasswordEmailForm()
  
  if form.validate_on_submit():
    user = db.session.scalar(
      sa.select(User).filter_by(email=form.email.data)
    )
    
    if user is None:
      flash("O endereço de e-mail é inválido, tente com o e-mail que você cadastrou no site.", "danger")
      return redirect(url_for("auth.reset_password_request"))
    else:
      send_email_reset_password(user)
    flash('Verifique seu e-mail para obter as instruções para redefinir sua senha.', "warning")
    return redirect(url_for("auth.signin"))

  return render_template(
    "auth/reset_password_request.html", 
    form=form,
    title="Redefinir a senha"
  )
  
# ATUALIZA A SENHA DO USUARIO
@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
  if current_user.is_authenticated:
    return redirect(url_for("main.index"))
    
  form = ResetPasswordForm()
  user = User.check_token_password_reset(token)
  
  if user is None:
    flash("Token inválido!", "danger")
    return redirect(url_for("auth.reset_password_request"))
    
  if form.validate_on_submit():
    if form.password.data == form.password2.data:
      user.set_password(form.password.data)
      db.session.commit()
      flash("Sua senha foi alterada!", "success")
      return redirect(url_for("auth.signin"))
    else:
      flash("As senhas não correspodem!", "danger")
      return redirect(url_for("auth.reset_password"))

  return render_template(
    "auth/reset_password.html",
    form=form,
    title="Alterar a senha"
  )

# FAZ O CADASTRO DE UM USUARIO
@bp.route("/signup", methods=["GET", "POST"])
def signup():
  if current_user.is_authenticated:
    return redirect(url_for("main.index"))
    
  form = SignupForm()
  
  if form.validate_on_submit():
    with db.session.no_autoflush:
      user = User(
        username=form.username.data,
        email=form.email.data
      )
      user.set_password(form.password.data)
    db.session.add(user)
    db.session.commit()
    flash("Cadastrado com sucesso!", "success")
    send_email_confirm_account(user)
    flash("Um novo e-mail de confirmação foi enviado a você por e-mail.")
    return redirect(url_for("auth.signin"))
    
  return render_template(
    "auth/signup.html", 
    title="Página de Cadastro", 
    form=form)

# FAZ O LOGIN DO USUARIO
@bp.route("/signin", methods=["GET", "POST"])
def signin():
  if current_user.is_authenticated:
    return redirect(url_for("main.index"))
    
  form = SigninForm()
  
  if form.validate_on_submit():
    query = sa.select(User).filter_by(email=form.email.data)
    user = db.session.scalar(query)
    
    if user is None or not user.check_password(form.password.data):
      flash("Falha na autenticação: usuário inexistente ou senha incorreta.", "danger")
      return redirect(url_for("auth.signin", next=url_for("main.index")))
      
    login_user(user, remember=form.remember_me.data)
    flash("Você logou no site", "success")
    return redirect(url_for("main.index"))
    
  return render_template(
    "auth/signin.html", 
    title="Página de Login", 
    form=form)
    
# ENCERRA SESSÃO DO USUARIO
@bp.route("/logout", methods=["GET",])
def logout():
  if current_user.is_authenticated:
    logout_user()
    flash("Você deslogou do site", "success")
  return redirect(url_for("main.index"))
  
# VERIFICA SE AINDA NÃO CONFIRMOU A ATUALIZAÇÃO DO NOVO EMAIL NO PERFIL - AJAX
@bp.route("/profile/check-token-email", methods=["POST"])
@login_required
def profile_check_token_email():
  email_change_token = current_user.email_change_token
  user = current_user.check_token_confirm_email(email_change_token)
  
  if user:
    return jsonify(is_valid=True)
  else:
    return jsonify(is_valid=False)

# ENVIA PEDIDO DE ATUALIZAÇÃO DO EMAIL - AJAX
@bp.route("/profile/email/change", methods=["POST"])
@login_required
def profile_email_change():
  user = current_user
  
  if request.method == "POST":
    new_email = request.form.get("new_email")
    send_email_confirm_email(user, new_email)
    return jsonify(status="success", message="Verifique sua lista de e-mails para confirmar seu novo e-mail.", color="success")
  else:
    return jsonify(status="error", message="Não foi possível enviar a solicitação de atualização do novo e-mail", color="success")
    
# CANCELA A ATUALIZAÇÃO DO EMAIL - AJAX
@bp.route("/profile/email/cancel", methods=["POST"])
@login_required
def profile_email_cancel():
  current_user.new_email = None
  current_user.email_change_token = None
  current_user.email_confirmed = False
  db.session.commit()
  return jsonify(status="success", message="Atualização de email cancelada", color="success")

#### Atualiza a senha do perfil ####

# RENDERIZA PAGINA DE SENHA NO PERFIL DO USUÁRIO - AJAX
@bp.route("/profile/password/view", methods=["GET"])
@login_required
def profile_password_view():
  return jsonify(
    render_template(
      "auth/_password.html"
    )
  )
  
# ATUALIZA SENHA DO USUÁRIO NO PERFILb- AJAX
@bp.route("/profile/password", methods=["POST"])
@login_required
def profile_password():
  user_id = request.form.get("user_id")
  current_password = request.form.get("current_password")
  password = request.form.get("password")
  password2 = request.form.get("password2")
  
  user = User.query.get(user_id)
  
  # Verifica existencia do USUARIO
  if user is None:
    return jsonify(status="error", message="Usuário não encontrado!", color="danger")
  
  # Se for o próprio usuário (não o admin ou admin mexendo em si mesmo)
  # if user == current_user and not user.check_password(current_password):
  #   return jsonify(status="error", message="Senha atual incorreta!", color="danger")
  if not user.check_password(current_password):
    return jsonify(status="error", message="Senha atual incorreta!", color="danger")
  
  if password != password2:
    return jsonify(status="error", message="As senhas não conferem!", color="danger")
  
  if len(password) < 6 or len(password2) < 6:
    return jsonify(status="error", message="O tamanho mínimo da senha é 6 caracteres!", color="danger")
  
  user.set_password(password)
  user.modified = datetime.utcnow()
  db.session.commit()
  return jsonify(status="success", message="Senha atualizada com sucesso!", color="success")
  
