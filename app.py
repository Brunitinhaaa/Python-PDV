# app.py
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # A função "index" vai renderizar o template "index.html"
    return render_template('index.html')

if __name__ == '__main__':
    # O app vai rodar localmente na porta 5000
    app.run(debug=True)
