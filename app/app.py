from flask import Flask
from flask_jwt_extended import JWTManager
from models.database import db
from config import Config

from controllers.admin import administradores_bp
from controllers.vendas import vendas_bp

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
jwt = JWTManager(app)

app.register_blueprint(administradores_bp, url_prefix='/admin')

app.register_blueprint(vendas_bp, url_prefix='/vendas')

@app.route('/')
def hello_world():
    return 'API está funcionando!'

if __name__ == '__main__':
    app.run(debug=True)
