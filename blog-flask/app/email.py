from threading import Thread
from flask_mail import Message
from flask import current_app, render_template
from app import mail

def send_async_email(app, msg):
  with app.app_context():
    mail.send(msg)
    
def send_email(subject, sender, recipients, text_body, html_body):
  msg = Message(subject, sender=sender, recipients=recipients)
  msg.text = text_body
  msg.html = html_body
  Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
  
def send_email_confirm_account(user):
  token = user.generate_token_confirm_account()
  
  send_email(
    "[Olive] Confirme a sua conta", 
    sender=current_app.config["ADMINS"][0], 
    recipients=[user.email], 
    text_body=render_template(
      "email/confirm_account.txt", 
      user=user, token=token
    ), 
    html_body=render_template(
      "email/confirm_account.html", 
      user=user, token=token
    )
  )
  
def send_email_confirm_email(user, new_email):
  token = user.generate_token_confirm_email(new_email)
  
  send_email(
    "[Olive] Confirme a alteração para o novo e-mail",
    sender=current_app.config["ADMINS"][0],
    recipients=[user.email],
    text_body=render_template(
      "email/confirm_email.txt",
      user=user,
      token=token
    ),
    html_body=render_template(
      "email/confirm_email.html",
      user=user,
      token=token
    )
  )
  
def send_email_reset_password(user):
  token = user.generate_token_password_reset()
  
  send_email(
    "[Olive] Redefina a sua senha",
    sender=current_app.config["ADMINS"][0],
    recipients=[user.email],
    text_body=render_template(
      "email/reset_password.txt",
      user=user,
      token=token
    ),
    html_body=render_template(
      "email/reset_password.html",
      user=user,
      token=token
    )
  )