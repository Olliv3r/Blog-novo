from app.admin import bp
from flask import render_template, redirect, url_for, flash, jsonify, request, current_app
from flask_login import login_required, current_user
from app.decorators import any_permission_required, admin_required
from app.models import Permission, User, Role, Suggestion, Situation, Profile, SocialMedia
from app import db
import sqlalchemy as sa
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import os
import re

# retorna o numero de registros de uma tabela
def count_table(table):
  return db.session.scalar(
    sa.select(sa.func.count()).select_from(table)
  )
  
#### ADMIN ####

#RENDERIZA PÁGINA PADRÃO DO PAINEL
@bp.route("/admin", methods=["GET"])
@login_required
@any_permission_required(Permission.MODERATE, Permission.ADMIN)
def admin():
  models = dict(total_users=User, total_roles=Role, total_suggestions=Suggestion, total_situations=Situation)
  
  counts = {key: count_table(model) for key, model in models.items()}
  
  return render_template(
    "admin/home.html", 
    **counts,
    title="Painel Administrativo", 
    use_admin_layout=True
  )
  
#### USUARIOS ####

# Renderiza página que carrega a lista de usuarios
@bp.route("/admin/users", methods=["GET"])
@login_required
@admin_required
def admin_users():
  return render_template(
    "admin/users.html",
    title="Usuários",
    use_admin_layout=True
  )
  
# Renderiza lista de usuários - AJAX
@bp.route("/admin/users/render", methods=["GET"])
@login_required
@admin_required
def admin_users_render():
  query = sa.select(User).order_by(User.id.desc())
  page = request.args.get("page", 1, type=int)
  users = db.paginate(query, page=page, per_page=current_app.config["PER_PAGE_USERS"], error_out=False)
  page_prev = url_for("admin.admin_users_render", page=users.prev_num) if users.has_prev else None
  page_next = url_for("admin.admin_users_render", page=users.next_num) if users.has_next else None
  
  return jsonify(
    render_template(
      "admin/_user_list.html",
      users=users,
      page_prev=page_prev,
      page_next=page_next
    )
  )

# Cria um usuário - AJAX
@bp.route("/admin/users/create", methods=["POST"])
@login_required
@admin_required
def admin_users_create():
  data = {
    "username": request.form.get("username", "").strip(), 
    "email": request.form.get("email", "").strip(), 
    "password": request.form.get("password"),
    "password2": request.form.get("password2"),
    "user_situation_id": request.form.get("user_situation_id", type=int),
    "user_role_id": request.form.get("user_role_id", type=int),
    "confirmed": request.form.get("confirmed") == "on"
  }
  
  if not all([
    data["username"], 
    data["email"], 
    data["password"], 
    data["password2"],
    data["user_situation_id"],
    data["user_role_id"]
  ]):
    return jsonify(status="error", message="Preencha todos os campos obrigatórios.", color="danger")
    
  query = sa.select(User).where(sa.or_(User.username == data["username"], User.email == data["email"]))
  existing_user = db.session.scalar(query)
  
  if existing_user:
    if existing_user.username == data["username"]:
      return jsonify(status="error", message="Nome de usuário ja está em uso.", color="danger")
      
    if existing_user.email == data["email"]:
      return jsonify(status="error", message="E-mail ja está em uso.", color="danger")
      
  user_situation = db.session.get(Situation, data["user_situation_id"])
  user_role = db.session.get(Role, data["user_role_id"])
  
  if not user_situation:
    return jsonify(status="error", message="Situação inválida.", color="danger")
    
  if not user_role:
    return jsonify(status="error", message="Papel não existe!", color="danger")

  user = User()
    
  fields = {
    "username": data["username"],
    "email": data["email"], 
    "confirmed": data["confirmed"]
  }
  
  for field, value in fields.items():
    setattr(user, field, value)
  
  if data["password"] != data["password2"]:
    return jsonify(status="error", message="A senha não confere.", color="danger")
    
  user.set_password(data["password"])

  with db.session.no_autoflush:
    user.user_situation = user_situation
    user.user_role = user_role
    db.session.add(user)
  db.session.commit()
  
  return jsonify(status="success", message="Usuário criado com sucesso.", color="success")
  
