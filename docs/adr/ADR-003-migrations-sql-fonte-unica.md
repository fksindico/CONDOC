# ADR-003: Migrations SQL em `supabase/migrations` como Fonte Única de DDL

## Status
Aprovado

## Data
2026-10-09

## Contexto
O Supabase utiliza migrações SQL nativas versionadas para definir esquemas, tabelas, índices, triggers, funções e políticas de Row Level Security (RLS). Por outro lado, o Django ORM tradicionalmente possui seu próprio sistema de migrações (`makemigrations`/`migrate`), o que criaria um cenário de "split-brain" (esquemas concorrentes e desalinhados entre o banco e o framework).

## Decisão
Estabelecer que a pasta **`supabase/migrations/` é a ÚNICA fonte de verdade do esquema de banco de dados (DDL)**:
1. Todas as alterações estruturais de tabelas, tipos ENUM, constraints, triggers, funções e políticas RLS serão escritas exclusivamente em scripts SQL sequenciais dentro de `supabase/migrations/`.
2. Os models do Django ORM no Core (`core/infrastructure/persistence/models.py`) serão configurados com a meta-opção `managed = False`.
3. Os models do Django serão utilizados apenas para mapeamento objeto-relacional, geração de consultas tipadas e serialização, nunca para criar ou alterar tabelas no banco de dados.
4. O script `scripts/migrate.sh` será o único executor responsável por aplicar as migrações no banco durante o deploy.

## Consequências
- **Positivas:**
  - Eliminação de conflitos entre migrações do Django e migrações do Supabase/PostgreSQL.
  - Controle preciso sobre sintaxe avançada do PostgreSQL (RLS, GIN indexes, pg_trgm, UUIDs v4, triggers atômicos).
  - Portabilidade total para ferramentas CLI do Supabase e runners de migração padronizados.
- **Negativas/Mitigações:**
  - Alterações nos models do Django devem ser acompanhadas manualmente de sua respectiva migration SQL em `supabase/migrations/`.
  - Devem ser criados testes automatizados que validem a correspondência entre os campos dos models Django e as colunas do banco de dados.
