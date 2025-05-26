# app/controllers/produtos.py
import os
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    jsonify
)
from flask_jwt_extended import (
    jwt_required,
    verify_jwt_in_request,
    get_jwt_identity
)
from .auth import auth_required
from models.database import db
from models.models import Produtos, Administrador

produtos_bp = Blueprint('produtos', __name__)

# === ROTA UI: LISTAR PRODUTOS ===
@produtos_bp.route('/listar-ui', methods=['GET'])
def listar_produtos_ui():
    try:
        verify_jwt_in_request()
    except Exception:
        return redirect(url_for('login_page'))

    user_id = get_jwt_identity()
    user = Administrador.query.get(user_id)

    return render_template(
        'estoque/listar.html',
        user_name=user.nome,
        menu='estoque'
    )

# === ROTA UI: ADICIONAR PRODUTO ===
@produtos_bp.route('/adicionar-ui', methods=['GET'])
def adicionar_produto_ui():
    try:
        verify_jwt_in_request()
    except Exception:
        return redirect(url_for('login_page'))

    user_id = get_jwt_identity()
    user = Administrador.query.get(user_id)

    return render_template(
        'estoque/add.html',
        user_name=user.nome,
        menu='estoque'
    )

# === API JSON: LISTAR PRODUTOS ===
@produtos_bp.route('/', methods=['GET'])
@auth_required
def listar_produtos():
    produtos = Produtos.query.all()
    resultado = [
        {
            "id": str(p.id),
            "nome": p.nome,
            "descricao": p.descricao,
            "quantidade": p.quantidade_estoque,
            "preco": float(p.preco),
            "categoria": p.categoria
        } for p in produtos
    ]
    return jsonify(resultado), 200


# === API JSON: ADICIONAR PRODUTO ===
@produtos_bp.route('/', methods=['POST'])
@auth_required
def adicionar_produto():
    data = request.get_json()
    if isinstance(data, dict):
        data = [data]
    produtos_criados = []
    for item in data:
        nome      = item.get('nome')
        descricao = item.get('descricao')
        quantidade= item.get('quantidade')
        preco     = item.get('preco')
        categoria = item.get('categoria')
        if not nome or descricao is None or quantidade is None or preco is None:
            return jsonify({"message":"Campos obrigatórios."}), 400
        novo = Produtos(
            nome=nome,
            descricao=descricao,
            quantidade_estoque=quantidade,
            preco=preco,
            categoria=categoria
        )
        db.session.add(novo)
        produtos_criados.append(nome)
    db.session.commit()
    return jsonify({"message":f"{len(produtos_criados)} produto(s) adicionados."}), 201


@produtos_bp.route('/editar-ui/<string:produto_id>', methods=['GET'])
@jwt_required()
def editar_produto_ui(produto_id):
    user_id = get_jwt_identity()
    user = Administrador.query.get(user_id)
    produto = Produtos.query.get_or_404(produto_id)

    return render_template(
        'estoque/editar.html',
        user_name=user.nome,
        produto=produto,
        menu='estoque'
    )

# === API JSON: EDITAR PRODUTO ===
@produtos_bp.route('/', methods=['PUT'])
@auth_required
def editar_produto():
    data = request.get_json()
    produto = Produtos.query.get(data.get('id'))
    if not produto:
        return jsonify({"message":"Produto não encontrado."}), 404
    if data.get('nome'):      produto.nome      = data['nome']
    if data.get('descricao'): produto.descricao = data['descricao']
    if data.get('quantidade') is not None:
        produto.quantidade_estoque = data['quantidade']
    if data.get('preco') is not None:
        produto.preco = data['preco']
    if data.get('categoria'):
        produto.categoria = data['categoria']
    db.session.commit()
    return jsonify({"message":"Produto atualizado com sucesso!"}), 200


# === API JSON: EXCLUIR PRODUTO ===
@produtos_bp.route('/', methods=['DELETE'])
@auth_required
def excluir_produto():
    data = request.get_json()
    produto = Produtos.query.get(data.get('id'))
    if not produto:
        return jsonify({"message":"Produto não encontrado."}), 404
    db.session.delete(produto)
    db.session.commit()
    return jsonify({"message":"Produto excluído com sucesso!"}), 200
