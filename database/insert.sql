INSERT INTO administradores (nome, email, senha_hash)
VALUES
    ('João Silva', 'joao.silva@email.com', 'senha_hash_123'),
    ('Maria Oliveira', 'maria.oliveira@email.com', 'senha_hash_456');

INSERT INTO clientes (nome, email, telefone, endereco)
VALUES
    ('Carlos Pereira', 'carlos.pereira@email.com', '(11) 91234-5678', 'Rua das Flores, 123, São Paulo, SP'),
    ('Ana Souza', 'ana.souza@email.com', '(11) 98765-4321', 'Avenida Paulista, 456, São Paulo, SP'),
    ('Pedro Costa', 'pedro.costa@email.com', '(11) 99876-5432', 'Rua dos Três Irmãos, 789, Campinas, SP');

INSERT INTO produtos (nome, descricao, preco, quantidade_estoque, categoria)
VALUES
    ('Camiseta Básica', 'Camiseta de algodão, confortável e de boa qualidade.', 39.99, 100, 'Roupas'),
    ('Caneca de Cerâmica', 'Caneca de cerâmica com estampa divertida.', 19.99, 200, 'Acessórios'),
    ('Tênis Esportivo', 'Tênis de corrida, leve e confortável.', 199.99, 50, 'Calçados');

-- Inserir venda 1
INSERT INTO vendas (administrador_id, cliente_id, itens, total, forma_pagamento)
VALUES
    (
        (SELECT id FROM administradores WHERE nome = 'João Silva'),
        (SELECT id FROM clientes WHERE nome = 'Carlos Pereira'),
        '[{"produto_id": 1, "quantidade": 2}, {"produto_id": 2, "quantidade": 1}]',
        99.97,  -- Total: 2 x Camiseta Básica + 1 x Caneca de Cerâmica
        'Cartão'
    );

-- Inserir venda 2
INSERT INTO vendas (administrador_id, cliente_id, itens, total, forma_pagamento)
VALUES
    (
        (SELECT id FROM administradores WHERE nome = 'Maria Oliveira'),
        (SELECT id FROM clientes WHERE nome = 'Ana Souza'),
        '[{"produto_id": 3, "quantidade": 1}]',
        199.99,  -- Total: 1 x Tênis Esportivo
        'Pix'
    );


