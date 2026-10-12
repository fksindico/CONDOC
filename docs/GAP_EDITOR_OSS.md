# GAP Analysis — CONDOC Editor Normativo ED-OSS-2.0

**Data:** 12/10/2026  
**Versão:** 1.0  
**Status:** Aprovado  
**Documento Base:** PRD Mestre v3.0 e PRD Complementar ED-OSS-2.0 (`docs/prd/PRD_Complementar_ED_OSS_2_0.md`)  

---

## 1. Sumário Executivo

O presente documento consolida a análise de aderência (Gap Analysis) do sistema CONDOC em relação às especificações do **PRD Complementar ED-OSS-2.0**.
O objetivo central é validar a transição definitiva para uma arquitetura **100% Open Source / Self-Hosted**, eliminando qualquer dependência de pacotes comerciais fechados (`@tiptap-pro/*`), licenças privadas pagas ou serviços em nuvem (SaaS) para conversão documental.

O sistema adota a estratégia canônica de **Dualidade de Modo**:
1. **Edição Estruturada em Fluxo Contínuo:** Tiptap Core MIT com extensões semânticas normativas próprias (`CondocNormativeFlow`, `CondocPageBreak`, `CondocNoteReference`).
2. **Visualização Canônica e Artefatos Finais:** Pipeline local de renderização via `python-docx` + `LibreOffice Headless` local (`soffice --headless`), gerando o DOCX definitivo e o PDF derivado idêntico a partir do mesmo DOCX, com manifesto criptográfico SHA-256 selado.

---

## 2. Inventário de Componentes e SBOM Atual

### 2.1. Frontend (`apps/web`)
- **Framework:** React 18.3.1 + TypeScript 5.6.3 + Vite 5.4.9
- **Estilização:** TailwindCSS 3.4.14 + Design System `ui-ux-pro-max` (Authority Navy `#1E3A8A` / Trust Gold `#B45309`)
- **Editor:** `@tiptap/core` 2.8.0, `@tiptap/pm` 2.8.0, `@tiptap/react` 2.8.0, `@tiptap/starter-kit` 2.8.0 (**Licença MIT**)
- **Dependências @tiptap-pro:** **ZERO (0)**. Nenhuma dependência comercial ou registro privado presente.
- **Roteamento & Estado:** React Router 6.27.0, TanStack React Query 5.59.0

### 2.2. Backend Core (`core/`)
- **Framework:** Django 5.2 + Django REST Framework + Python 3.12
- **Banco de Dados:** PostgreSQL 16 (Supabase self-hosted DB-1.0)
- **Fila e Cache:** Celery + Redis
- **Renderizador de Documentos:** `python-docx` + LibreOffice local (`soffice`)
- **Conexões Externas em Runtime:** Zero conexões a serviços terceirizados para documentos.

### 2.3. Infraestrutura
- **LXC 1 (Aplicação):** Caddy 2 + Frontend SPA + Django API Core + Workers Celery + LibreOffice Headless (`192.168.10.200` / `https://condoc.fk.adm.br`)
- **LXC 2 (Dados):** Supabase PostgreSQL 16 + Supabase Auth + Supabase Storage (`192.168.10.201`)

---

## 3. Matriz de Requisitos EDOSS (Gap Analysis Detalhado)

