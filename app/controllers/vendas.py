import smtplib
import os
from flask import Blueprint, request, jsonify
from models.database import db

from flask_jwt_extended import create_access_token, jwt_required
from flask_jwt_extended.exceptions import NoAuthorizationError
from flask_jwt_extended import jwt_required, get_jwt_identity

from .auth import auth_required

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from passlib.hash import pbkdf2_sha256

from models.models import Clientes
from models.models import Vendas
from models.models import Produtos

vendas_bp = Blueprint('vendas', __name__)

@vendas_bp.route('/clientes', methods=['GET'])
@auth_required  
def listar_clientes():
    clientes = Clientes.query.all()

    lista_clientes = [
        {   "id": cliente.id,
            "nome": cliente.nome, 
            "email": cliente.email,
            "telefone": cliente.telefone,
            "endereço": cliente.endereco }
        for cliente in clientes
    ]

    print("\nClientes cadastrados:")
    for cliente in lista_clientes:
          print(f"| ID: {cliente['id']} | Nome: {cliente['nome']} | Email: {cliente['email']} | Telefone: {cliente['telefone']} | Endereço  : {cliente['endereço']}")
    print("-" * 30)

    return jsonify(lista_clientes), 200

@vendas_bp.route('/clientes', methods=['POST'])
@auth_required  
def adicionar_clientes():
    data = request.get_json()

    nome = data.get('nome')
    email = data.get('email')
    telefone = data.get('telefone')
    endereco = data.get('endereco')

    if Clientes.query.filter_by(email=email).first():
        return jsonify({"message": "cliente já existe com esse e-mail."}), 400

    novo_cliente = Clientes (nome=nome, email=email, telefone=telefone, endereco=endereco) 
    db.session.add(novo_cliente)
    db.session.commit()

    return jsonify({"message": "Cliente adicionado com sucesso!"}), 201

@vendas_bp.route('/clientes', methods=['PUT'])
@auth_required  
def editar_cliente():
    data = request.get_json()
    cliente_id = data.get('id')

    cliente = Clientes.query.get(cliente_id)

    if "email" in data and Clientes.query.filter(Clientes.email == data["email"], Clientes.id != cliente_id).first():
        return jsonify({"message": "E-mail já está em uso por outro cliente."}), 400

    cliente.nome = data.get("nome", cliente.nome)
    cliente.email = data.get("email", cliente.email)
    cliente.telefone = data.get("telefone", cliente.telefone)
    cliente.endereco = data.get("endereco", cliente.endereco)

    db.session.commit()

    return jsonify({"message": "Cliente atualizado com sucesso!"}), 200

@vendas_bp.route('/clientes', methods=['DELETE'])
@auth_required  
def excluir_cliente():
    data = request.get_json()
    cliente_id = data.get('id')

    cliente = Clientes.query.get(cliente_id)

    db.session.delete(cliente)
    db.session.commit()

    return jsonify({"message": "Cliente excluído com sucesso!"}), 200

'''@vendas_bp.route('/vendas', methods=['POST'])
@auth_required
def iniciar_venda():
    data = request.get_json()
    cliente_id = data.get('cliente_id')
    itens = data.get('itens')
    administrador_id = get_jwt_identity()

    for item in itens:
        produto = Produtos.query.get(item['produto_id'])
        if not produto:
            return jsonify({"message": f"Produto {item['produto_id']} não encontrado!"}), 400
        if produto.quantidade_estoque < item['quantidade']:
            return jsonify({"message": f"Estoque insuficiente para o produto {item['produto_id']}."}), 400

    venda = Vendas(
        administrador_id=administrador_id,
        cliente_id=cliente_id,
        itens=itens,
        total=sum([produto.preco * item['quantidade'] for item in itens]),  
        forma_pagamento=None
    )

    db.session.add(venda)
    db.session.commit()

    return jsonify({"message": "Venda iniciada com sucesso!", "venda_id": venda.id}), 201'''

