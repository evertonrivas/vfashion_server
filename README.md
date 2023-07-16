# Bee2Bee (Server)

Repositório para hospedar o backend do sistema de CLM desenvolvido em Python.

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
   * Comercial (Empresa): histórico de movimentação no sistema, avaliação FLIMV, prospecção e manutenção de informações
   * Representantes: realiza gestão de relacionamento com o clientes dele(a)
- B2B (Business to Business) = Gestão de Pedidos de clientes
   * Lojistas: Realizam pedidos, Cancelam pedidos e acompanham devoluções
   * Representantes: Aprovam pedidos, Acompanham situação de pedido
   * Comercial (Empresa): Acompanham e gerenciam pedidos
- FPR (Finished Product Return) = Gestão de devolução de clientes
   * Comercial (Empresa): Tramitam e destinam as devoluções
- SCM (Sales Calendar Manager) = Gestão de Calendário comercial e Orçamento
   * Comercial (Empresa): Centro de controle para acompahamento de vendas e orçamentos
- FCM (Financial Customer Manager) = Gestão Financeira do Cliente
   * Financeiro (Empresa): gestão de pagamentos, emissão de boletos, regras de avaliação
