from flask import Flask, render_template, request
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import (
    jwt_required,
    JWTManager,
    get_jwt_identity
)  
from models.database import db
from models.models import Administrador
from config import Config
from dotenv import load_dotenv

from controllers.admin import administradores_bp
from controllers.vendas import vendas_bp
from controllers.produtos import produtos_bp
from controllers.relatorios import relatorios_bp

load_dotenv() 

app = Flask(
    __name__,
    static_folder='frontend_web/static',
    template_folder='frontend_web/templates'
)

CORS(app, supports_credentials=True)

app.config.from_object(Config)

db.init_app(app)
jwt = JWTManager(app)

app.register_blueprint(administradores_bp, url_prefix='/admin')
app.register_blueprint(vendas_bp, url_prefix='/vendas')
app.register_blueprint(produtos_bp, url_prefix='/produtos')
app.register_blueprint(relatorios_bp, url_prefix='/relatorios')

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/home')
@jwt_required()
def home_page():
    user_id = get_jwt_identity()
    user = Administrador.query.get(user_id)
    return render_template('home.html', user_name=user.nome, menu='home')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("Webhook recebido:", data)

    if data.get('type') == 'payment':
        pagamento_id = data['data']['id']

        import requests
        from utils.mercado_pago import get_access_token

        url = f"https://api.mercadopago.com/v1/payments/{pagamento_id}"
        headers = {"Authorization": f"Bearer {get_access_token()}"}
        response = requests.get(url, headers=headers)
        pagamento = response.json()

        print("Detalhes do pagamento:", pagamento)

        if pagamento.get('status') == 'approved':
            admin_id = pagamento.get('external_reference')
            
            from controllers.vendas import carrinhos_em_memoria
            
            carrinho = carrinhos_em_memoria.get(admin_id)
            if carrinho:
                carrinho['status_pagamento'] = 'APROVADO'
                print(f"Carrinho do admin {admin_id} atualizado para APROVADO!")

    return 'OK', 200

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000, debug=False)