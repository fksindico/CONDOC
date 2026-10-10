# CONDC — Sistema de Gestão de Documentos Normativos Condominiais

O **CONDC** é uma plataforma especializada de apoio ao síndico, comissões e moradores para a elaboração, modernização, revisão colaborativa e publicação de minutas de **Convenção de Condomínio** e **Regimento Interno**.

O sistema transforma documentos jurídicos complexos em dispositivos digitais estruturados com rastreabilidade histórica granular, preservando a origem de cada alteração textual, garantindo a privacidade das contribuições dos moradores e assegurando a prerrogativa de publicação exclusiva do síndico ativo.

---

## 🚫 Restrições Inegociáveis de Escopo

O sistema possui limites mandatórios que **NÃO** podem ser violados:

1. **Vedação Eleitoral e Deliberativa:** O sistema **NÃO** realiza votação, eleições, apuração de votos, cálculo de quórum de assembleia, ponderação por fração ideal ou aprovação vinculante. O CONDC não substitui a assembleia geral nem realiza registro em cartório.
2. **"Concordo" Estritamente Consultivo:** A manifestação de concordância é um mecanismo consultivo de engajamento da comunidade sobre a redação publicada de um dispositivo. É intransferível entre alterações substanciais de redação.
3. **Privacidade Rigorosa (LGPD):** Sugestões e complementos nascem privados por padrão. Revisor, comissão e conselho analisam o teor sem acesso à identidade ou dados da unidade do morador. Acesso a dados de identidade exige papel administrativo com auditoria expressa.
4. **Publicação Exclusiva do Síndico Ativo:** Nenhuma automação, administrador delegado ou membro de comissão pode autorizar a publicação pública de uma sugestão ou minuta.
5. **Desacoplamento Contato x Residência:** A mera confirmação de e-mail/telefone valida apenas o canal e não comprova residência. A validação de residência reside exclusivamente no vínculo (`UnitMembership`), auditado documentalmente.

---

## 🏗️ Arquitetura de Referência

O CONDC adota uma arquitetura em 5 camadas lógicas de conteúdo:
1. **Arquivo Original (`SourceFile`):** Documento original imutável (PDF/DOCX) armazenado em Storage privado com hash SHA-256.
2. **Transcrição Conferida (`SourceTranscription`):** Extração textual OCR (Tesseract pt) conferida humanamente pelo síndico.
3. **Minuta em Evolução (`Provision` / `ProvisionRevision`):** Dispositivos normativos estruturados com UUID permanente e mapeamento explícito de origem (`OriginMapping` DePara).
4. **Contribuições Sociais e Decisão Editorial (`Suggestion` / `PublicationDecision`):** Sugestões privadas protocoladas, mesa editorial em 4 dimensões e publicação de versão sanitizada.
5. **Versões Congeladas e Artefatos Exportados (`DocumentSnapshot` / `ExportArtifact`):** Fotografias imutáveis da minuta e pacotes de exportação limpos (PDF, DOCX, DePara, JSON com manifesto).

### Stack Tecnológica
* **Frontend:** React 18+, TypeScript, Vite, Tailwind CSS, Tiptap.
* **Core / Backend:** Django 5+, Django REST Framework, arquitetura limpa (domain, application, infrastructure, api), BFF com cookies `HttpOnly`, `Secure` e `SameSite=Lax`.
* **Processamento Assíncrono:** Celery, Redis, OCR Tesseract e conversor documental isolado.
* **Banco de Dados & Autenticação:** Supabase PostgreSQL 15+ com Row Level Security (RLS) transacional, Supabase Auth (fonte única de identidade), Supabase Storage privado.
* **Contratos:** Schemas OpenAPI 3.1 e tipos TypeScript compartilhados (`packages/api-contracts`).

---

## 🖥️ Topologia de Produção (Proxmox VE LXC)

* **LXC 1 — Aplicação CONDC:**
  * Reverse Proxy (Caddy 2 / Nginx com TLS/SSL)
  * Frontend SPA React (arquivos estáticos compilados)
  * Core Django API (porta 8000)
  * Celery Workers (processamento assíncrono)
  * Redis Server (porta 6379 local)
* **LXC 2 — Supabase Local Stack:**
  * PostgreSQL 15 com RLS e extensões
  * Supabase Auth (GoTrue - porta 9999)
  * Supabase Storage Engine (porta 5000)
  * Kong Gateway (porta 8000)
  * Supabase Studio (porta 3000 restrita à rede administrativa)

---

## 📁 Estrutura de Diretórios

```text
├── AGENTS.md               # Diretrizes globais de governança para agentes de IA
├── apps/web/               # Aplicação frontend SPA
├── core/                   # Backend Core Django / DRF
│   ├── AGENTS.md           # Invariantes de domínio e regras de RLS
│   ├── domain/             # Entidades e regras de negócio puras
│   ├── application/        # Casos de uso e orquestração
│   ├── infrastructure/     # Adaptadores Supabase e models
│   └── api/                # Controllers, DTOs e serializers
├── workers/                # Celery workers e tarefas assíncronas
├── packages/api-contracts/ # Contratos OpenAPI e tipos TypeScript
├── supabase/               # Migrations SQL, seeds e testes pgTAP
├── infra/                  # Docker Compose, proxy e configurações de ambiente
├── scripts/                # Scripts operacionais (install, doctor, migrate, backup, restore)
└── docs/                   # Documentação técnica consolidada e ADRs
```

---

## 📖 Documentação Normativa

* **PRD Mestre v3.0 (Fonte Soberana):** [docs/prd/PRD_Mestre_v3.md](docs/prd/PRD_Mestre_v3.md)
* **Contrato da API:** [docs/api/Contrato_API_v3.md](docs/api/Contrato_API_v3.md)
* **Telas e Fluxos:** [docs/ui/Telas_Portal_Fluxos_v3.md](docs/ui/Telas_Portal_Fluxos_v3.md)
* **Arquitetura e Instalação:** [docs/deployment/Arquitetura_Instalacao_v3.md](docs/deployment/Arquitetura_Instalacao_v3.md)
* **Critérios de Aceite:** [docs/security/Criterios_Aceite_v3.md](docs/security/Criterios_Aceite_v3.md)
* **Matriz de Rastreabilidade:** [docs/security/Matriz_Rastreabilidade_v3.csv](docs/security/Matriz_Rastreabilidade_v3.csv)
* **Plano de Fases:** [docs/phases/Plano_Fases_v3.md](docs/phases/Plano_Fases_v3.md)
