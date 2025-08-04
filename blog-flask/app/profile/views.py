from app.profile import bp
from flask_login import login_required, current_user
from flask import render_template, jsonify, request, current_app
from app.models import Profile, User
import sqlalchemy as sa
from app import db
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import os

# Renderiza página de perfil do usuário
@bp.route("/profile", methods=["GET",])
@login_required
def profile():
  return render_template(
    "profile/profile.html",
    title="Perfil do Usuário"
  )
  
# Renderiza página de dados pessoais no perfil - AJAX
@bp.route("/profile/info", methods=["GET",])
@login_required
def profile_info():
  email_change_token = current_user.email_change_token
  user, token_message = current_user.check_token(email_change_token)
  
  token = False
  
  if user is not None:
    token = True
    
  return jsonify(
    render_template(
      "profile/_info.html",
      token=token,
      token_message=token_message
    )
  )
  
# Edita dados pessoais de perfil do usuário - AJAX
@bp.route("/profile/edit/info", methods=["GET", "POST"])
@login_required
def profile_edit_info():
  if not request.form.get("user_id"):
    return jsonify(status="error", message="ID de usuário não existe!", color="danger")
    
  user_id = request.form.get("user_id")
    
  if str(current_user.id) != str(user_id):
    return jsonify(status="error", message="Acesso negado!", color="danger")
    
  user = db.session.scalar(
    sa.select(User).where(User.id == user_id)
  )
  
  if user is None:
    return jsonify(status="error", message="Usuário não existe!", color="danger")
    
  profile = user.profile or Profile(user=user)
  inputs = ["name", "location", "website", "about_me"]
  
  for _input in inputs:
    setattr(profile, _input, request.form.get(_input))
    
  profile.modified = datetime.utcnow()
  
  db.session.add(profile)
  db.session.commit()
  
  return jsonify(status="success", message="Dados pessoais atualizados!", color="success")

# RENDERIZA PAGINA DE FOTO DO USUÁRIO NO PERFIL - AJAX
@bp.route("/profile/photo/view", methods=["GET"])
@login_required
def profile_photo_view():
  return jsonify(
    render_template(
      "profile/_photo.html"
    )
  )
  
# VERIFICA A EXTENSÃO DA FOTO
def allowed_file(file):
  if not file or '.' not in file.filename:
    return False
    
  filename = file.filename
  file_ext = filename.rsplit('.', 1)[1].lower()
  
  return '.' in filename and file_ext in current_app.config["ALLOWED_EXTENSIONS"]
  
# SALVA FOTO DE PERFIL - AJAX
@bp.route("/profile/photo", methods=["POST"])
@login_required
def profile_photo_save():
  if "croppedImage" not in request.files or "user_id" not in request.form:
    return jsonify(status="error", message="Dados ausentes", color="danger")
    
  user_id = request.form.get("user_id")
  croppedImage = request.files.get("croppedImage")
  
  if croppedImage.filename == "" or not allowed_file(croppedImage):
    return jsonify(status="error", message="Arquivo de imagem não permitido", color="danger")
    
  if not os.path.exists(current_app.config["UPLOAD_FOLDER"]):
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    
  filename = secure_filename(croppedImage.filename)
  unique_filename = f"{uuid.uuid4().hex}.{filename.rsplit('.', 1)[1].lower()}"
  
  file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
  croppedImage.save(file_path)
  relative_path = os.path.join("images", "uploads", "profile", unique_filename)
  
  user = User.query.get(user_id)
  profile = user.profile or Profile(user=user)
  
  if user is None:
    return jsonify(status="error", message="Usuário não existe!", color="danger"), 404
    
  if user.profile.profile_image_url:
    old_image_path = os.path.join(current_app.root_path, "static", user.profile.profile_image_url)
    
    if os.path.exists(old_image_path):
      os.remove(old_image_path)
      
  user.profile.profile_image_url = relative_path
  db.session.add(profile)
  db.session.commit()
  
  return jsonify(status="success", message="Foto salva com sucesso!", color="success")

# EXCLUI FOTO DE PERFIL - AJAX
@bp.route("/profile/photo/delete", methods=["POST"])
@login_required
def profile_photo_delete():
  user_id = request.form.get("user_id")
  user = User.query.get(user_id)

  if user is None or not user.profile.profile_image_url:
    return jsonify(status="error", message="Usuário ou arquivo de imagem não existe!", color="danger")
    
  file_path = os.path.join(current_app.root_path, "static", user.profile.profile_image_url)
  
  if os.path.exists(file_path):
    os.remove(file_path)
    user.profile.profile_image_url = None
    db.session.commit()
    return jsonify(status="success", message="Foto de Perfil excluída!", color="success")
  else:
    return jsonify(status="error", message="Não foi possível excluir a foto de perfil", color="danger")
