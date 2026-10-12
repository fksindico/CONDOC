# ADR-005: Editor Normativo 100% Open Source baseado em Tiptap Core e ProseMirror MIT

## Status
Aprovado

## Data
2026-10-12

## Contexto
O projeto CONDOC exige uma experiência avançada de edição de atos normativos (Convenções de Condomínio e Regimentos Internos) com estruturação hierárquica (Livro, Título, Capítulo, Seção, Artigo, Caput, Parágrafo, Inciso, Alínea, Item), quebras de página, notas de rodapé/fim e tabelas com formatação rica.

Propostas anteriores sugeriam a adoção do ecossistema comercial fechado `@tiptap-pro/*` (`@tiptap-pro/extension-pages`, `@tiptap-pro/extension-table-kit`, `@tiptap-pro/extension-convert-kit`, etc.). No entanto, essa dependência viola as diretrizes mandatórias de self-hosted e soberania do CONDOC:
1. Requer registro npm privado com credenciais proprietárias pagas por assinatura;
2. Bloqueia builds autônomos em ambientes locais e LXC isolados (arquitura self-hosted);
3. Impede auditoria independente de segurança do código-fonte;
4. Introduz risco de descontinuidade ou mudanças arbitrárias de licenciamento.

## Decisão
1. **Rejeição total de `@tiptap-pro`**: Nenhuma dependência comercial fechada será adicionada aos `package.json`, lockfiles ou imagens de container.
2. **Adoção do Tiptap Core MIT**: A base de edição permanece no `@tiptap/core`, `@tiptap/react`, `@tiptap/pm` e `@tiptap/starter-kit`, licenciados sob MIT.
3. **Dualidade Canônica (Continuous Flow + Paged Preview)**:
   - O editor visual opera em modo **Fluxo Contínuo Estruturado** com divisórias visuais de página (`CondocPageBreak`) e semântica de dispositivos normativos (`CondocNormativeFlow`).
   - A paginação real e oficial é delegada ao pipeline de renderização canônica local (ADR-006) e visualizada pelo usuário via preview embutido do PDF oficial gerado por esse mesmo pipeline.
4. **Extensões de Domínio Próprias**:
   - `CondocNormativeFlow`: Gerencia os tipos jurídicos de dispositivos, Caput obrigatório, numeração conforme LC 95 e atalhos de teclado controlados (Enter não cria dispositivos acidentalmente; Shift+Enter cria quebra de linha interna).
   - `CondocPageBreak`: Permite a inserção de quebras manuais de página exportadas de forma determinística como quebras de seção/página OOXML (`w:br w:type="page"`).
   - `CondocNoteReference`: Gerencia marcadores em linha para notas de rodapé (Footnotes) e notas de fim (Endnotes), associadas por UUID estável a entidades de notas documentais.
   - `CondocTableManager`: Suporta tabelas semânticas abertas com colWidths definidos, repetição de cabeçalho em quebra de página e bordas padronizadas.

## Consequências
- **Positivas**:
  - Soberania tecnológica 100% self-hosted, sem custos recorrentes de SaaS ou riscos de licenciamento.
  - Reprodutibilidade total em builds isolados (inclusive sem acesso à internet).
  - Controle preciso sobre a gramática jurídica brasileira (LC 95/98).
- **Compromissos**:
  - A paginação em tempo real é aproximada visualmente no editor, sendo o PDF gerado pelo pipeline canônico a única representação com contagem final de páginas e geometria gráfica idêntica.
