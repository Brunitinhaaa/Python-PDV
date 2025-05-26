import smtplib
import os
import re

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from models.database import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from .auth import auth_required
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from passlib.hash import pbkdf2_sha256
from models.models import Clientes, Vendas, Produtos, Administrador
from utils.mercado_pago import criar_pagamento_pix
from datetime import datetime, timezone

vendas_bp = Blueprint('vendas', __name__)

carrinhos_em_memoria = {}

# ==== CARRINHO UI ====
@vendas_bp.route('/listar-ui', methods=['GET'])
@jwt_required()
def listar_vendas_ui():
    admin_id = get_jwt_identity()
    user = Administrador.query.get(admin_id)
    carrinho = carrinhos_em_memoria.get(admin_id, {"itens": []})

    return render_template(
        'vendas/carrinho.html',
        user_name=user.nome,
        carrinho=carrinho,
        menu='vendas'
    )


# ==== ROTA: Adicionar item ====

@vendas_bp.route('/adicionar-item', methods=['POST'])
@auth_required
def adicionar_item():
    data = request.form or request.get_json()
    admin_id = get_jwt_identity()
    codigo_barras = data.get('codigo_barras')
    quantidade = int(data.get('quantidade', 1))

    produto = Produtos.query.filter_by(codigo_barras=codigo_barras).first()
    if not produto:
        return jsonify({"message": "Produto não encontrado."}), 400

    carrinho = carrinhos_em_memoria.get(admin_id, {"cliente_id": None, "itens": []})

    for item in carrinho["itens"]:
        if item["produto_id"] == str(produto.id):
            item["quantidade"] += quantidade
            item["subtotal"] = item["preco_unitario"] * item["quantidade"]
            item["erro_estoque"] = item["quantidade"] > produto.quantidade_estoque
            break
    else:
        erro_estoque = quantidade > produto.quantidade_estoque
        carrinho["itens"].append({
            "produto_id": str(produto.id),
            "nome": produto.nome,
            "quantidade": quantidade,
            "preco_unitario": float(produto.preco),
            "subtotal": float(produto.preco) * quantidade,
            "erro_estoque": erro_estoque
        })

    carrinhos_em_memoria[admin_id] = carrinho
    return jsonify({"message": f"Produto {produto.nome} adicionado ao carrinho."}), 201

# ==== CLIENTES ====
@vendas_bp.route('/clientes/adicionar-ui')
@auth_required
def adicionar_cliente_ui():
    return render_template('clientes/add.html')

@vendas_bp.route('/clientes', methods=['GET'])
@auth_required
def listar_clientes():
    termo = request.args.get('termo', '').strip()
    if termo:
        clientes = Clientes.query.filter(Clientes.nome.ilike(f'%{termo}%')).all()
    else:
        clientes = Clientes.query.all()

    return jsonify([
        {"id": str(c.id), "nome": c.nome, "email": c.email}
        for c in clientes
    ]), 200

@vendas_bp.route('/clientes', methods=['POST'])
@auth_required
def adicionar_clientes():
    data = request.form or request.get_json()
    nome = data.get('nome')
    email = data.get('email')
    telefone = data.get('telefone')
    endereco = data.get('endereco')
    cpf = data.get('cpf')
    cep = data.get('cep')

    if Clientes.query.filter_by(email=email).first():
        return jsonify({"message": "Cliente já existe com esse e-mail."}), 400

    if Clientes.query.filter_by(cpf=cpf).first():
        return jsonify({"message": "Cliente já existe com esse CPF."}), 400

    novo_cliente = Clientes(nome=nome, email=email, telefone=telefone, endereco=endereco, cpf=cpf, cep=cep)
    db.session.add(novo_cliente)
    db.session.commit()
    return jsonify({"message": "Cliente adicionado com sucesso!"}), 201

# ==== ALTERAR ITEM ====

