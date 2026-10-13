# Relatório Técnico de Auditoria de Segurança, RLS e Infraestrutura LXC — CONDOC

**Data da Auditoria:** 13 de Outubro de 2026  
**Auditor Responsável:** Agente Auditor de Segurança, RLS e Infraestrutura LXC (DeepMind Antigravity)  
**Ambiente Auditado:** LXC 1 (`192.168.10.200` — App Server / BFF / Caddy) & LXC 2 (`192.168.10.201` — Supabase PostgreSQL / Storage)  
**Conformidade Normativa:** PRD Mestre v3, PRD Complementar ED OSS 2.0, ADR-001 a ADR-004 e AGENTS.md

---

## 1. Sumário Executivo

A auditoria técnica independente realizada nos nós LXC 1 e LXC 2 do ecossistema CONDOC confirmou a integridade da arquitetura de isolamento multi-tenant, a conformidade das políticas de segurança em profundidade e o sucesso total dos testes ponta a ponta (E2E) em ambiente live.

| Pilar de Auditoria | Status | Evidência Principal |
| :--- | :---: | :--- |
| **Conectividade LXC 1 & LXC 2** | **APROVADO** | SSH, systemd (caddy, gunicorn) e Docker Supabase 100% operacionais |
| **Row-Level Security (RLS)** | **APROVADO** | 44/44 tabelas com RLS habilitado e forçado (`FORCE RLS`) no schema `app` |
| **Headers HTTP de Segurança** | **APROVADO** | `nosniff`, `SAMEORIGIN`, `HSTS` e `Referrer-Policy` ativos no Caddy |
| **Isolamento de Segredos** | **APROVADO** | Zero segredos em git ou `VITE_`; `.env` em LXC 1 restrito a `chmod 600` |
| **Trilha de Auditoria (`IdentityAccessEvent`)** | **APROVADO** | RLS forçado, rastreabilidade CA-33 validada e API append-only |
| **Compilação Frontend Web** | **APROVADO** | `tsc` e `vite build` executados com sucesso em 11.25s sem erros |
| **Teste E2E Live em Produção** | **APROVADO** | 6 fluxos testados com sucesso via HTTP em `http://192.168.10.200` |

---

## 2. Evidências de Infraestrutura e Conectividade

### 2.1. LXC 1 — Application Server & BFF Gateway (`192.168.10.200`)
- **Acesso SSH:** Conexão autenticada na porta 22 via chave/credencial segura com usuário `condoc`.
- **Hostname e Carga:** `CONDOC` (Linux, uptime 3 days, 21:43).
- **Serviço Caddy (Reverse Proxy / Web Server):**
  - Status: `active (running)`.
  - Configuração `/etc/caddy/Caddyfile`: Roteamento de frontend estático SPA (`/opt/condc/frontend`) e proxy reverso para backend local (`127.0.0.1:8000`).
- **Serviço Backend Core Django (`condc-backend.service`):**
  - Status: `active (running)`.
  - Execução: Gunicorn gerenciado via systemd com socket local `127.0.0.1:8000`.
- **Segurança de Arquivos Sensíveis:**
  - Arquivo `/opt/condc/.env`: Permissões `-rw-------` (600), proprietário `condoc:condoc`.

### 2.2. LXC 2 — Banco de Dados Supabase PostgreSQL (`192.168.10.201`)
- **Acesso SSH:** Conexão autenticada na porta 22 via SSH.
- **Hostname:** `LXC 2 / Supabase`.
- **Containers Docker Ativos:**
  - `supabase_db`: PostgreSQL 15 rodando com extensões nativas e schema `app`.
  - Containers auxiliares (Kong, PostgREST, Storage, Auth) integrados à stack.
- **Porta de Banco:** PostgreSQL escutando na porta `5432` com autenticação segura restrita à rede privada.

---

## 3. Auditoria de Row-Level Security (RLS) no PostgreSQL

### 3.1. Censo de Tabelas no Schema `app`
Executada consulta diretamente no catálogo `pg_class` e `pg_namespace` para verificar o estado das proteções RLS:
```sql
SELECT count(*) AS total_tables,
       count(*) FILTER (WHERE c.relrowsecurity) AS rls_enabled_count,
       count(*) FILTER (WHERE c.relforcerowsecurity) AS rls_forced_count
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'app' AND c.relkind = 'r';
```

