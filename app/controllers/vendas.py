import smtplib
import os
import re

from flask import Blueprint, request, jsonify
from models.database import db
from flask_jwt_extended import create_access_token, jwt_required
from flask_jwt_extended.exceptions import NoAuthorizationError
from flask_jwt_extended import jwt_required, get_jwt_identity
from .auth import auth_required
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from passlib.hash import pbkdf2_sha256
from models.models import Clientes, Vendas, Produtos
from utils.mercado_pago import criar_pagamento_pix
from datetime import datetime, timezone

vendas_bp = Blueprint('vendas', __name__)

carrinhos_em_memoria = {}

@vendas_bp.route('/clientes', methods=['GET'])
@auth_required  
def listar_clientes():
    clientes = Clientes.query.all()
    lista_clientes = [
        {
            "id": cliente.id,
            "nome": cliente.nome, 
            "email": cliente.email,
            "telefone": cliente.telefone,
            "endereco": cliente.endereco,
            "cpf": cliente.cpf,
            "cep": cliente.cep
        }
        for cliente in clientes
    ]
    return jsonify(lista_clientes), 200


@vendas_bp.route('/clientes', methods=['POST'])
@auth_required  
def adicionar_clientes():
    data = request.get_json()
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

    # Enviar e-mail de boas-vindas
    sender = "pdvpython@gmail.com"
    senha = os.getenv("EMAIL_SENHA")
    subject = "Bem-vindo(a) ao PDV-Python!"

    body_plain = f"""
Olá {nome},

Seja muito bem-vindo(a) ao sistema PDV-Python!

Agora você pode acompanhar suas compras e ter um atendimento muito mais eficiente.

Qualquer dúvida, estamos à disposição!

Equipe PDV-Python
"""

    body_html = f"""
<html>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f8ff; padding: 40px;">
    <div style="max-width: 650px; margin: auto; background: #ffffff; padding: 35px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
    <div style="text-align: center;">
        <img src="https://i.imgur.com/IPSNJqn.png" style="max-width: 120px; margin-bottom: 25px;" alt="Logo PDV-Python">
        <h1 style="color: #0a58ca;">Bem-vindo(a), {nome}!</h1>
    </div>
    <p style="font-size: 18px; color: #444; text-align: center;">É um prazer ter você conosco no <strong>PDV-Python</strong>!</p>
    <p style="font-size: 16px; color: #555; text-align: center;">
        Agora você pode realizar compras com mais praticidade, segurança e receber os melhores atendimentos.
    </p>
    <div style="margin-top: 30px; text-align: center;">
        <a href="#" style="padding: 12px 30px; background-color: #0d6efd; color: white; text-decoration: none; border-radius: 8px; font-size: 16px;">Acessar sistema</a>
    </div>
    <hr style="margin-top: 40px; border: none; border-top: 1px solid #ddd;">
    <p style="font-size: 12px; color: #aaa; text-align: center;">Este é um e-mail automático. Por favor, não responda.</p>
    </div>
</body>
</html>
"""

    msg = MIMEMultipart("alternative")
    msg['From'] = sender
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body_plain, 'plain', 'utf-8'))
    msg.attach(MIMEText(body_html, 'html', 'utf-8'))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
            servidor.starttls()
            servidor.login(sender, senha)
            servidor.sendmail(sender, email, msg.as_string())
        print("E-mail de boas-vindas enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail de boas-vindas: {e}")

    return jsonify({"message": "Cliente adicionado com sucesso!"}), 201

@vendas_bp.route('/clientes', methods=['PUT'])
@auth_required  
def editar_cliente():
    data = request.get_json()
    cliente_id = data.get('id')

    if not cliente_id:
        return jsonify({"message": "ID do cliente não foi fornecido."}), 400

    cliente = Clientes.query.get(cliente_id)
    if not cliente:
        return jsonify({"message": "Cliente não encontrado."}), 404

    if "email" in data and Clientes.query.filter(Clientes.email == data["email"], Clientes.id != cliente_id).first():
        return jsonify({"message": "E-mail já está em uso por outro cliente."}), 400

    if "cpf" in data and Clientes.query.filter(Clientes.cpf == data["cpf"], Clientes.id != cliente_id).first():
        return jsonify({"message": "CPF já está em uso por outro cliente."}), 400

    cliente.nome = data.get("nome", cliente.nome)
    cliente.email = data.get("email", cliente.email)
    cliente.telefone = data.get("telefone", cliente.telefone)
    cliente.endereco = data.get("endereco", cliente.endereco)
    cliente.cpf = data.get("cpf", cliente.cpf)
    cliente.cep = data.get("cep", cliente.cep)

    db.session.commit()

    return jsonify({"message": "Cliente atualizado com sucesso!"}), 200

