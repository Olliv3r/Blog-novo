from app import db, login
from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app
from app.default_dict import situations, block_types
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from time import time
from hashlib import md5
from slugify import slugify

def populates_default_situations():
  for situation in situations:
    existing_situation = Situation.query.filter_by(name=situation["name"], entity_type=situation["entity_type"]).first()
    
    default_situation_role = "Ativo"
    default_situation_user = "Aguardando"
    default_situation_comment = "Aguardando"
    default_situation_article = "Aguardando revisão"
    
    if existing_situation is None:
      new_situation = Situation(name=situation["name"], description=situation["description"], entity_type=situation["entity_type"], default = False)
      
      if situation["entity_type"] == "role":
        new_situation.default = (situation["name"] == default_situation_role)
      
      elif situation["entity_type"] == "user":
        new_situation.default = (situation["name"] == default_situation_user)
        
      elif situation["entity_type"] == "article":
        new_situation.default = (situation["name"] == default_situation_article)
        
      elif situation["entity_type"] == "comment":
        new_situation.default = (situation["name"] == default_situation_comment)
  
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
  # Relacionamento Principal: Situation relacionado ao Article
  articles: so.WriteOnlyMapped["Article"] = so.relationship(
    back_populates="article_situation",
    passive_deletes=True
  )
  # Relacionamento Principal: Situation relacionado ao Comment
  comments: so.WriteOnlyMapped["Comment"] = so.relationship(
    back_populates="comment_situation",
    passive_deletes=True
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
  
  # Relacionamento Principal: User relacionado ao Article
  articles: so.WriteOnlyMapped[Optional["Article"]] = so.relationship(
    back_populates="user",
    passive_deletes=True
  )
  # Relacionamento Principal: User relacionado ao Comment
  comments: so.WriteOnlyMapped[Optional["Comment"]] = so.relationship(
    back_populates="user",
    passive_deletes=True
  )
  
  created: so.Mapped[datetime] = so.mapped_column(default=datetime.utcnow)
  modified: so.Mapped[Optional[datetime]] = so.mapped_column(default=datetime.utcnow)
  
  def __init__(self, **kwargs):
    super(User, self).__init__(**kwargs)
    
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
        "username": "", 
        "email": "", 
        "password": ""
      },
      {
        "username": "", 
        "email": "", 
        "password": ""
      }
    ]
    
    with db.session.no_autoflush:
      for u in users:
        user = User.query.filter_by(email=u["email"]).first()
        
        if user is None:
          user = User(username=u["username"], email=u["email"])
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
    
class Profile(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True, index=True)
  name: so.Mapped[Optional[str]] = so.mapped_column(sa.String(60))
  profile_image_url: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256), unique=True)
  location: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
  website: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
  about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
  
  user: so.Mapped[User] = so.relationship(
    back_populates="profile"
  )
  user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id))
  
  created: so.Mapped[datetime] = so.mapped_column(default=datetime.utcnow)
  modified: so.Mapped[Optional[datetime]] = so.mapped_column(default=datetime.utcnow)
  
class Article(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True, index=True)
  title: so.Mapped[str] = so.mapped_column(sa.String(200))
  slug: so.Mapped[str] = so.mapped_column(sa.String(200), unique=True)
  
  # Relacionamento Inverso: Article associado ao Situation
  article_situation: so.Mapped[Situation] = so.relationship(
    back_populates="articles"
  )
  article_situation_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Situation.id, ondelete="CASCADE"))
  
  # Relacionamento Inverso: Article associado ao User
  user: so.Mapped[User] = so.relationship(
    back_populates="articles"
  )
  user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id, ondelete="CASCADE"))
  
  # Relacionamento Principal: Article relacionado ao ArticleBlock
  blocks: so.WriteOnlyMapped[Optional["ArticleBlock"]] = so.relationship(
    back_populates="article",
    cascade="all, delete-orphan"
  )
  
  # Relacionamento Principal: Article relacionado ao Comment
  comments: so.WriteOnlyMapped[Optional["Comment"]] = so.relationship(
    back_populates="article",
    passive_deletes=True
  )
  
  created: so.Mapped[datetime] = so.mapped_column(default=datetime.utcnow)
  modified: so.Mapped[Optional[datetime]] = so.mapped_column(default=datetime.utcnow)
  
  def __init__(self, **kwargs):
    super(Article, self).__init__(**kwargs)
  
    # Define a situação padrão do artigo
    if self.article_situation is None:
      self.article_situation = db.session.scalar(
        sa.select(Situation).filter_by(default=True, entity_type="article")
      )
      
    # Cria a slug do artigo automaticamente
    if not self.slug and self.title:
      self.slug = self.generate_unique_slug(self.title)
      
  @classmethod
  def generate_unique_slug(cls, title):
    base_slug = slugify(title)
    slug = base_slug
    
    counter = 1
    
    query = sa.select(cls).filter_by(slug=slug)
    slug_existing = db.session.scalar(query)
    
    while slug_existing:
      slug = f"{base_slug}-{counter}"
      counter += 1
      
      query = sa.select(cls).filter_by(slug=slug)
      slug_existing = db.session.scalar(query)
    
    return slug

  @property
  def comment_count(self):
    query = sa.select(sa.func.count(Comment.id)).where(Comment.article_id == self.id)
    return db.session.scalar(query)
  