| ID do Requisito | Descrição | Status no CONDOC | Evidência / Plano de Ação |
|---|---|---|---|
| **EDOSS-OSS-01** | Zero `@tiptap-pro` ou registry privado | **Atendido** | `apps/web/package.json` auditado; apenas pacotes MIT/OSS utilizados. |
| **EDOSS-OSS-02** | Zero envio documental a serviço externo SaaS | **Atendido** | Processamento 100% local no servidor LXC 1. |
| **EDOSS-OSS-03** | SBOM e licenças verificadas | **Atendido** | Todas as dependências possuem licenças permissivas (MIT/BSD/Apache-2.0). |
| **EDOSS-OSS-04** | Tiptap público e extensões sem duplicação | **Atendido** | StarterKit MIT configurado sem redundâncias. |
| **EDOSS-OSS-05** | Supabase self-hosted como alvo autorizado | **Atendido** | Instalação em LXC 2 com esquemas `app`, `app_private`, `app_acl`. |
| **EDOSS-OSS-06** | Fluxo documental funciona sem internet | **Atendido** | Nenhuma chamada externa é executada durante edição/exportação. |
| **EDOSS-OSS-07** | Assets e fontes servidos localmente | **Atendido** | Fontes padrão instaladas no container e fontes web embutidas no build. |
| **EDOSS-OSS-08** | Nenhum código proprietário copiado | **Atendido** | Implementações próprias baseadas em especificações abertas da LC 95. |
| **EDOSS-BL-01** | Separação de tipos jurídicos e parágrafos | **Parcial** | Tipos existem no banco; editor granularizado adicionado na Fase F1. |
| **EDOSS-BL-02** | Um caput inicial por artigo sem duplicar texto | **Parcial** | Regra de integridade implementada no serviço de artigos na Fase F1. |
| **EDOSS-BL-03** | UUID estável em mover e renumerar | **Atendido** | `Provision.id` / `DocumentNode.id` imutáveis nas movimentações. |
| **EDOSS-BL-04** | Origem antigo/novo muitos-para-muitos | **Atendido** | Tabela `OriginMapping` implementada com tipo de relação e excerto. |
| **EDOSS-BL-05** | Gramática normalizada LC 95 | **Parcial** | Catálogo de blocos normativos integrado ao Core na Fase F1. |
| **EDOSS-BL-06** | Enter e Backspace controlados | **Parcial** | Comandos customizados do editor Tiptap na Fase F2. |
| **EDOSS-BL-07** | Colagem/importação com conferência | **Atendido** | Módulo de transcrição com status `revisao_pendente` e `conferido`. |
| **EDOSS-BL-08** | Projeção visual não cria segunda fonte | **Atendido** | Fonte de verdade única no banco PostgreSQL. |
| **EDOSS-BL-09** | Renumeração com prévia | **Parcial** | Serviço de renumeração sequencial/automática na Fase F1. |
| **EDOSS-BL-10** | Referência cruzada por UUID estável | **Atendido** | `CrossReference` liga revisões e dispositivos por UUID permanente. |
| **EDOSS-BL-11** | Numeração ordinal/cardinal/romana correta | **Parcial** | Política LC 95: Art. 1º a 9º, Art. 10; § 1º a 9º, § 10; Incisos I..X. |
| **EDOSS-BL-12** | Templates com UUIDs novos instanciados | **Parcial** | Gerador de minutas a partir dos templates JSON OSS na Fase F1. |
| **EDOSS-ST-01** | Estilos semânticos separados do tipo legal | **Atendido** | Configurações de estilo armazenadas em `ConfigurationVersion`. |
| **EDOSS-ST-02** | Fontes, tamanhos e recuos persistidos | **Atendido** | `Perfil_Estilos_Layout_OSS.json` suporta tamanhos pt, cm e recuos. |
| **EDOSS-ST-03** | Não confundir unidades pt e px | **Atendido** | Mapeamento explícito de pontos tipográficos pt para OOXML dxa. |
| **EDOSS-ST-04** | Fonte ausente bloqueia finalização | **Atendido** | Preflight checa fontes disponíveis no SO antes de exportar. |
| **EDOSS-PG-01** | Quebra manual de página salva e exportada | **Parcial** | Tag `CondocPageBreak` inserida e traduzida para `w:br w:type="page"`. |
| **EDOSS-PG-02** | Paginação automática não cria revisão | **Atendido** | Paginação calculada no renderizador sem alterar banco. |
| **EDOSS-PG-03** | Artigo longo sem caixas indivisíveis | **Atendido** | Parágrafos normativos fluem naturalmente entre páginas. |
| **EDOSS-PG-05** | Preview final é PDF local do renderer | **Atendido** | Preview gerado a partir do PDF oficial derivado do DOCX. |
| **EDOSS-HF-01** | Cabeçalhos e rodapés com variantes | **Parcial** | Entidade `RegionRevision` e `SnapshotRegion` suportam default/first/odd/even. |
| **EDOSS-HF-05** | PageNumber e PageCount resolvidos | **Atendido** | Campos nativos OOXML `PAGE` e `NUMPAGES` computados no LibreOffice. |
| **EDOSS-HF-08** | Regiões sem autoria de moradores | **Atendido** | Anonimato absoluto garantido; cabeçalhos institucionais apenas. |
| **EDOSS-NT-01** | Notas documentais separadas de internas | **Atendido** | `DocumentNote` (pública/Word) separada de `InternalNote` (privada). |
| **EDOSS-NT-02** | Marcador noteId persistido | **Parcial** | Extensão Tiptap `CondocNoteReference` na Fase F3. |
| **EDOSS-NT-07** | DOCX com notas de rodapé OOXML reais | **Parcial** | Elementos `w:footnote` integrados no gerador python-docx na Fase F5. |
| **EDOSS-TB-01** | Tabelas no editor contínuo | **Atendido** | Tabelas semânticas renderizadas no editor e no DOCX. |
| **EDOSS-TB-02** | ColWidths e alinhamento persistidos | **Atendido** | Larguras de colunas armazenadas e respeitadas na exportação. |
| **EDOSS-TB-03** | Repetição de cabeçalho de tabela | **Atendido** | Tag OOXML `w:tblHeader` ativada nas tabelas normativas. |
| **EDOSS-EX-01** | PDF gerado do DOCX definitivo | **Atendido** | Pipeline unificado: Core gera DOCX -> LibreOffice converte para PDF. |
| **EDOSS-EX-03** | Snapshot único durante todo o render | **Atendido** | Snapshot congelado é a única referência de dados para o job. |
| **EDOSS-EX-05** | Par DOCX/PDF com manifesto e hashes | **Atendido** | Gravação de `ExportArtifact` com SHA-256 e manifesto de integridade. |
| **EDOSS-EX-07** | Documento público sem PII ou notas | **Atendido** | DTOs sanitizados e anotações internas expurgadas da exportação. |
| **EDOSS-OP-01** | Perfil/temp isolado por job | **Atendido** | Parâmetro `-env:UserInstallation` efêmero por execução do LibreOffice. |
| **EDOSS-OP-07** | Arquitetura de duas LXCs validada | **Atendido** | LXC 1 (Aplicação/Caddy/Core) e LXC 2 (Supabase). |
| **EDOSS-OP-10** | Ausência absoluta de voto/eleição | **Atendido** | Conformidade com AGENTS.md; apenas processos consultivos sem voto. |

---

## 4. Plano de Implementação por Fases (OSS-F0 a OSS-F7)

- **OSS-F0 (Concluído):** Inventário, SBOM, GAP Analysis, ADRs (ADR-005, ADR-006, ADR-007) e validação de dependências estritamente abertas.
- **OSS-F1 (Atual):** Modelagem normativa formal conforme LC 95 (gramática de Artigos, Caputs, Parágrafos, Incisos, Alíneas, Itens), numeração determinística e templates de Regimento e Convenção.
- **OSS-F2 & F3:** Extensões abertas do editor Tiptap, quebra de página manual, regiões de cabeçalho/rodapé e notas de rodapé documentais.
- **OSS-F4 & F5:** Pipeline de renderização canônica python-docx + LibreOffice headless local com manifesto SHA-256 e preflight validation.
- **OSS-F7:** Suíte integrada de testes (100% verde), hardening e homologação final em produção.
