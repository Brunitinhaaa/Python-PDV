from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
import uuid
from models.database import db
from passlib.hash import pbkdf2_sha256
from datetime import datetime

class Administrador(db.Model):
    __tablename__ = 'administradores'

    id = db.Column(db.UUID, primary_key=True, default=db.func.gen_random_uuid())
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False) 

    def __init__(self, nome, email, senha):
        self.nome = nome
        self.email = email
       
        self.senha_hash = pbkdf2_sha256.hash(senha, rounds=1000000) 

    def verify_password(self, senha):
        return pbkdf2_sha256.verify(senha, self.senha_hash)
    
class Clientes(db.Model):
    __tablename__ = 'clientes'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    endereco = db.Column(db.String(255), nullable=False)

    def __init__(self, nome, email, telefone, endereco):
        self.nome = nome
        self.email = email
        self.telefone = telefone
        self.endereco = endereco
    
class Vendas(db.Model):
    __tablename__ = 'vendas'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    administrador_id = db.Column(UUID(as_uuid=True), db.ForeignKey('administradores.id'), nullable=False)
    cliente_id = db.Column(UUID(as_uuid=True), db.ForeignKey('clientes.id'), nullable=False)
    data_venda = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    itens = db.Column(db.JSON, nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    forma_pagamento = db.Column(db.String(50), nullable=False)

    administrador = db.relationship('Administrador', backref=db.backref('vendas', lazy=True))
    cliente = db.relationship('Clientes', backref=db.backref('vendas', lazy=True))

    def __init__(self, administrador_id, cliente_id, itens, total, forma_pagamento):
        self.administrador_id = administrador_id
        self.cliente_id = cliente_id
        self.itens = itens
        self.total = total
        self.forma_pagamento = forma_pagamento

class Produtos(db.Model):
    __tablename__ = 'produtos'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    quantidade_estoque = db.Column(db.Integer, nullable=False)
    categoria = db.Column(db.String(100))

    def __init__(self, nome, descricao, preco, quantidade_estoque, categoria=None):
        self.nome = nome
        self.descricao = descricao
        self.preco = preco
        self.quantidade_estoque = quantidade_estoque
        self.categoria = categoria

    def atualizar_estoque(self, quantidade):
        if self.quantidade_estoque + quantidade < 0:
            raise ValueError("Quantidade insuficiente no estoque.")
        self.quantidade_estoque += quantidade

    