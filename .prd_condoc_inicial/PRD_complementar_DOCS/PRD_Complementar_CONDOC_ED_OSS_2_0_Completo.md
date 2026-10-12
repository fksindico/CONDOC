# PRD complementar consolidado — CONDOC Editor Normativo Open Source

Versão: ED-OSS-2.0  
Data: 11/10/2026  
Base: PRD mestre v3.0 e decisões funcionais da conversa  
Status: especificação para atualização, desenvolvimento e homologação  
Implantação: full self-hosted  
Idioma: português brasileiro

> Fonte normativa deste subsistema: este complemento. Substitui o ED-1.0 e as propostas TP/PN/HF/NT/FM/TB/TC que dependam de pacotes proprietários Tiptap. Mantém privacidade, rastreabilidade, autorização de publicação e ausência de votação do PRD mestre. Não é uma aplicação pronta nem um renderer já testado.
>
> Restrição absoluta: componentes utilizados em produção devem ser open source, com licença identificada e compatível; nenhum @tiptap-pro/*, registro privado de licença, SaaS de conversão ou autenticação comercial de extensões será requisito. O fato de um produto ser executável localmente não o torna open source.

## 1. Missão e resultado

Atualizar o CONDOC para criar e revisar Convenção e Regimento Interno como documentos normativos estruturados e diagramados, preservando conteúdo, relações, estilos, histórico e origem. Entregar DOCX editável e PDF final conferidos, provenientes do mesmo snapshot.

Não implementar voto, eleição, apuração, cálculo de quórum, peso eleitoral, aprovação vinculante ou registro cartorial. É permitido redigir conteúdo jurídico sobre assembleias/quóruns dentro do documento: proibição é funcionalidade de apuração no software, não censura desses assuntos.

CONDOC é o nome de exibição adotado nesta versão. CONDC em arquivos legados se refere ao mesmo projeto; não renomear serviços, banco, diretórios ou domínios automaticamente.

## 2. Decisão mandatória de licenciamento e operação

Tiptap core/editor aberto, ProseMirror e extensões públicas aprovadas permanecem possíveis. Pacotes Pages, PagesTableKit, ConvertKit, ExportDocx Pro e extensões Pro de notas NÃO fazem parte da solução. A documentação distingue core MIT de extensões Pro acessadas por registro privado. [web:303][web:289]

Stack do subsistema: React/TypeScript/Tiptap core; extensões OSS; plugins próprios; Core Django/DRF; Supabase self-hosted; Celery/Redis; python-docx com geração OOXML controlada; LibreOffice/UNO/headless; Tesseract e ferramentas de inspeção PDF aprovadas por licença.

python-docx declara MIT; LibreOffice é software livre MPL 2.0 com outros componentes/licenças que devem constar do inventário da distribuição. Não reduzir todas as licenças transitivas a uma única licença do produto. [web:305][web:285]

Todas dependências diretas/transitivas, imagens, fontes e recursos devem entrar em SBOM/licenças, com versões e avisos exigidos. Não escolher a licença do código próprio sem decisão do responsável. Remover tokens @tiptap-pro da configuração/CI; revogar tokens existentes pelo responsável se aplicável. Nunca copiar código proprietário para reimplementação.

Operação documental não transmite conteúdo a serviço externo. Fonts/icons/assets locais, sem CDN obrigatória ou Google Fonts runtime. Build pode obter dependências públicas aprovadas; operação sem saída para internet deve ser testada. SMTP para convites pertence ao produto maior, depende de autorização/configuração e não é usado pelo renderer.

Supabase Cloud deixa de ser alvo autorizado desta atualização: produção e homologação deste complemento são self-hosted. Código continua desacoplado de host, mas isso não autoriza uso Cloud por conveniência.

## 3. Estrutura condominial e base editorial

Convenção aborda instituição/organização, contribuições, administração, assembleias, sanções e relação com Regimento. Regimento detalha convivência e uso/funcionamento. Modelos são organizacionais, não cláusulas jurídicas aprovadas. [web:189][web:190]

Lei 4.591, art. 9º, é referência de conteúdo, mas fonte original não deve ser tomada como compilação vigente isolada; conferir legislação e documentação aplicável. [web:170] LC 95, arts. 10/11, inspira articulação/clara redação; não é apresentada como imposição universal direta aos instrumentos privados. [web:142][web:143]

Não inventar rateio, fração, área, matrícula, prazo, quórum ou sanção. Preservar particularidades registrais e estruturais do original. O sistema identifica pendências; não certifica legalidade nem substitui profissional responsável.

## 4. Fidelidade: alcance verificável

Três dimensões: semântica (texto/ordem/hierarquia/rótulos/referências), apresentação (propriedades suportadas), paginação (renderização no ambiente canônico).

“Fiel” significa zero perda silenciosa e aprovação de invariantes no corpus homologado. Não prometer identidade binária do DOCX original ou paginação idêntica em qualquer Word/LibreOffice. PDF digitalizado não contém estrutura jurídica confiável automaticamente.

Recursos não suportados geram relatório e decisão. Original privado preservado; normalização explícita; exportação final bloqueada se houver perda relevante não resolvida. PDF oficial é representação do DOCX definitivo pelo motor homologado; DOCX aberto/editado externamente pode refluír ou alterar conteúdo.

## 5. Escopo e prioridades de experiência

Inclui: catálogo normativo, templates, campos, editor, estilos, tabelas, notas, regiões, referências, importação/OCR, diagnóstico, numeração, preservação, prévia, exportação e testes.

Há dois modos obrigatórios de trabalho:

- Edição estrutural contínua, funcional e recuperável com Tiptap OSS.
- Prévia paginada final, produzida localmente pelo renderer e exibida no navegador.

Edição em páginas ao vivo com plugin OSS próprio é incremento adicional de layout, não um Pages Pro disfarçado. Não anunciar experiência Word-like completa antes de homologar. Nas situações não suportadas pelo plugin visual, usar edição contínua + prévia final; isso não reduz obrigações de DOCX/PDF.

Não implementar fragmentação DOM sofisticada como condição para salvar o primeiro documento. Gate de exportação profissional exige todas capacidades normativas/support declaradas, não mera aparência de folhas A4.

## 6. Modelo normativo e projeção de edição

Modelo canônico: documento → agrupamentos opcionais → artigo → caput/parágrafos/incisos/alíneas/itens. Todos com UUID/revisões; pai/ordem do snapshot imutáveis.

Projeção visual: sequência de headings/parágrafos/tabelas/figuras com flowBlockId, normativeNodeId, articleId, parentNormativeId, styleId e isFirstBodyBlock. Um dispositivo pode ter vários blocos textuais. Número jurídico separado de texto. Não duplicar article.text e caput.text.

ProseMirror define árvore/schema/transactions e permite relações/atributos explícitos; isso não fornece paginação pronta. [web:298][web:300]

Página não é pai jurídico. Layout não cria revisões de conteúdo. Controle do artigo aparece em painel/overlay fora do fluxo, não card flex/overflow indivisível.

## 7. Catálogo de blocos

| Tipo | Papel | Rótulo | Regras |
|---|---|---|---|
| document_root | Raiz | Não | Árvore/metadados |
| cover_block | Capa | Não | Dados/logo autorizados |
| document_heading | Nome do documento | Não | Não é TÍTULO I |
| preamble | Abertura | Não | Contexto sem aprovação inventada |
| scope_block | Objeto | Configurável | Pode integrar art. 1º |
| toc_block | Sumário | Gerado | Headings selecionados e páginas finais |
| legal_part | Parte | Romano/texto | Opcional |
| legal_book | Livro | Romano | Opcional |
| legal_title | Título normativo | Romano | Agrupador |
| chapter | Capítulo | Romano | Agrupador |
| legal_section | Seção jurídica | Romano | Não altera seção Word |
| subsection | Subseção | Romano | Opcional |
| article | Artigo | Art. 1º/Art. 10 | Um caput inicial |
| caput | Texto inicial | Herda artigo | Não duplica label |
| legal_paragraph | Parágrafo jurídico | Único/§ | Não é paragraph rich-text |
| inciso | Enumeração | I/II/III | Filho artigo ou parágrafo |
| alinea | Desdobramento | a)/b) | Filho inciso |
| item | Desdobramento | 1./2. | Filho alínea |
| legacy_clause | Cláusula legada | Preservado | Conferência/mapeamento |
| narrative_block | Texto auxiliar | Não | Somente integrante intencional |
| normative_table | Tabela documental | Legenda opcional | Editável, dados conferidos |
| figure | Figura | Legenda opcional | Dimensões/alt text |
| annex | Anexo normativo | Configurável | Não evidência privada |
| signature_group | Fecho/assinaturas | Não | Campos, sem assinatura automática |
| unsupported_preserved | Recurso importado | Original | Diagnóstico/decisão, sem perda silenciosa |

Notas/referências são objetos auxiliares e marcadores inline. LayoutSection/PageRegion são estruturas de apresentação, não agrupamentos jurídicos. Observações internas são recurso de gestão separado.

## 8. Gramática, modo legado e transações

Normalizado: níveis agregadores inferiores opcionais, sem ciclos; artigo com um caput primeiro; incisos diretos/parágrafos; parágrafo pode ter incisos; inciso alíneas; alínea itens. Corpos suportam paragraphs textuais e blocos de mídia/tabela compatíveis.

Legado: rótulos/cláusulas/arranjos conferidos preservados, exceções explícitas. Não classificar documento inválido só por divergir da gramática nova.

Enter cria paragraph textual no mesmo dispositivo; Shift+Enter quebra linha; toolbar cria dispositivo jurídico novo; Backspace entre dispositivos não funde silenciosamente. Colagem sanitizada, múltiplos rótulos abrem conferência. Copiar dispositivo cria novos IDs; dividir texto cria flow ID, não novo § por acidente.

Concorrência por revisão/ETag. Atualização desatualizada rejeitada sem perda do rascunho. Alteração de bloco, origem/ref e auditoria consistentes. Não reatribuir sugestão após divisão/movimento sem vínculo explícito.

## 9. Numeração e referências

Perfil inspirado LC 95: Art. 1º a 9º, Art. 10 em diante; Parágrafo único.; § 1º a 9º e § 10; romano inciso; letra minúscula alínea; arábico item. [web:142]

Políticas: preserved, sequential, inserted_suffix e exceção manual auditada. Art. 10-A é opção editorial, não imposição geral. Artigos contínuos no documento por padrão; legado pode reiniciar.

Rótulos calculados e congelados; runs jurídicos explícitos no DOCX, não dependentes de listas genéricas. Único→vários com prévia e impacto. Referências por UUID e namespace do documento/anexo; renderer resolve rótulo/bookmark. Anexo pode ter numeração própria se configurado, sem colisão global.

Detectar duplicidade, alvo ausente/excluído, marcador pendente, ciclo e referência externa sem fonte. Não transformar referência textual importada automaticamente em vínculo sem conferência.

## 10. Templates de Convenção e Regimento

Convenção: identificação; objeto/destinação; unidades/comuns; direitos/deveres; administração; conselhos; assembleias/regras documentais; contribuições/rateio/fundos; conservação/obras; seguro/responsabilidades; infrações/procedimento; relação Regimento/comunicação; alteração/finais; transitórias; anexos/fecho.

Regimento: identificação/vínculo; objeto/definições; convivência; entrada/visitantes/prestadores; mudanças/entregas; reformas; circulação/comuns; garagens; lazer existente; limpeza/resíduos; segurança/emergências; animais/convivência; ocorrências; finais/transitórias; anexos.

Áreas opcionais conforme condomínio; sem piscina inexistente ou restrição automática a animais. Texto de template é placeholder, não norma recomendada pronta. Matrícula/áreas/frações não inferidas de cadastro administrativo.

Templates de bloco: capítulo; artigo simples; artigo com único; vários parágrafos; inciso direto; parágrafo com incisos; inciso/alíneas; alínea/itens; cláusula; tabela; anexo; assinatura. Instância gera UUID novos uma vez; snapshot não regenera IDs. Placeholder tem tipo/valor/origem/status e bloqueia perfil final.

## 11. Estilos semânticos e formatação direta

StyleProfile versionado: identificação, preâmbulo, títulos, capítulo/seção/subseção, artigo-caput, §, inciso, alínea, item, narrativa, tabela/célula/header, legenda, nota, anexo, assinatura, header/footer.

Default proposto, não obrigação ABNT/legal: A4, margens 3 cm esquerda/2 direita/2,5 superior e inferior; Liberation Serif 12 pt homologada; corpo justificado, 1,15 e 6 pt após; rótulos destacados; capítulo centralizado/negrito/keep-with-next; recuos por nível e hanging indent; regiões 9–10 pt.

Persistir unidades físicas: pt, cm/mm e valores de espaçamento. Converter só na borda; não confundir 12px/12pt. Fonte instalada/licenciada; faltar fonte bloqueia final. Sem CDN. Fonte própria não adquirida/redistribuída sem licença.

Formatação direta: marks texto de negrito/itálico/sublinhado/tachado/cor/fundo/família/tamanho, com allowlist. Estilo semântico separado do tipo normativo: querer fonte maior não transforma caput em capítulo. Normalizar importado é ação explícita com prévia. Overrides locais são versionados e exportáveis.

## 12. Extensões OSS e comandos do produto

Usar pacotes públicos aprovados, evitando duplicatas: @tiptap/core/react/starter-kit, @tiptap/extension-table, @tiptap/extension-text-style, alinhamento/underline/links conforme versão e necessidade. TableKit público reúne table/tableCell/tableHeader/tableRow. [web:301] Verificar composição da versão para não registrar extensão duplicada.

Implementar extensões próprias CondocNormativeFlow, CondocPageBreak, CondocNoteReference, CondocRegionAdapter e CondocStyleRegistry. Esses nomes são contratos a implementar, não pacotes existentes.

Comandos próprios: insertNormativeBlock, splitNormativeBlock, mergeNormativeBlocks, applySemanticStyle, previewNumbering, insertDocumentPageBreak, insertDocumentNote, editDocumentNote, resolveReference. Contratos públicos não expõem ator/vínculo privado.

Nenhum comando insertFootnote/setHeader/registerLayoutParticipant da extensão Pro deve ser invocado como se existisse no core aberto. Equivalentes do produto são implementados/testados com schema/plugins públicos.

## 13. Quebras de página e paginação

Automático: fluxo natural no editor contínuo e renderer. Não salvar fragmentação visual como conteúdo. Quebra explícita é nó/instrução independente com motivo opcional e anchor; mapa para DOCX page break. Não inserir quebra em todo artigo.

Políticas: artigo/§ longo pode atravessar; rótulo acompanha começo; heading acompanha início seguinte quando possível; imagem/assinatura curta indivisível só se cabe. Texto sem height fixa/overflow hidden; componentes de gestão fora do fluxo.

Pré-validação de bloco indivisível maior que página: redimensionar/dividir com ação do usuário, nunca empurrar eternamente. Substituir lógica Pages por algoritmo próprio se live mode for implementado. Medidas após fonts/images prontos, batch de mudanças, limite de iterações e fallback estrutural. Não usar CSS break-inside como garantia universal de paginação contenteditable.

Preview final vem do PDF local; impressão usa PDF, não window.print. Zoom/gap são preferência de visualização, não estilo normativo/exportável. Plugins de layout não escrevem alterações no conteúdo a cada resize.

## 14. Layout e cabeçalhos/rodapés

PageLayoutProfile com tamanho/orientação/margens/distâncias, primeira página, pares/ímpares, início/continuidade de número e segmentos ancorados. Seção normativa ≠ Word section; docs python-docx definem layout por seção. [web:159]

Regiões persistidas separadamente do body, com rich JSON, state template/explicit/cleared e regras de variante. Precedência: first quando ativa, odd/even quando ativos, default nos demais. Ativo e vazio fica vazio; null/uninitialized não equivale a deletado.

Condomínio/tipo/versão/status resolvidos do snapshot. PageNumber/PageCount são campos tipados, não texto livre com token ambíguo. Estender display {page}/{total} só como convenção própria; app interpreta, não PagesPro.

Na edição contínua, região é preview/bloco separado e subeditor de produto. Salvar body/regiões/layout atomicamente por revisão. Permissão layout.edit conferida servidor; toolbar segue editor ativo. Nunca alterar header global por cursor para simular capítulo da página.

Capa sem número visível e reinício no corpo são opções separadas. Capítulo corrente por página é recurso opcional avançado: só implementar mapeamento real de field/section no renderer após ADR/corpus.

## 15. Notas de rodapé e de fim

Implementação própria OSS: marcador inline atômico com noteId/kind; conteúdo rico em DocumentNote e revisões, não dentro do footer nem comentário interno. Editor auxiliar do produto para conteúdo, toolbar direcionada e save state.

Contagem segue ordem das referências do snapshot. Footnote decimal contínua e endnote roman minúscula são defaults configuráveis do produto; não afirmar que core possui numeração automática pronta. UUID não é número. Não aninhar notas/referências circulares. Repetição intencional de referência à mesma nota requer política explícita; bloquear ambiguidade.

Rascunho pode ter nota órfã para undo/history; não cleanup em todo save. Snapshot de export usa notas referenciadas e diagnostica órfãs/ausentes. Declaração de notas finais antes/depois de anexos e por seção é opção explícita, a homologar; default fim do documento.

Renderer gera notas Word reais via OOXML/UNO, não simulação por texto superscrito/lista. python-docx não deve ser presumido suficiente sozinho para todas essas partes: complementar relações/content types/footnotes/endnotes/markers com builder testado. Mapeamento UUID→ID OOXML versionado e sem colisão.

Nota longa é testada no motor final; se não cabe ou não continua corretamente, bloquear e oferecer conversão explícita para fim/anexo. Não cortar texto nem repetir limitação PagesPro como se fosse regra do LibreOffice. Notas de layout final aparecem no PDF canônico; editor pode usar painel enquanto posicionamento live não é homologado.

## 16. Tabelas: schema, edição e aparência

Tabela pública Tiptap em fluxo contínuo: inserir linhas/colunas/header, adicionar/remover, mesclar/dividir, redimensionar. Botões só quando operação permitida; apagar tabela com conteúdo exige confirmação.

Persistir grid/row/cell IDs, colspan/rowspan, colWidths físicas, table width, padding, align, valign, background, borders quatro lados e regra rowHeight automatic/min/exact. Header semântico separado de repeatHeader. Presets classic/minimal/striped versionados com exceções por célula.

Preset classic: borda fina, header cinza claro, texto escuro e padding. CSS da interface não é fonte única; renderer resolve estilos. Cores validadas/allowlisted, sem style arbitrário. Zebragem pela ordem lógica, não DOM de página. Não cortar para caber.

Coluna espaçadora importada não é erro automaticamente. Validar colWidth inconsistentes, mínimo legível e mesclas. Figure em célula proporcional, sem indivisibilidade maior que área útil.

## 17. Tabelas e quebra entre páginas

No editor contínuo não é preciso fragmentar DOM para persistir tabela. Preview canônico mostra quebra real. Mesmo row/cell ID continua único quando renderer divide apresentação. Sem nodes artificiais Linha8A/8B.

Renderer mapeia permitir divisão de linha, repeatHeader, min/exact heights, mesclas e border/shading reais. Normalização de exact que corta exige decisão; modo final bloqueia loss. Imagem grande deve caber/reduzir/dividir contexto.

Paginação live de tabelas, se implementada: plugin próprio/OSS com licença aprovada e corpus. Não usar @tiptap-pro/extension-pages-tablekit nem experimentalRowFragmentation. Mesclas/continuações/caret/selection são problemas reais a testar, não declarar suporte só por CSS.

TableHeader não garante repetição; mapear propriedade específica no DOCX e conferir PDF. Border em quebra/continuação não duplica indevidamente; preservar JSON original e export sem spacer/clone visual.

## 18. Importação DOCX, comentários e compatibilidade

Preservar arquivo privado, hash e versão. Parser OOXML lê styles, numbering, paragraph/runs, tabelas/mesclas, layout, regiões, notas, bookmarks/fields, imagens e relações relevantes. Propor semântica por rótulo/estilo/contexto e exigir conferência.

Relatório: preservado; normalizado com decisão; parcial; preservado como referência não editável; não suportado bloqueante. Original/posição/recurso/ação registrados. Não sumir com objeto.

Tracked changes exigem escolher visão/base; não aceitar/rejeitar silenciosamente. Comentários importados privados. Campos externos/DDE/OLE/macros/relacionamentos externos não executados. Não buscar recurso remoto. Notas/mídia restritas obedecem ACL.

Arquivo público posterior sem comments, tracked deletions, hidden text, custom props/metadados ou alt-text indevidos. Não basta inspecionar texto aparente.

## 19. PDF/OCR e documentos legados

PDF textual extrai ordem/texto/layout propostos; scan via Tesseract local, conferência de §/º/números/tabelas. Não prometer round-trip perfeito. Preservar páginas originais e mostrar lado a lado com estrutura.

Transcrição conferida imutável; correção gera versão/motivo/impacto. Preservação legada tem rótulo/manual/estilos suportados; normalizar perfil somente após prévia. Documento reconstruído informa se layout é normalizado ou aproximado.

## 20. Renderer canônico DOCX/PDF

Pipeline local obrigatório:

1. Autorizar perfil, congelar snapshot e anexos elegíveis.
2. Resolver templates/campos/rótulos/ref/estilo/layout/notas.
3. Preflight semântico/compatibilidade/privacidade/fontes.
4. Compilar DOCX com python-docx e OOXML controlado.
5. Abrir no LibreOffice/UNO isolado, atualizar índices/fields/layout.
6. Salvar DOCX definitivo normalizado.
7. Renderizar o mesmo DOCX definitivo para PDF.
8. Revalidar conteúdo, notas, refs, tabelas e campos.
9. Conferir visual/privacidade e salvar par + manifesto.
10. Rerender de conferência a partir do DOCX efetivamente entregue quando necessário ao gate.

python-docx documenta criação/edição; LibreOffice documenta exportação PDF. Essas capacidades não dispensam implementação/QA de campos/notas/layout. [web:160][web:157][web:278]

Não gerar PDF paralelo por HTML/ReportLab e chamar idêntico. Não congelar quebras automáticas do browser no DOCX. Não confiar em múltiplos espaços para alinhamento. Styles Word nomeados, fields PAGE/NUMPAGES/TOC/REF apropriados e bookmarks estáveis.

DOCX editável, PDF visual oficial. Não garantir identidade em qualquer Word/máquina. Word não é dependência nem alvo obrigatório desta solução OSS; compatibilidade externa pode ser testada sem virar condição de execução.

## 21. Perfis de saída, preflight e privacidade

Perfis: draft marcado; clean working; final presentation; DePara; internal restricted; preservation structured. Final não é juridicamente aprovado pelo sistema.

Final bloqueia: placeholder pendente, fonte ausente, ref quebrada relevante, perda não resolvida, fields/TOC não atualizados, texto/nota/tabela cortados e recurso sem export suporte não tratado. Não inventar aprovação por quantidade de concordâncias.

Labels/regions/status do snapshot, não versão atual ao longo do job. Comentários internos e identidade de sugestor excluídos também de OOXML/metadata, PDF attachments/layers e filenames. Metadados institucionais configurados.

PDF/A opcional com validação apropriada, não afirmar conformidade só por nome de filtro. Assinatura, chancela, protocolo e registro externo fora do escopo.

## 22. Modelo de dados complementar

Estender Provision/Revision ou migrar com IDs preservados para DocumentNode/Revision; ADR escolhe, sem fontes concorrentes de texto. Snapshots resolvem árvore/body/estilos/layout/notas completos.

| Entidade | Campos mínimos |
|---|---|
| BlockTypeDefinition | type, schema_version, grammar, allowed_body, defaults |
| DocumentNodeRevision | id/node UUID, parent/order, kind, body, number policy, style/overrides, author/date |
| FlowProjection | mapeamento derivado node→flow IDs, não segundo banco de texto |
| DocumentTemplateVersion | skeleton, field definitions, version, metadata |
| StyleProfileVersion | semantic styles, font manifest, defaults/overrides |
| PageLayoutVersion | format/margins/regions policy and segments |
| PageRegionRevision | kind/variant/state/rich body, expected revision |
| NumberingPolicy/FrozenLabel | values/rendered labels por snapshot |
| InlineReference/Bookmark | source node/position, target UUID/namespace, frozen label |
| DocumentNoteRevision | note UUID/kind, rich body, author/date, snapshot ref |
| NoteReference | note UUID, source node/position, order/label per snapshot |
| FieldValue | type, value, source, confirmation/pending state |
| TableStyleVersion | preset, borders/shading/padding/header defaults |
| ImportCompatibilityIssue | feature/location/severity/state/decision/actor |
| RenderJob | snapshot, versions/options, state, actor/tenant, idempotency |
| RenderManifest | hashes, renderer/templates/fonts/options, validation |
| ExportValidationIssue | target, category, severity, resolution/evidence |

Tenant isolation/FKs/constraints e contextos de worker mantidos. Referência privada de autor não entra no payload público. Storage privado e autorização antes de URLs; para revogação imediata usar proxy, pois URL assinada emitida pode durar até expiry.

## 23. Contratos de API

REST /api/v1, sessão/autorização existentes, CSRF, revisions/ETag, idempotência, pagination e errors code/message/field_errors/request_id. Não inferir validade por render accepted.

- GET /document-block-types
- GET/POST /document-templates; /{id}/versions
- POST /documents/{id}/instantiate-template
- GET/POST /style-profiles; /{id}/versions
- GET/PUT /documents/{id}/layout e /regions
- POST /documents/{id}/numbering-preview e /numbering-apply
- GET/POST /documents/{id}/notes; PATCH /notes/{id}; referências validadas
- PUT /documents/{id}/table-style com target/revision
- GET /source-imports/{id}/compatibility
- POST /source-imports/{id}/issues/{issue}/decision
- POST /documents/{id}/export-preflight
- POST /render-jobs; GET /{id}/status, /preview, /artifacts, /manifest

Render request: snapshot_id, style/layout/template versions, export_profile, formats docx/pdf, expected authorization scope e idempotency. Ator real da sessão, não actor enviado cliente. Job 202 não finaliza. Estados queued/preflight/rendering/finalizing/validating/ready/failed/cancelled. Artifact só após gate. Conflito revision 412 ou domínio409 conforme contrato; não salvar metade do layout/notas.

## 24. UX e permissões

S11 permanece editor: árvore, corpo e contexto; menus inserir normativo/tabela/nota/quebra; presets e propriedades. Painéis: estilos, layout/regiões, notas, compatibilidade, preflight e preview final. Portal do morador só lê conteúdo autorizado e sugere; não edita artefato.

Permissões: document.edit, document.layout.edit, document.style.edit, document.notes.edit, document.template.manage, document.export e restricted_export conforme grants. Roles não concedem identidade automaticamente. Alterações sensíveis versionadas/auditadas. Síndico continua único publicador de sugestões.

Barra ativa para corpo/região/nota; read-only de todos subeditores também no servidor. Ações finais mostram snapshot e estado. “Pronto para apresentação” não é “aprovado”. Preview final é PDF com mesma versão/hashes dos downloads.

## 25. Segurança, isolamento e performance

Renderer sem rede externa para documentos/relacionamentos/fonts. ZIP/OOXML com limites de bytes/descompactação/tempo/memória, XML seguro sem resolução externa, nomes privados não interpolados em shell. Temp/perfil LibreOffice por job; sem profile compartilhado concorrente; limpeza após resultado.

Fontes/templates locais licenciados; lockfiles/images pinned. Core/worker revalidam tenant/grants e não usam admin Supabase para contornar RLS. Serviços distribuídos usam StoragePort, não disco da mesma VPS pressuposto.

Limites iniciais herdados: 1.000 dispositivos, importação 50MB/300 páginas, lista de moradores não alterada. Documentar carga/hardware antes de prometer p95. Cache keyed por snapshot+template/style/layout/font/renderer+opções, sem vazamento tenant. Falha não entrega final incompleto.

Offline runtime: bloquear saída internet durante teste de criação/edição/import/render/preview/export; acesso a serviços privados e storage interno continua permitido. Não confundir offline local com isolamento absoluto do navegador do usuário.

## 26. Reprodutibilidade, equivalência e manifesto

Mesmo snapshot e renderer fixo. Sem campos voláteis/data externa; versão/data documental congeladas. Fonts/style/templates/options registrados. Hash garante integridade de arquivo, não igualdade visual DOCX/PDF.

Rerender do DOCX entregue e comparação semântica/visual contra PDF oficial; ignorar só metadados/antialiasing conhecidos, não conteúdo. Diferenças de page count, tabela, nota, ref e sumário exigem decisão. Golden tests versionados com revisão humana.

Manifest: snapshot, version refs, docx/pdf SHA256, renderer/version/container digest, fonts list/license/hash, locale, options, validations, timestamps/actor, supersedes quando corrigido. Não reportar passed sem evidência. DOCX externo editado é novo arquivo a reimportar/conferir.

## 27. Operação e duas LXC

LXC aplicação: frontend/Core/Redis/workers/render stack, após autorização e dimensionamento. LXC Supabase: DB/Auth/Storage self-hosted. Não deslocar Core para banco nem criar terceira LXC automaticamente. URLs/hosts/paths configuráveis. Sem Proxmox/DNS/firewall alterado por inferência.

Backups de banco, objetos, templates/style/fontes licenciadas, manifests e configuração protegida. Restore em teste; exportação recuperável. Snapshot técnico não substitui backup. Installer idempotente e mudança destrutiva exige aprovação/rollback. Não comprometer requisitos de operação do PRD mestre.

## 28. Migração e remoção de dependências incompatíveis

1. Inventariar manifests/lockfiles/imports/config/registry e renderer atual.
2. Classificar pacote público OSS, Pro, serviço externo e licença desconhecida.
3. Produzir plano de substituição sem apagar dados.
4. Criar adapters de importação das estruturas existentes para modelo canônico.
5. Preservar body, header/footer, notes, labels, table attrs, IDs e referências.
6. Rodar migração em cópia/seed e comparar antes/depois.
7. Remover dependência/runtime Pro e configs apenas após cobertura funcional correspondente ou limitação explicitamente aprovada.
8. Backup/corte/rollback autorizado antes de produção.

Dados exportados pelo sistema antigo podem ser processados sob autorização; não copiar implementação de biblioteca fechada. Função não reimplementada deve ficar pendente, não simulada como pronta. Campos antigos desconhecidos preservados em diagnóstico privado até decisão, sem propagar segredo/PII a export público.

## 29. Fases complementares

### OSS-F0 — Inventário, licenças e prova de conceito

Gap PRD, SBOM, ADR schema/renderer/notas/paginação, versões, corpus e pipeline local simples. Bloquear dependências Pro/runtime externo e registrar incompatibilidades.

### OSS-F1 — Modelo normativo, numeração e templates

Gramática, IDs/revisões, referências, fields, modelos por tema, migração e testes. Nenhuma segunda fonte de texto.

### OSS-F2 — Editor aberto e formatação

Extensões OSS, custom semantic commands, fluxo contínuo, estilos, tabela/células, presets, Enter/Backspace/colagem e concorrência. Layout live não pressuposto.

### OSS-F3 — Layout, regiões e notas locais

Perfis/seções, subeditores próprios, note model/commands, persistência atomic e campos dinâmicos. Preview estrutural com limitações claras.

### OSS-F4 — Importação e diagnóstico

DOCX/OCR legado, comentários/track changes, styles/regions/notes/tables e relatório. Gate zero perda silenciosa e original preservado.

### OSS-F5 — Renderer final e preview

DOCX/OOXML/UNO, fields/TOC/notes/tables/layout, PDF do DOCX definitivo, jobs/preflight/manifest, viewer local e offline runtime. Não liberar final só por existir arquivo.

### OSS-F6 — Paginação visual adicional

Plugin próprio opcional de páginas ao vivo, a partir de contratos/corpus. Manter contínuo+PDF como caminho obrigatório recuperável. Avanço não pode exigir Pro nem mudar hierarquia por resize. Não bloquear entrega documental OSS-F5 se recurso opcional não contratado; comunicar o limite visual.

### OSS-F7 — Hardening, migração e homologação

Regressão semântica/visual, permissões/metadata, selfhost LXC separadas, offline/licenças, restore, migração e manuais. Gates funcionais essenciais e critérios relevantes aprovados. Aceite humano para produção.

Dependências sequenciais, exceto F6 opcional independente de gate final de documentos. Requisitos essenciais F0–F5/F7 obrigatórios. Sem estimativa inventada; capacidade da equipe define prazo.

## 30. Corpus, testes e Definition of Done

Corpus: Art.1º/9º/10/10-A; único→vários; incisos/alíneas/itens; caput em vários paragraphs; cláusula legada; refs cruzadas; tabela longa/mesclada/header/exact/min; landscape annex; primeira/par/ímpar; sumário multipágina; imagem; nota extensa/fim; comentário/deleted text/PII oculta; recurso unsupported; scan OCR; dois tenants/jobs concorrentes.

Unit schema/commands; integration transactions/OOXML/UNO/Storage/RLS; E2E UX; semantic compare; visual rasterizado com ferramenta OSS aprovada; package inspection privacy; font substitution; network blocked; restore e migration rollback.

DoD fase: código/migrations, testes reais, evidências, docs/corpus, licença/segurança verificadas e pendências explícitas. DoD final: arquivos completos/conferidos, nenhum uso Pro/SaaS, nenhuma perda/corte/PII indevida e metadados consistentes. Mocks não são homologação.

## 31. Critérios de aceite consolidados

Identificadores EDOSS substituem requisitos de implementação vinculados a APIs Pro. Regras funcionais anteriores são preservadas ou reinterpretadas como recursos locais. Status inicial de todos é não executado.

### Grupo OSS

| ID | Resultado obrigatório |
|---|---|
| EDOSS-OSS-01 | Nenhuma dependência @tiptap-pro ou registry privado no build/runtime |
| EDOSS-OSS-02 | Nenhum envio documental a serviço externo em operação |
| EDOSS-OSS-03 | SBOM e licenças de dependências/imagens/fontes verificadas |
| EDOSS-OSS-04 | Tiptap público e extensões sem duplicação |
| EDOSS-OSS-05 | Supabase self-hosted é alvo autorizado |
| EDOSS-OSS-06 | Fluxo documental funciona com saída internet bloqueada |
| EDOSS-OSS-07 | Assets e fontes servidos localmente |
| EDOSS-OSS-08 | Nenhum código proprietário copiado para substituição |

### Grupo BL

| ID | Resultado obrigatório |
|---|---|
| EDOSS-BL-01 | Tipos jurídicos e paragraphs textuais separados |
| EDOSS-BL-02 | Um caput inicial por artigo sem duplicar texto |
| EDOSS-BL-03 | UUID estável em mover e renumerar |
| EDOSS-BL-04 | Origem antigo/novo muitos-para-muitos preservada |
| EDOSS-BL-05 | Gramática normalizada e modo legado suportados |
| EDOSS-BL-06 | Enter e Backspace não criam/fundem dispositivos silenciosamente |
| EDOSS-BL-07 | Colagem/importação exige conferência de segmentação |
| EDOSS-BL-08 | Projeção visual não cria segunda fonte de texto |
| EDOSS-BL-09 | Renumeração e único/vários com prévia |
| EDOSS-BL-10 | Referência por UUID/namespace com rótulo atualizado |
| EDOSS-BL-11 | Número ordinal/cardinal/romano/letra/item correto |
| EDOSS-BL-12 | Templates geram UUID novos uma vez e placeholders tipados |

### Grupo ST

| ID | Resultado obrigatório |
|---|---|
| EDOSS-ST-01 | Estilos semânticos versionados e separados do tipo jurídico |
| EDOSS-ST-02 | Fontes/tamanhos/cores/recuos/spaces persistidos |
| EDOSS-ST-03 | pt e px não confundidos |
| EDOSS-ST-04 | Fonte ausente bloqueia final |
| EDOSS-ST-05 | Normalização de importado não é silenciosa |
| EDOSS-ST-06 | Override local mapeado no DOCX/PDF |
| EDOSS-ST-07 | Zoom/gap visual não viram propriedade normativa |
| EDOSS-ST-08 | Snapshot resolve versão de estilo e layout exata |

### Grupo PG

| ID | Resultado obrigatório |
|---|---|
| EDOSS-PG-01 | Quebra manual salva e exportada como instrução |
| EDOSS-PG-02 | Paginação automática não cria nó/revisão jurídica |
| EDOSS-PG-03 | Artigo longo continua sem caixa indivisível |
| EDOSS-PG-04 | Objeto maior que página exige tratamento, não loop |
| EDOSS-PG-05 | Preview final é PDF local do renderer |
| EDOSS-PG-06 | Live layout opcional sem dependência Pro |
| EDOSS-PG-07 | Seção jurídica não é layout Word |
| EDOSS-PG-08 | Margens/orientação/segmentos preservados |

### Grupo HF

| ID | Resultado obrigatório |
|---|---|
| EDOSS-HF-01 | Regiões padrão/first/odd/even salvas e restauradas |
| EDOSS-HF-02 | Vazio explícito não recebe fallback |
| EDOSS-HF-03 | Header/body/layout salvos consistentemente por revisão |
| EDOSS-HF-04 | Permissão servidor para edição de regiões |
| EDOSS-HF-05 | PageNumber/PageCount e dados do snapshot resolvidos |
| EDOSS-HF-06 | Ocultar número na capa não reinicia implicitamente |
| EDOSS-HF-07 | Cursor não muda header global como capítulo corrente |
| EDOSS-HF-08 | Regiões sem autoria de sugestões ou notas internas |

### Grupo NT

| ID | Resultado obrigatório |
|---|---|
| EDOSS-NT-01 | Notas do documento separadas de observações privadas |
| EDOSS-NT-02 | Marcador noteId e corpo persistidos consistentemente |
| EDOSS-NT-03 | Numeração por ordem do snapshot independente de UUID |
| EDOSS-NT-04 | Editor auxiliar próprio respeita permissão |
| EDOSS-NT-05 | Undo/history preservados sem cleanup indiscriminado |
| EDOSS-NT-06 | Export usa notas referenciadas e detecta ausência/órfã |
| EDOSS-NT-07 | DOCX tem notas reais e relações OOXML válidas |
| EDOSS-NT-08 | Nota longa sem corte; incompatibilidade bloqueia final |
| EDOSS-NT-09 | Nenhum comando Pro presumido existente |
| EDOSS-NT-10 | Notas sem nesting/ciclo ambíguo |

### Grupo TB

| ID | Resultado obrigatório |
|---|---|
| EDOSS-TB-01 | Tabela pública OSS em editor contínuo |
| EDOSS-TB-02 | Mescla/colWidth/altura/padding/align persistidos |
| EDOSS-TB-03 | Header semântico e repetição são propriedades distintas |
| EDOSS-TB-04 | Preset/bordas/shading versionados, não só CSS |
| EDOSS-TB-05 | Linha fragmentada no renderer não duplica JSON |
| EDOSS-TB-06 | Altura exata que corta bloqueia final |
| EDOSS-TB-07 | Imagem em célula não cortada/empurrada infinitamente |
| EDOSS-TB-08 | Continuação de mescla mantém bordas/fundos conferidos |
| EDOSS-TB-09 | Cabeçalho repetido homologado no PDF |
| EDOSS-TB-10 | Fragmentação live não depende de PagesTableKit Pro |
| EDOSS-TB-11 | Redimensionamento preserva conteúdo e alerta largura inválida |
| EDOSS-TB-12 | Export não contém clones/spacers de view |

### Grupo IM

| ID | Resultado obrigatório |
|---|---|
| EDOSS-IM-01 | Original privado com hash e versão preservados |
| EDOSS-IM-02 | DOCX parsing inclui estilos/layout/notas/refs/tabelas |
| EDOSS-IM-03 | Track changes com escolha explícita da visão |
| EDOSS-IM-04 | Comentários importados privados |
| EDOSS-IM-05 | Recurso unsupported com diagnóstico sem perda silenciosa |
| EDOSS-IM-06 | PDF/OCR não declarado reconstrução universal perfeita |
| EDOSS-IM-07 | Fontes/dados registrais não inventados na importação |
| EDOSS-IM-08 | Relacionamentos remotos/macros/fields perigosos não executados |

### Grupo EX

| ID | Resultado obrigatório |
|---|---|
| EDOSS-EX-01 | PDF gerado do DOCX definitivo entregue |
| EDOSS-EX-02 | Fields/sumário resolvidos antes de final |
| EDOSS-EX-03 | Snapshot único durante job inteiro |
| EDOSS-EX-04 | Placeholder/perda/ref bloqueante impede pronto |
| EDOSS-EX-05 | Par DOCX/PDF tem manifesto e hashes |
| EDOSS-EX-06 | Rerender de conferência e regressão semântica/visual |
| EDOSS-EX-07 | Público sem PII/notas/comments/deleted/hidden metadata |
| EDOSS-EX-08 | Font/template/renderer fixos e registrados |
| EDOSS-EX-09 | Cache inclui versões, opções e tenant |
| EDOSS-EX-10 | Falha não entrega arquivo parcial como final |

### Grupo OP

| ID | Resultado obrigatório |
|---|---|
| EDOSS-OP-01 | Worker com perfil/temp isolados por job |
| EDOSS-OP-02 | Serviço sem rede externa livre e XML/ZIP seguro |
| EDOSS-OP-03 | Runtime DB limitado e tenant checado no worker |
| EDOSS-OP-04 | StoragePort remoto sem filesystem compartilhado presumido |
| EDOSS-OP-05 | Migração preserva IDs/sugestões/revisões e permite rollback |
| EDOSS-OP-06 | Backup/restore inclui banco/objetos/templates/config |
| EDOSS-OP-07 | Duas LXC homologadas sem mudança de domínio |
| EDOSS-OP-08 | Instalador preserva volumes/segredos sem seed produtivo |
| EDOSS-OP-09 | AGENTS módulo e prompt não relaxam privacidade |
| EDOSS-OP-10 | Ausência de voto/quórum funcional e texto jurídico correspondente permitido |

## 32. Instruções mandatórias para agentes

Ler PRD mestre/AGENTS e este complemento completo. Em conflito, a exigência atual full self-hosted/open source prevalece nas escolhas do subsistema. Não interpretar demonstrações anteriores com @tiptap-pro como autorização de implementação.

Inventariar código real, separar atendido/parcial/ausente/incompatível, produzir gap/ADRs/licenças e plano por OSS-F. Não substituir biblioteca fechada por pacote sem licença verificada. Não anunciar recurso implementado por existir endpoint/botão.

Implementar em loop pequeno→teste→correção→evidência; após cinco tentativas não convergentes relatar bloqueio. Dado fictício/sandbox por padrão. Sem envio real, dado privado externo, produção, migração destrutiva, rotação/DNS/Proxmox sem autorização. Backup/rollback antes de risco.

Fonte única de texto/style/layout/notas. Migrations SQL app conforme arquitetura, não catálogo Auth paralelo. Artefato exportado é derivado, não novo banco. APIs próprias possuem testes, não nomes Pro renomeados sem implementação.

Entregar: atualização funcional, migração compatível, editor aberto, notas/regiões/tabelas, renderer local, exemplares fictícios DOCX/PDF conferidos, SBOM, manifests, manuais e matriz com resultados reais. Este pacote fornece especificação/modelos/prompts, não esses componentes executáveis.

## 33. Uso do pacote e plano de atualização

Copiar documentação para repositório preservando originais. Fonte deste complemento em docs/prd/PRD_Complementar_ED_OSS_2_0.md. Módulo documental recebe core/domain/documents/AGENTS.md sem sobrescrever instruções globais. Atualizar AGENTS raiz/Core para referenciar o complemento e a proibição Pro/runtime externo.

Primeiro prompt: auditoria/licenças e prova de conceito OSS-F0. Depois fases pelos gates. Se código já usa Pro, produzir adaptação/retirada com migração de dados, não remover de modo destrutivo sem substituição/limitação aprovada.

Lista de modelos deste pacote contém esqueletos com campos pendentes, não Convenção/Regimento válidos ou aprovados. Catálogos JSON são contratos de desenvolvimento; não são plugins executáveis. Todos UUID de instância ilustrativa são substituídos na instanciação real.

## 34. Checklist final e limite de garantia

- [ ] Nenhuma dependência Pro/fechada obrigatória ou saída documental SaaS.
- [ ] Licenças/SBOM/versões/fontes aprovados.
- [ ] Modelo normativo fiel, legado preservado e IDs estáveis.
- [ ] Templates completos como estrutura, sem conteúdo jurídico inventado.
- [ ] Estilos/layout/regiões/notas/tabelas versionados e editáveis.
- [ ] Importação com relatório e zero perda silenciosa.
- [ ] DOCX finalizado e PDF derivado dele, conferidos.
- [ ] Preflight/preview/manifest e privacidade completa.
- [ ] Testes reais, migração/rollback e restore aprovados.
- [ ] Operação selfhost com serviços separados e runtime sem saída externa testada.
- [ ] Manual, prompts/AGENTS e matriz atualizados.

Garantia é por capacidade declarada, corpus e renderer homologado. Não prometer identidade universal entre motores nem documento juridicamente aprovado. Trabalho completo preserva o caminho fonte→minuta→revisões/contribuições→snapshot→DOCX/PDF, com controle e rastreabilidade.
