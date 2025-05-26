from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
from models.models import Vendas, Clientes
from sqlalchemy import func
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from reportlab.lib.utils import ImageReader
import matplotlib
matplotlib.use('Agg')
from pandas import date_range
import pandas as pd


relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/listar-ui', methods=['GET'])
def listar_relatorios_ui():
    try:
        verify_jwt_in_request()
    except Exception:
        return redirect(url_for('login_page'))
    
    user_id = get_jwt_identity()
    user = Administrador.query.get(user_id)
    
    return render_template(
        'relatorios/listagemRelatorios.html',
        user_name=user.nome,
        menu='relatorios'
    )

def aplicar_filtros(query, filtros):
    if filtros.get('dataInicio'):
        data_inicio = datetime.strptime(filtros['dataInicio'], '%Y-%m-%d')
        query = query.filter(Vendas.data_venda >= data_inicio)
    if filtros.get('dataFim'):
        data_fim = datetime.strptime(filtros['dataFim'], '%Y-%m-%d')
        query = query.filter(Vendas.data_venda <= data_fim)
    if filtros.get('precoMin'):
        query = query.filter(Vendas.total >= float(filtros['precoMin']))
    if filtros.get('precoMax'):
        query = query.filter(Vendas.total <= float(filtros['precoMax']))
    if filtros.get('formaPagamento'):
        query = query.filter(Vendas.forma_pagamento == filtros['formaPagamento'])
    if filtros.get('emailCliente'):
        query = query.join(Clientes).filter(Clientes.email == filtros['emailCliente'])
    return query

@relatorios_bp.route('/download', methods=['GET'])
@jwt_required()
def gerar_pdf():
    filtros = request.args
    query = Vendas.query
    query = aplicar_filtros(query, filtros)
    vendas = query.all()

    # Dados para Gráficos
    vendas_por_data = {}
    formas_pagamento = {}
    produtos = {}
    clientes = {}

    for venda in vendas:
        data_str = venda.data_venda.strftime('%Y-%m-%d')
        vendas_por_data[data_str] = vendas_por_data.get(data_str, 0) + float(venda.total)
        formas_pagamento[venda.forma_pagamento] = formas_pagamento.get(venda.forma_pagamento, 0) + float(venda.total)
        for item in venda.itens:
            produtos[item['nome']] = produtos.get(item['nome'], 0) + item['quantidade']
        clientes[venda.cliente.nome] = clientes.get(venda.cliente.nome, 0) + float(venda.total)

    # Estilo limpo: fundo branco e fontes escuras
    fig, axs = plt.subplots(2, 2, figsize=(10, 8), facecolor='white')

    # Evolução das Vendas
    if vendas_por_data:
        df = pd.DataFrame(list(vendas_por_data.items()), columns=['Data', 'Total'])
        df['Data'] = pd.to_datetime(df['Data'])
        df = df.set_index('Data')

        idx = pd.date_range(df.index.min() - pd.Timedelta(days=7), df.index.max() + pd.Timedelta(days=7), freq='D')
        df = df.reindex(idx, fill_value=0)

        axs[0, 0].plot(df.index.strftime('%Y-%m-%d'), df['Total'], marker='o', color='#3366cc', linewidth=2)
        axs[0, 0].set_title('Evolução das Vendas', fontsize=10)
        axs[0, 0].tick_params(axis='x', rotation=45)
    else:
        axs[0, 0].set_title('Sem dados de vendas')

    axs[0, 0].set_facecolor('white')

    # Formas de Pagamento
    axs[0, 1].pie(
        list(formas_pagamento.values()), 
        labels=list(formas_pagamento.keys()), 
        autopct='%1.1f%%', 
        colors=['#ff9999', '#99ccff', '#c2f0c2']
    )
    axs[0, 1].set_title('Formas de Pagamento', fontsize=10)

    # Top Produtos
    produtos_ordenados = sorted(produtos.items(), key=lambda x: x[1], reverse=True)[:5]
    nomes_produtos = [p[0] for p in produtos_ordenados]
    quantidades = [p[1] for p in produtos_ordenados]
    axs[1, 0].bar(nomes_produtos, quantidades, color='#ffcc66')
    axs[1, 0].set_title('Top 5 Produtos', fontsize=10)
    axs[1, 0].tick_params(axis='x', rotation=45)

    # Top Clientes
    clientes_ordenados = sorted(clientes.items(), key=lambda x: x[1], reverse=True)[:5]
    nomes_clientes = [c[0] for c in clientes_ordenados]
    totais_clientes = [c[1] for c in clientes_ordenados]
    axs[1, 1].bar(nomes_clientes, totais_clientes, color='#66b3ff')
    axs[1, 1].set_title('Top 5 Clientes', fontsize=10)
    axs[1, 1].tick_params(axis='x', rotation=45)

    for ax in axs.flat:
        ax.set_facecolor('white')
        ax.grid(True, linestyle='--', alpha=0.3)

    plt.tight_layout()
    img_stream = BytesIO()
    plt.savefig(img_stream, format='png', facecolor='white')
    img_stream.seek(0)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(0, 0, letter[0], letter[1], fill=1)

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(160, 770, "Relatório de Vendas - PDV Python")

    c.drawImage(ImageReader(img_stream), 50, 280, width=500, height=400)
    c.setFont("Helvetica", 9)
    c.drawString(50, 265, "Gráficos gerados com base nos filtros aplicados.")
    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='relatorio_vendas.pdf', mimetype='application/pdf')
