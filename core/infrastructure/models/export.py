"""
Modelos ORM para Preservação e Artefatos de Exportação — CONDC (Fase 7)
ADR-003: managed = False. O schema SQL em supabase/migrations é a fonte única de DDL.
"""
import uuid
from django.db import models
from .identity import Condominium, Account
from .documents import Document, DocumentSnapshot


class ExportArtifact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True, db_column='document_id')
    snapshot = models.ForeignKey(DocumentSnapshot, on_delete=models.SET_NULL, null=True, blank=True, db_column='snapshot_id')
    kind = models.CharField(max_length=50)  # pacote_externo_publico, relatorio_interno_comissao, minuta_final_limpa, relatorio_depara_final
    status = models.CharField(max_length=50, default='concluido')
    is_public = models.BooleanField(default=True)
    manifest_hash = models.CharField(max_length=64)
    files_manifest = models.JSONField(default=list)
    disclaimer = models.TextField()
    generated_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, db_column='generated_by_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."export_artifacts'
        verbose_name = 'Artefato de Exportação'
        verbose_name_plural = 'Artefatos de Exportação'

    def __str__(self):
        return f"{self.kind} ({self.manifest_hash[:8]})"
