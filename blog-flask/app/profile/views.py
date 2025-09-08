from app.profile import bp
from flask_login import login_required, current_user
from flask import render_template, jsonify, request, current_app, session
from app.models import Profile, User, SocialMedia, Situation
import sqlalchemy as sa
from app import db
from datetime import datetime, timedelta
import uuid
from werkzeug.utils import secure_filename
import os

#### PERFIL ####

# Renderiza página de perfil do usuário
@bp.route("/profile", methods=["GET",])
@login_required
def profile():
  return render_template(
    "profile/profile.html",
    title="Perfil do Usuário"
  )
  
#### DADOS PESSOAIS ####

# Renderiza página de dados pessoais no perfil - AJAX
@bp.route("/profile/info", methods=["GET"])
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
  
@bp.route("/profile/<username>", methods=["GET"])
def profile_user(username):
  user = db.session.scalar(
    sa.select(User).filter_by(username=username)
  )
  return render_template(
    "profile/public_profile.html",
    user=user,
    title="Perfil público"
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
  inputs = ["name", "location", "website", "occupation", "about_me"]
  
  for _input in inputs:
    setattr(profile, _input, request.form.get(_input))
    
  profile.modified = datetime.utcnow()
  
  db.session.add(profile)
  db.session.commit()
  
  return jsonify(status="success", message="Dados pessoais atualizados!", color="success")
  
#### REDES SOCIAIS ####

# Renderiza página de redes sociais no perfil - AJAX
@bp.route("/profile/social-media", methods=["GET",])
@login_required
def profile_social_media():
  return jsonify(
    render_template(
      "profile/_social_media.html"
    )
  )
  
# RENDERIZA REDES SOCIAIS
@bp.route("/profile/social-media/render", methods=["GET"])
@login_required
def profile_social_media_render():
  profile_id = current_user.profile.id
  query = sa.select(SocialMedia).join(Situation).where(
    SocialMedia.profile_id == profile_id,
    Situation.name == "Ativo",
    Situation.entity_type == "social_media"
  ).order_by(SocialMedia.order_index)
  
  social_medias = db.session.scalars(query).all()
  
  return jsonify(
    render_template(
      'profile/_social_media_list.html',
      social_medias=social_medias
    )
  )
  
@bp.route("/profile/social-media/create", methods=["GET", "POST"])
@login_required
def profile_social_media_create():
  profile_id = current_user.profile.id

  current_count = db.session.scalar(
    sa.select(sa.func.count(SocialMedia.id).filter(SocialMedia.profile_id == profile_id)
    )
  )
  
  if current_count >= 5:
    return jsonify(message="Você pode adicionar no máximo 5 redes sociais", color="danger", status="error")
    
  user = db.session.get(User, profile_id)
  
  if user is None:
    return jsonify(message="Usuário não encontrado!", color="danger", status="error")

  sm_existing = db.session.scalar(
    sa.select(SocialMedia).filter_by(url=request.form.get("url"))
  )
  
  if sm_existing is not None:
    return jsonify(message="Ja existe uma rede social com essa URL", color="danger", status="error")
    
  sm = SocialMedia(
    name=request.form["name"], 
    url=request.form["url"], 
    icon=request.form["icon"]
  )
  
  user.profile.social_media.append(sm)
  db.session.commit()
  
  return jsonify(message="Nova rede social adicionada!", color="success", status="success")

# Edita um sm
@bp.route("/profile/social-media/<sm_id>/update", methods=["GET", "POST"])
@login_required
def profile_social_media_update(sm_id):
  sm = db.session.get(SocialMedia, sm_id)
  
  if sm is None:
    return jsonify(message="Rede social não encontrada!", color="danger", status="success")

  fields = {
    "name": request.form.get('name'),
    "url": request.form.get('url'),
    "icon": request.form.get('icon')
  }
  
  for field, value in fields.items():
    setattr(sm, field, value)
  
  sm.modified = datetime.utcnow()
  db.session.commit()
  return jsonify(message="Rede social atualizada com sucesso!", color="success", status="success")

# Apagar rede social
@bp.route("/profile/social-media/<sm_id>/delete", methods=["GET", "POST"])
@login_required
def profile_social_media_delete(sm_id):
  sm = db.session.get(SocialMedia, sm_id)

  if sm is None:
    return jsonify(message="Rede social não encontrada!", color="danger", status="error")

  db.session.delete(sm)
  db.session.commit()
  return jsonify(message="Rede social excluída com sucesso", color="success", status="success")

# Alterar o status da rede social
@bp.route("/profile/social-media/status/<int:sm_id>/update", methods=["GET", "POST"])
def profile_social_media_status_update(sm_id):
  sm = db.session.get(SocialMedia, sm_id)

  if not sm or sm.profile_id != current_user.profile.id:
    return jsonify(message="Rede social não enontrada!", color="danger", status="error")
  
  # Rate limiting simples
  now = datetime.utcnow()
  if sm.modified and now - sm.modified < timedelta(seconds=1):
    return jsonify(message="Muitas requisições, tente novamente em breve!", color="danger", status="error")
  
  visible = request.form.get("sit_sm")
  if visible is None:
    return jsonify(message="Campo 'visible' é obrigatório!", color="danger", status="error")
  
  sm.is_active = request.form.get("sit_sm") == "true"
  sm.modified = now
  db.session.commit()
  return jsonify(message="Status da rede social atualizada com sucesso!", color="success", status="success")

# Atualiza ordem das redes sociais
@bp.route("/profile/social-media/order/update", methods=["GET", "POST"])
@login_required
def profile_social_media_order_update():
  last_update = session.get('last_update_sm')
  now = datetime.utcnow()
  
  if last_update:
    last_update = datetime.fromisoformat(last_update)
    
    if now - last_update < timedelta(seconds=2):
      return jsonify(message="Você está atualizando muito rápido, tenha paciência :)!", color="danger", status="error")

  data = request.get_json()
  new_order = data.get("order")
  
  for item in new_order:
    sm_id = item["id"]
    order_index = item["order"]
    
    sm_item = db.session.get(SocialMedia, sm_id)
    
    if sm_item:
      sm_item.order_index = order_index
  
  db.session.commit()
  session["last_update_sm"] = now.isoformat()
  
  return jsonify(message="Ordem atualizada com sucesso!", color="success", status="success")

#### FOTO DE PERFIL ####

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
    
  if user.profile.image_url:
    old_image_path = os.path.join(current_app.root_path, "static", user.profile.image_url)
    
    if os.path.exists(old_image_path):
      os.remove(old_image_path)
      
  user.profile.image_url = relative_path
  db.session.add(profile)
  db.session.commit()
  
  return jsonify(status="success", message="Foto salva com sucesso!", color="success")

# EXCLUI FOTO DE PERFIL - AJAX
@bp.route("/profile/photo/delete", methods=["POST"])
@login_required
def profile_photo_delete():
  user_id = request.form.get("user_id")
  user = User.query.get(user_id)

  if user is None or not user.profile.image_url:
    return jsonify(status="error", message="Usuário ou arquivo de imagem não existe!", color="danger")
    
  file_path = os.path.join(current_app.root_path, "static", user.profile.image_url)
  
  if os.path.exists(file_path):
    os.remove(file_path)
    user.profile.image_url = None
    db.session.commit()
    return jsonify(status="success", message="Foto de Perfil excluída!", color="success")
  else:
    return jsonify(status="error", message="Não foi possível excluir a foto de perfil", color="danger")