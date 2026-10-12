# Prompt de atualização — CONDOC Editor Normativo ED-OSS-2.0

Você atua como arquiteto/engenheiro responsável por atualizar o CONDOC existente. Leia AGENTS raiz/Core/módulo e o PRD mestre, depois docs/prd/PRD_Complementar_ED_OSS_2_0.md integralmente.

A decisão atual é full self-hosted com componentes open source. Propostas antigas Pages/PagesTableKit/ConvertKit/ExportDocx/notas @tiptap-pro estão substituídas. Não compre licença, use registro privado, copie código fechado ou envie documento a serviço externo.

## Início obrigatório

1. Inventarie repository, lockfiles, packages, licenças, tabelas, editor, import/export e ambiente.
2. Produza docs/GAP_EDITOR_OSS.md e SBOM/lista de conflitos.
3. Classifique EDOSS como atendido/parcial/ausente/incompatível com evidência.
4. Faça ADR modelo e migration de IDs/dados, fonte única SQL, fluxo editor contínuo+preview, renderer/notas/regiões e licença/fontes.
5. Defina plano OSS-F0…F7, dependências e gate. Live pagination próprio F6 é opcional, não PagesPro obrigatório.

## Implementação

Use Tiptap/ProseMirror OSS e extensões públicas aprovadas. Implemente blocos/estilos/regiões/notes commands próprios. Não invoque API Pro como se pertencesse ao core aberto. Fonte única de árvore/body/styles/layout/notas; preserve base/revisões/sugestões/ref IDs.

Renderer python-docx/OOXML + LibreOffice local: congelar→preflight→DOCX→atualizar fields/sumário/layout→salvar definitivo→PDF dele→verificar→manifest. Não PDF paralelo HTML/ReportLab apresentado como igual. Footnotes/endnotes reais e completa inspeção de privacidade.

Tabelas com atributos persistidos, labels sem duplicação, refs por UUID, templates placeholders sem dados legais inventados. Conteúdo sobre assembleia/quórum permitido como texto; nenhum mecanismo de votação.

## Processo

Incrementos com testes unitários/integration/E2E/semânticos/visuais, licenças, rede bloqueada e restore. Não remover integração atual destrutivamente antes de migração/substituição aprovada. Não usar dados reais/mensagens/produção/SSH destrutivo/Proxmox sem autorização. Ao bloquear, evidência e próxima ação, não simulação silenciosa.

## Saída de cada fase

Arquivos/migrations, critérios implementados, comandos e resultados reais, gaps, riscos, corpus/exemplares DOCX/PDF quando pipeline implementado e gate. Atualize matriz. Hash/ZIP validado não equivale a software homologado.

Comece pela auditoria OSS-F0 e prossiga nos passos autorizados. Antes de alterar produção, backup/rollback e aprovação específica.
