# ADR-001: Supabase como Plataforma de Persistência, Autenticação e Storage

## Status
Aprovado

## Data
2026-10-09

## Contexto
O sistema CONDC requer uma infraestrutura robusta de banco de dados relacional com suporte a Row Level Security (RLS), autenticação segura de usuários com suporte a MFA, e armazenamento seguro e privado de documentos originais digitalizados e artefatos de exportação. O sistema precisa suportar tanto instâncias em nuvem (Supabase Cloud) quanto instalações self-hosted locais em servidores virtuais (ex: Proxmox VE LXC).

## Decisão
Adotar o **Supabase** como plataforma integrada para:
1. **Banco de Dados:** PostgreSQL 15+ com extensões criptográficas e RLS ativado em 100% das tabelas de negócio.
2. **Autenticação:** Supabase Auth (GoTrue) como a **única** autoridade de identidade e credenciais de acesso, sem criação de senhas paralelas no backend Django.
3. **Armazenamento:** Supabase Storage com buckets privados (`source-documents`, `export-artifacts`) e URLs temporárias assinadas para visualização segura.
4. O Core Django acessará o Supabase via PostgreSQL nativo para persistência de dados e via cliente REST oficial/GoTrue para validação e emissão de tokens de autenticação.

## Consequências
- **Positivas:**
  - Modelo relacional unificado e compatível com migração entre Supabase Cloud e self-hosted.
  - Supabase Auth elimina o risco de vazamento de senhas locais no banco da aplicação.
  - Políticas de RLS reforçam a segurança multi-tenant no nível mais profundo do banco.
- **Negativas/Mitigações:**
  - O Core backend deve gerenciar rigorosamente o ciclo de vida dos tokens e sincronizar o estado da conta local (`Account`) com a identidade do Supabase Auth.
  - Para instalações self-hosted (LXC 2), a stack do Supabase deve ser mantida via Docker Compose com health checks automatizados.
