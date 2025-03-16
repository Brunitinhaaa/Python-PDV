CREATE TABLE administradores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL
);

CREATE TABLE clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    endereco TEXT
);

CREATE TABLE produtos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    preco DECIMAL(10, 2) NOT NULL,
    quantidade_estoque INT NOT NULL,
    categoria VARCHAR(100)
);

CREATE TABLE vendas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    administrador_id UUID REFERENCES administradores(id) ON DELETE CASCADE,
    cliente_id UUID REFERENCES clientes(id) ON DELETE CASCADE,
    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    itens JSONB NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    forma_pagamento VARCHAR(50) NOT NULL
);

CREATE TABLE relatorios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filtros JSONB,
    data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    formato VARCHAR(50)
);
