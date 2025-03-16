from sqlalchemy.dialects.postgresql import UUID
from models.database import db
from passlib.hash import pbkdf2_sha256

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