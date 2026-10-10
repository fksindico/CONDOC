# Plano de fases — extração do PRD mestre v3.0

## 31. Fases de desenvolvimento e gates

O MVP completo abrange fases 0 a 8. A fase 9 é opcional. Não estimar prazo sem capacidade real. Uma fase isolada não é produto completo.

### Fase 0 — Preparação e contratos

Dependências: Nenhuma.

Entregas: Repositório, inventário/gap analysis, ADR Supabase/BFF/RLS/migrations, versões e lockfiles, Docker de desenvolvimento, contrato API, protótipos, AGENTS, massa fictícia, hardware e carga de referência.

Gate de conclusão: Build base reproduzível; nenhum segredo; matriz de critérios; plataforma e DB role definidos; contratos sem votação.

Critérios de referência: AR-03, AR-11, AR-16, AR-18.

### Fase 1 — Identidade e estrutura física

Dependências: 0.

Entregas: Supabase Auth/BFF/MFA, papéis/permissões, RLS/contexto de pool, condomínio/torres/unidades, pré-cadastro manual, perfis/vínculos e validação auditada.

Gate de conclusão: Testes positivos e negativos de Auth, tenant e identidade; unidade/cadastro/vínculo sem misturar conta; sem Auth mock como integração concluída.

Critérios de referência: CA-01, CA-02, CA-06, CA-12 a CA-16, CA-33; AR-04 a AR-09.

### Fase 2 — Importação cadastral e convites

Dependências: 1.

Entregas: CSV/XLSX e modelo, mapping, prévia/conflitos, transação/idempotência, relatório, convites, resgate, associação, distribuição e SMTP opcional em sandbox.

Gate de conclusão: Arquivo malicioso/formulas/zeros, reenvio, contato incompleto, account existente, limite concorrente e revogação; jornada completa sem envio automático.

Critérios de referência: CA-03 a CA-11, CA-43; V21-06 a V21-25.

### Fase 3 — Núcleo documental

Dependências: 1; preferir após 2.

Entregas: Projeto/documento, arquivo original Storage, OCR/transcrição, estrutura, editor/revisões, notas/campos, conflitos e snapshot básico.

Gate de conclusão: Criar novo e revisar importado, recuperar task, árvore sem ciclos, snapshot reproduzível e nota privada.

Critérios de referência: CA-17, CA-18, CA-23, CA-24, CA-41; AR-10.

### Fase 4 — Comparação e exportação

Dependências: 3.

Entregas: Lado a lado/diferenças, classes de alteração, origem múltipla, referências/numeração, pendências, PDF/DOCX/DePara.

Gate de conclusão: Demonstrar todas as classes, novo sem origem, exclusão/consolidação/desmembramento, renumeração e exports conferidos.

Critérios de referência: CA-19 a CA-22, CA-42; UI-12 a UI-18.

### Fase 5 — Consulta e moderação

Dependências: 2 e 4.

Entregas: Campanha em snapshot, habilitação, portal, rascunhos/sugestões, quatro estados, esclarecimentos, versão sanitizada, autorização do síndico, ocultação e complemento.

Gate de conclusão: Privada→análise→publicação; revisor sem identidade, autor sem notas, toggle não publica pendentes e anexos sem automação.

Critérios de referência: CA-25 a CA-34; V21-26 a V21-28, V21-32, V21-36.

### Fase 6 — Concordâncias e consolidação

Dependências: 5.

Entregas: Acordo por versão/retirada/eventos, métricas pessoa/unidade, contagens ocultas, fotografia, substancialidade e incorporação transacional.

Gate de conclusão: Sem duplicação ou transferência, invalidação de vínculo preserva histórico, snapshot estatístico substitutivo e linguagem não eleitoral.

Critérios de referência: CA-35 a CA-40, CA-45; V21-29 a V21-31, V21-34, V21-37.

### Fase 7 — Preservação e publicação de conteúdo

Dependências: 6.

Entregas: Final de trabalho, leitura autorizada, pacote externo, relatório interno, JSON/manifesto, arquivo informativo externo, retenção/exportação.

Gate de conclusão: Recuperar estrutura exportada, separar identidade do público, nenhuma deliberação formal introduzida.

Critérios de referência: CA-41, CA-42, CA-45; UI-33, UI-38.

### Fase 8 — Hardening e produção

Dependências: 7.

Entregas: Homologação Cloud/selfhost e web/Core separados, instalador/doctor, carga, acessibilidade, monitoramento, backup/restauração, retenção, manuais e rollback.

Gate de conclusão: Todos critérios aplicáveis aprovados; restauração real em teste; MFA/segredos/rede; metas medidas; liberação humana expressa.

Critérios de referência: Todos CA/UI/V21/AR.

### Fase 9 — Evoluções opcionais

Dependências: MVP aceito e nova decisão de escopo.

Entregas: IA supervisionada, edição simultânea avançada, integrações autorizadas e modelos revisados. Sem votação também nesta fase.

Gate de conclusão: Novo planejamento/testes e ADR sem relaxar privacidade e missão. Não faz parte da entrega inicial.

Critérios de referência: Critérios afetados e regressão completa.

Piloto: massa fictícia com 2 torres, 10 unidades, vários moradores por unidade, pessoa em múltiplas unidades/condomínios, documento de 30 dispositivos e 20 sugestões diversas. Quantidades são cenário de teste, não limite operacional. Usar dado real somente com autorização e política definida.
