from app.users import bp
from app.decorators import admin_required, permission_required
from app.models import Permission, User, Situation, Role
from flask import render_template, jsonify, request, current_app, url_for
from flask_login import login_required, current_user
import sqlalchemy as sa
from app import db
from datetime import datetime

############ USUÁRIO ############

# Renderiza página que carrega a lista de usuarios
@bp.route("/dashboard/users", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users():
  return render_template(
    "users/users.html",
    title="Usuários",
    use_admin_layout=True
  )
  
# Renderiza lista de usuários - AJAX
@bp.route("/dashboard/users/render", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_render():
  query = sa.select(User).order_by(User.id.desc())
  page = request.args.get("page", 1, type=int)
  users = db.paginate(query, page=page, per_page=current_app.config["PER_PAGE_USERS"], error_out=False)
  page_prev = url_for("users.dashboard_users_render", page=users.prev_num) if users.has_prev else None
  page_next = url_for("users.dashboard_users_render", page=users.next_num) if users.has_next else None
  
  return jsonify(
    render_template(
      "users/_user_list.html",
      users=users,
      page_prev=page_prev,
      page_next=page_next
    )
  )
  
# Renderiza usuários pesquidados - AJAX
@bp.route("/dashboard/users/search", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_search():
  word = request.args.get("word", "").strip()
  query = sa.select(User).filter(User.username.ilike(f'%{word}%')).limit(10)
  
  if word:
    users = db.session.scalars(query).all()
  else:
    users = []
  
  return jsonify(
    render_template(
      "users/_user_search.html",
      users=users,
      total_result=len(users)
    )
  )

# Busca situaçôes relacionadas ao usuário - AJAX
@bp.route("/dashboard/users/situations/options", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def get_situations_options():
  situations = db.session.scalars(sa.select(Situation).filter_by(entity_type="user").order_by(Situation.id.asc())).all()
  data = [{"id": situation.id, "name": situation.name} for situation in situations]
  
  return jsonify(data)
  
# Busca cargos relacionados ao usuário - AJAX
@bp.route("/dashboard/users/roles/options", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def get_roles_options():
  roles = db.session.scalars(sa.select(Role).order_by(Role.id.asc())).all()
  data = [{"id": role.id, "name": role.name} for role in roles]
  
  return jsonify(data) 

# Cria um usuário - AJAX
@bp.route("/dashboard/users/create", methods=["POST"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_create():
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
@bp.route("/dashboard/users/<int:id>/data", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_get_data(id):
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
@bp.route("/dashboard/users/<int:id>/update", methods=["POST"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_update(id):
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
@bp.route("/dashboard/users/<int:id>/view", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_view(id):
  user = db.session.get(User, id)
  
  if not user:
    return jsonify(status="error", message="Usuário nâo encontrado.", color="danger")
    
  return jsonify(
    render_template(
      "users/_user.html",
      user=user
    )
  )
  
# Exclui um usuário - AJAX
@bp.route("/dashboard/users/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_delete(id):
  user = db.session.get(User, id)
  
  if current_user.id == id:
    return jsonify(status="error", message="Você não pode excluir a si mesmo.", color="warning")
  
  if not user:
    return jsonify(status="error", message="Usuário nâo encontrado.", color="danger")
  
  db.session.delete(user)
  db.session.commit()
  return jsonify(status="success", message="Usuário excluido com sucesso.", color="success")

############ SITUAÇÃO ############

# Renderiza página que lista situaçôes de usuários
@bp.route("/dashboard/users/situations", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_situations():
  return render_template(
    "users/users_situations.html",
    title="Situaçôes de usuários",
    use_admin_layout=True
  )
  
# Renderiza lista de situaçôes relacionadas a usuario - AJAX
@bp.route("/dashboard/users/situations/render", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_situations_render():
  query = sa.select(Situation).filter_by(entity_type="user").order_by(Situation.id.desc())
  page = request.args.get("page", 1, type=int)
  situations = db.paginate(query, page=page, per_page=current_app.config["PER_PAGE_SITUATIONS_USERS"], error_out=False)
  page_prev = url_for("users.dashboard_users_situations_render", page=situations.prev_num) if situations.has_prev else None
  page_next = url_for("users.dashboard_users_situations_render", page=situations.next_num) if situations.has_next else None
  
  return jsonify(
    render_template(
      "users/_user_situations_list.html",
      situations=situations,
      page_prev=page_prev,
      page_next=page_next
    )  
  )

# Renderiza lista de situaçôes pesquisada relacionadas a usuário - AJAX
@bp.route("/dashboard/users/situations/search", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_situations_search():
  word = request.args.get("word", "").strip()
  query = sa.select(Situation).filter_by(entity_type="user").filter(Situation.name.ilike(f'%{word}%')).limit(10)
  
  if word:
    situations = db.session.scalars(query).all()
  else:
    situations = []
    
  return jsonify(
    render_template(
      "users/_user_situation_search.html",
      situations=situations,
      total_result=len(situations)
    )
  )

# Cria uma situação em uma entidade - AJAX
@bp.route("/dashboard/situations/create", methods=["POST"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_situations_create():
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
@bp.route("/dashboard/users/situations/<int:id>/view", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_situations_view(id):
  user_situation = db.session.get(Situation, id)
  
  if not user_situation:
    return jsonify(status="error", message="Situação de usuário nâo encontrada.", color="danger")
    
  return jsonify(
    render_template(
      "users/_user_situation.html",
      user_situation=user_situation
    )
  )
  
# Busca dados de uma situação - AJAX
@bp.route("/dashboard/users/situations/<int:id>/data", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_situations_get_data(id):
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
@bp.route("/dashboard/situations/<int:id>/update", methods=["POST"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_situations_update(id):
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
@bp.route("/dashboard/situations/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_situations_delete(id):
  situation = db.session.get(Situation, id)
  
  if not situation:
    return jsonify(status="error", message="Situação não encontrada!.", color="danger")

  db.session.delete(situation)
  db.session.commit()
  return jsonify(status="success", message="Situação excluida com sucesso.", color="success")


############ FUNÇÃO ############


#FUNCAO: RENDERIZA PÁGINA QUE LISTA OS PAPÈIS DE USUÁRIOS
@bp.route("/dashboard/users/roles", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_roles():
  return render_template(
    "users/users_roles.html",
    title="Pepéis de usuários",
    use_admin_layout=True
  )

# RENDERIZA UMA LISTA DE PAPÉIS DE USUARIOS - AJAX
@bp.route("/dashboard/users/roles/render", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_roles_render():
  query = sa.select(Role).order_by(Role.id.desc())
  page = request.args.get("page", 1, type=int)
  roles = db.paginate(query, page=page, per_page=current_app.config["PER_PAGE_ROLES"], error_out=False)
  page_prev = url_for("users.dashboard_users_roles_render", page=roles.prev_num) if roles.has_prev else None
  page_next = url_for("users.dashboard_users_roles_render", page=roles.next_num) if roles.has_next else None
  
  return jsonify(
    render_template(
      "users/_user_roles_list.html",
      roles=roles,
      page_prev=page_prev,
      page_next=page_next
    )
  )
  
# RENDERIZA PAPÉIS DE USUARIOS PESQUISADOS - AJAX
@bp.route("/dashboard/users/roles/search", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_roles_search():
  word = request.args.get("word", "").strip()
  query = sa.select(Role).filter(Role.name.ilike(f'%{word}%')).limit(10)
  
  if word:
    roles = db.session.scalars(query).all()
  else:
    roles = []
    
  return jsonify(
    render_template(
      "users/_user_role_search.html",
      roles=roles,
      total_result=len(roles)
    )  
  )

# Consegue situaçôes relacionadas a papel
@bp.route("/dashboard/users/roles/situations/options", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def get_roles_situations_options():
  situations = db.session.scalars(sa.select(Situation).filter_by(entity_type="role").order_by(Situation.id.asc())).all()
  data = [{"id": situation.id, "name": situation.name} for situation in situations]
  
  return jsonify(data)

# Cria uma função de usuário - AJAX
@bp.route("/dashboard/users/roles/create", methods=["POST"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_roles_create():
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
@bp.route("/dashboard/users/roles/<int:id>/view", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_roles_view(id):
  user_role = db.session.get(Role, id)
  
  if not user_role:
    return jsonify(status="error", message="Função de usuário nâo encontrada.", color="danger")
    
  return jsonify(
    render_template(
      "users/_user_role.html",
      user_role=user_role
    )
  )
  
# Busca dados de uma função - AJAX
@bp.route("/dashboard/users/roles/<int:id>/data", methods=["GET"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_roles_get_data(id):
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
@bp.route("/dashboard/users/roles/<int:id>/update", methods=["POST"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_users_roles_update(id):
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
@bp.route("/dashboard/roles/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
@permission_required(Permission.MODERATE)
def dashboard_roles_delete(id):
  role = db.session.get(Role, id)
  
  if not role:
    return jsonify(status="error", message="Cargo não encontrado!.", color="warning")

  db.session.delete(role)
  db.session.commit()
  return jsonify(status="success", message="Cargo excluido com sucesso.", color="success")