@vendas_bp.route('/alterar-item', methods=['POST'])
@auth_required
def alterar_item():
    data = request.form or request.get_json()
    admin_id = get_jwt_identity()
    produto_id = data.get('produto_id')
    nova_qtd = int(data.get('quantidade'))

    carrinho = carrinhos_em_memoria.get(admin_id)
    if not carrinho:
        return jsonify({"message": "Carrinho não encontrado."}), 404

    for item in carrinho['itens']:
        if item['produto_id'] == produto_id:
            produto = Produtos.query.get(produto_id)
            if not produto:
                return jsonify({"message": "Produto não encontrado."}), 404
            item['quantidade'] = nova_qtd
            item['subtotal'] = float(produto.preco) * nova_qtd
            item['erro_estoque'] = nova_qtd > produto.quantidade_estoque
            return redirect(url_for('vendas.carrinho_ui'))

    return jsonify({"message": "Produto não encontrado no carrinho."}), 404

# ==== REMOVER ITEM ====

@vendas_bp.route('/remover-item', methods=['POST'])
@auth_required
def remover_item():
    data = request.form or request.get_json()
    admin_id = get_jwt_identity()
    produto_id = data.get('produto_id')

    carrinho = carrinhos_em_memoria.get(admin_id)
    if not carrinho:
        return jsonify({"message": "Carrinho não encontrado."}), 404

    carrinho['itens'] = [item for item in carrinho['itens'] if item['produto_id'] != produto_id]
    return redirect(url_for('vendas.carrinho_ui'))

# ==== LIMPAR CARRINHO ====

@vendas_bp.route('/limpar-carrinho', methods=['POST'])
@auth_required
def limpar_carrinho():
    admin_id = get_jwt_identity()
    if admin_id in carrinhos_em_memoria:
        del carrinhos_em_memoria[admin_id]
    return redirect(url_for('vendas.carrinho_ui'))

# ==== PAGAMENTO PIX ====

@vendas_bp.route('/pagar-pix', methods=['POST'])
@auth_required
def pagar_pix():
    admin_id = get_jwt_identity()
    carrinho = carrinhos_em_memoria.get(admin_id)

    if not carrinho or not carrinho['itens']:
        return jsonify({"message": "Carrinho vazio ou não iniciado."}), 400

    total = sum(item['subtotal'] for item in carrinho['itens'])
    cliente = Clientes.query.get(carrinho['cliente_id'])

    try:
        pagamento = criar_pagamento_pix(total, "Pagamento PDV-Python", {
            "email": cliente.email,
            "first_name": cliente.nome.split()[0],
            "last_name": " ".join(cliente.nome.split()[1:]),
            "identification": {"type": "CPF", "number": cliente.cpf},
            "address": {"zip_code": cliente.cep, "street_name": cliente.endereco, "city": "São Paulo", "federal_unit": "SP"},
            "phone": {"area_code": "11", "number": cliente.telefone[-8:]}
        }, external_reference=admin_id)
        return jsonify({
            "message": "Pagamento Pix criado!",
            "qr_code_base64": pagamento["qr_code_base64"],
            "ticket_url": pagamento["ticket_url"]
        }), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

# ==== FINALIZAR VENDA ====

@vendas_bp.route('/finalizar', methods=['POST'])
@auth_required
def finalizar_venda():
    admin_id = get_jwt_identity()
    data = request.form or request.get_json()
    forma_pagamento = data.get('forma_pagamento')

    carrinho = carrinhos_em_memoria.get(admin_id)
    if not carrinho or not carrinho['itens']:
        return jsonify({"message": "Carrinho vazio ou não iniciado."}), 400

    if forma_pagamento == 'Pix' and carrinho.get('status_pagamento') != 'APROVADO':
        return jsonify({"message": "Pagamento Pix não aprovado."}), 400

    cliente = Clientes.query.get(carrinho['cliente_id'])
    total = sum(item['subtotal'] for item in carrinho['itens'])

    for item in carrinho['itens']:
        produto = Produtos.query.get(item['produto_id'])
        if produto.quantidade_estoque < item['quantidade']:
            return jsonify({"message": f"Estoque insuficiente para '{item['nome']}'."}), 400
        produto.quantidade_estoque -= item['quantidade']
        db.session.add(produto)

    nova_venda = Vendas(
        administrador_id=admin_id,
        cliente_id=carrinho['cliente_id'],
        itens=carrinho['itens'],
        total=total,
        forma_pagamento=forma_pagamento or "PENDENTE",
        data_hora=datetime.now(timezone.utc)
    )

    db.session.add(nova_venda)
    db.session.commit()
    del carrinhos_em_memoria[admin_id]

    return jsonify({"message": "Venda finalizada com sucesso!"}), 200
