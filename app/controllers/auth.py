from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps

def auth_required(fn):
    @wraps(fn) 
    @jwt_required()  
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()

        if not user_id:
            return jsonify({"message": "Usuário não autenticado."}), 401

        return fn(*args, **kwargs)

    return wrapper