# Busca dados de um usuário - AJAX
@bp.route("/admin/users/<int:id>/data", methods=["GET"])
@login_required
@admin_required
def admin_users_get_data(id):
  user = db.session.get(User, id)
  
  if not user:
    return jsonify(status="error", message="Usuário não encontrado!", color="danger")
    
  situations = db.session.scalars(
    sa.select(Situation).filter_by(entity_type="user").order_by(Situation.id.asc())
  ).all()
  roles = db.session.scalars(
    sa.select(Role).order_by(Role.id.asc())
  ).all()
  
  return jsonify({
    "user": {
      "id": user.id,
      "username": user.username,
      "email": user.email,
      "confirmed": user.confirmed,
      "is_administrator": user.is_administrator(),
      "is_moderator": user.is_moderator(),
      "user_situation_id": user.user_situation_id,
      "user_role_id": user.user_role_id
    },
    "situations": [{
      "id": s.id,
      "name": s.name
    } for s in situations],
    "roles": [{
      "id": r.id, 
      "name": r.name
    } for r in roles]
  })
  
# Atualizar dados de um usuário - AJAX
@bp.route("/admin/users/<int:id>/update", methods=["POST"])
@login_required
@admin_required
def admin_users_update(id):
  user = db.session.get(User, id)
  
  if not user:
    return jsonify(status="error", message="Usuário não encontrado", color="danger")
    
  data = {
    "username": request.form.get("username", "").strip(),
    "email": request.form.get("email", "").strip(), 
    "password": request.form.get("password"),
    "password2": request.form.get("password2"),
    "user_situation_id": request.form.get("user_situation_id", type=int),
    "user_role_id": request.form.get("user_role_id", type=int),
    "confirmed": request.form.get("confirmed") == "on"
  }
  
  if not all([
    data["username"], 
    data["email"], 
    data["password"], 
    data["password2"],
    data["user_situation_id"],
    data["user_role_id"]
  ]):
    return jsonify(status="error", message="Preencha todos os campos obrigatórios.", color="danger")
    
  existing_user = db.session.scalar(
    sa.select(User).where(sa.or_(User.username == data["username"], User.email == data["email"]), User.id != user.id)
  )
  
  if existing_user:
    if existing_user.username == data["username"]:
      return jsonify(status="error", message="Nome de usuário ja está em uso", color="danger")
      
    if existing_user.email == data["email"]:
      return jsonify(status="error", message="Email ja está em uso", color="danger")
      
  user_situation = db.session.get(Situation, data["user_situation_id"])
  user_role = db.session.get(Role, data["user_role_id"])
  
  if not user_situation:
    return jsonify(status="error", message="Situação não existe!", color="danger")
    
  if not user_role:
    return jsonify(status="error", message="Papel não existe!", color="danger")

  # Impede o admin de sabotar o sistema
  if user.id == current_user.id and (current_user.is_administrator() or current_user.is_moderator()):
    if user.user_role_id != data["user_role_id"]:
      return jsonify(status="error", message="Você nâo pode alterar seu próprio papel", color="warning")
    if user.user_situation_id != data["user_situation_id"]:
      return jsonify(status="error", message="Você nâo pode alterar sua própria situação", color="warning")
      
  fields = {
    "username": data["username"],
    "email": data["email"],
    "confirmed": data["confirmed"],
    "modified": datetime.utcnow()
  }
  
  for field, value in fields.items():
    setattr(user, field, value)
    
  if data["password"] != data["password2"]:
    return jsonify(status="error", message="A senha não confere.", color="danger")
  
  user.set_password(data["password"])
  
  with db.session.no_autoflush:
    user.user_situation = user_situation
    user.user_role = user_role
  db.session.commit()

  return jsonify(status="success", message="Usuário atualizado com sucesso.", color="success")
 
# Visualiza dados de um usuário - AJAX
@bp.route("/admin/users/<int:id>/view", methods=["GET"])
@login_required
@admin_required
def admin_users_view(id):
  user = db.session.get(User, id)
  
  if not user:
    return jsonify(status="error", message="Usuário nâo encontrado.", color="danger")
    
  return jsonify(
    render_template(
      "admin/_user.html",
      user=user
    )
  )
  
