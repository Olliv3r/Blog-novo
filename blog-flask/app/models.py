from app import db, login
from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app
from app.default_dict import situations
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from time import time
from hashlib import md5

# Cadastra Situaçôes padrôes
def populates_default_situations():
  for situation in situations:
    existing_situation = Situation.query.filter_by(name=situation["name"], entity_type=situation["entity_type"]).first()
    
    default_situation_role = "Ativo"
    default_situation_user = "Aguardando"
    default_situation_suggestion = "Aguardando"
    default_situation_sm = "Aguardando"
    
    if existing_situation is None:
      new_situation = Situation(name=situation["name"], description=situation["description"], entity_type=situation["entity_type"], default = False)
      
      if situation["entity_type"] == "role":
        new_situation.default = (situation["name"] == default_situation_role)
      
      elif situation["entity_type"] == "user":
        new_situation.default = (situation["name"] == default_situation_user)
        
      elif situation["entity_type"] == "suggestion":
        new_situation.default = (situation["name"] == default_situation_suggestion)
        
      elif situation["entity_type"] == "social_media":
        new_situation.default = (situation["name"] == default_situation_sm)
  
      db.session.add(new_situation)
  db.session.commit()

class Permission:
  WRITE = 4
  MODERATE = 8
  ADMIN = 16
  
class Situation(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True, index=True)
  name: so.Mapped[str] = so.mapped_column(sa.String(60))
  description: so.Mapped[str] = so.mapped_column(sa.String(500))
  entity_type: so.Mapped[str] = so.mapped_column(sa.String(100))
  default: so.Mapped[Optional[bool]] = so.mapped_column(default=False, index=True)
  
  # Relacionamento Principal: Situation relacionado ao Role
  roles: so.WriteOnlyMapped["Role"] = so.relationship(
    back_populates="role_situation",
    passive_deletes=True
  )
  # Relacionamento Principal: Situation relacionado ao User
  users: so.WriteOnlyMapped["User"] = so.relationship(
    back_populates="user_situation",
    passive_deletes=True
  )
  
  # Relacionamento Principal: Situation relacionado ao Comment
  suggestions: so.WriteOnlyMapped["Suggestion"] = so.relationship(
    back_populates="suggestion_situation",
    passive_deletes=True
  )
  
  # Relacionamento principal: SocialMedia relacionado ao Situation
  social_media: so.WriteOnlyMapped["SocialMedia"] = so.relationship(
    back_populates = "social_media_situation", 
    passive_deletes = True
  )
    
  created: so.Mapped[datetime] = so.mapped_column(default=datetime.utcnow)
  modified: so.Mapped[Optional[datetime]] = so.mapped_column(default=datetime.utcnow)
  
  @property
  def user_count(self):
    query = sa.select(sa.func.count(User.id)).where(User.user_situation_id == self.id)
    return db.session.scalar(query)
  
