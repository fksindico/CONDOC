"""
Serviços de Aplicação para Importação Cadastral — CONDC (Fase 2)
Implementa o fluxo de upload, mapeamento, classificação, prévia e aplicação atômica de lotes.
Critérios atendidos: CA-03 a CA-05; V21-06 a V21-18; ADR-003, ADR-004.
"""
import csv
import io
import hashlib
import uuid
from typing import Optional, Dict, Any, List, Tuple
from django.db import transaction
from django.utils import timezone

from infrastructure.models import (
    Condominium,
    Building,
    Unit,
    Account,
    ResidentRegistration,
    ImportBatch,
    ImportRow,
)
from domain.identity.invariants import assert_same_tenant
from domain.imports.invariants import (
    assert_no_formula_injection,
    preserve_textual_code,
    assert_revision_matches,
    sanitize_csv_cell,
)
from domain.imports.exceptions import (
    FormulaInjectionDetectedError,
    ImportPreviewOutdatedError,
    InvalidImportFileError,
    UnknownUnitError,
    UnresolvedConflictError,
    BatchAlreadyProcessedError,
)

MAX_IMPORT_FILE_SIZE = 10 * 1024 * 1024  # 10 MB (PRD 8)

class ImportService:
    @classmethod
    def create_batch_from_file(
        cls,
        condominium_id: uuid.UUID,
        file_obj,
        actor_id: uuid.UUID,
        file_name: str,
        source_label: str = 'upload_manual'
    ) -> ImportBatch:
        """
        CA-03, V21-06: Upload de arquivo cria o lote de importação SEM alterar cadastros.
        Valida tamanho, integridade, injeção de fórmulas e preserva zeros à esquerda.
        """
        content = file_obj.read()
        if len(content) > MAX_IMPORT_FILE_SIZE:
            raise InvalidImportFileError("Arquivo excede o limite máximo permitido de 10 MB.")

        if len(content) == 0:
            raise InvalidImportFileError("Arquivo de importação está vazio.")

        file_hash = hashlib.sha256(content).hexdigest()

        # Decodifica conteúdo texto (suporta UTF-8 e UTF-8 com BOM)
        try:
            text_stream = io.StringIO(content.decode('utf-8-sig'))
        except UnicodeDecodeError:
            try:
                text_stream = io.StringIO(content.decode('latin-1'))
            except Exception as e:
                raise InvalidImportFileError(f"Codificação de arquivo não suportada: {str(e)}")

        # Detecta delimitador (vírgula ou ponto-e-vírgula)
        sample = text_stream.read(2048)
        text_stream.seek(0)
        delimiter = ';' if sample.count(';') > sample.count(',') else ','

        reader = csv.reader(text_stream, delimiter=delimiter)
        rows_list = list(reader)

        if not rows_list or len(rows_list) < 2:
            raise InvalidImportFileError("O arquivo deve conter pelo menos uma linha de cabeçalho e uma linha de dados.")

        header = [preserve_textual_code(c) for c in rows_list[0]]
        data_rows = rows_list[1:]

        # Cria lote com status 'awaiting_mapping'
        batch = ImportBatch.objects.create(
            condominium_id=condominium_id,
            file_name=file_name,
            file_hash=file_hash,
            source_label=source_label,
            status='awaiting_mapping',
            revision=1,
            created_by_id=actor_id
        )

        # Sugere mapeamento padrão com base nos nomes das colunas
        default_mapping = cls._detect_columns_mapping(header)
        batch.mapping = {
            "header_row": 1,
            "columns": default_mapping,
            "delimiter": delimiter
        }
        batch.save(update_fields=['mapping'])

        # Cria as linhas ImportRow e valida injeção de fórmulas
        import_rows_to_create = []
        for idx, row in enumerate(data_rows, start=2):
            raw_dict = {}
            for col_idx, col_name in enumerate(header):
                val = row[col_idx] if col_idx < len(row) else ""
                # Preserva zeros à esquerda e valida injeção de fórmula
                val_text = preserve_textual_code(val)
                assert_no_formula_injection(val_text)
                raw_dict[col_name] = val_text

            import_rows_to_create.append(
                ImportRow(
                    batch=batch,
                    row_number=idx,
                    raw_data=raw_dict,
                    normalized_data={},
                    classification='nova_pendente',
                    selected=True,
                    action='create_registration'
                )
            )

        ImportRow.objects.bulk_create(import_rows_to_create)

        # Classifica as linhas e calcula os totais da prévia
        cls.classify_and_validate_batch(batch.id)
        batch.refresh_from_db()
        return batch

    @classmethod
    def _detect_columns_mapping(cls, header: List[str]) -> Dict[str, str]:
        """Detecta heuristicamente as colunas canônicas no cabeçalho."""
        mapping = {
            "nome": "",
            "unidade": "",
            "torre_bloco": "",
            "telefone": "",
            "email": "",
            "relacao": ""
        }
        for col in header:
            col_lower = col.lower().strip()
            if col_lower in ('nome', 'nome completo', 'morador', 'titular') and not mapping["nome"]:
                mapping["nome"] = col
            elif col_lower in ('unidade', 'apartamento', 'apto', 'casa', 'sala') and not mapping["unidade"]:
                mapping["unidade"] = col
            elif col_lower in ('torre', 'bloco', 'torre/bloco', 'edificio', 'predio') and not mapping["torre_bloco"]:
                mapping["torre_bloco"] = col
            elif col_lower in ('telefone', 'celular', 'whatsapp', 'fone') and not mapping["telefone"]:
                mapping["telefone"] = col
            elif col_lower in ('email', 'e-mail', 'correio eletronico') and not mapping["email"]:
                mapping["email"] = col
            elif col_lower in ('relacao', 'relação', 'tipo', 'vinculo', 'categoria') and not mapping["relacao"]:
                mapping["relacao"] = col
        return mapping

    @classmethod
    @transaction.atomic
    def update_mapping(
        cls,
        condominium_id: uuid.UUID,
        batch_id: uuid.UUID,
        mapping_data: Dict[str, Any],
        actor_id: uuid.UUID
    ) -> ImportBatch:
        """
        V21-09: Alteração de mapeamento incrementa a revisão e invalida a prévia anterior.
        """
        batch = ImportBatch.objects.select_for_update().get(id=batch_id, condominium_id=condominium_id)
        if batch.status in ('completed', 'cancelled'):
            raise BatchAlreadyProcessedError("Lote já finalizado ou cancelado não permite alteração de mapeamento.")

        batch.mapping = mapping_data
        batch.revision += 1
        batch.save(update_fields=['mapping', 'revision', 'updated_at'])

        cls.classify_and_validate_batch(batch_id)
        batch.refresh_from_db()
        return batch

    @classmethod
    @transaction.atomic
    def classify_and_validate_batch(cls, batch_id: uuid.UUID) -> None:
        """
        Classifica cada linha do lote contra a base física e cadastral do condomínio.
        CA-04: Unidade desconhecida não é criada silenciosamente e gera problema bloqueante.
        """
        batch = ImportBatch.objects.select_for_update().get(id=batch_id)
        condominium_id = batch.condominium_id
        mapping = batch.mapping.get("columns", {})

        col_nome = mapping.get("nome")
        col_unidade = mapping.get("unidade")
        col_bloco = mapping.get("torre_bloco")
        col_tel = mapping.get("telefone")
        col_email = mapping.get("email")
        col_rel = mapping.get("relacao")

        # Carrega unidades existentes do condomínio em memória para checagem rápida
        units = list(Unit.objects.filter(condominium_id=condominium_id).select_related('building'))
        # Mapeia por (código da unidade, código do prédio ou None) e por (código da unidade)
        units_by_code_and_building = {}
        units_by_code = {}
        for u in units:
            b_code = u.building.code.upper() if u.building else None
            u_code = u.code.upper()
            if b_code:
                units_by_code_and_building[(u_code, b_code)] = u
            units_by_code[u_code] = u

        # Carrega cadastros prévios existentes do condomínio
        existing_registrations = list(ResidentRegistration.objects.filter(condominium_id=condominium_id).select_related('unit'))

        totals = {
            "total_rows": 0,
            "selected_rows": 0,
            "create_registrations": 0,
            "update_registrations": 0,
            "add_unit_registrations": 0,
            "skipped_rows": 0,
            "blocking_issues": 0
        }

        rows = list(batch.rows.all().order_by('row_number'))
        seen_in_file = set()

        for r in rows:
            totals["total_rows"] += 1
            raw = r.raw_data

            nome = preserve_textual_code(raw.get(col_nome, "")) if col_nome else ""
            unidade_code = preserve_textual_code(raw.get(col_unidade, "")).upper() if col_unidade else ""
            bloco_code = preserve_textual_code(raw.get(col_bloco, "")).upper() if col_bloco else ""
            telefone = preserve_textual_code(raw.get(col_tel, "")) if col_tel else ""
            email = preserve_textual_code(raw.get(col_email, "")).lower() if col_email else ""
            relacao = preserve_textual_code(raw.get(col_rel, "")) if col_rel else "proprietario_residente"

            normalized = {
                "nome": nome,
                "unidade": unidade_code,
                "torre_bloco": bloco_code,
                "telefone": telefone,
                "email": email,
                "relacao": relacao or "other_authorized"
            }
            r.normalized_data = normalized

            issues = []
            classification = 'nova_pendente'
            action = 'create_registration'
            selected = True
            target_reg = None

            # 1. Validação de formato básico (nome e unidade obrigatórios)
            if not nome or not unidade_code:
                classification = 'formato_invalido'
                issues.append({
                    "code": "MISSING_REQUIRED_FIELDS",
                    "message": "Nome completo e número da unidade são campos obrigatórios.",
                    "severity": "blocking"
                })
                selected = False
                action = 'skip'

            # 2. Validação da unidade física existente (CA-04)
            unit_obj = None
            if unidade_code:
                if bloco_code and (unidade_code, bloco_code) in units_by_code_and_building:
                    unit_obj = units_by_code_and_building[(unidade_code, bloco_code)]
                elif unidade_code in units_by_code:
                    unit_obj = units_by_code[unidade_code]

                if not unit_obj and classification != 'formato_invalido':
                    # CA-04: Unidade desconhecida NÃO é criada silenciosamente
                    classification = 'unidade_desconhecida'
                    issues.append({
                        "code": "UNKNOWN_UNIT",
                        "message": f"Unidade '{unidade_code}' (Bloco: '{bloco_code or '-'}') não está cadastrada no condomínio.",
                        "severity": "blocking"
                    })
                    selected = False
                    action = 'skip'

            # 3. Verificação de duplicidade no próprio arquivo
            file_key = (nome.lower(), unidade_code, bloco_code)
            if file_key in seen_in_file and classification not in ('formato_invalido', 'unidade_desconhecida'):
                classification = 'duplicada_no_arquivo'
                issues.append({
                    "code": "DUPLICATE_IN_FILE",
                    "message": "Registro idêntico já presente em linha anterior deste arquivo.",
                    "severity": "warning"
                })
                selected = False
                action = 'skip'
            seen_in_file.add(file_key)

            # 4. Comparação com cadastros existentes no condomínio
            if unit_obj and classification not in ('formato_invalido', 'unidade_desconhecida', 'duplicada_no_arquivo'):
                # Busca registro existente
                matching_same_name = [
                    reg for reg in existing_registrations
                    if reg.unit_id == unit_obj.id and reg.full_name.strip().lower() == nome.strip().lower()
                ]

                matching_same_unit = [
                    reg for reg in existing_registrations
                    if reg.unit_id == unit_obj.id
                ]

                if matching_same_name:
                    # Registro já existe exatamente igual na unidade
                    classification = 'existente_igual'
                    action = 'skip'
                    selected = False
                    target_reg = matching_same_name[0]
                elif matching_same_unit:
                    # Já existem moradores nesta unidade; nova pessoa na mesma unidade (CA-13)
                    classification = 'vinculo_adicional'
                    action = 'add_registration_for_unit'
                    selected = True
                else:
                    # Novo cadastro
                    if email and telefone:
                        classification = 'nova_completa'
                    else:
                        classification = 'nova_pendente'
                    action = 'create_registration'
                    selected = True

            r.classification = classification
            r.issues = issues
            r.action = action
            r.selected = selected
            r.target_registration = target_reg
            r.save()

            # Incrementa contadores
            if selected:
                totals["selected_rows"] += 1
                if action == 'create_registration':
                    totals["create_registrations"] += 1
                elif action == 'update_registration':
                    totals["update_registrations"] += 1
                elif action == 'add_registration_for_unit':
                    totals["add_unit_registrations"] += 1
            else:
                totals["skipped_rows"] += 1

            if any(i.get('severity') == 'blocking' for i in issues):
                totals["blocking_issues"] += 1

        batch.status = 'awaiting_review'
        batch.totals = totals
        batch.save(update_fields=['status', 'totals', 'updated_at'])

    @classmethod
    def get_preview(cls, condominium_id: uuid.UUID, batch_id: uuid.UUID) -> Dict[str, Any]:
        """
        Retorna os dados da prévia do lote conforme Contrato de API (PRD 30.4).
        """
        batch = ImportBatch.objects.get(id=batch_id, condominium_id=condominium_id)
        totals = batch.totals or {}

        # Determina se o lote pode ser confirmado
        can_confirm = (
            batch.status == 'awaiting_review' and
            totals.get("selected_rows", 0) > 0 and
            totals.get("blocking_issues", 0) == 0
        )

        return {
            "batch_id": str(batch.id),
            "revision": batch.revision,
            "status": batch.status,
            "summary": totals,
            "can_confirm": can_confirm,
            "sends_invitations": False,      # Invariante mandatório: importação NÃO envia convites
            "creates_credentials": False     # Invariante mandatório: importação NÃO cria contas
        }

    @classmethod
    @transaction.atomic
    def update_row_resolution(
        cls,
        condominium_id: uuid.UUID,
        batch_id: uuid.UUID,
        row_id: uuid.UUID,
        selected: bool,
        action: str,
        actor_id: uuid.UUID,
        target_registration_id: Optional[uuid.UUID] = None
    ) -> ImportRow:
        """
        Permite ao operador alterar a seleção ou ação de uma linha específica.
        Incrementa a revisão do lote para concorrência otimista (V21-09).
        """
        batch = ImportBatch.objects.select_for_update().get(id=batch_id, condominium_id=condominium_id)
        row = ImportRow.objects.select_for_update().get(id=row_id, batch=batch)

        # Se houver problema bloqueante, não permite selecionar
        has_blocking = any(i.get('severity') == 'blocking' for i in row.issues)
        if selected and has_blocking and action != 'skip':
            raise UnresolvedConflictError("Linhas com problemas bloqueantes não podem ser selecionadas sem resolução prévia.")

        row.selected = selected
        row.action = action
        if target_registration_id:
            row.target_registration_id = target_registration_id
        row.save()

        batch.revision += 1
        batch.save(update_fields=['revision', 'updated_at'])

        # Recalcula contadores rápidos
        cls.recalculate_totals(batch)
        return row

    @classmethod
    def recalculate_totals(cls, batch: ImportBatch) -> None:
        """Recalcula o sumário de totais do lote."""
        rows = batch.rows.all()
        totals = {
            "total_rows": rows.count(),
            "selected_rows": rows.filter(selected=True).count(),
            "create_registrations": rows.filter(selected=True, action='create_registration').count(),
            "update_registrations": rows.filter(selected=True, action='update_registration').count(),
            "add_unit_registrations": rows.filter(selected=True, action='add_registration_for_unit').count(),
            "skipped_rows": rows.filter(selected=False).count(),
            "blocking_issues": 0
        }
        for r in rows:
            if any(i.get('severity') == 'blocking' for i in r.issues):
                totals["blocking_issues"] += 1

        batch.totals = totals
        batch.save(update_fields=['totals', 'updated_at'])

    @classmethod
    @transaction.atomic
    def confirm_and_apply_batch(
        cls,
        condominium_id: uuid.UUID,
        batch_id: uuid.UUID,
        expected_revision: int,
        actor_id: uuid.UUID,
        acknowledge_selected_operations: bool = True
    ) -> Dict[str, Any]:
        """
        CA-03, V21-06: A aplicação do lote altera os cadastros de forma atômica.
        V21-13: Rejeita confirmação se a revisão for desatualizada.
        V21-10, V21-16: Falha impeditiva reverte toda a transação do lote.
        V21-17, V21-18: NUNCA envia convites e NUNCA cria contas/credenciais.
        """
        batch = ImportBatch.objects.select_for_update().get(id=batch_id, condominium_id=condominium_id)

        if batch.status == 'completed':
            raise BatchAlreadyProcessedError("Este lote já foi confirmado e aplicado.")

        assert_revision_matches(batch.revision, expected_revision)

        # Checa se há conflitos impeditivos entre as linhas selecionadas
        selected_rows = list(batch.rows.filter(selected=True))
        for r in selected_rows:
            if any(i.get('severity') == 'blocking' for i in r.issues):
                raise UnresolvedConflictError(
                    f"A linha {r.row_number} possui problemas impeditivos não resolvidos e não pode ser aplicada."
                )

        created_count = 0
        skipped_count = batch.rows.filter(selected=False).count()

        # Cache de unidades do condomínio
        units_cache = {u.code.upper(): u for u in Unit.objects.filter(condominium_id=condominium_id)}

        for r in selected_rows:
            norm = r.normalized_data
            unidade_code = norm.get('unidade', '').upper()
            unit = units_cache.get(unidade_code)

            if not unit:
                raise UnknownUnitError(
                    f"Falha na aplicação: unidade '{unidade_code}' não existe no condomínio."
                )

            if r.action in ('create_registration', 'add_registration_for_unit'):
                reg = ResidentRegistration.objects.create(
                    condominium_id=condominium_id,
                    unit=unit,
                    full_name=norm.get('nome', ''),
                    relationship=norm.get('relacao', 'other_authorized'),
                    phone_e164=norm.get('telefone') or None,
                    email=norm.get('email') or None,
                    source='importacao',
                    status='pendente',
                    preverified_by_id=actor_id
                )
                r.result_id = reg.id
                r.save(update_fields=['result_id'])
                created_count += 1

        batch.status = 'completed'
        batch.confirmed_by_id = actor_id
        batch.confirmed_at = timezone.now()
        batch.save(update_fields=['status', 'confirmed_by', 'confirmed_at', 'updated_at'])

        return {
            "batch_id": str(batch.id),
            "status": "completed",
            "applied_operations": {
                "created_registrations": created_count,
                "skipped_rows": skipped_count
            },
            "sends_invitations": False,
            "creates_credentials": False
        }

    @staticmethod
    def generate_template_csv() -> str:
        """Gera o modelo CSV de referência com instruções e dados fictícios sem fórmulas."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerow(["Nome", "Torre/Bloco", "Unidade", "Telefone", "Email", "Relação"])
        writer.writerow(["Carlos Drummond", "Torre A", "0101", "+5511999990001", "carlos.drummond@exemplo.com", "proprietario_residente"])
        writer.writerow(["Clarice Lispector", "Torre B", "0202", "+5511999990002", "clarice.lispector@exemplo.com", "inquilino"])
        return output.getvalue()
