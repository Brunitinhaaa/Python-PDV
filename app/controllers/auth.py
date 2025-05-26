from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from functools import wraps
from flask import jsonify

def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        print("Auth_required: iniciando verificação...")

        try:
            verify_jwt_in_request()
            print("Auth_required: JWT + CSRF OK")
        except Exception as e:
            print(f"Auth_required: erro -> {e}")
            return jsonify({"message": "Token inválido ou ausente."}), 401

        user_id = get_jwt_identity()
        print(f"Auth_required: user_id -> {user_id}")

        if not user_id:
            return jsonify({"message": "Usuário não autenticado."}), 401

        return fn(*args, **kwargs)

    return wrapper