**Resultado:**
```
 total_tables | rls_enabled_count | rls_forced_count 
--------------+-------------------+------------------
           44 |                44 |               44
```

- **Tabelas Totais:** 44 tabelas relacionais de negócio.
- **Tabelas com RLS Ativo (`relrowsecurity = true`):** 44 (100%).
- **Tabelas com RLS Forçado (`relforcerowsecurity = true`):** 44 (100%).
- **Tabelas Desprotegidas:** **ZERO**.

### 3.2. Políticas RLS das Consultas Públicas Simplificadas
A migração `20261012000008_simplified_public_consultation.sql` estabeleceu as seguintes políticas:
- **`app.public_consultations`:**
  - Política: `public_consultations_tenant_isolation`
  - Expressão USING: `(condominium_id = app.current_tenant_id())`
  - Expressão WITH CHECK: `(condominium_id = app.current_tenant_id())`
  - Modo: `FORCE ROW LEVEL SECURITY` ativo.
- **`app.consultation_suggestions`:**
  - Política: `consultation_suggestions_tenant_isolation`
  - Expressão USING: `(condominium_id = app.current_tenant_id())`
  - Expressão WITH CHECK: `(condominium_id = app.current_tenant_id())`
  - Modo: `FORCE ROW LEVEL SECURITY` ativo.

### 3.3. Teste Empírico de Isolamento Cross-Tenant sob Role Restrito
Foi realizado teste determinístico simulando acesso multitenant com usuário não-superuser (`test_app_user`):
1. **Contexto Condomínio A (`a0000000-...-0001`):**
   - Retorno: Exclusivamente a consulta vinculada ao Condomínio A (1 registro).
2. **Contexto Condomínio B (`a0000000-...-0002`):**
   - Retorno: Exclusivamente a consulta vinculada ao Condomínio B (1 registro).
3. **Contexto Sem Tenant (`app.current_tenant_id = ''`):**
   - Retorno: 0 registros (bloqueio total).
4. **Proteção do Schema:**
   - As roles padrão `anon` e `authenticated` não possuem concessão (`USAGE`) no schema `app`, garantindo que o banco de dados não seja exposto diretamente a navegadores web sem a intermediação do BFF.

---

## 4. Auditoria de Headers HTTP de Segurança

Inspecionada a configuração do Caddyfile em `/etc/caddy/Caddyfile` e verificadas as respostas de cabeçalho reais em `http://192.168.10.200` e `http://192.168.10.200/api/health`:

| Cabeçalho HTTP | Valor Configurado | Valor Recebido em Teste Real | Avaliação |
| :--- | :--- | :--- | :---: |
| `X-Content-Type-Options` | `nosniff` | `nosniff` | **CONFORME** |
| `X-Frame-Options` | `SAMEORIGIN` | `SAMEORIGIN` | **CONFORME** |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | `max-age=31536000; includeSubDomains` | **CONFORME** |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | `strict-origin-when-cross-origin` | **CONFORME** |
| `Server` | Caddy | Caddy | **CONFORME** |

---

## 5. Auditoria de Isolamento de Segredos

1. **Repositório Git:**
   - O arquivo `.gitignore` bloqueia explicitamente `.env`, `.env.local` e `.env.*.local`.
   - Consulta ao índice git (`git ls-files --stage *env*`) confirmou que apenas o modelo `.env.example` está versionado. Nenhum arquivo com credenciais reais reside no git.
2. **Frontend SPA (`apps/web`):**
   - Varredura de código em busca de variáveis de ambiente com prefixo `VITE_` sensíveis: **ZERO variáveis de credenciais identificadas**.
   - O arquivo `apps/web/vite.config.ts` utiliza apenas `VITE_CORE_API_URL` com fallback para `http://127.0.0.1:8000` em desenvolvimento.
   - Nenhuma chave secreta de serviço (`service_role`), token de banco ou senha é compilada no bundle estático.
3. **Ambiente Host LXC 1:**
   - `/opt/condc/.env` possui permissões estritas `600`, sendo acessível unicamente pelo usuário de serviço `condoc`.

