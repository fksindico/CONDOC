"""
Modelos ORM Django para o Núcleo Documental — CONDC (Fase 3)
Fonte única de DDL: supabase/migrations/20261009000003_phase3_documents_provisions.sql
Compatível com PRD Mestre v3.0 (Seções 11, 12, 13, 14, 15, 22.4).
"""
import uuid
from django.db import models


class Project(models.Model):
    """Projeto de criação, revisão ou alteração de documentos normativos."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(
        'infrastructure.Condominium',
        on_delete=models.CASCADE,
        related_name='projects',
        db_column='condominium_id'
    )
    name = models.CharField(max_length=255)
    purpose = models.TextField(blank=True, null=True)
    kind = models.CharField(
        max_length=50,
        default='revisao',
        choices=[
            ('criacao', 'Criação Nova'),
            ('revisao', 'Revisão / Modernização'),
            ('conjunta', 'Revisão Conjunta (Convenção + Regimento)'),
        ]
    )
    coordinator_account = models.ForeignKey(
        'infrastructure.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coordinated_projects',
        db_column='coordinator_account_id'
    )
    status = models.CharField(
        max_length=50,
        default='preparacao',
        choices=[
            ('preparacao', 'Preparação'),
            ('estruturacao', 'Estruturação'),
            ('redacao', 'Redação'),
            ('consulta', 'Consulta Pública'),
            ('consolidacao', 'Consolidação'),
            ('revisao_opcional', 'Revisão Opcional'),
            ('final_trabalho', 'Final de Trabalho'),
            ('publicado', 'Publicado'),
            ('arquivado', 'Arquivado'),
        ]
    )
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."projects'
        verbose_name = 'Projeto Documental'
        verbose_name_plural = 'Projetos Documentais'


class Document(models.Model):
    """Documento normativo (Convenção, Regimento Interno ou Anexo)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='documents',
        db_column='project_id'
    )
    condominium = models.ForeignKey(
        'infrastructure.Condominium',
        on_delete=models.CASCADE,
        related_name='documents',
        db_column='condominium_id'
    )
    type = models.CharField(
        max_length=50,
        default='regimento_interno',
        choices=[
            ('convencao', 'Convenção de Condomínio'),
            ('regimento_interno', 'Regimento Interno'),
            ('anexo_normativo', 'Anexo Normativo'),
        ]
    )
    title = models.CharField(max_length=255)
    editorial_status = models.CharField(
        max_length=50,
        default='rascunho',
        choices=[
            ('rascunho', 'Rascunho'),
            ('em_revisao', 'Em Revisão'),
            ('aprovado_para_consulta', 'Aprovado para Consulta'),
            ('congelado', 'Congelado'),
            ('consolidado', 'Consolidado'),
        ]
    )
    numbering_policy = models.CharField(
        max_length=50,
        default='preservar_original',
        choices=[
            ('preservar_original', 'Preservar Numeração Original'),
            ('renumeracao_automatica', 'Renumeração Automática'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."documents'
        verbose_name = 'Documento Normativo'
        verbose_name_plural = 'Documentos Normativos'


class SourceFile(models.Model):
    """Arquivo original de entrada armazenado no Supabase Storage (AR-10)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(
        'infrastructure.Condominium',
        on_delete=models.CASCADE,
        related_name='source_files',
        db_column='condominium_id'
    )
    storage_key = models.CharField(max_length=500)
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    size_bytes = models.BigIntegerField()
    file_hash = models.CharField(max_length=64)  # SHA-256
    uploaded_by = models.ForeignKey(
        'infrastructure.Account',
        on_delete=models.CASCADE,
        related_name='uploaded_source_files',
        db_column='uploaded_by_id'
    )
    state = models.CharField(
        max_length=50,
        default='uploaded',
        choices=[
            ('uploaded', 'Enviado'),
            ('processing_ocr', 'Processando OCR'),
            ('ocr_completed', 'OCR Concluído'),
            ('ocr_failed', 'Falha no OCR'),
            ('ready', 'Pronto para Análise'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."source_files'
        verbose_name = 'Arquivo Original'
        verbose_name_plural = 'Arquivos Originais'


class SourceTranscription(models.Model):
    """Transcrição bruta e conferida de arquivo original (CA-17, CA-18)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='transcriptions',
        db_column='document_id'
    )
    condominium = models.ForeignKey(
        'infrastructure.Condominium',
        on_delete=models.CASCADE,
        related_name='source_transcriptions',
        db_column='condominium_id'
    )
    source_file = models.ForeignKey(
        SourceFile,
        on_delete=models.CASCADE,
        related_name='transcriptions',
        db_column='source_file_id'
    )
    version = models.IntegerField(default=1)
    status = models.CharField(
        max_length=50,
        default='draft',
        choices=[
            ('draft', 'Rascunho de Transcrição'),
            ('under_review', 'Em Conferência'),
            ('confirmed', 'Conferido por Humano'),
            ('superseded', 'Substituído por Nova Versão'),
        ]
    )
    raw_text = models.TextField()
    corrected_text = models.TextField(blank=True, null=True)
    checked_by = models.ForeignKey(
        'infrastructure.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_transcriptions',
        db_column='checked_by_id'
    )
    checked_at = models.DateTimeField(null=True, blank=True)
    replaces_transcription = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='successor_transcriptions',
        db_column='replaces_transcription_id'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."source_transcriptions'
        verbose_name = 'Transcrição da Fonte'
        verbose_name_plural = 'Transcrições da Fonte'


class SourceProvision(models.Model):
    """Dispositivo segmentado a partir da transcrição original."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transcription = models.ForeignKey(
        SourceTranscription,
        on_delete=models.CASCADE,
        related_name='provisions',
        db_column='transcription_id'
    )
    condominium = models.ForeignKey(
        'infrastructure.Condominium',
        on_delete=models.CASCADE,
        related_name='source_provisions',
        db_column='condominium_id'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        db_column='parent_id'
    )
    kind = models.CharField(
        max_length=50,
        default='artigo',
        choices=[
            ('titulo', 'Título'),
            ('capitulo', 'Capítulo'),
            ('secao', 'Seção'),
            ('subsecao', 'Subseção'),
            ('artigo', 'Artigo'),
            ('caput', 'Caput'),
            ('paragrafo', 'Parágrafo'),
            ('inciso', 'Inciso'),
            ('alinea', 'Alínea'),
            ('preambulo', 'Preâmbulo'),
            ('anexo', 'Anexo'),
        ]
    )
    label = models.CharField(max_length=100)
    display_order = models.IntegerField(default=0)
    text = models.TextField()
    page_number = models.IntegerField(null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."source_provisions'
        verbose_name = 'Dispositivo da Fonte'
        verbose_name_plural = 'Dispositivos da Fonte'


class Provision(models.Model):
    """Dispositivo normativo com identidade permanente e estável (UUID)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='provisions',
        db_column='document_id'
    )
    condominium = models.ForeignKey(
        'infrastructure.Condominium',
        on_delete=models.CASCADE,
        related_name='provisions',
        db_column='condominium_id'
    )
    kind = models.CharField(
        max_length=50,
        default='artigo',
        choices=[
            ('titulo', 'Título'),
            ('capitulo', 'Capítulo'),
            ('secao', 'Seção'),
            ('subsecao', 'Subseção'),
            ('artigo', 'Artigo'),
            ('caput', 'Caput'),
            ('paragrafo', 'Parágrafo'),
            ('inciso', 'Inciso'),
            ('alinea', 'Alínea'),
            ('preambulo', 'Preâmbulo'),
            ('anexo', 'Anexo'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."provisions'
        verbose_name = 'Dispositivo Normativo'
        verbose_name_plural = 'Dispositivos Normativos'


class ProvisionRevision(models.Model):
    """Revisão histórica de dispositivo normativo (CA-23: ETag/Concorrência otimista)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provision = models.ForeignKey(
        Provision,
        on_delete=models.CASCADE,
        related_name='revisions',
        db_column='provision_id'
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='provision_revisions',
        db_column='document_id'
    )
    condominium = models.ForeignKey(
        'infrastructure.Condominium',
        on_delete=models.CASCADE,
        related_name='provision_revisions',
        db_column='condominium_id'
    )
    revision_number = models.IntegerField(default=1)
    parent_provision = models.ForeignKey(
        Provision,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_revisions',
        db_column='parent_provision_id'
    )
    position = models.IntegerField(default=0)
    label = models.CharField(max_length=100)
    text = models.TextField()
    theme = models.CharField(max_length=100, blank=True, null=True)
    change_type = models.CharField(
        max_length=50,
        default='mantido',
        choices=[
            ('mantido', 'Mantido Original'),
            ('alterado', 'Texto Alterado'),
            ('incluido', 'Novo Dispositivo Incluído'),
            ('excluido', 'Excluído da Minuta'),
            ('movido', 'Movido de Posição'),
            ('renumerado', 'Renumerado'),
            ('desmembrado', 'Desmembrado em Vários'),
            ('consolidado', 'Consolidado a Partir de Vários'),
            ('reestruturado', 'Reestruturado'),
        ]
    )
    status = models.CharField(
        max_length=50,
        default='draft',
        choices=[
            ('draft', 'Rascunho'),
            ('review_pending', 'Pendente de Revisão'),
            ('approved', 'Aprovado para Publicação'),
            ('archived', 'Arquivado'),
        ]
    )
    author_account = models.ForeignKey(
        'infrastructure.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authored_revisions',
        db_column='author_account_id'
    )
    etag = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."provision_revisions'
        verbose_name = 'Revisão de Dispositivo'
        verbose_name_plural = 'Revisões de Dispositivos'


class InternalNote(models.Model):
    """Nota interna privada com visibilidade restrita (CA-24)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(
        'infrastructure.Condominium',
        on_delete=models.CASCADE,
        related_name='internal_notes',
        db_column='condominium_id'
    )
    provision = models.ForeignKey(
        Provision,
        on_delete=models.CASCADE,
        related_name='internal_notes',
        db_column='provision_id'
    )
    revision = models.ForeignKey(
        ProvisionRevision,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='internal_notes',
        db_column='revision_id'
    )
    author_account = models.ForeignKey(
        'infrastructure.Account',
        on_delete=models.CASCADE,
        related_name='authored_notes',
        db_column='author_account_id'
    )
    content = models.TextField()
    visibility = models.CharField(
        max_length=50,
        default='equipe',
        choices=[
            ('equipe', 'Toda a Equipe Administrativa'),
            ('juridico', 'Apenas Assessoria Jurídica'),
            ('gestao', 'Apenas Gestão / Síndico'),
        ]
    )
    category = models.CharField(
        max_length=50,
        default='redacao',
        choices=[
            ('juridico', 'Parecer Jurídico'),
            ('redacao', 'Ajuste de Redação'),
            ('duvida', 'Dúvida Operacional'),
            ('alerta', 'Alerta de Inconsistência'),
        ]
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        'infrastructure.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_notes',
        db_column='resolved_by_id'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."internal_notes'
        verbose_name = 'Nota Interna'
        verbose_name_plural = 'Notas Internas'


class DocumentSnapshot(models.Model):
    """Snapshot imutável e reproduzível de um documento normativo (CA-41)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='snapshots',
        db_column='document_id'
    )
    condominium = models.ForeignKey(
        'infrastructure.Condominium',
        on_delete=models.CASCADE,
        related_name='document_snapshots',
        db_column='condominium_id'
    )
    version_label = models.CharField(max_length=100)
    purpose = models.CharField(
        max_length=50,
        default='consulta_publica',
        choices=[
            ('consulta_publica', 'Base para Consulta Pública'),
            ('marco_revisao', 'Marco Histórico de Revisão'),
            ('versao_final', 'Versão Final de Assembleia'),
        ]
    )
    frozen_by = models.ForeignKey(
        'infrastructure.Account',
        on_delete=models.CASCADE,
        related_name='frozen_snapshots',
        db_column='frozen_by_id'
    )
    frozen_at = models.DateTimeField(auto_now_add=True)
    content_hash = models.CharField(max_length=64)  # SHA-256
    is_immutable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."document_snapshots'
        verbose_name = 'Snapshot de Documento'
        verbose_name_plural = 'Snapshots de Documentos'


class SnapshotItem(models.Model):
    """Dispositivo congelado em um snapshot específico (CA-41)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot = models.ForeignKey(
        DocumentSnapshot,
        on_delete=models.CASCADE,
        related_name='items',
        db_column='snapshot_id'
    )
    provision = models.ForeignKey(
        Provision,
        on_delete=models.CASCADE,
        related_name='snapshot_items',
        db_column='provision_id'
    )
    provision_revision = models.ForeignKey(
        ProvisionRevision,
        on_delete=models.RESTRICT,
        related_name='snapshot_items',
        db_column='provision_revision_id'
    )
    rendered_label = models.CharField(max_length=100)
    position = models.IntegerField(default=0)
    parent_provision = models.ForeignKey(
        Provision,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_snapshot_items',
        db_column='parent_provision_id'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."snapshot_items'
        verbose_name = 'Item de Snapshot'
        verbose_name_plural = 'Itens de Snapshot'


class OriginMapping(models.Model):
    """Mapeamento explícito de origem entre a revisão da minuta e a fonte original (CA-21)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(
        'infrastructure.Condominium',
        on_delete=models.CASCADE,
        related_name='origin_mappings',
        db_column='condominium_id'
    )
    revision = models.ForeignKey(
        ProvisionRevision,
        on_delete=models.CASCADE,
        related_name='origin_mappings',
        db_column='revision_id'
    )
    source_provision = models.ForeignKey(
        SourceProvision,
        on_delete=models.CASCADE,
        related_name='target_mappings',
        db_column='source_provision_id'
    )
    relation_type = models.CharField(
        max_length=50,
        default='mantido',
        choices=[
            ('mantido', 'Mantido'),
            ('alterado', 'Alterado'),
            ('desmembrado', 'Desmembrado'),
            ('consolidado', 'Consolidado'),
        ]
    )
    excerpt = models.TextField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."origin_mappings'
        verbose_name = 'Mapeamento de Origem'
        verbose_name_plural = 'Mapeamentos de Origem'


class CrossReference(models.Model):
    """Referência cruzada entre dispositivos baseada em UUID permanente (CA-22)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(
        'infrastructure.Condominium',
        on_delete=models.CASCADE,
        related_name='cross_references',
        db_column='condominium_id'
    )
    revision = models.ForeignKey(
        ProvisionRevision,
        on_delete=models.CASCADE,
        related_name='outgoing_cross_references',
        db_column='revision_id'
    )
    target_provision = models.ForeignKey(
        Provision,
        on_delete=models.CASCADE,
        related_name='incoming_cross_references',
        db_column='target_provision_id'
    )
    label_template = models.CharField(max_length=100, default='art. {target_label}')
    status = models.CharField(
        max_length=50,
        default='valido',
        choices=[
            ('valido', 'Válido'),
            ('quebrado', 'Quebrado / Alvo Excluído'),
            ('pendente', 'Pendente de Conferência'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."cross_references'
        verbose_name = 'Referência Cruzada'
        verbose_name_plural = 'Referências Cruzadas'

