# Prompt — CONDOC banco Supabase self-hosted DB-1.0

Leia AGENTS raiz/Core e PRD mestre/ED-OSS-2.0, depois docs/Modelo_Dados_Supabase_DB_1_0.md e todas migrations deste pacote.

Objetivo: adaptar o desenho ao repositório/instância self-hosted autorizada, preservar dados e implementar o núcleo documental/privacidade. Não usar Cloud, pacote Pro ou banco paralelo. Nenhuma votação/quórum.

1. Inventarie schema/release/roles/grants/migrations/ORM/dados e produza gap. Estes SQLs são para base nova: em existente crie migration incremental, não sobrescreva.
2. Verifique FKs, índices, roles/owner/search_path e fonte única SQL; models Django domínio managed=False.
3. Homologue em banco descartável com Auth/Storage reais de teste; não diga testado por haver SQL.
4. Contexto GUC só do Core validado, transaction-local; nunca liberar credencial runtime a cliente nem confiar header de ator/tenant.
5. Preserve ACL privada sem grants diretos runtime; implemente rotinas estreitas de provisionamento/gestão com autorização e audit. Não solucionar conectando como owner/postgres.
6. Complete validators de gramática/ref/style/note/snapshot e transações. Snapshot não latest.
7. Implemente suites com fixtures de tenants/contas/roles, testes allow/deny e invariantes, incluindo pool/suspensão/identity/snapshots.
8. Participação/convites/sugestões ainda são extensão: não declare portal completo; planeje migrations com autoria privada/publicação por síndico.
9. Valide backup DB+objetos e operação das duas LXC sem paths/hosts fixos.
10. Sem dados reais, migrations destrutivas/produção/SSH/DNS sem autorização; backup/rollback antes de risco.

Entregue inventário/gap/ADRs, migrations adaptadas, contratos Core, testes e resultados reais, pendências e plano de implantação. Smoke test sozinho não é homologação. Hash/ZIP verificado não é SQL executado.