class BlockType(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True, index=True)
  name: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True)
  description: so.Mapped[str] = so.mapped_column(sa.Text(100))
  label: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
  
  # Relacionamento Principal: BlockType relacionado ao ArticleBlock
  article_blocks: so.WriteOnlyMapped[List["ArticleBlock"]] = so.relationship(
    back_populates="block_type"
  )
  
  created: so.Mapped[datetime] = so.mapped_column(default=datetime.utcnow)
  modified: so.Mapped[datetime] = so.mapped_column(default=datetime.utcnow)
  
  @classmethod
  def insert_block_types(cls):
    for block in block_types:
      query = sa.select(cls).filter_by(name=block["name"])
      existing_block = db.session.scalar(query)
      
      if not existing_block:
        new_block = cls(name=block["name"], description=block["description"])
        db.session.add(new_block)
      db.session.commit()
      
  @classmethod
  def view_block_types(cls):
    blocks = cls.query.all()
    
    for block in blocks:
      print(block.name)
  
class ArticleBlock(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True, index=True)
  content: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
  extra: so.Mapped[Optional[str]] = so.mapped_column(sa.JSON)
  position: so.Mapped[int] = so.mapped_column()
  
  # Relacionamento Inverso: ArticleBlock associado ao Article
  article: so.Mapped[Article] = so.relationship(
    back_populates="blocks"
  )
  article_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Article.id, ondelete="CASCADE"))
  
  # Relacionamento Inverso: ArticleBlock associado ao BlockType
  block_type: so.Mapped[BlockType] = so.relationship(
    back_populates="article_blocks"
  )
  block_type_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(BlockType.id, ondelete="CASCADE"))
  
  created: so.Mapped[datetime] = so.mapped_column(default=datetime.utcnow)
  modified: so.Mapped[Optional[datetime]] = so.mapped_column(default=datetime.utcnow)
  
class Comment(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True, index=True)
  content: so.Mapped[str] = so.mapped_column(sa.Text)
  
  # Relacionamento Inverso: Comment associado ao Situation
  comment_situation: so.Mapped[Situation] = so.relationship(
    back_populates="comments"
  )
  comment_situation_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Situation.id, ondelete="CASCADE"))
  
  # Relacionamento Inverso: Comment associado ao User
  user: so.Mapped[User] = so.relationship(
    back_populates="comments"
  )
  user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id, ondelete="CASCADE"))
  
  # Relacionamento Inverso: Comment associado ao Article
  article: so.Mapped[Article] = so.relationship(
    back_populates="comments"
  )
  article_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Article.id, ondelete="CASCADE"))
  
  created: so.Mapped[datetime] = so.mapped_column(default=datetime.utcnow)
  modified: so.Mapped[Optional[datetime]] = so.mapped_column(default=datetime.utcnow)
  
  def __init__(self, **kwargs):
    super(Comment, self).__init__(**kwargs)
    
    if self.comment_situation is None:
      self.comment_situation = db.session.scalar(
        sa.select(Situation).filter_by(default=True, entity_type="comment")
      )
  
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