class Role(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True, index=True)
  name: so.Mapped[str] = so.mapped_column(sa.String(60), unique=True)
  description: so.Mapped[Optional[str]] = so.mapped_column(sa.String(500))
  default: so.Mapped[bool] = so.mapped_column(default=False, index=True)
  permissions: so.Mapped[int] = so.mapped_column()
  
  # Relacionamento Inverso: Role associado ao Situation
  role_situation: so.Mapped[Situation] = so.relationship(
    back_populates="roles"
  )
  role_situation_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Situation.id, ondelete="CASCADE"))
  
  # Relacionamento Principal: Role Relacionado ao User
  users: so.WriteOnlyMapped["User"] = so.relationship(
    back_populates="user_role",
    passive_deletes=True
  )
  
  created: so.Mapped[datetime] = so.mapped_column(default=datetime.utcnow)
  modified: so.Mapped[Optional[datetime]] = so.mapped_column(default=datetime.utcnow)
  
  def __init__(self, *args, **kwargs):
    super(Role, self).__init__(*args, **kwargs)
    
    if self.permissions is None:
      self.permissions = 0
      
    if self.role_situation is None:
      role_situation = db.session.scalar(sa.select(Situation).filter_by(default=True, entity_type="role"))
      self.role_situation = role_situation
  
  @staticmethod
  def insert_roles():
    roles = {
      "User": {
        "permissions": [Permission.WRITE],
        "description": "Usuário padrão com acesso limitado"
      },
      "Moderator": {
        "permissions": [Permission.WRITE, Permission.MODERATE],
        "description": "Pode moderar o conteúdo e gerenciar usuários"
      },
      "Administrator": {
        "permissions": [Permission.WRITE, Permission.MODERATE, Permission.ADMIN],
        "description": "Acesso total ao sistema"
      }
    }
  
    default_role = "User"
    
    for role_name, role_info in roles.items():
      role = db.session.scalar(
        sa.select(Role).filter_by(name=role_name)
      )
      
      if role is None:
        role = Role(name=role_name)
        
      role.description = role_info["description"]
      
      if role.role_situation is None:
        role_situation = db.session.scalar(
          sa.select(Role).filter_by(default=True, entity_type="role")
        )
        role.role_situation = role_situation
        
      role.reset_permissions()
      
      for perm in roles[role_name]["permissions"]:
        role.add_permission(perm)
        
      role.default = (role.name == default_role)
      db.session.add(role)
      
    db.session.commit()
    
  def has_permission(self, perm):
    return self.permissions & perm == perm
    
  def add_permission(self, perm):
    if not self.has_permission(perm):
      self.permissions += perm
      
  def remove_permission(self, perm):
    if self.has_permission(perm):
      self.permissions -= perm
      
  def reset_permissions(self):
    self.permissions = 0
      
  @staticmethod
  def view_roles():
    roles = db.session.scalars(
      sa.select(Role).order_by(Role.name.asc())
    ).all()
    
    for role in roles:
      print(role.name)
      
  @property
  def user_count(self):
    query = sa.select(sa.func.count(User.id)).where(User.user_role_id == self.id)
    return db.session.scalar(query)

