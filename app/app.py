from flask import Flask
from flask_jwt_extended import JWTManager
from models.database import db
from config import Config

from controllers.admin import administradores_bp
from controllers.vendas import vendas_bp
from controllers.produtos import produtos_bp
from controllers.relatorios import relatorios_bp

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
jwt = JWTManager(app)

app.register_blueprint(administradores_bp, url_prefix='/admin')

app.register_blueprint(vendas_bp, url_prefix='/vendas')

app.register_blueprint(produtos_bp, url_prefix='/produtos')

app.register_blueprint(relatorios_bp, url_prefix='/relatorios')

@app.route('/')
def hello_world():
    return 'API está funcionando!'

if __name__ == '__main__':
    app.run(debug=False)

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
            
            # Importa o carrinho em memória do vendas.py
            from controllers.vendas import carrinhos_em_memoria
            
            carrinho = carrinhos_em_memoria.get(admin_id)
            if carrinho:
                carrinho['status_pagamento'] = 'APROVADO'
                print(f"Carrinho do admin {admin_id} atualizado para APROVADO!")

    return 'OK', 200