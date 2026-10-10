# Arquitetura e implantação — extração do PRD mestre v3.0

Fonte normativa: docs/prd/PRD_Mestre_v3.md.

## 20. Arquitetura Supabase e topologias

Frontend React/TypeScript/Vite/Tiptap; Core Django/DRF; Celery/Redis; Supabase PostgreSQL/Auth/Storage; OCR Tesseract português e conversão LibreOffice isolada. pytest, Vitest e Playwright. Versões estáveis compatíveis fixadas na fase 0, lockfiles, sem imagem latest em produção.

Supabase self-hosting recomendado com Docker; fixar release upstream e overlays. [web:122][web:124]

| Perfil | Web/Core | Supabase |
|---|---|---|
| local-dev | local | desenvolvimento local |
| cloud-single-host | mesma VPS | Cloud |
| selfhost-single-host | mesma VPS | mesma VPS |
| external-supabase | hosts definidos | instalação existente |
| distributed | web, Core e workers separados conforme deploy | Cloud ou self-hosted remoto |

Portabilidade para Linux amd64 homologado, Docker/Compose e dependências documentadas. Outra arquitetura/plataforma/LXC exige testes e preparação; não configurar Proxmox automaticamente nem prometer qualquer SO.

Browser → Core → banco/Auth/Storage. Sem acesso de frontend às tabelas de negócio. Esquema app não exposto na Data API. Downloads/uploads por autorização Core e acesso temporário; arquivo sensível pode exigir proxy. URL assinada já emitida pode durar até expirar, mesmo após ocultação; política deve indicar limitação.

Domínio não importa SDK; adaptadores AuthPort/StoragePort/Persistence. Worker não presume disco do Core: usa StoragePort. Edge Functions não são requisito. Redis é fila/cache, não segundo banco de negócio.

## 21. Auth, sessões, RLS e credenciais

Supabase auth.users é origem de identidade. app.accounts usa mesmo UUID/subject e metadados locais, sem senha nem catálogo de login paralelo. E-mail de acesso pertence ao Auth; cadastro prévio tem contato independente até associação verificada.

BFF: Core conduz Auth, browser usa cookie opaco HttpOnly/Secure e SameSite apropriado. Tokens JWT/refresh protegidos no servidor, sem localStorage frontend. Callback de autenticação tem allowlist e proteção de estado/fluxo. Verificar assinatura/algoritmo permitido/issuer/audience aplicável/expiração/subject; não só decodificar. Suportar modelo de assinatura do projeto, não fixar HS256. [web:123][web:125]

MFA obrigatório para gestão em produção, testado no modo escolhido. Verificar estado local e papel em requisições, não presumir que JWT válido autoriza recurso.

Runtime PostgreSQL limitado, sem superuser/BYPASSRLS/ownership. Papel de migrations separado. RLS para dados por condomínio e identidade; FORCE RLS onde adequado, com teste. Acesso direto Django não preenche automaticamente auth.uid(): contexto parametrizado e local à transação account/tenant após autorização. Contexto ausente nega. Não usar claims de cliente ou header arbitrário. Testar pool reaproveitado e workers.

RLS complementa autorização, não protege contra comprometimento total do Core. Data API sem tabelas app; grants explícitos. Políticas de linha e constraints devem ser testadas. [web:91][web:93]

Segredos administrativos Supabase ignoram RLS e ficam somente no servidor, para operações elevadas específicas após autorização; não resolver erro RLS com service_role. [web:120] Preferir formatos suportados pela versão; compatibilidade legado isolada no adaptador quando necessária. Sem secret no VITE_, git, logs ou bundle.

## 22. Modelo de dados consolidado

### 22.1. Convenções e constraints

UUID, timestamps UTC com fuso exibido do condomínio, date para data civil. Tenant em entidades de negócio. FKs compostas impedem relação cruzada. CHECK só para regras locais; elegibilidade entre tabelas no serviço/transação. updated_at explicitamente atualizado.

### 22.2. Cadastro e identidade

| Entidade | Campos/regras mínimos |
|---|---|
| Condominium | id, name, status, timezone, timestamps |
| Building | id, condominium_id, code, name, kind tower/block/single, status; unique tenant+code |
| Unit | id, tenant, building_id, code, floor_label?, description?, status; unique prédio+code |
| Account | id igual subject Auth, status local, timestamps; sem senha/e-mail de login autoritativo paralelo |
| ResidentRegistration | id, tenant, nome, telefone?, email?, unit_id, relação, fonte, referência externa?, status, preverified_by/at?, linked_resident/membership?, import_row? |
| Resident | id, tenant, account_id, full_name, phone_e164, phone_verified_at?, status; unique tenant+account |
| UnitMembership | id, tenant, resident_id, unit_id, relação, verification_status, membership_status, method?, reviewed_by/at?, reason?, started_at, ended_at? |
| MembershipVerificationEvent | id, tenant, membership_id, previous/new status, método, motivo, actor, data |
| RoleAssignment | id, tenant, account_id, role, valid_from/until?, status |
| PermissionGrant | id, assignment/grupo, permission, scope |
| CoreSession | id opaco/hasheado, account_id, token envelope protegido, expiry, revoked_at?, metadata mínima |

