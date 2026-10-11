import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTenant } from '@/contexts/TenantContext';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/lib/api';
import {
  ArrowLeft,
  BookmarkCheck,
  CheckCircle2,
  ShieldAlert,
  Users,
  Building,
  RotateCcw,
  MessageSquare,
  Send,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { CardSkeleton } from '@/components/ui/Skeleton';
import { LegalDisclaimerBanner, LEGAL_DISCLAIMER_TEXT } from '@/components/ui/LegalDisclaimerBanner';

export const PublicSuggestionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { activeCondominiumId } = useTenant();
  const { toast } = useToast();

  const [suggestion, setSuggestion] = useState<any | null>(null);
  const [stats, setStats] = useState<any | null>(null);
  const [hasAgreed, setHasAgreed] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmittingAgreement, setIsSubmittingAgreement] = useState(false);
  const [participantId, setParticipantId] = useState<string | null>(null);
  const [publishedRevisionId, setPublishedRevisionId] = useState<string | null>(null);

  const fetchDetail = async () => {
    if (!activeCondominiumId || !id) return;
    setIsLoading(true);
    try {
      // CA-32: Busca detalhe da sugestão pública (se estiver oculta, a API retorna 404)
      const res = await api.get<any>(`/condominiums/${activeCondominiumId}/suggestions/${id}`);
      setSuggestion(res.data);

      // Busca estatísticas com visão pública (CA-38: contagens ocultas se configurado)
      const resStats = await api.get<any>(`/condominiums/${activeCondominiumId}/suggestions/${id}/stats?viewer=public`);
      setStats(resStats.data);

      // Identifica participante local
      const resC = await api.get<any[]>(`/condominiums/${activeCondominiumId}/campaigns`);
      if (resC.data && resC.data.length > 0) {
        const camp = resC.data[0];
        const resP = await api.get<any[]>(`/condominiums/${activeCondominiumId}/campaigns/${camp.id}/participants`);
        if (resP.data && resP.data.length > 0) {
          setParticipantId(resP.data[0].id);
        }
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [activeCondominiumId, id]);

  const handleAgree = async () => {
    if (!activeCondominiumId || !id || !participantId) {
      toast.error('Você precisa ter seu vínculo de morador habilitado para registrar concordância.');
      return;
    }
    setIsSubmittingAgreement(true);
    try {
      // CA-35: Registro consultivo de concordância sobre a versão pública exata
      await api.post(`/condominiums/${activeCondominiumId}/suggestions/${id}/agreements`, {
        participant_id: participantId,
        published_suggestion_revision_id: id,
        reason: 'Concordância consultiva registrada pelo morador.',
      });
      setHasAgreed(true);
      toast.success('Concordância consultiva registrada com sucesso!');
      fetchDetail();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao registrar concordância.');
    } finally {
      setIsSubmittingAgreement(false);
    }
  };

  const handleWithdraw = async () => {
    if (!activeCondominiumId || !id || !participantId) return;
    setIsSubmittingAgreement(true);
    try {
      // CA-36: Retirada de concordância atualiza agregado e preserva evento
      await api.delete(`/condominiums/${activeCondominiumId}/suggestions/${id}/agreements`, {
        body: JSON.stringify({
          participant_id: participantId,
          published_suggestion_revision_id: id,
        }),
      });
      setHasAgreed(false);
      toast.info('Manifestação de concordância retirada.');
      fetchDetail();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao retirar concordância.');
    } finally {
      setIsSubmittingAgreement(false);
    }
  };

  if (!suggestion) {
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <CardSkeleton />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <Link
          to="/portal/mural"
          className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 mb-1 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Voltar ao Mural</span>
        </Link>
        <div className="flex items-center gap-3">
          <span className="font-mono text-sm font-bold text-slate-700 bg-slate-100 px-2.5 py-0.5 rounded">
            {suggestion.public_protocol}
          </span>
          <Badge variant="outline" className="text-xs uppercase">
            {suggestion.category}
          </Badge>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg leading-relaxed font-serif text-slate-900">
            {suggestion.sanitized_public_text}
          </CardTitle>
          {suggestion.sanitized_justification && (
            <CardDescription className="text-xs text-slate-600 mt-2 leading-relaxed">
              <strong>Justificativa da Proposta:</strong> {suggestion.sanitized_justification}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Se houver resposta da gestão */}
          {suggestion.public_shared_reason && (
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
              <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Posicionamento Oficial da Comissão</span>
              </span>
              <p className="text-xs text-slate-700 leading-relaxed">{suggestion.public_shared_reason}</p>
            </div>
          )}

          {/* Botão Consultivo de Concordância (CA-35, UI-28, PRD p. 255) */}
          <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h4 className="text-sm font-bold text-slate-900">Manifestação de Apoio Consultivo</h4>
                <p className="text-xs text-slate-500">
                  Sinalize para a comissão que esta redação atende ao interesse coletivo.
                </p>
              </div>

              {hasAgreed ? (
                <Button
                  variant="outline"
                  onClick={handleWithdraw}
                  isLoading={isSubmittingAgreement}
                  className="text-rose-600 border-rose-200 hover:bg-rose-50"
                >
                  <RotateCcw className="w-4 h-4 mr-1.5" />
                  <span>Retirar Concordância</span>
                </Button>
              ) : (
                <Button
                  onClick={handleAgree}
                  isLoading={isSubmittingAgreement}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  <BookmarkCheck className="w-4 h-4 mr-1.5" />
                  <span>Concordo com esta proposta</span>
                </Button>
              )}
            </div>

            {/* Aviso Legal Permanente Obrigatório (UI-28) */}
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80 text-xs text-slate-600 leading-tight">
              <strong>Aviso Legal Permanente:</strong> {LEGAL_DISCLAIMER_TEXT}
            </div>

            {/* Ação de Complemento (CA-30) */}
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
              <span className="text-slate-500">Deseja aprimorar ou propor um ajuste nesta sugestão pública?</span>
              <Link to={`/portal/sugerir?parent_suggestion_id=${suggestion.id}&target_provision_id=${suggestion.target_provision_id || ''}`}>
                <Button variant="outline" size="sm" className="font-semibold text-slate-800 hover:text-brand-700">
                  <Send className="w-3.5 h-3.5 mr-1 text-brand-600" />
                  <span>Propor Complemento</span>
                </Button>
              </Link>
            </div>
          </div>

          {/* Métricas Agregadas (se contagens não estiverem ocultas - CA-38, CA-39) */}
          {stats && !stats.hide_counts && (
            <div className="grid grid-cols-2 gap-4 text-center p-4 bg-slate-50 border rounded-xl">
              <div>
                <span className="text-xl font-bold text-slate-900">{stats.concordant_individuals || 0}</span>
                <p className="text-xs text-slate-500 mt-0.5">Moradores Concordantes</p>
              </div>
              <div>
                <span className="text-xl font-bold text-slate-900">{stats.concordant_units || 0}</span>
                <p className="text-xs text-slate-500 mt-0.5">Unidades Representadas</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
