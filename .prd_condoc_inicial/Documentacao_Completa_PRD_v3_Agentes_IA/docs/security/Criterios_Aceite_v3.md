# Aceite — extração do PRD mestre v3.0

## 32. Critérios de aceite, rastreabilidade e testes

Os identificadores anteriores são preservados por compatibilidade. Sobreposição é intencional; um teste pode cobrir vários IDs. A matriz deve ser completada com implementação, teste executado, evidência e resultado. Ter uma linha na matriz não significa teste aprovado.

### Grupo CA

| ID | Resultado obrigatório |
|---|---|
| CA-01 | Acesso entre condomínios negado no servidor e arquivos |
| CA-02 | Cadastro manual cria registro prévio sem credencial automática |
| CA-03 | Upload cadastral não modifica antes da confirmação |
| CA-04 | Unidade desconhecida não é criada silenciosamente |
| CA-05 | Reenvio de confirmação não duplica registros |
| CA-06 | Conta em outro condomínio não é revelada |
| CA-07 | Convite por unidade fixa unidade e mantém contas individuais |
| CA-08 | Convite amplo exige conferência de vínculo |
| CA-09 | Individual pré-conferido exige contato previsto confirmado |
| CA-10 | GET no convite não consome nem autentica |
| CA-11 | Revogação bloqueia resgate sem apagar perfil ativado |
| CA-12 | Dados incompletos não habilitam interação |
| CA-13 | Vários moradores podem ter vínculos na mesma unidade |
| CA-14 | Pessoa com várias unidades não ganha concordâncias extras |
| CA-15 | Confirmar e-mail não valida vínculo declarado |
| CA-16 | Mudança de unidade preserva referência das interações anteriores |
| CA-17 | Original documental preservado com conferência humana |
| CA-18 | Corrigir transcrição gera versão e não simula alteração normativa |
| CA-19 | Dispositivo incluído não inventa origem |
| CA-20 | Excluído sai do limpo e permanece em histórico e DePara |
| CA-21 | Desmembrar/consolidar preserva relação muitos-para-muitos |
| CA-22 | Renumerar preserva referência e comentários |
| CA-23 | Edição concorrente gera conflito sem sobrescrita |
| CA-24 | Nota interna ausente em API e export público |
| CA-25 | Sugestão privada recebe protocolo e versão consultada |
| CA-26 | Conselho analisa conteúdo sem identidade |
| CA-27 | Análise não publica automaticamente |
| CA-28 | Admin sem papel de síndico não publica |
| CA-29 | Toggle global mostra apenas versões autorizadas |
| CA-30 | Complemento privado e moderado independentemente |
| CA-31 | Edição publicada cria versão pendente |
| CA-32 | Ocultação bloqueia API link busca listagem e interação |
| CA-33 | Identidade exige permissão e auditoria |
| CA-34 | Anexo não publica automaticamente |
| CA-35 | Cliques repetidos produzem uma concordância ativa |
| CA-36 | Retirada atualiza agregado e preserva evento |
| CA-37 | Mudança substancial não transfere concordâncias |
| CA-38 | Contagem oculta ausente no payload |
| CA-39 | Estatística explicita texto versão corte denominador e ressalva |
| CA-40 | Incorporação liga revisão e contribuição atomicamente |
| CA-41 | Snapshot imutável e reproduzível |
| CA-42 | Documento limpo sem identidade notas ou referência antiga indevida |
| CA-43 | Distribuição restrita e envio real confirmado |
| CA-44 | Banco e objetos restaurados consistentemente |
| CA-45 | Nenhuma votação apuração ou cálculo de quórum |

### Grupo UI

| ID | Resultado obrigatório |
|---|---|
| UI-01 | Troca de condomínio limpa contexto |
| UI-02 | Menu e backend respeitam permissões |
| UI-03 | Telas têm loading vazio erro e acesso negado |
| UI-04 | Confirmação mostra alvo e efeito |
| UI-05 | Dashboard sem identidade ou contatos |
| UI-06 | Pré-cadastro distinto de conta ativada |
| UI-07 | Importação exige prévia |
| UI-08 | Relatório por linha sem envio automático |
| UI-09 | Contato vínculo participação em estados separados |
| UI-10 | Convite informa validade e revogação |
| UI-11 | Link não revela cadastro antes de verificação |
| UI-12 | Original somente leitura e minuta editável |
| UI-13 | Salvo depende de resposta do servidor |
| UI-14 | Conflito não sobrescreve |
| UI-15 | Novo dispositivo sem origem fictícia |
| UI-16 | Renumeração com impacto |
| UI-17 | Snapshot sem edição direta |
| UI-18 | Nota restrita ausente no portal e limpo |
| UI-19 | Portal usa snapshot da campanha |
| UI-20 | Sugestão privada com protocolo |
| UI-21 | Autor acompanha sem notas internas |
| UI-22 | Quatro dimensões da sugestão separadas |
| UI-23 | Revisor não recebe identidade pela API |
| UI-24 | Só síndico publica |
| UI-25 | Prévia pública sem autor unidade avatar contato |
| UI-26 | Complemento moderado |
| UI-27 | Edição publicada pendente |
| UI-28 | Concordância avisa caráter consultivo e versão |
| UI-29 | Alteração substancial sem transferência |
| UI-30 | Contagem oculta não enviada |
| UI-31 | Estatística corte versão denominador |
| UI-32 | Ausência de tela eleitoral |
| UI-33 | Exports distinguem restrito e público |
| UI-34 | Consulta identidade e export pessoal auditadas |
| UI-35 | Mobile e teclado completos |
| UI-36 | Ocultação bloqueia todas as superfícies |
| UI-37 | Falha recuperável sem duplicação |
| UI-38 | Publicação não é aprovação normativa |

