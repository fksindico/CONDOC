# Contrato API — extração do PRD mestre v3.0

Fonte normativa: docs/prd/PRD_Mestre_v3.md.

## 30. API geral e contrato da importação

### 30.1. Padrões

REST JSON /api/v1, sessão BFF segura, CSRF, paginação, filtros validados, versões/ETag e request_id. OpenAPI deve refletir implementação. Campos públicos/administrativos distintos. Erros code/message/field_errors/request_id sem segredos e sem enumeração de outros tenants.

GET sem side effects. Mutações têm autorização e confirmação conforme UI. Idempotency-Key para operações com risco de duplicação; escopo actor+tenant+endpoint+key, hash do payload. Mesmo conteúdo devolve resultado anterior, diferente retorna 409. Retenção operacional da chave documentada e configurável.

### 30.2. Endpoints de domínio

- /condominiums/{id}/buildings, /units, /resident-registrations, /residents, /memberships.
- /memberships/{id}/review, /suspend, /end.
- /invitations, /invitations/batch, /invitations/{id}/revoke, /distribution-export.
- /access/invitations/inspect e /redeem; /access/login/request e callback/confirm definidos pelo Auth escolhido.
- /projects, /documents, /source-imports, /source-transcriptions/{id}/confirm.
- /provisions, /provisions/{id}/revisions, /origin-mappings, /snapshots, /exports.
- /campaigns, /campaign-participants, /suggestions, /suggestions/{id}/revisions e /review.
- /publication-authorizations, /published-suggestions/{public_id}/hide, /incorporations.
- /published-suggestions/{public_id}/complements e /agreement.
- /me/profile, /me/memberships, /me/suggestions, /me/agreements.
- /statistics/snapshots, /audit, /identity-access.

PUT agreement ativa, DELETE retira, ambos idempotentes e vinculados à versão. Recursos tenant podem usar prefixo explícito /condominiums/{id}; não confiar no prefixo sem checagem.

Transações: resgate/contagem/associação; vínculo/evento; publicação/decisão; acordo/evento; incorporação/revisão/vínculo; snapshot/itens. Não salvar estado parcial.

DTO público exemplo:

```json
{
  "public_id": "sg_identificador_opaco",
  "version": 2,
  "theme": "Áreas comuns",
  "provision_label": "Art. 22",
  "text": "Texto autorizado para consulta",
  "editorial_status": "under_analysis",
  "shared_response": null,
  "can_agree": true,
  "can_complement": true
}
```

Não enviar identidade nem aggregate quando oculto. Alvo não autorizado/oculto não expõe conteúdo em erro.

### 30.3. Estados da importação

received → parsing → awaiting_mapping → validating → awaiting_review → applying → completed. failed/cancelled adicionais. Completo informa operações aplicadas e linhas excluídas, não sucesso fictício para todas.

Base: /api/v1/condominiums/{condominium_id}/resident-imports.

| Método/rota relativa | Contrato |
|---|---|
| GET /template?format=csv ou xlsx | Modelo fictício |
| POST / | multipart file/source_label; chave idempotente; 202 com id/status/revision |
| GET /{id} | Status, totais e operação atual |
| PUT /{id}/mapping | JSON mapping, sheet/header/CSV opções; If-Match, nova revisão/validação |
| GET /{id}/rows | Classificação/filtros/paginação; dados restritos |
| PATCH /{id}/rows/{row_id} | Seleção/ação/motivo/target esperado; If-Match |
| GET /{id}/preview | Totais e can_confirm, revisão |
| POST /{id}/confirm | expected_revision, acknowledgment; If-Match e idempotência; 202 |
| POST /{id}/cancel | Apenas não aplicado; não cancelar transação parcialmente |
| GET /{id}/report | Relatório restrito |

### 30.4. Mapeamento e resolução

```json
{
  "sheet": "Moradores",
  "header_row": 1,
  "columns": {
    "nome": "Nome completo",
    "torre_bloco": "Bloco",
    "unidade": "Apartamento",
    "telefone": "Celular",
    "email": "Email",
    "relacao": "Tipo"
  },
  "csv_options": null
}
```

Ações conforme classificação: create_registration, update_registration, add_registration_for_unit, skip, request_manual_review. Update exige target e versão; sem merge genérico. Dados ativados divergentes viram conflito. Alteração de mapping/decisão incrementa revision e invalida prévia.

Row DTO: id, row_number, classification, selected, normalized_data restrito, issues(code/message), allowed_actions, proposed_action e target/version quando permitido. Linha desconhecida/erro bloqueante não selecionável sem resolução.

Prévia:

```json
{
  "revision": 5,
  "status": "awaiting_review",
  "summary": {
    "total_rows": 120,
    "selected_rows": 105,
    "create_registrations": 90,
    "update_registrations": 10,
    "add_unit_registrations": 5,
    "skipped_rows": 15,
    "selected_blocking_issues": 0
  },
  "can_confirm": true,
  "sends_invitations": false,
  "creates_credentials": false
}
```

Confirmar com expected_revision e acknowledge_selected_operations=true. Rever targets/permissões no processamento, exclusão mútua no lote. Falha impeditiva reverte conjunto e retorna para nova prévia ou failed com motivo. Relatório pode ser regenerado sem reaplicar lote.

### 30.5. HTTP e erros

202 é aceitação para processamento, não conclusão. 400 malformed, 401 sessão inválida, 403 operação proibida no escopo acessível, 404 fora do escopo/inexistente, 409 domínio/idempotência, 412 If-Match desatualizado, 413 limite, 415 formato, 422 dados semânticos, 429 rate limit. Semântica fundamentada em HTTP. [web:103]

```json
{
  "code": "IMPORT_PREVIEW_OUTDATED",
  "message": "A prévia mudou. Revise antes de confirmar.",
  "field_errors": {},
  "request_id": "req_identificador_opaco"
}
```

### 30.6. Autorização da importação

Exigir sessão administrativa, papel no tenant, resident.import e contact/identity necessários. Fonte/relatório privados. Nome de arquivo não vira storage path confiável. Limitar descompactação XLSX/tempo/memória além do tamanho de upload. Rejeitar macro/fórmula executável; não confiar em MIME declarado. [web:105]
