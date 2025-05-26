# app/controllers/admin.py
import os
import smtplib
from flask import (
    Blueprint, render_template,
    request, jsonify
)
from models.models import Administrador
from models.database import db
from flask_jwt_extended import (
    create_access_token,
    set_access_cookies,
    jwt_required,
    get_jwt_identity
)
from .auth import auth_required
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from passlib.hash import pbkdf2_sha256

administradores_bp = Blueprint('administradores', __name__)

@administradores_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    admin = Administrador.query.filter_by(email=data.get('email')).first()
    if not admin or not admin.verify_password(data.get('senha')):
        return jsonify({"message": "Credenciais inválidas"}), 401

    token = create_access_token(identity=admin.id)
    resp = jsonify({"message": "Login OK"})
    set_access_cookies(resp, token)
    return resp, 200

@administradores_bp.route('/listar-ui')
def listar_admins_ui():
    admins = Administrador.query.all()
    return render_template('administradores/listar.html', admins=admins, user_name='Bruna', menu='admin')

@administradores_bp.route('/listar')
def listar_admins():
    admins = Administrador.query.all()
    return jsonify([{'id':a.id,'nome':a.nome,'email':a.email} for a in admins])

@administradores_bp.route('/adicionar-ui')
def adicionar_admin_ui():
    return render_template('administradores/add.html', user_name='Bruna')

@administradores_bp.route('/adicionar', methods=['POST'])
def adicionar_admin():
    data = request.get_json()
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')

    if Administrador.query.filter_by(email=email).first():
        return jsonify({"message": "Já existe um administrador cadastrado com esse e-mail!"}), 400

    novo = Administrador(
      nome=nome,
      email=email,
      senha=senha
    )

    db.session.add(novo)
    db.session.commit()

    return jsonify({'message':'Administrador adicionado com sucesso!'}), 201

@administradores_bp.route('/editar-ui/<string:admin_id>', methods=['GET'])
@jwt_required()
def editar_admin_ui(admin_id):
    user_id = get_jwt_identity()
    user = Administrador.query.get(user_id)
    admin = Administrador.query.get_or_404(admin_id)
    return render_template(
        'administradores/editar.html',
        user_name=user.nome,
        admin=admin, menu='admin'
    )

@administradores_bp.route('/editar', methods=['PUT'])
@auth_required
def editar_admin():
    data = request.get_json()
    admin = Administrador.query.get(data.get('id'))
    if not admin:
        return jsonify({"message": "Administrador não encontrado."}), 404
    if data.get('nome'):
        admin.nome = data['nome']
    if data.get('email'):
        admin.email = data['email']
    if data.get('senha'):
        admin.senha_hash = pbkdf2_sha256.hash(data['senha'])
    db.session.commit()
    return jsonify({"message": "Administrador atualizado com sucesso!"}), 200


@administradores_bp.route('/excluir', methods=['DELETE'])
@auth_required
def excluir_administrador():
    data = request.get_json()
    nome = data.get('nome').strip()
    admin = Administrador.query.filter_by(nome=nome).first()
    if not admin:
        return jsonify({"message": "Administrador não encontrado!"}), 404
    if Administrador.query.count() <= 1:
        return jsonify({"message": "Não é possível excluir o último administrador!"}), 400

    db.session.delete(admin)
    db.session.commit()
    enviar_email_exclusao(admin.email, admin.nome)
    return jsonify({"message": f"Administrador {nome} excluído com sucesso!"}), 200

def enviar_email_exclusao(email_destino, nome_administrador):
    sender = "pdvpython@gmail.com"
    senha = os.getenv("EMAIL_SENHA")
    subject = "Exclusão de conta"
    body_plain = f"Olá {nome_administrador},\n\nSua conta foi excluída..."
    body_html = f"<p>Olá <strong>{nome_administrador}</strong>, sua conta foi excluída...</p>"
    msg = MIMEMultipart("alternative")
    msg['From'] = sender
    msg['To'] = email_destino
    msg['Subject'] = subject
    msg.attach(MIMEText(body_plain, 'plain', 'utf-8'))
    msg.attach(MIMEText(body_html, 'html', 'utf-8'))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
            servidor.starttls()
            servidor.login(sender, senha)
            servidor.sendmail(sender, email_destino, msg.as_string())
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")