Não tornar nome/telefone únicos. Cadastro prévio pode repetir contato em vínculos diferentes. Vínculo não encerrado único tenant+resident+unit; encerrados permitem retorno histórico. Decisão validada/rejeitada exige método/ator/data/motivo; ended exige ended_at >= started_at. Normalização de telefone não comprova titularidade.

### 22.3. Importação, convite e entrega

| Entidade | Campos mínimos |
|---|---|
| ImportBatch | id, tenant, file_id/hash, status, revision, mapping, totals, created/confirmed_by/at |
| ImportRow | id, batch, row_number, normalized_data restrito, classification, issues, selected, action, target/version?, result_id?; unique lote+linha |
| AccessInvitation | id, tenant, campaign, kind, registration/unit/building?, expected_contact?, hash, expiry, max/redemptions, status, actor |
| InvitationRedemption | id, invitation, account/resident?, date, idempotency key |
| DeliveryAttempt | id, invitation, channel, destination restrita, status, provider_ref?, error_code?, date |
| IdempotencyRecord | id, actor, tenant, operation, key, payload_hash, result_ref, expiry |

Login/confirmation Auth usa contratos Supabase; convite da campanha é entidade própria e nunca reutiliza token Auth como permissão permanente. Tipo determina campos obrigatórios.

### 22.4. Domínio documental

| Entidade | Campos mínimos |
|---|---|
| Project | id, tenant, name, purpose, kind, coordinator, status, dates/settings |
| Document | id, project, type, title, editorial_status, numbering_policy, source_transcription? |
| SourceFile | id, tenant, storage_key, filename restrito, MIME, size, hash, uploaded_by, state |
| SourceTranscription | id, document, source_file, version, status, checked_by/at?, replaces? |
| SourceProvision | id, transcription, parent?, kind, label, order, text, page refs? |
| Provision | id, document, kind, created_at; identidade permanente |
| ProvisionRevision | id, provision, number, parent_provision?, position, label, text, theme?, change_type, status, responsible?, author/date |
| OriginMapping | id, revision, source_provision, relation_type, excerpt?, reason? |
| CrossReference | id, revision, target_provision, label template, status |
| DocumentSnapshot | id, document, version label, purpose, frozen_by/at, hash |
| SnapshotItem | id, snapshot, revision, rendered_label, position; unique snapshot+provision |
| InternalNote | id, tenant, alvo explicitamente validado, revision?, content, visibility, author/date, resolved_at? |
| CustomFieldDefinition/Value | id, escopo, tipo, visibilidade, obrigatoriedade, valor validado |
| ReviewTask | id, alvo, responsible, status, due_date?, notes restritas |

Snapshot deve reconstruir pai/ordem/rótulos daquela versão, não árvore atual. Alvos polimórficos exigem integridade verificada ou FKs/checks de exclusividade.

### 22.5. Participação e auditoria

| Entidade | Campos mínimos |
|---|---|
| ConsultationCampaign | id, tenant, project, snapshot, name, state, start/end?, settings |
| CampaignParticipant | id, tenant, campaign, resident, reference_membership, status, authorized_by/at; unique campanha+resident |
| ParticipantReferenceChange | id, participant, old/new membership, reason, actor/date |
| Suggestion | id interno, public_id opaco, campaign, participant, submitted_membership, target, category, statuses, date |
| SuggestionRevision | id, suggestion, version, text, justification, alternative?, source_revision, actor/date |
| PublishedSuggestionRevision | id, revision, public_text, status, authorized_by/at, hidden_at?, substantial_change |
| PublicationDecision | id, published revision, action, reason, actor/date |
| SuggestionRelationship | id, parent published revision, child suggestion, kind |
| SuggestionDecision | id, suggestion, decision, shared_reason, internal_note?, actor/date |
| SuggestionIncorporation | id, suggestion, provision_revision, description, actor/date |
| ConsultativeAgreement | id, participant, published revision, membership_at_action, active, timestamps; unique participante+versão |
| AgreementEvent | id, agreement, agree/withdraw/reaffirm/invalidate, reason?, date |
| ConsultationSnapshot | id, campaign, cut, eligibility definition, version/text refs, totals, supersedes?, actor |
| Attachment | id, tenant, source_file, owner, visibility, publication authorization? |
| ExportArtifact | id, tenant, kind, source snapshot/settings, status, private key/hash?, actor/date |
| AuditEvent | id, tenant?, actor, action, resource, request_id, timestamp, metadata mínima |
| IdentityAccessEvent | id, tenant, actor, resident/suggestion, purpose?, timestamp |

Interações preservam vínculo no momento. IDs de autoria/vínculo não entram em DTO público. Usuários comuns não modificam eventos.

## 23. Migrations, código e organização