@vendas_bp.route('/clientes', methods=['DELETE'])
@auth_required  
def excluir_cliente():
    data = request.get_json()
    cliente_id = data.get('id')

    cliente = Clientes.query.get(cliente_id)

    nome_cliente = cliente.nome
    email_cliente = cliente.email

    db.session.delete(cliente)
    db.session.commit()

    # Enviar e-mail de exclusão
    sender = "pdvpython@gmail.com"
    senha = os.getenv("EMAIL_SENHA")
    subject = "Conta excluída do PDV-Python"

    body_plain = f"""
Olá {nome_cliente},

Sua conta foi removida do sistema PDV-Python.

Se você não solicitou isso, entre em contato com nosso suporte imediatamente.

Equipe PDV-Python
"""

    body_html = f"""
<html>
<body style="font-family: 'Segoe UI', sans-serif; background-color: #fff6f6; padding: 40px;">
    <div style="max-width: 650px; margin: auto; background: #fff; padding: 35px; border-radius: 15px; box-shadow: 0 5px 15px rgba(255,0,0,0.1);">
    <div style="text-align: center;">
        <img src="https://i.imgur.com/IPSNJqn.png" style="max-width: 100px; margin-bottom: 20px;" alt="PDV-Python">
        <h2 style="color: #dc3545;">Conta Excluída</h2>
    </div>
    <p style="font-size: 16px; color: #444; text-align: center;">
        Olá <strong>{nome_cliente}</strong>, sua conta foi <strong>removida com sucesso</strong> do sistema <strong>PDV-Python</strong>.
    </p>
    <p style="font-size: 15px; color: #666; text-align: center;">
        Caso isso tenha sido um engano ou você tenha qualquer dúvida, nossa equipe de suporte está à disposição.
    </p>
    <div style="text-align: center; margin-top: 25px;">
        <a href="#" style="color: #dc3545; text-decoration: underline;">Falar com o suporte</a>
    </div>
    <hr style="margin-top: 40px; border: none; border-top: 1px solid #eee;">
    <p style="font-size: 12px; color: #999; text-align: center;">Este é um e-mail automático. Por favor, não responda.</p>
    </div>
</body>
</html>
"""

    msg = MIMEMultipart("alternative")
    msg['From'] = sender
    msg['To'] = email_cliente
    msg['Subject'] = subject
    msg.attach(MIMEText(body_plain, 'plain', 'utf-8'))
    msg.attach(MIMEText(body_html, 'html', 'utf-8'))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
            servidor.starttls()
            servidor.login(sender, senha)
            servidor.sendmail(sender, email_cliente, msg.as_string())
        print("E-mail de exclusão enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail de exclusão: {e}")

    return jsonify({"message": "Cliente excluído com sucesso!"}), 200

@vendas_bp.route('/vendas/adicionar-item', methods=['POST'])
@auth_required
def adicionar_item():
    data = request.get_json()
    admin_id = get_jwt_identity()
    cliente_id = data.get('cliente_id')
    produto_id = data.get('produto_id')
    quantidade = data.get('quantidade')

    if not cliente_id or not produto_id or not quantidade:
        return jsonify({"message": "cliente_id, produto_id e quantidade são obrigatórios."}), 400

    produto = Produtos.query.get(produto_id)
    if not produto:
        return jsonify({"message": "Produto não encontrado."}), 400

    if produto.quantidade_estoque < quantidade:
        return jsonify({"message": f"Estoque insuficiente para o produto '{produto.nome}'."}), 400

    carrinho = carrinhos_em_memoria.get(admin_id, {"cliente_id": cliente_id, "itens": []})

    # Verifica se o item já está no carrinho
    for item in carrinho["itens"]:
        if item["produto_id"] == produto_id:
            item["quantidade"] += quantidade
            item["subtotal"] += float(produto.preco) * quantidade
            break
    else:
        carrinho["itens"].append({
            "produto_id": produto_id,
            "nome": produto.nome,
            "quantidade": quantidade,
            "preco_unitario": float(produto.preco),
            "subtotal": float(produto.preco) * quantidade
        })

    carrinhos_em_memoria[admin_id] = carrinho
    return jsonify({"message": "Item adicionado ao carrinho!", "carrinho": carrinho}), 200


# Alterar item no carrinho
@vendas_bp.route('/vendas/alterar-item', methods=['PUT'])
@auth_required
def alterar_item():
    data = request.get_json()
    admin_id = get_jwt_identity()
    produto_id = data.get('produto_id')
    nova_qtd = data.get('quantidade')

    carrinho = carrinhos_em_memoria.get(admin_id)
    if not carrinho:
        return jsonify({"message": "Carrinho não encontrado."}), 404

    for item in carrinho['itens']:
        if item['produto_id'] == produto_id:
            produto = Produtos.query.get(produto_id)
            if not produto or produto.quantidade_estoque + item['quantidade'] < nova_qtd:
                return jsonify({"message": "Estoque insuficiente para alteração."}), 400

            item['quantidade'] = nova_qtd
            item['subtotal'] = float(produto.preco) * nova_qtd
            return jsonify({"message": "Item atualizado no carrinho!", "carrinho": carrinho}), 200

    return jsonify({"message": "Produto não encontrado no carrinho."}), 404


