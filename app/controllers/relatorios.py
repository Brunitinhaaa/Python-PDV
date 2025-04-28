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

    fig, axs = plt.subplots(2, 2, figsize=(10, 8), facecolor='#1e1e1e')

    # Evolução das Vendas
    datas = list(vendas_por_data.keys())
    totais = list(vendas_por_data.values())

    if vendas_por_data:
        df = pd.DataFrame(list(vendas_por_data.items()), columns=['Data', 'Total'])
        df['Data'] = pd.to_datetime(df['Data'])
        df = df.set_index('Data')
        
        data_min = df.index.min()
        data_max = df.index.max()

        if (data_max - data_min).days < 14:
            data_min -= pd.Timedelta(days=7)
            data_max += pd.Timedelta(days=7)

        idx = pd.date_range(data_min, data_max, freq='D')
        df = df.reindex(idx, fill_value=0)

        axs[0, 0].plot(df.index.strftime('%Y-%m-%d'), df['Total'], marker='o', color='#00ffcc', linewidth=2)
        axs[0, 0].set_title('Evolução das Vendas', color='white')
        axs[0, 0].tick_params(axis='x', rotation=45, labelcolor='white')
        axs[0, 0].tick_params(axis='y', labelcolor='white')
        axs[0, 0].set_facecolor('#2e2e2e')
    else:
        axs[0, 0].set_title('Sem dados de vendas', color='white')
        axs[0, 0].set_facecolor('#2e2e2e')

    # Formas de Pagamento
    labels = list(formas_pagamento.keys())
    sizes = list(formas_pagamento.values())
    wedges, texts, autotexts = axs[0, 1].pie(sizes, labels=labels, autopct='%1.1f%%', colors=['#ff6666', '#66b3ff', '#99ff99'])
    for text in texts + autotexts:
        text.set_color('white')
    axs[0, 1].set_title('Formas de Pagamento', color='white')

    # Produtos mais vendidos
    produtos_ordenados = sorted(produtos.items(), key=lambda x: x[1], reverse=True)[:5]
    nomes_produtos = [p[0] for p in produtos_ordenados]
    quantidades = [p[1] for p in produtos_ordenados]
    axs[1, 0].bar(nomes_produtos, quantidades, color='#ffcc00')
    axs[1, 0].set_title('Top 5 Produtos', color='white')
    axs[1, 0].tick_params(axis='x', rotation=45, labelcolor='white')
    axs[1, 0].tick_params(axis='y', labelcolor='white')
    axs[1, 0].set_facecolor('#2e2e2e')

    # Clientes que mais compram
    clientes_ordenados = sorted(clientes.items(), key=lambda x: x[1], reverse=True)[:5]
    nomes_clientes = [c[0] for c in clientes_ordenados]
    totais_clientes = [c[1] for c in clientes_ordenados]
    axs[1, 1].bar(nomes_clientes, totais_clientes, color='#6699ff')
    axs[1, 1].set_title('Top 5 Clientes', color='white')
    axs[1, 1].tick_params(axis='x', rotation=45, labelcolor='white')
    axs[1, 1].tick_params(axis='y', labelcolor='white')
    axs[1, 1].set_facecolor('#2e2e2e')

    for ax in axs.flat:
        ax.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()

    img_stream = BytesIO()
    plt.savefig(img_stream, format='png', facecolor=fig.get_facecolor())
    img_stream.seek(0)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFillColorRGB(0, 0, 0)
    c.rect(0, 0, letter[0], letter[1], fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.drawString(100, 750, "Relatório de Vendas Completo")
    c.drawImage(ImageReader(img_stream), 50, 250, width=500, height=400)
    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='relatorio_vendas.pdf', mimetype='application/pdf')
