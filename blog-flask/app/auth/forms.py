from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import User
from app import db
import sqlalchemy as sa

# FORMULÁRIO DE CADASTRO DE USUÁRIOS
class SignupForm(FlaskForm):
  username = StringField("Usuário *", validators=[DataRequired()])
  email = StringField("Email *", validators=[Email(), DataRequired()])
  password = PasswordField("Senha *", validators=[DataRequired(), Length(min=6, message="A senha deve ter no mínimo 6 caracteres!")])
  password2 = PasswordField("Confime a senha *", validators=[DataRequired(), EqualTo("password", message="Senha não confere!")])
  submit = SubmitField("Se cadastrar")
  
  def validate_email(self, email):
    user = db.session.scalar(
      sa.select(User).where(User.email == email.data)
    )
    
    if user is not None:
      raise ValidationError("Por favor, use um e-mail diferente!")
      
  def validate_username(self, username):
    user = db.session.scalar(
      sa.select(User).where(User.username == username.data)
    )
    
    if user is not None:
      raise ValidationError("Por favor, use um usuário diferente!")
  
# FORMULÁRIO DE ACESSO A CONTA DE USUÁRIO
class SigninForm(FlaskForm):
  email = StringField("Email", validators=[Email(), DataRequired()])
  password = PasswordField("Senha", validators=[DataRequired()])
  remember_me = BooleanField("Lembrar-me")
  submit = SubmitField("Acessar")
  
# FORMULÁRIO PARA VERIFICAR E-MAIL
class ResetPasswordEmailForm(FlaskForm):
  email = StringField("E-mail", validators=[DataRequired(), Email()])
  submit = SubmitField("Verificar")
  
# FORMULÁRIO PARA ATUALIZAR A SENHA
class ResetPasswordForm(FlaskForm):
  password = PasswordField("Nova senha", validators=[DataRequired(), Length(min=6, message="A senha deve ter no mínimo 6 caracteres!")])
  password2 = PasswordField("Digite novamente a senha", validators=[DataRequired(), EqualTo("password", message="As senhas não conferem!")])
  submit = SubmitField("Alterar")