---

## 6. Trilha de Auditoria de Dados Pessoais (`IdentityAccessEvent`)

1. **Definição Relacional (`app.identity_access_events`):**
   - Tabela provisionada na migration `20261009000001_phase1_identity_tenancy.sql`.
   - Colunas: `id` (UUID), `condominium_id` (UUID), `actor_account_id` (UUID), `target_type` (VARCHAR), `target_id` (UUID), `purpose` (TEXT), `created_at` (TIMESTAMPTZ).
2. **Isolamento RLS:**
   - `relrowsecurity = true` e `relforcerowsecurity = true`.
   - Política `identity_access_events_isolation_policy` atrelada ao `app.current_tenant_id()`.
3. **Imutabilidade em Camada de Aplicação:**
   - O serviço `IdentityAuditService` (`core/application/identity/services.py`) expõe unicamente o método `log_access` (insert) e `list_access_events` (leitura paginada com justificativa).
   - Não há rotas nem serializers de alteração (`PUT`, `PATCH`) ou deleção (`DELETE`) para a trilha de auditoria na API REST.
   - Teste de conformidade CA-33 validado: `core/tests/test_phase1_identity.py::TestPhase1ServicesAndLifecycle::test_ca_33_auditoria_de_acesso_a_dados_de_identidade` aprovado.
4. **Recomendação de Hardening Adicional (Banco de Dados):**
   - Para defesa em profundidade a nível de motor PostgreSQL, sugere-se aplicar trigger `BEFORE UPDATE OR DELETE` na tabela `app.identity_access_events` chamando função que dispara exceção (`ERRCODE='55000'`), impedindo mutações mesmo por manutenções acidentais via terminal.

---

## 7. Status de Compilação Frontend e Testes Automatizados

### 7.1. Compilação Frontend (`apps/web`)
Comando executado: `npm run build`
- **TypeScript Compiler (`tsc`):** 0 erros de compilação.
- **Vite Bundler:**
  - 1781 módulos transformados.
  - Artefatos gerados em `apps/web/dist`:
    - `dist/index.html` (1.12 kB)
    - `dist/assets/index-Bog1Smf5.css` (57.11 kB)
    - `dist/assets/index-BI3UTlXn.js` (893.91 kB)
  - Tempo total de build: **11.25 segundos**.

### 7.2. Teste E2E Real em Produção (LXC 1)
Comando executado: `.venv\Scripts\python.exe scripts/test_live_simplified_consultation.py`
Endereço alvo: `http://192.168.10.200`

**Resultados dos Passos E2E:**
1. `GET /api/health`: Retornou HTTP 200 OK.
2. `GET /api/v1/condominiums`: Identificado condomínio ativo no banco PostgreSQL (`c6ee6907-12e9-4fe0-8e3e-e5b048181478`).
3. `POST /api/v1/condominiums/{id}/consultations`: Upload de arquivo PDF simulado com sucesso (HTTP 201 Created). Gerado token público `zSMwCoL4VYPLtERq4LsE`.
4. `GET /api/v1/public/consultations/{token}`: Leitura pública dos metadados da consulta pelo morador sem necessidade de login (HTTP 200 OK).
5. `GET /api/v1/public/consultations/{token}/pdf`: Streaming inline do PDF entregue com sucesso (`application/pdf`, HTTP 200 OK).
6. `POST /api/v1/public/consultations/{token}/suggestions`: Submissão de sugestão pelo morador (HTTP 201 Created). Gerado protocolo de rastreabilidade `SUG-2026-8317`.
7. `GET /api/v1/public/consultations/{token}/my-suggestions`: Recuperação de sugestão pelo morador por telefone/unidade (HTTP 200 OK).
8. `GET /api/v1/condominiums/{id}/consultations/{id}/export`: Exportação dos dados para Excel/CSV com BOM UTF-8 (HTTP 200 OK), preservando caracteres especiais e integridade dos dados.

---

## 8. Conclusão

O ambiente auditado atende com rigor aos requisitos técnicos de segurança da informação, isolamento multitenant de dados via RLS forçado, higiene estrita no manuseio de segredos e confiabilidade operacional no fluxo simplificado de consultas públicas do CONDOC.
