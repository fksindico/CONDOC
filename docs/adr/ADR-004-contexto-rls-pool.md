# ADR-004: Isolamento Transacional de RLS via `SET LOCAL` em Pools de Conexão

## Status
Aprovado

## Data
2026-10-09

## Contexto
O CONDC é uma plataforma multi-tenant isolada por condomínio. O PostgreSQL utiliza Row Level Security (RLS) para garantir que usuários de um condomínio não visualizem nem modifiquem dados de outro. No entanto, em aplicações web modernas com pools de conexão persistentes (ex: PgBouncer, pool de conexões do Django/psycopg), variáveis de sessão configuradas via `SET session_var = ...` persistem na conexão caso esta seja devolvida ao pool sem limpeza, gerando o risco crítico de vazamento de contexto entre requisições de tenants distintos.

## Decisão
Adotar o comando transacional **`SET LOCAL`** gerenciado por um Context Manager explícito no Core Django:
1. Ao abrir qualquer transação com o banco de dados que execute em nome de uma requisição autenticada, o backend executará:
   ```sql
   SET LOCAL app.current_tenant_id = '<condominium_uuid>';
   SET LOCAL app.current_account_id = '<account_uuid>';
   ```
2. O modificador `LOCAL` restringe o escopo das variáveis estritamente à transação corrente (`current transaction`). No momento do `COMMIT` ou `ROLLBACK`, as variáveis são automaticamente descartadas pelo PostgreSQL.
3. As funções SQL de avaliação de RLS (`app.current_tenant_id()`) retornarão `NULL` caso a transação não tenha definido as variáveis, forçando a recusa de acesso a qualquer registro protegido.
4. O usuário de banco da aplicação (`condc_runtime`) não possuirá privilégio de `BYPASSRLS`.
5. Serão implementados testes automatizados de integração que simulam conexões reaproveitadas de pool para garantir que nenhuma transação herde variáveis da anterior.

## Consequências
- **Positivas:**
  - Impossibilidade de vazamento de contexto de tenant entre requisições concorrentes ou sequenciais no pool de conexões.
  - Segurança de dados garantida na própria camada do motor do PostgreSQL, mesmo se uma consulta na aplicação omitir o filtro de condomínio.
- **Negativas/Mitigações:**
  - Todas as operações de leitura e escrita dependentes de RLS devem obrigatoriamente ser executadas dentro de um bloco transacional atômico (`transaction.atomic()` no Django) com o Context Manager de tenant ativo.
