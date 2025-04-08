import smtplib
import os
from flask import Blueprint, request, jsonify
from models.models import Administrador
from models.database import db
from flask_jwt_extended import create_access_token, jwt_required
from flask_jwt_extended.exceptions import NoAuthorizationError
from .auth import auth_required
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from passlib.hash import pbkdf2_sha256


administradores_bp = Blueprint('administradores', __name__)

@administradores_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')

    administrador = Administrador.query.filter_by(email=email).first()

    if not administrador or not administrador.verify_password(senha):
        return jsonify({"message": "Credenciais inválidas"}), 401

    token = create_access_token(identity=administrador.id)
    return jsonify({"token": token}), 200


@administradores_bp.route('/adicionar', methods=['POST'])
@auth_required  
def adicionar_admin():
    data = request.get_json()

    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')

    if Administrador.query.filter_by(email=email).first():
        return jsonify({"message": "Administrador já existe com esse e-mail."}), 400

    novo_admin = Administrador(nome=nome, email=email, senha=senha) 
    db.session.add(novo_admin)
    db.session.commit()

    return jsonify({"message": "Administrador adicionado com sucesso!"}), 201

@administradores_bp.errorhandler(NoAuthorizationError)
def handle_no_authorization_error(error):
    return jsonify({"message": "Usuário administrador não logado"}), 401

@administradores_bp.route('/listar', methods=['GET'])
@auth_required
def listar_administradores():
    administradores = Administrador.query.all()

    lista_admins = [
        {   "id": admin.id,
            "nome": admin.nome, "email": admin.email}
        for admin in administradores
    ]

    print("\nAdministradores cadastrados:")
    for admin in lista_admins:
          print(f"| ID: {admin['id']} | Nome: {admin['nome']} | Email: {admin['email']}")
    print("-" * 30)

    return jsonify(lista_admins), 200

@administradores_bp.route('/excluir', methods=['DELETE'])
@auth_required
def excluir_administrador():
    data = request.get_json()
    nome = data.get('nome').strip()

    print(f"Procurando pelo nome: {nome}")
    admin = Administrador.query.filter_by(nome=nome).first()

    print(f"Administrador encontrado: {admin}")

    if not admin:
        print("Administrador não encontrado.")
        return jsonify({"message": "Administrador não encontrado!"}), 404

    total_admins = Administrador.query.count()
    if total_admins <= 1:
        print("Erro: Não é possível excluir o último administrador!")
        return jsonify({"message": "Erro: Não é possível excluir o último administrador!"}), 400

    nome_administrador = admin.nome

    db.session.delete(admin)
    db.session.commit()

    enviar_email_exclusao(admin.email, nome_administrador)

    print(f"Administrador {nome} excluído com sucesso!")
    return jsonify({"message": f"Administrador {nome} excluído com sucesso!"}), 200


def enviar_email_exclusao(email_destino, nome_administrador):
    sender = "pdvpython@gmail.com"
    senha = os.getenv("EMAIL_SENHA")
    subject = "Exclusão de conta"

    # ✅ Parte texto simples (fallback)
    body_plain = f"""
Olá {nome_administrador},

Sua conta foi excluída com sucesso do sistema PDV-Python.

Se você não solicitou isso, entre em contato com o suporte.

Equipe PDV-Python
    """

    # ✅ Parte HTML estilizada
    body_html = f"""
<html>
 <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
  <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
   <div style="text-align: center;">
     <img src="https://i.imgur.com/IPSNJqn.png" alt="PDV Python" style="max-width: 150px; margin-bottom: 20px;">
    <h2 style="color: #333;">Conta Excluída</h2>
   </div>
   <p style="font-size: 16px; color: #555;">Olá <strong>{nome_administrador}</strong>,</p>
   <p style="font-size: 16px; color: #555;">Informamos que sua conta foi <strong>excluída com sucesso</strong> do sistema <strong>PDV-Python</strong>.</p>
   <p style="font-size: 16px; color: #555;">Caso você não tenha solicitado essa exclusão ou tenha dúvidas, entre em contato com nosso suporte.</p>
   <p style="font-size: 16px; color: #555;">Atenciosamente,<br><strong>Equipe PDV-Python</strong></p>
   <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
   <p style="font-size: 12px; color: #999; text-align: center;">Este é um e-mail automático. Por favor, não responda.</p>
  </div>
 </body>
</html>
"""

    # 🧩 Monta a mensagem multipart
    msg = MIMEMultipart("alternative")
    msg['From'] = sender
    msg['To'] = email_destino
    msg['Subject'] = subject

    # Adiciona as duas versões do corpo
    msg.attach(MIMEText(body_plain, 'plain', 'utf-8'))
    msg.attach(MIMEText(body_html, 'html', 'utf-8'))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
            servidor.starttls()
            servidor.login(sender, senha)
            servidor.sendmail(sender, email_destino, msg.as_string())
        print("E-mail de exclusão enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

@administradores_bp.route('/editar', methods=['PUT'])
@auth_required
def editar_admin():
    # Extraímos o ID do administrador que será editado da requisição
    data = request.get_json()
    admin_id = data.get('id')  
    
    # Supondo que o frontend envie o ID do admin a ser editado

    administrador = Administrador.query.filter_by(id=admin_id).first()

    if not administrador:
        return jsonify({"message": "Administrador não encontrado."}), 404

    nome = data.get('nome')
    if nome:
        if Administrador.query.filter_by(nome=nome).first():
            return jsonify({"message": "Este nome já está em uso por outro administrador."}), 400
        administrador.nome = nome

    email = data.get('email')
    if email:
        if Administrador.query.filter_by(email=email).first():
            return jsonify({"message": "Este e-mail já está em uso por outro administrador."}), 400
        administrador.email = email

    senha = data.get('senha')
    administrador.senha_hash = pbkdf2_sha256.hash(senha)  

    db.session.commit()

    return jsonify({"message": "Administrador atualizado com sucesso!"}), 200