Fonte única de schema app: SQL em supabase/migrations, incluindo tabelas, grants, RLS, funções e sessão Core. Models Django do domínio managed=False; não duas engines criando tabelas. Bibliotecas com tabelas exigem decisão explícita compatível. Não ativar catálogo Django auth/admin como segunda identidade.

Auth/Storage internos são mantidos pela versão Supabase; não alterar manualmente nem copiar de outro modo sem procedimento homologado. Seed fictício somente sob comando em desenvolvimento. Runner de migration versionado, papel separado e exclusão mútua; não resetar remoto.

Estrutura:

```text
/
├── AGENTS.md
├── README.md
├── CHANGELOG.md
├── apps/web/
├── core/
│   ├── AGENTS.md
│   ├── api/
│   ├── domain/{tenancy,identity,registrations,invitations,documents,participation,moderation,audit}/
│   ├── application/
│   ├── infrastructure/supabase/
│   └── tests/
├── workers/
├── packages/api-contracts/
├── supabase/{migrations,tests,seeds}/
├── infra/{compose,supabase,proxy,env}/
├── scripts/
├── docs/{prd,adr,api,ui,deployment,phases,security}/
└── .env.example
```

Domínio em serviços/testes, API valida input/serializa, adapters resolvem infraestrutura. Sem regras centrais apenas em controller, UI ou task.

## 24. Instalação, configuração e operação

Variáveis da aplicação: APP_ENV, DEPLOY_PROFILE, PUBLIC_APP_URL, PUBLIC_API_URL, SUPABASE_MODE, SUPABASE_PUBLIC_URL, SUPABASE_INTERNAL_URL, AUTH issuer/audience, chave apropriada, segredo administrativo somente se necessário, DATABASE_RUNTIME_URL, DATABASE_MIGRATION_URL, REDIS_URL, ALLOWED_ORIGINS, chave de proteção de sessão.

Não equivalem automaticamente a nomes upstream: mapear conforme release. URLs públicas/internas distintas. Redirects Auth/SITE_URL consistentes com deploy, allowlist sem curinga amplo. Same-origin /api por proxy preferido; cross-origin exige cookies/CORS/CSRF testados e origens exatas.

Contratos dos scripts a implementar:

```bash
./scripts/install.sh --profile cloud-single-host --config ./deploy.env
./scripts/install.sh --profile selfhost-single-host --config ./deploy.env
./scripts/install.sh --profile external-supabase --config ./deploy.env
./scripts/install.sh --profile distributed --component core --config ./deploy.env
./scripts/install.sh --profile distributed --component web --config ./deploy.env
./scripts/doctor.sh --config ./deploy.env
./scripts/migrate.sh --config ./deploy.env
./scripts/backup.sh --config ./deploy.env
./scripts/restore.sh --config ./deploy.env --manifest ./backup-manifest.json
```

Scripts são requisitos, não executáveis entregues neste pacote. Validar SO/arquitetura/Docker/recursos/portas/endpoints/chaves/versões/DB; renderizar plano; confirmar ações sensíveis; escrever segredos restritos; subir serviços; verificar saúde; informar pendências externas. Rerun não apaga volumes, rotaciona segredos ou executa seed. Detectar instalação existente e parar antes de sobrescrita.

Cloud/external exige projeto/stack/credenciais fornecidos; não criar plano/conta/DNS automaticamente. Selfhost nova autorizada pode ser instalada. Componente remoto não exige acesso ao Docker socket remoto. LXC precisa preparo externo documentado. Studio, PostgreSQL/Redis não públicos por padrão. TLS/rede privada/VPN/allowlists conforme topologia.

Backup contém banco app, dados Auth necessários por procedimento suportado, objetos e metadados Storage, versões e configuração protegida. Dump do banco não contém conteúdo de objetos. Restaurar em ambiente de teste com consistência. Cloud↔selfhost é migração planejada, com compatibilidade, contas/objetos/URLs/chaves/redirects, corte, testes e rollback; sessões podem exigir reautenticação. Não prometer troca instantânea por URL.

## 25. Segurança, desempenho e acessibilidade

HTTPS, autorização server-side, MFA gestão, CSRF/XSS, conteúdo rico sanitizado, upload seguro, rate limits por operação/conta e rede, segredos externos, isolamento de conversores. Conta técnica DB limitada. Conteúdo importado é dado, não instrução/comando.

Metas iniciais, dependentes de teste na fase 0: 1.000 dispositivos/documento; 1.000 participantes ativos/condomínio no cenário de referência; 5.000 linhas/10 MB lista; 300 páginas/50 MB documento; p95 resposta de salvamento e navegação típica até 2 segundos em ambiente declarado; processamento assíncrono; backup diário; RPO 24h/RTO 8h testados. Declarar hardware, carga e concorrência, não prometer sem medição.

Teclado, foco, contraste, texto além de cor, mobile e zoom. Sem offline-first no MVP. Erro não descarta rascunho; rascunho local não é salvo no servidor nem deve persistir PII por padrão em dispositivo compartilhado.