# Exclui um usuário - AJAX
@bp.route("/admin/users/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_users_delete(id):
  user = db.session.get(User, id)
  
  if current_user.id == id:
    return jsonify(status="error", message="Você não pode excluir a si mesmo.", color="warning")
  
  if not user:
    return jsonify(status="error", message="Usuário nâo encontrado.", color="danger")
  
  db.session.delete(user)
  db.session.commit()
  return jsonify(status="success", message="Usuário excluido com sucesso.", color="success")
  
# Renderiza usuários pesquisados
@bp.route("/admin/users/search", methods = ["GET"])
@login_required
@admin_required
def admin_users_search():
  search = request.args.get("q", "").strip()
  
  query = db.session.query(User)
  query = query.join(User.user_situation)
  query = query.join(User.user_role)
  query = query.join(User.profile)
  
  if search:
    if search.isdigit():
      query = query.filter(User.id == int(search))
    
    else:
      search_term = f"%{search}%"
      query = query.filter(
        sa.or_(
          Profile.name.ilike(search_term),
          User.username.ilike(search_term),
          User.email.ilike(search_term),
          Situation.name.ilike(search_term),
          Role.name.ilike(search_term),
        )
      )
  
  users = query.distinct().all()
  
  return jsonify(
    render_template(
      "admin/_user_search_list.html", 
      users=users
    )
  )

############ SITUAÇÃO ############

# Busca situaçôes relacionadas ao usuário - AJAX
@bp.route("/admin/users/situations/options", methods=["GET"])
@login_required
@admin_required
def get_situations_options():
  situations = db.session.scalars(sa.select(Situation).filter_by(entity_type="user").order_by(Situation.id.asc())).all()
  data = [{"id": situation.id, "name": situation.name} for situation in situations]
  
  return jsonify(data)

# Renderiza página que lista situaçôes de usuários
@bp.route("/admin/users/situations", methods=["GET"])
@login_required
@admin_required
def admin_users_situations():
  return render_template(
    "admin/users_situations.html",
    title="Situaçôes de usuários",
    use_admin_layout=True
  )
  
# Renderiza lista de situaçôes relacionadas a usuario - AJAX
@bp.route("/admin/users/situations/render", methods=["GET"])
@login_required
@admin_required
def admin_users_situations_render():
  query = sa.select(Situation).filter_by(entity_type="user").order_by(Situation.id.desc())
  page = request.args.get("page", 1, type=int)
  situations = db.paginate(query, page=page, per_page=current_app.config["PER_PAGE_SITUATIONS_USERS"], error_out=False)
  page_prev = url_for("admin.admin_users_situations_render", page=situations.prev_num) if situations.has_prev else None
  page_next = url_for("admin.admin_users_situations_render", page=situations.next_num) if situations.has_next else None
  
  return jsonify(
    render_template(
      "admin/_user_situations_list.html",
      situations=situations,
      page_prev=page_prev,
      page_next=page_next
    )  
  )

# Cria uma situação em uma entidade - AJAX
@bp.route("/admin/situations/create", methods=["POST"])
@login_required
@admin_required
def admin_situations_create():
  data = {
    "name": request.form.get("name", "").strip(),
    "description": request.form.get("description", "").strip()
  }
  
  if not all(data):
    return jsonify(status="error", message="Preencha todos os campos!", color="warning")
  
  situation = Situation(
    name=data["name"], 
    description=data["description"], 
    entity_type="user")
  db.session.add(situation)
  db.session.commit()
  return jsonify(status="success", message="Situação criada com sucesso.", color="success")
  
# Visualiza dados de uma situação - AJAX
@bp.route("/admin/users/situations/<int:id>/view", methods=["GET"])
@login_required
@admin_required
def admin_users_situations_view(id):
  user_situation = db.session.get(Situation, id)
  
  if not user_situation:
    return jsonify(status="error", message="Situação de usuário nâo encontrada.", color="danger")
    
  return jsonify(
    render_template(
      "admin/_user_situation.html",
      user_situation=user_situation
    )
  )
  
# Busca dados de uma situação - AJAX
@bp.route("/admin/users/situations/<int:id>/data", methods=["GET"])
@login_required
@admin_required
def admin_users_situations_get_data(id):
  situation = db.session.scalar(
    sa.select(Situation).where(Situation.id == id).order_by(Situation.id.asc())
  )
  
  if not situation:
    return jsonify(status="error", message="Situação não existe!", color="danger")
  
  return jsonify({
    "situation": {
      "id": situation.id,
      "name": situation.name,
      "description": situation.description,
      "entity_type": situation.entity_type
    }
  })
  
# Edita uma situação da entidade user - AJAX
@bp.route("/admin/situations/<int:id>/update", methods=["POST"])
@login_required
@admin_required
def admin_situations_update(id):
  data = {
    "name": request.form.get("name", "").strip(),
    "description": request.form.get("description", "").strip()
  }
  
  if not all(data):
    return jsonify(status="error", message="Preencha todos os campos!", color="warning")
    return jsonify(status="error", message="Preencha todos os campos!", color="warning")
    
  situation = db.session.get(Situation, id)
  
  if not situation:
    return jsonify(status="error", message="Situação não encontrada!", color="danger")
    
  situation.name = data["name"]
  situation.description = data["description"]
  situation.entity_type = "user"
  db.session.commit()
  return jsonify(status="success", message="Situação atualizada com sucesso.", color="success")
  
# Excluir uma situação - AJAX
@bp.route("/admin/situations/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_situations_delete(id):
  situation = db.session.get(Situation, id)
  
  if not situation:
    return jsonify(status="error", message="Situação não encontrada!.", color="danger")

  db.session.delete(situation)
  db.session.commit()
  return jsonify(status="success", message="Situação excluida com sucesso.", color="success")
  
# Renderiza situaçôes pesquisadas
@bp.route("/admin/users/situations/search", methods = ["GET"])
@login_required
@admin_required
def admin_users_situations_search():
  search = request.args.get("q", "").strip()
  
  query = db.session.query(Situation).filter_by(entity_type="user")
  
  if search:
    if search.isdigit():
      query = query.filter(Situation.id == int(search))
    
    else:
      search_term = f"%{search}%"
      query = query.filter(
        sa.or_(
          Situation.name.ilike(search_term),
          Situation.description.ilike(search_term),
          Situation.entity_type.ilike(search_term)
        )
      )
  
  situations = query.distinct().all()
  
  return jsonify(
    render_template(
      "admin/_user_situation_search_list.html", 
      situations=situations
    )
  )

############ FUNÇÃO ############

# Renderiza página que carrega a lista de Cargos de usuarios
@bp.route("/admin/users/roles", methods=["GET"])
@login_required
@admin_required
def admin_users_roles():
  return render_template(
    "admin/users_roles.html",
    title="Pepéis de usuários",
    use_admin_layout=True
  )

# RENDERIZA UMA LISTA DE PAPÉIS DE USUARIOS - AJAX
@bp.route("/admin/users/roles/render", methods=["GET"])
@login_required
@admin_required
def admin_users_roles_render():
  query = sa.select(Role).order_by(Role.id.desc())
  page = request.args.get("page", 1, type=int)
  roles = db.paginate(query, page=page, per_page=current_app.config["PER_PAGE_ROLES"], error_out=False)
  page_prev = url_for("admin.admin_users_roles_render", page=roles.prev_num) if roles.has_prev else None
  page_next = url_for("admin.admin_users_roles_render", page=roles.next_num) if roles.has_next else None
  
  return jsonify(
    render_template(
      "admin/_user_role_list.html",
      roles=roles,
      page_prev=page_prev,
      page_next=page_next
    )
  )
  
# Busca cargos relacionados ao usuário - AJAX
@bp.route("/admin/users/roles/options", methods=["GET"])
@login_required
@admin_required
def get_roles_options():
  roles = db.session.scalars(sa.select(Role).order_by(Role.id.asc())).all()
  data = [{"id": role.id, "name": role.name} for role in roles]
  
  return jsonify(data) 

# Consegue situaçôes relacionadas a papel
@bp.route("/admin/users/roles/situations/options", methods=["GET"])
@login_required
@admin_required
def get_roles_situations_options():
  situations = db.session.scalars(sa.select(Situation).filter_by(entity_type="role").order_by(Situation.id.asc())).all()
  data = [{"id": situation.id, "name": situation.name} for situation in situations]
  
  return jsonify(data)

# Cria uma função de usuário - AJAX
@bp.route("/admin/users/roles/create", methods=["POST"])
@login_required
@admin_required
def admin_users_roles_create():
  data = {
    "name": request.form.get("name", "").strip(), 
    "description": request.form.get("description", "").strip(), 
    "role_situation_id": request.form.get("role_situation_id", type=int)
  }
  
  if not all([
    data["name"], 
    data["description"], 
    data["role_situation_id"]
  ]):
    return jsonify(status="error", message="Preencha todos os campos obrigatórios.", color="danger")
    
  role_existing = db.session.scalar(
    sa.select(Role).where(Role.name == data["name"])
  )
  
  if role_existing:
    return jsonify(status="error", message="Já existe um cargo com esse nome!", color="warning")
  
  # Garante que a situação pertence ao tipo 'role'
  role_situation = db.session.scalar(
    sa.select(Situation).filter_by(id=data["role_situation_id"], entity_type="role")
  )
  
  if not role_situation:
    return jsonify(status="error", message="Situação inválida.", color="danger")
  
  role = Role()
    
  fields = {
    "name": data["name"],
    "description": data["description"]
  }
  
  for field, value in fields.items():
    setattr(role, field, value)

  with db.session.no_autoflush:
    role.role_situation = role_situation
    db.session.add(role)
  db.session.commit()
  
  return jsonify(status="success", message="Papel de usuário criado com sucesso.", color="success")
  
# Visualiza dados de uma função - AJAX
@bp.route("/admin/users/roles/<int:id>/view", methods=["GET"])
@login_required
@admin_required
def admin_users_roles_view(id):
  user_role = db.session.get(Role, id)
  
  if not user_role:
    return jsonify(status="error", message="Função de usuário nâo encontrada.", color="danger")
    
  return jsonify(
    render_template(
      "admin/_user_role.html",
      user_role=user_role
    )
  )
  
# Busca dados de uma função - AJAX
@bp.route("/admin/users/roles/<int:id>/data", methods=["GET"])
@login_required
@admin_required
def admin_users_roles_get_data(id):
  role = db.session.scalar(
    sa.select(Role).where(Role.id == id)
  )
  
  role_situations = db.session.scalars(
    sa.select(Situation).filter_by(entity_type="role").order_by(Situation.id.asc())
  ).all()
  
  if not role_situations:
    return jsonify(status="error", message="Situaçôes das funçôes de usuário não existe!", color="danger")
  
  return jsonify({
    "role": {
      "id": role.id,
      "name": role.name,
      "description": role.description,
      "role_situation_id": role.role_situation_id
    },
    "role_situations": [
      {
        "id": situation.id,
        "name": situation.name,
      } for situation in role_situations
    ]
  })
  
# Atualizar dados de um cargo - AJAX
@bp.route("/admin/users/roles/<int:id>/update", methods=["POST"])
@login_required
@admin_required
def admin_users_roles_update(id):
  role = db.session.get(Role, id)
  
  if not role:
    return jsonify(status="error", message="Cargo não encontrado!", color="danger")
    
  data = {
    "name": request.form.get("name", "").strip(),
    "description": request.form.get("description", "").strip(), 
    "role_situation_id": request.form.get("role_situation_id", type=int)
  }
  
  if not all([
    data["name"], 
    data["description"], 
    data["role_situation_id"]
  ]):
    return jsonify(status="error", message="Preencha todos os campos obrigatórios!", color="warning")
    
  existing_role = db.session.scalar(
    sa.select(Role).filter_by(name=data["name"])
  )
  
  if existing_role and existing_role.id != role.id:
    return jsonify(status="error", message="Ja existe um cargo com esse nome!", color="warning")
    
  role_situation = db.session.get(Situation, data["role_situation_id"])
  
  if not role_situation:
    return jsonify(status="error", message="Situação de cargo não existe!", color="warning")
    
  fields = {
    "name": data["name"],
    "description": data["description"],
    "modified": datetime.utcnow()
  }
  
  for field, value in fields.items():
    setattr(role, field, value)

  with db.session.no_autoflush:
    role.role_situation = role_situation
  db.session.commit()

  return jsonify(status="success", message="Função atualizada com sucesso.", color="success")
  
# Excluir um cargo - AJAX
@bp.route("/admin/roles/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_roles_delete(id):
  role = db.session.get(Role, id)
  
  if not role:
    return jsonify(status="error", message="Cargo não encontrado!.", color="warning")

  db.session.delete(role)
  db.session.commit()
  return jsonify(status="success", message="Cargo excluido com sucesso.", color="success")

# Renderiza cargos pesquisados
@bp.route("/admin/users/roles/search", methods = ["GET"])
@login_required
@admin_required
def admin_users_roles_search():
  search = request.args.get("q", "").strip()
  
  query = db.session.query(Role)
  
  if search:
    if search.isdigit():
      query = query.filter(Role.id == int(search))
    
    else:
      search_term = f"%{search}%"
      query = query.filter(
        sa.or_(
          Role.name.ilike(search_term),
          Role.description.ilike(search_term)
        )
      )
  
  roles = query.distinct().all()
  
  return jsonify(
    render_template(
      "admin/_user_role_search_list.html", 
      roles=roles
    )
  )
  
#### PERFIS ####

# Renderiza página que carrega a lista de usuarios
@bp.route("/admin/profiles", methods=["GET"])
@login_required
@admin_required
def admin_profiles():
  return render_template(
    "admin/profiles.html",
    title="Perfis",
    use_admin_layout=True
  )
  
# Renderiza cards de perfis - AJAX
@bp.route("/admin/profiles/render", methods=["GET"])
@login_required
@admin_required
def admin_profiles_render():
  query = sa.select(Profile).order_by(Profile.id.desc())
  page = request.args.get("page", 1, type=int)
  profiles = db.paginate(query, page=page, per_page=current_app.config["PER_PAGE_PROFILES"], error_out=False)
  page_prev = url_for("admin.admin_profiles_render", page=profiles.prev_num) if profiles.has_prev else None
  page_next = url_for("admin.admin_profiles_render", page=profiles.next_num) if profiles.has_next else None
  
  return jsonify(
    render_template(
      "admin/_profile_card.html",
      profiles=profiles,
      page_prev=page_prev,
      page_next=page_next
    )
  )
  
def get_profile_image_url(profile, user, size=128):
  """
  Retorna a URL completa da imagem do perfil, tratando todos os cenários:
  1. Se image_url for None → avatar padrão
  2. Se image_url for URL absoluta (http/https) → usa diretamente
  3. Se image_url for caminho relativo → converte com url_for
  4. Se image_url já contiver 'static/' → remove e usa url_for
  """
  if not profile or not profile.image_url:
    return user.avatar(size) if user else None
  
  image_url = profile.image_url.strip()
  
  # Caso 1: URL absoluta (http://, https://)
  if image_url.startswith(('http://', 'https://')):
    return image_url
  
  # Caso 2: Se já começar com static/, remove para evitar duplicação
  if image_url.startswith('static/'):
    image_url = image_url[7:]  # Remove "static/" do início
  
  # Caso 3: Caminho relativo - usa url_for para gerar URL completa
  try:
    return url_for('static', filename=image_url, _external=True)
  except:
    # Fallback em caso de erro no url_for
    return f"/static/{image_url}"
  
# Busca dados de um perfil - AJAX
@bp.route("/admin/users/profiles/<int:profile_id>/data", methods=["GET"])
@login_required
@admin_required
def admin_users_profiles_get_data(profile_id):
  profile = db.session.scalar(
    sa.select(Profile).where(Profile.id == profile_id)
  )
  
  user = profile.user

  if not profile:
    return jsonify(status="error", message="Perfil não existe!", color="danger")
    
  image_url = get_profile_image_url(profile, user)
  
  return jsonify({
    "user": {
      "id": user.id,
      "username": user.username,
      "email": user.email,
      "avatar": user.avatar(128)
    },
    "profile": {
      "id": user.profile.id,
      "name": user.profile.name,
      "occupation": user.profile.occupation,
      "location": user.profile.location,
      "website": user.profile.website,
      "about_me": user.profile.about_me,
      "image_url": image_url
    }
  })


#### EMAIL ####

#### Foto de perfil ####

# Função auxiliar para remover imagem antiga
def _remove_old_image(image_url):
  """Remove imagem anterior se for um arquivo local"""
  if image_url and not image_url.startswith(('http://', 'https://')):
    try:
      old_image_path = os.path.join(current_app.root_path, "static", image_url)
      
      if os.path.exists(old_image_path):
        os.remove(old_image_path)
        
    except OSError:
      pass
  
# Função de validação de arquivo (mantida da versão original)
def allowed_file(file):
  if not file or '.' not in file.filename:
    return False
      
  filename = file.filename
  file_ext = filename.rsplit('.', 1)[1].lower()
  
  allowed_extensions = current_app.config.get("ALLOWED_EXTENSIONS", {'png', 'jpg', 'jpeg', 'gif'})
  return file_ext in allowed_extensions

def is_gravatar_url(url):
  if not url:
    return False
  return ('gravatar.com') in url or 'avatar/' in url or bool(re.match(r'[0-9a-f]{32}', url))

# SALVA FOTO DE PERFIL - AJAX (Versão Corrigida)
@bp.route("/admin/users/profiles/update-photo", methods=["POST"])
@login_required
@admin_required
def admin_users_profile_update_photo():
  # Verificação dos dados de entrada
  if "image_upload" not in request.files or "image_url" not in request.form:
    return jsonify(
      status="error", 
      message="Dados ausentes", 
      color="danger")
    
  # Dados de entrada
  profile_id = request.form.get("profile_id")
  image_upload = request.files.get("image_upload")
  image_url = request.form.get("image_url")
  
  # Validação do perfil
  profile = db.session.get(Profile, profile_id)
  
  if profile is None:
    return jsonify(
      status="error", 
      message="Perfil não encontrado.", 
      color="danger"), 404
    
  user = profile.user
  
  has_upload = image_upload and image_upload.filename != ''
  has_url = image_url and image_url.strip() != ''
  
  # Se ambos URL e upload foram enviados
  if has_upload and has_url:
    if is_gravatar_url(image_url):
      image_url = None
    else:
      return jsonify(
        status="error", 
        message="Envie apenas uma URL ou um arquivo de upload. Não ambos.", 
        color="danger")
  
  # OPÇÃO 1: Upload por URL (nova funcionalidade)
  if image_url:
    if not image_url.startswith(('http://', 'https://')):
      return jsonify(
        status="error", 
        message="URL deve começar com http:// ou https://", 
        color="danger"), 404
        
    # Remove imagem anterior se existir (apenas arquivos locais)
    _remove_old_image(profile.image_url)
    
    # Atualiza com a URL
    profile.image_url = image_url
    db.session.commit()
    
    return jsonify(
      status="success", 
      message="URL da imagem salva com sucesso!", 
      color="success",
      new_image_url=image_url
    )
  
  # OPÇÃO 2: Upload por arquivo (versão original melhorada)
  if not image_upload or image_upload.filename == '.':
    return jsonify(
      status="error", 
      message="Nenhum arquivo selecionado.", 
      color="danger"
    ), 400
    
  # Validação do tipo de arquivo
  if not allowed_file(image_upload):
    allowed_extensions = ', '.join(current_app.config["ALLOWED_EXTENSIONS"], [])
    
    return jsonify(
      status="error", 
      message=f"Tipo de arquivo não permitido. Use: {allowed_extensions}", 
      color="danger"
    ), 400
    
  # Verificação do tamanho do arquivo
  if hasattr(current_app.config, 'MAX_CONTENT_LENGTH'):
    if request.content_length > current_app.config["MAX_CONTENT_LENGTH"]:
      return jsonify(
        status="error", 
        message="Arquivo muito grande.", 
        color="danger"
      ), 400
      
  # Verifica e cria o diretório
  upload_folder = current_app.config["UPLOAD_FOLDER"]
  
  if not os.path.exists(upload_folder):
    os.makedirs(upload_folder, exist_ok=True)

  # Gera nome seguro para o arquivo
  filename = secure_filename(image_upload.filename)
  unique_filename = f"{uuid.uuid4().hex}.{filename.rsplit('.', 1)[1].lower()}"
  
  # Caminho completo do arquivo
  file_path = os.path.join(upload_folder, unique_filename)

  # Salvar imagem no Caminho do arquivo
  image_upload.save(file_path)
  
  # Verifica se a imagem não foi salva
  if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
    return jsonify(
      status="error", 
      message="Falha ao salvar o arquivo.", 
      color="danger"
    ), 400

  # Caminho relativo para guardar na base
  relative_path = os.path.join("images", "uploads", "profiles", unique_filename)
  
  # Remove a imagem anterior se existir
  _remove_old_image(profile.image_url)
  
  # Atualizar a url da imagem do perfil
  profile.image_url = relative_path
  db.session.commit()
  
  # URL completa para retorno no frontend
  new_image_url = url_for('static', filename=relative_path, _external=True)
  image_url = get_profile_image_url(profile, user)
  
  return jsonify(
    new_image_url=new_image_url,
    image_url=image_url,
    status="success", 
    message="Foto salva com sucesso!", 
    color="success")

# EXCLUI FOTO DE PERFIL - AJAX (Diretório corrigido)
@bp.route("/admin/users/profiles/delete-photo", methods=["POST"])
@login_required
@admin_required
def delete_profile_photo():
  profile_id = request.form.get("profile_id")
  profile = Profile.query.get_or_404(profile_id)
  
  if not profile.image_url:
    return jsonify(
      status="error", 
      message="Perfil não possui foto para excluir!", 
      color="danger"
    )
  
  # Remove arquivo físico apenas se for arquivo local
  if not profile.image_url.startswith(('http://', 'https://')):
    # CAMINHO CORRETO: static/ + caminho_relativo
    file_path = os.path.join(current_app.root_path, "static", profile.image_url)
    
    if os.path.exists(file_path):
      os.remove(file_path)
      
    else:
      return jsonify(
        status="error", 
        message="Arquivo de imagem não encontrado!", 
        color="danger"
      )
  
  # Remove a referência no banco
  profile.image_url = None
  db.session.commit()
  
  return jsonify(
    status="success", 
    message="Foto de perfil excluída!", 
    color="success",
    new_image_url=profile.user.avatar(150)
  )

#### Redes Sociais ####
  
# Renderiza lista de redes sociais - AJAX
@bp.route("/admin/users/profiles/<int:profile_id>/social-medias/render", methods=["GET"])
@login_required
@admin_required
def admin_users_profiles_social_medias_render(profile_id):
  query = sa.select(SocialMedia).where(SocialMedia.profile_id == profile_id).order_by(SocialMedia.id.desc())
  page = request.args.get("page", 1, type=int)
  social_medias = db.paginate(query, page=page, per_page=current_app.config["PER_PAGE_USERS"], error_out=False)
  page_prev = url_for("admin.admin_users_profiles_social_medias_render", page=social_medias.prev_num) if social_medias.has_prev else None
  page_next = url_for("admin.admin_users_profiles_social_medias_render", page=social_medias.next_num) if social_medias.has_next else None
  
  return jsonify(
    render_template(
      "admin/_social_media_list.html",
      social_medias=social_medias,
      page_prev=page_prev,
      page_next=page_next
    )
  )

# Busca dados de uma rede social - AJAX
@bp.route("/admin/users/profiles/social-media/<int:sm_id>/data", methods=["GET"])
@login_required
@admin_required
def admin_users_profiles_social_media_get_data(sm_id):
  sm = db.session.get(SocialMedia, int(sm_id))
  
  return jsonify({
    "social_media": {
      "id": sm.id,
      "name": sm.name,
      "icon": sm.icon,
      "url": sm.url,
      "order_index": sm.order_index
    }
  })