class User(db.Model, UserMixin):
  id: so.Mapped[int] = so.mapped_column(primary_key=True, index=True)
  username: so.Mapped[str] = so.mapped_column(sa.String(60), unique=True)
  email: so.Mapped[str] = so.mapped_column(sa.String(120), unique=True)
  password_hash: so.Mapped[str] = so.mapped_column(sa.String(128))
  confirmed: so.Mapped[bool] = so.mapped_column(default=False)
  new_email: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
  email_change_token: so.Mapped[Optional[str]] = so.mapped_column(sa.String(128))
  email_confirmed: so.Mapped[bool] = so.mapped_column(default=False)
  
  # Relacionamento Inverso: User associado ao Situation
  user_situation: so.Mapped[Situation] = so.relationship(
    back_populates="users"
  )
  user_situation_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Situation.id, ondelete="CASCADE"))
  
  # Relacionamento Inverso: User associado ao Role
  user_role: so.Mapped[Role] = so.relationship(
    back_populates="users"
  )
  user_role_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Role.id, ondelete="CASCADE"))
  
  profile: so.Mapped[Optional["Profile"]] = so.relationship(
    back_populates="user",
    passive_deletes=True,
    uselist=False
  )
  
  # Relacionamento Principal: User relacionado ao Comment
  suggestions: so.WriteOnlyMapped[Optional["Suggestion"]] = so.relationship(
    back_populates="user",
    passive_deletes=True
  )
  
  # Relacionamento principal: Likes relacionado ao User
  likes: so.WriteOnlyMapped["Likes"] = so.relationship(
    back_populates = "user", 
    passive_deletes = True
  )
  
  last_message_read_time: so.Mapped[Optional[datetime]]

  # Relacionamento principal: Message relacionado ao User
  messages_sent: so.WriteOnlyMapped["Message"] = so.relationship(
    foreign_keys="Message.sender_id",
    back_populates = "messages_author",
    passive_deletes=True
  )

  # Relacionamento principal: Message relacionado ao User
  messages_received: so.WriteOnlyMapped["Message"] = so.relationship(
    foreign_keys="Message.recipient_id",
    back_populates = "messages_recipient",
    passive_deletes=True
  )
  
  # Relacionamento principal: Notification relacionado ao User
  notifications: so.WriteOnlyMapped["Notification"] = so.relationship(
    back_populates = "user",
    passive_deletes=True
  )
  
  created: so.Mapped[datetime] = so.mapped_column(default=datetime.utcnow)
  modified: so.Mapped[Optional[datetime]] = so.mapped_column(default=datetime.utcnow)
  
  def __init__(self, **kwargs):
    super(User, self).__init__(**kwargs)
    
    # Cria um perfil vazio automático
    if not self.profile:
      with db.session.no_autoflush:
        self.profile = Profile()
    
    if self.user_role is None:
      if self.email == current_app.config["BLOG_ADMIN"]:
        self.user_role = db.session.scalar(
          sa.select(Role).filter_by(name="Administrator")
        )
      else:
        self.user_role = db.session.scalar(
          sa.select(Role).filter_by(default=True)
        )
    
    with db.session.no_autoflush:
      if self.user_situation is None:
        self.user_situation = db.session.scalar(
          sa.select(Situation).filter_by(default=True, entity_type="user")
        )
      
  def can(self, perm):
    return self.user_role is not None and self.user_role.has_permission(perm)
    
  @property
  def get_permissions(self):
    permissions_map = {
      Permission.WRITE: "WRITE",
      Permission.MODERATE: "MODERATE",
      Permission.ADMIN: "ADMIN"
    }
    
    result = [name for bit, name in permissions_map.items() if self.can(bit)]
    
    return ", ".join(result) if result else "Nenhuma"
    
  def is_administrator(self):
    return self.can(Permission.ADMIN)
    
  def is_moderator(self):
    return self.can(Permission.MODERATE)
    
  def set_password(self, password):
    self.password_hash = generate_password_hash(password)
    
  def check_password(self, password):
    return check_password_hash(self.password_hash, password)
  
  @staticmethod
  def insert_users():
    users = [
      {
        "username": "oliveradm", 
        "email": "oliveradm@example.com", 
        "password": "catcat",
        "confirmed": True
      },
      {
        "username": "lana", 
        "email": "lana@example.com", 
        "password": "catcat",
        "confirmed": False
      }
    ]
    
    with db.session.no_autoflush:
      for u in users:
        user = User.query.filter_by(email=u["email"]).first()
        
        if user is None:
          user = User(username=u["username"], email=u["email"], confirmed=u["confirmed"])
          user.set_password(u["password"])
          db.session.add(user)
      db.session.commit()
      
  #GERA TOKEN VÁLIDO POR 10 PRA CONFIRMAÇÃO DA CONTA
  def generate_token_confirm_account(self, expires_in=600):
    return jwt.encode(
      {
        "id": self.id, 
        "exp": time() + expires_in
      },
      current_app.config["SECRET_KEY"],
      algorithm="HS256"
    )
    
  #VERIFICA TOKEN GERADO PARA A CONFIRMAÇÃO DA CONTA
  def check_token_confirm_account(self, token):
    try:
      data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except:
      return
    
    if data.get("id") != self.id:
      return False
      
    self.confirmed = True
    query = sa.select(Situation).filter_by(entity_type="user", name="Ativo")
    self.user_situation = db.session.scalar(query)
    db.session.add(self)
    return True
    
  #GERA TOKEN VÁLIDO POR 10m PRA CONFIRMAR A ALTERAÇÃO DO NOVO E-MAIL
  def generate_token_confirm_email(self, new_email, expires_in=600):
    self.new_email = new_email
    
    encoded_jw = jwt.encode(
      {
        "id": self.id, 
        "new_email": new_email, 
        "exp": time() + expires_in
      },
      current_app.config["SECRET_KEY"],
      algorithm="HS256"
    )
    
    self.email_change_token = encoded_jw
    db.session.commit()
    return self.email_change_token
  
  #VERIFICA O TOKEN GERADO PARA A CONFIRMAÇÃO DE ALTERAÇÃO DE EMAIL
  def check_token_confirm_email(self, token):
    try:
      data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except:
      return
    
    user = db.session.get(User, int(data.get("id")))
    
    if user and user.new_email == data.get("new_email"):
      return user
    return None
    
  #GERA TOKEN VÁLIDO POR 10m PARA A REDEFINIÇÃO DE SENHA
  def generate_token_password_reset(self, expires_in=600):
    return jwt.encode(
      {"id": self.id, "exp": time() + expires_in},
      current_app.config["SECRET_KEY"],
      algorithm="HS256"
    )
    
  #VERIFICA TOKEN GERADO PARA A REDEFINIÇÃO DE SENHA
  @staticmethod
  def check_token_password_reset(token):
    try:
      data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except:
      return
    
    return db.session.get(User, int(data.get("id")))
    
  def check_token(self, token):
    try:
      data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
      return None, "O token expirou"
    except jwt.InvalidTokenError:
      return None, "Token inválido"
      
    user = User.query.get(int(data.get("id")))
    
    if user and user.new_email == data.get("new_email"):
      return user, None
    
  def avatar(self, size):
    digest = md5(self.email.lower().encode("utf-8")).hexdigest()
    return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}"
    
  def unread_message_count(self):
    last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
    query = sa.select(Message).where(Message.messages_recipient == self, Message.timestamp > last_read_time)
    return db.session.scalar(sa.select(sa.func.count()).select_from(query.subquery()))
    
  def add_notification(self, name, data):
    db.session.execute(self.notifications.delete().where(Notification.name == name))
    n = Notification(name=name, payload_json=json.dumps(data), user=self)
    db.session.add(n)
    return n
    
