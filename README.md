# Venda Fashion (Server)

Repositório para hospedar a versão server do sistema de CLM desenvolvido em Python.

A documentação e demo da API podem ser vistos em:
https://evertonrivas.pythonanywhere.com/

Possui 6 níveis de acesso sendo:
1. Administrador: possui acesso em todos os sistemas.
2. Lojista: apenas sinaliza devoluções e pedidos.
3. Financeiro: consegue criar regras financeiras, bloqueia ou desbloqueia clientes e cancela pedidos.
4. Representante: relaiza pedidos, aprova ou desaprova pedidos
5. Comercial (Empresa): gerencia a vida do representante e/ou lojista e condições de pedidos.
6. Usuário: realiza acesso simplificado aos sistemas (ainda por definir)

O sistema consiste em uma solução web para gestão do ciclo de vida do cliente. 

Em termos de funcionalidade o sistema está dividido em:
- CRM (Customer Relationship Management) = Gestão de relacionamento com o cliente
   * Comercial (Empresa): realiza gestão de relacionamento com o cliente, gestão de zondas de atuação, movimentações em funis de vendas
   * Representantes: realiza gestão de relacionamento com o cliente
- B2B (Business to Business) = Gestão de Pedidos de clientes
   * Lojistas: Realizam pedidos e acompanham devoluções
   * Representantes: Aprovam pedidos
   * Comercial (Empresa): Acompanham e gerenciam pedidos
- FPR (Finished Product Return) = Gestão de devolução de clientes
   * Comercial (Empresa): Tramitam e destinam as devoluções
- POS (Point Of Sale) = Gestão de Vendas Cliente x Consumidor
   * Lojistas realizam: gestão de vendas, gestão de estoque, gestão de contas a pagar, fluxo de caixa