# Venda Fashion (Server)

Repositório para hospedar a versão server do sistema de CLM desenvolvido em Python.

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
   * Comercial (Empresa): realiza gestão de relacionamento com o cliente
   * Representantes: realiza gestão de relacionamento com o cliente
- B2B (Business to Business) = Gestão de Pedidos de clientes
   * Lojistas: Realizam pedidos e acompanham devoluções
   * Representantes: Aprovam pedidos
   * Comercial (Empresa): Acompanham pedidos
- FPR (Finished Product Return) = Gestão de devolução de clientes
   * Comercial (Empresa): Tramitam e destinam as devoluções
- POS (Point Of Sale) = Gestão de Vendas Cliente x Consumidor
   * Lojistas realizam: gestão de vendas, gestão de estoque, gestão de contas a pagar, fluxo de caixa














Dentro do sistema o setor comercial da empresa consegue acompanhar toda a vida do cliente que foi movimentada por representantes.

Os lojistas conseguem ter acesso na plataforma B2B para realizar diretamente seus pedidos ou através de representantes. As devoluções são tratadas diretamente no sistema.

Representantes realizam a emissão de pedidos, gerencia informações dos clientes, gerencia oportunidades, gerencia calendário, realiza consultas ao mapa e movimenta o funil de vendas.

Comercial da empresa gerencia automações, gerencia funis, define metas, limita produtos, gerencia pedidos, realiza traduções no sistema, gerencia oportunidades, gerencia inforações dos clientes, realiza consultas ao mapa e movimenta funil de vendas.

