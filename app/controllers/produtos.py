from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from .auth import auth_required
from models.database import db
from models.models import Produtos

produtos_bp = Blueprint('produtos', __name__)

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from .auth import auth_required
from models.database import db
from models.models import Produtos

produtos_bp = Blueprint('produtos', __name__)

# GET /produtos - Listar Produtos no Estoque
@produtos_bp.route('/', methods=['GET'])
@auth_required
def listar_produtos():
    produtos = Produtos.query.all()
    resultado = [
        {
            "id": str(p.id),
            "nome": p.nome,
            "quantidade": p.quantidade_estoque,
            "preco": float(p.preco)
        } for p in produtos
    ]
    return jsonify(resultado), 200

# POST /produtos - Adicionar Novo Produto ao Estoque
@produtos_bp.route('/', methods=['POST'])
@auth_required
def adicionar_produto():
    data = request.get_json()

    # Se for apenas um produto (dicionário)
    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list):
        return jsonify({"message": "Formato inválido. Envie um objeto ou uma lista de produtos."}), 400

    produtos_criados = []

    for item in data:
        nome = item.get('nome')
        descricao = item.get('descricao')
        quantidade = item.get('quantidade')
        preco = item.get('preco')

        if not nome or quantidade is None or preco is None or not descricao:
            return jsonify({"message": "Nome, descrição, quantidade e preço são obrigatórios."}), 400
        if not isinstance(quantidade, int) or quantidade < 0:
            return jsonify({"message": "Quantidade deve ser um número inteiro positivo."}), 400
        if not isinstance(preco, (int, float)) or preco <= 0:
            return jsonify({"message": "Preço deve ser um número maior que zero."}), 400

        novo_produto = Produtos(
            nome=nome,
            descricao=descricao,
            quantidade_estoque=quantidade,
            preco=preco
        )
        db.session.add(novo_produto)
        produtos_criados.append({
            "nome": nome,
            "preco": preco,
            "quantidade": quantidade
        })

    db.session.commit()

    return jsonify({
        "message": f"{len(produtos_criados)} produto(s) cadastrado(s) com sucesso!",
        "produtos": produtos_criados
    }), 201

# PUT /produtos - Editar Produto no Estoque
@produtos_bp.route('/', methods=['PUT'])
@auth_required
def editar_produto():
    data = request.get_json()
    produto_id = data.get('produto_id')
    produto = Produtos.query.get(produto_id)

    if not produto:
        return jsonify({"message": "Produto não encontrado."}), 404

    nome = data.get('nome')
    quantidade = data.get('quantidade')
    preco = data.get('preco')

    if nome:
        produto.nome = nome
    if quantidade is not None:
        if not isinstance(quantidade, int) or quantidade < 0:
            return jsonify({"message": "Quantidade deve ser um número inteiro positivo."}), 400
        produto.quantidade_estoque = quantidade
    if preco is not None:
        if not isinstance(preco, (int, float)) or preco <= 0:
            return jsonify({"message": "Preço deve ser um número maior que zero."}), 400
        produto.preco = preco

    db.session.commit()

    return jsonify({
        "id": str(produto.id),
        "nome": produto.nome,
        "quantidade": produto.quantidade_estoque,
        "preco": float(produto.preco),
        "message": "Produto editado com sucesso!"
    }), 200


# DELETE /produtos - Excluir Produto do Estoque
@produtos_bp.route('/', methods=['DELETE'])
@auth_required
def excluir_produto():
    data = request.get_json()
    produto_id = data.get('produto_id')
    produto = Produtos.query.get(produto_id)

    if not produto:
        return jsonify({"message": "Produto não encontrado."}), 404

    db.session.delete(produto)
    db.session.commit()

    return jsonify({"message": "Produto excluído com sucesso!"}), 200