# Remover item do carrinho
@vendas_bp.route('/vendas/remover-item', methods=['DELETE'])
@auth_required
def remover_item():
    data = request.get_json()
    admin_id = get_jwt_identity()
    produto_id = data.get('produto_id')

    carrinho = carrinhos_em_memoria.get(admin_id)
    if not carrinho:
        return jsonify({"message": "Carrinho não encontrado."}), 404

    novos_itens = [item for item in carrinho['itens'] if item['produto_id'] != produto_id]

    if len(novos_itens) == len(carrinho['itens']):
        return jsonify({"message": "Produto não encontrado no carrinho."}), 404

    carrinho['itens'] = novos_itens
    return jsonify({"message": "Item removido do carrinho!", "carrinho": carrinho}), 200

# Limpar carrinho
@vendas_bp.route('/vendas/limpar-carrinho', methods=['DELETE'])
@auth_required
def limpar_carrinho():
    admin_id = get_jwt_identity()
    if admin_id in carrinhos_em_memoria:
        del carrinhos_em_memoria[admin_id]
        return jsonify({"message": "Carrinho limpo!"}), 200
    return jsonify({"message": "Carrinho já está vazio."}), 200

# fazer pix
@vendas_bp.route('/pagar-pix', methods=['POST'])
@auth_required
def pagar_pix():
    admin_id = get_jwt_identity()
    carrinho = carrinhos_em_memoria.get(admin_id)

    if not carrinho or not carrinho['itens']:
        return jsonify({"message": "Carrinho vazio ou não iniciado."}), 400

    total = sum(item['subtotal'] for item in carrinho['itens'])
    cliente = Clientes.query.get(carrinho['cliente_id'])

    if not cliente:
        return jsonify({"message": "Cliente inválido."}), 400

    # ------ Formatar Telefone ------
    def formatar_telefone(telefone):
        numeros = re.sub(r'\D', '', telefone)
        if len(numeros) >= 10:
            return numeros[:2], numeros[2:]
        return "", numeros

    ddd, numero_tel = formatar_telefone(cliente.telefone)

    # ------ Separar Endereço ------
    endereco_split = cliente.endereco.split(",")
    street_name = endereco_split[0].strip()
    street_number = endereco_split[1].strip() if len(endereco_split) > 1 else ""
    neighborhood = endereco_split[2].strip() if len(endereco_split) > 2 else ""
    federal_unit = endereco_split[3].strip() if len(endereco_split) > 3 else ""
    
    # ------ Montar Payer ------
    payer = {
        "email": cliente.email,
        "first_name": cliente.nome.split()[0],
        "last_name": " ".join(cliente.nome.split()[1:]),
        "identification": {
            "type": "CPF",
            "number": cliente.cpf
        },
        "address": {
            "zip_code": cliente.cep,
            "street_name": street_name,
            "street_number": street_number,
            "neighborhood": neighborhood,
            "city": "São Paulo",
            "federal_unit": federal_unit
        },
        "phone": {
            "area_code": ddd,
            "number": numero_tel
        }
    }

    try:
        pagamento = criar_pagamento_pix(total, "Pagamento PDV-Python", payer, external_reference=admin_id)
        return jsonify({
            "message": "Pagamento Pix criado!",
            "qr_code_base64": pagamento["qr_code_base64"],
            "ticket_url": pagamento["ticket_url"]
        }), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

# finaliza a venda
@vendas_bp.route('/vendas/finalizar', methods=['POST'])
@auth_required
def finalizar_venda():
    admin_id = get_jwt_identity()
    data = request.get_json()
    forma_pagamento = data.get('forma_pagamento')

    carrinho = carrinhos_em_memoria.get(admin_id)
    if not carrinho or not carrinho['itens']:
        return jsonify({"message": "Carrinho vazio ou não iniciado."}), 400

    # Verifica se o pagamento foi aprovado
    if forma_pagamento == 'Pix' and carrinho.get('status_pagamento') != 'APROVADO':
        return jsonify({"message": "Pagamento Pix não aprovado ainda."}), 400

    cliente = Clientes.query.get(carrinho['cliente_id'])
    if not cliente:
        return jsonify({"message": "Cliente inválido."}), 400

    total = sum(item['subtotal'] for item in carrinho['itens'])

    # Atualiza estoque antes de salvar
    for item in carrinho['itens']:
        produto = Produtos.query.get(item['produto_id'])
        if not produto or produto.quantidade_estoque < item['quantidade']:
            return jsonify({"message": f"Estoque insuficiente para o produto '{item['nome']}'."}), 400
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

    return jsonify({
        "message": "Venda finalizada com sucesso!",
        "venda_id": str(nova_venda.id),
        "total": total
    }), 200