class Profile(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True, index=True)
  name: so.Mapped[Optional[str]] = so.mapped_column(sa.String(60))
  image_url: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
  occupation: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
  location: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
  website: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
  about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
  
  user: so.Mapped[User] = so.relationship(
    back_populates="profile"
  )
  user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id))
  
  # Relacionamento principal: SocialMedia associado ao Profile
  social_media: so.Mapped[List["SocialMedia"]] = so.relationship(
    back_populates="profile",
    passive_deletes=True
  )
  
  created: so.Mapped[datetime] = so.mapped_column(default=datetime.utcnow)
  modified: so.Mapped[Optional[datetime]] = so.mapped_column(default=datetime.utcnow)
  
class Suggestion(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True, index=True)
  content: so.Mapped[str] = so.mapped_column(sa.Text)
  
  # Relacionamento Inverso: Suggestion associado ao Situation
  suggestion_situation: so.Mapped[Situation] = so.relationship(
    back_populates="suggestions"
  )
  suggestion_situation_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Situation.id, ondelete="CASCADE"))
  
  # Relacionamento Inverso: Suggestion associado ao User
  user: so.Mapped[User] = so.relationship(
    back_populates="suggestions"
  )
  user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id, ondelete="CASCADE"))
  
  likes_count: so.Mapped[Optional[int]] = so.mapped_column(default = 0)

  # Relacionamento principal: Likes relacionado ao Suggestion
  likes: so.WriteOnlyMapped["Likes"] = so.relationship(
    back_populates = "suggestion", 
    passive_deletes = True
  )
  
  created: so.Mapped[datetime] = so.mapped_column(default=datetime.utcnow)
  modified: so.Mapped[Optional[datetime]] = so.mapped_column(default=datetime.utcnow)
  
  def __init__(self, **kwargs):
    super(Suggestion, self).__init__(**kwargs)
    
    if self.suggestion_situation is None:
      self.suggestion_situation = db.session.scalar(
        sa.select(Situation).filter_by(default=True, entity_type="suggestion")
      )
  
class Likes(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True)
  
  # Relacionamento inverso: User associado ao Likes
  user: so.Mapped[User] = so.relationship(
    back_populates = "likes"
  )
  # Chave estrangeira referenciando o ID do User
  user_id: so.Mapped[int] = so.mapped_column(
    sa.ForeignKey(
      User.id,
      ondelete="CASCADE"
    )
  )

  # Relacionamento inverso: Comment associado ao Likes
  suggestion: so.Mapped[Suggestion] = so.relationship(
    back_populates = "likes"
  )
  # Chave estrangeira referenciando o ID do Suggestion
  suggestion_id: so.Mapped[int] = so.mapped_column(
    sa.ForeignKey(
      Suggestion.id, 
      ondelete="CASCADE"
    )
  )
  
