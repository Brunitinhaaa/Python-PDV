from flask import Blueprint, request, jsonify
from models.models import Administrador
from models.database import db
from flask_jwt_extended import create_access_token, jwt_required
from flask_jwt_extended.exceptions import NoAuthorizationError
from .auth import auth_required 

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
