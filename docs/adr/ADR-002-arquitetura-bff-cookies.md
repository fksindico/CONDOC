# ADR-002: Arquitetura Backend for Frontend (BFF) com Cookies Seguros

## Status
Aprovado

## Data
2026-10-09

## Contexto
O frontend React SPA precisa autenticar usuários de forma segura. O armazenamento de tokens de acesso JWT no `localStorage` ou `sessionStorage` do navegador é vulnerável a ataques de Cross-Site Scripting (XSS). Além disso, o frontend não deve ter conhecimento direto de chaves privilegiadas do Supabase nem acessar tabelas de negócio diretamente sem passar pelas regras e auditoria do Core Django.

## Decisão
Implementar o padrão **Backend for Frontend (BFF)** integrado ao Core Django:
1. O frontend comunica-se exclusivamente com os endpoints `/api/v1/` do Core Django.
2. A sessão do usuário é gerenciada por cookies opacos com as flags `HttpOnly`, `Secure` e `SameSite=Lax`.
3. O Core valida o cookie de sessão, gerencia os tokens de refresh do Supabase Auth e injeta o contexto do usuário na requisição.
4. O Core implementa proteção anti-CSRF utilizando tokens padrão com validação em métodos de mutação (POST, PUT, PATCH, DELETE).

## Consequências
- **Positivas:**
  - Impossibilidade de exfiltração de tokens de autenticação via scripts maliciosos injetados no navegador (XSS).
  - Todas as regras de negócio, limites de tentativas, moderação e auditoria são aplicadas centralizadamente no servidor.
  - O frontend permanece desacoplado dos detalhes internos de autenticação e banco de dados.
- **Negativas/Mitigações:**
  - O Core backend precisa lidar com a rotação de refresh tokens e a manutenção da sessão segura na camada de proxy e cookies.