class SocialMedia(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True)
  name: so.Mapped[str] = so.mapped_column(sa.String(35))
  icon: so.Mapped[Optional[str]] = so.mapped_column(sa.String(60))
  url: so.Mapped[str] = so.mapped_column(sa.String(250), unique=True)
  is_active: so.Mapped[Optional[bool]] = so.mapped_column(default = True)
  order_index: so.Mapped[Optional[int]] = so.mapped_column()

  # Relacionamento inverso: Situation associado ao SocialMedia
  social_media_situation: so.Mapped["Situation"] = so.relationship(
    back_populates = "social_media"
  )

  # Chave estrangeira referenciando o ID da Situation
  social_media_situation_id: so.Mapped[int] = so.mapped_column(
    sa.ForeignKey(
      Situation.id, 
      ondelete="CASCADE"
    )
  )
  
  # Relacionamento inverso: Profile associado ao SocialMedia
  profile: so.Mapped["Profile"] = so.relationship(
    back_populates="social_media"
  )
  # Chave estrangeira referenciando o ID da Profile
  profile_id: so.Mapped[int] = so.mapped_column(
    sa.ForeignKey(Profile.id, ondelete="CASCADE")
  )
  
  created: so.Mapped[datetime] = so.mapped_column(default=datetime.utcnow)
  modified: so.Mapped[Optional[datetime]] = so.mapped_column(default=datetime.utcnow)
  
  def __init__(self, **kwargs):
    super(SocialMedia, self).__init__(**kwargs)
    
    social_media_situation = db.session.scalar(sa.select(Situation).filter_by(default=True, entity_type="social_media"))
    self.social_media_situation = social_media_situation
  
class Message(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key = True)
  is_read: so.Mapped[bool] = so.mapped_column(default=False)

  # Relacionamento inverso: User associado ao Message
  messages_author: so.Mapped[User] = so.relationship(
    foreign_keys="Message.sender_id", 
    back_populates = "messages_sent"
  )
  # Chave estrangeira referenciando o ID do User
  sender_id: so.Mapped[int] = so.mapped_column(
    sa.ForeignKey(
      User.id, 
      ondelete="CASCADE"
    ), 
    index = True
  )

  # Relacionamento inverso: User associado ao Message
  messages_recipient: so.Mapped[User] = so.relationship(
    foreign_keys="Message.recipient_id", 
    back_populates = "messages_received"
  )
  # Chave estrangeira referenciando o ID do User
  recipient_id: so.Mapped[int] = so.mapped_column(
    sa.ForeignKey(
      User.id, 
      ondelete="CASCADE"
    ), 
    index = True
  )
  
  message_body: so.Mapped[str] = so.mapped_column(sa.String(500))
  timestamp: so.Mapped[datetime] = so.mapped_column(default = lambda: datetime.now(timezone.utc))
  
  def __repr__(self):
    return f"<Messsage {self.message_body}>"
    
class Notification(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key = True)
  name: so.Mapped[str] = so.mapped_column(sa.String(130), index=True)

  # Chave estrangeira referenciando o ID do User
  user_id: so.Mapped[int] = so.mapped_column(
    sa.ForeignKey(
      User.id, 
      ondelete="CASCADE"
    ), 
    index=True
  )
  
  timestamp: so.Mapped[float] = so.mapped_column(default = time, index=True)
  payload_json: so.Mapped[str] = so.mapped_column(sa.Text)

  # Relacionamento inverso: User associado ao Notification
  user: so.Mapped[User] = so.relationship(
    back_populates = "notifications"
  )
  
  def get_data(self):
    return json.loads(str(self.payload_json))
  
class AnonymousUser(AnonymousUserMixin):
  def can(self, permissions):
    return False
  
  def is_administrator(self):
    return False
  
@login.user_loader
def load_user(id):
  return User.query.get(int(id))
  
login.anonymous_user = AnonymousUser

def insert_all():
  print("Situaçôes padrão")
  populates_default_situations()
  print("Papeis padrão")
  Role.insert_roles()
  print("Usuarios padrão")
  User.insert_users()
