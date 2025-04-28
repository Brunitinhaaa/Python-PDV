import os
import requests
from dotenv import load_dotenv
import uuid 

load_dotenv()

def get_access_token():
    return os.getenv("MERCADO_PAGO_ACCESS_TOKEN")

def criar_pagamento_pix(valor, descricao, payer, external_reference):
    url = "https://api.mercadopago.com/v1/payments"
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4()) 
    }

    body = {
        "transaction_amount": valor,
        "description": descricao,
        "payment_method_id": "pix",
        "payer": payer,
        "external_reference": external_reference 
    }

    response = requests.post(url, json=body, headers=headers)
    data = response.json()

    if response.status_code == 201:
        return {
            "ticket_url": data['point_of_interaction']['transaction_data']['ticket_url'],
            "qr_code_base64": data['point_of_interaction']['transaction_data']['qr_code_base64']
        }
    else:
        raise Exception(f"Erro ao criar pagamento: {data}")