### Grupo V21

| ID | Resultado obrigatório |
|---|---|
| V21-01 | Acesso fora do tenant negado inclusive arquivo |
| V21-02 | Revisor privado sem autoria |
| V21-03 | Admin prepara mas não autoriza publicação |
| V21-04 | Síndico autoriza versão exata com auditoria |
| V21-05 | Papel de síndico encerrado perde poder |
| V21-06 | Upload cria lote sem alterar cadastros |
| V21-07 | Formato disfarçado rejeitado |
| V21-08 | Zeros iniciais preservados |
| V21-09 | Mapping alterado invalida prévia |
| V21-10 | Conflito não aplicado sem resolução |
| V21-11 | Nome telefone não fundem pessoas |
| V21-12 | Contato não revela conta externa |
| V21-13 | Revisão antiga rejeita confirmação |
| V21-14 | Mesma chave não duplica |
| V21-15 | Mesma chave com conteúdo diferente retorna conflito |
| V21-16 | Falha impeditiva reverte lote |
| V21-17 | Importação não envia convites |
| V21-18 | Pré-cadastro não gera credencial |
| V21-19 | GET não resgata convite |
| V21-20 | Compartilhado exige conta e conferência |
| V21-21 | Contato não valida residência |
| V21-22 | Pré-conferido corresponde ao contato previsto |
| V21-23 | Revogação impede novos resgates |
| V21-24 | Revogar convite não suspende conta |
| V21-25 | Incompleto não interage |
| V21-26 | Sugestão privada com versão consultada |
| V21-27 | Complemento privado independente |
| V21-28 | Edição publicada cria revisão |
| V21-29 | Nova versão substancial não herda apoio |
| V21-30 | Várias unidades não multiplicam apoio |
| V21-31 | Contagem oculta não enviada |
| V21-32 | Autor não recebe notas internas |
| V21-33 | Identidade autorizada e auditada |
| V21-34 | Relatório com ressalvas e corte |
| V21-35 | Público sem notas e contatos |
| V21-36 | Ocultação bloqueia API busca link |
| V21-37 | Incorporação consistente |
| V21-38 | Jornadas mobile completas |
| V21-39 | Suspenso não interage |
| V21-40 | Ausência de rotas eleitorais |

### Grupo AR

| ID | Resultado obrigatório |
|---|---|
| AR-01 | Domínio igual em Cloud e selfhost homologados |
| AR-02 | Web e Core juntos ou separados por configuração |
| AR-03 | Nenhum host IP ou caminho produtivo hardcoded |
| AR-04 | Auth Supabase única origem |
| AR-05 | Frontend sem acesso a tabela de negócio |
| AR-06 | Nenhum segredo em browser logs git |
| AR-07 | Runtime sem BYPASSRLS superuser ownership |
| AR-08 | RLS nega contexto ausente ou tenant alheio |
| AR-09 | Pool não transfere contexto entre usuários tenants |
| AR-10 | Storage privado e acesso autorizado |
| AR-11 | Migrations SQL fonte única |
| AR-12 | Rerun preserva dados segredos volumes |
| AR-13 | Credencial inválida falha antes de mudanças parciais |
| AR-14 | Backup e restore com objetos |
| AR-15 | Auth redirects MFA testados nos dois modos |
| AR-16 | AGENTS raiz e Core coerentes |
| AR-17 | Migração modalidade com teste e rollback |
| AR-18 | Nenhuma função eleitoral |

### Estratégia de verificação

Unitários de estados/normalização/regras; integração de transações/constraints/RLS/tasks/Storage; E2E de jornadas; negativos de tenant/PII; concorrência de resgate/acordo; inspeção de exportações; carga; restauração e recuperação da exportação estruturada.

Massa: homônimos, telefone compartilhado, conta em dois condomínios, e-mail já existente, zeros/alfanumérico, registro incompleto, unidade inativa, OCR errado, número duplicado, referência removida, sugestão com identificação pessoal, edição substancial, URL de anexo expirando e pool reutilizado.

Definition of Done de fase: código, migrations, tests, docs, seed fictício, evidência, permissões verificadas e pendências explícitas. Mock não equivale a integração homologada. Gate final requer todos testes relevantes e aceite operacional humano; build verde não significa produção segura.
