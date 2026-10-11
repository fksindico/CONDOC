import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTenant } from '@/contexts/TenantContext';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/lib/api';
import {
  ArrowLeft,
  Lock,
  CheckCircle2,
  Send,
  Eye,
  FileCheck2,
  ShieldAlert,
  User,
  Sliders,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { CardSkeleton } from '@/components/ui/Skeleton';
import { IdentityRevealModal } from '@/components/ui/IdentityRevealModal';
import { Breadcrumb } from '@/components/ui/Breadcrumb';

export const SuggestionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { activeCondominiumId } = useTenant();
  const { isSindico } = useAuth();
  const { toast } = useToast();

  const [suggestion, setSuggestion] = useState<any | null>(null);
  const [revealedIdentity, setRevealedIdentity] = useState<any | null>(null);
  const [isIdentityModalOpen, setIsIdentityModalOpen] = useState(false);
  const [isRevealing, setIsRevealing] = useState(false);

  // Decisão Editorial
  const [editorialDecision, setEditorialDecision] = useState('acolhida');
  const [publicSharedReason, setPublicSharedReason] = useState('');
  const [internalNote, setInternalNote] = useState('');
  const [isSubmittingDecision, setIsSubmittingDecision] = useState(false);

  // Mesa de Publicação do Síndico (CA-28)
  const [sanitizedText, setSanitizedText] = useState('');
  const [sanitizedJustification, setSanitizedJustification] = useState('');
  const [isPublishing, setIsPublishing] = useState(false);

  // Dimensão 4: Incorporação na Minuta (CA-40)
  const [incorporateText, setIncorporateText] = useState('');
  const [isIncorporating, setIsIncorporating] = useState(false);

  const fetchDetail = async () => {
    if (!activeCondominiumId || !id) return;
    try {
      const queueRes = await api.get<any[]>(`/condominiums/${activeCondominiumId}/moderation/queue`);
      const found = (queueRes.data || []).find((s) => s.id === id);
      if (found) {
        setSuggestion(found);
        setSanitizedText(found.text || '');
        setSanitizedJustification(found.justification || '');
        setIncorporateText(found.text || '');
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [activeCondominiumId, id]);

  const handleIncorporate = async () => {
    if (!activeCondominiumId || !id || !suggestion) return;
    if (!suggestion.target_provision_id) {
      toast.error('Esta sugestão não possui dispositivo normativo alvo vinculado para incorporação.');
      return;
    }
    if (incorporateText.trim().length < 5) {
      toast.error('O texto da nova revisão deve conter no mínimo 5 caracteres.');
      return;
    }
    setIsIncorporating(true);
    try {
      // CA-40: Incorporação atômica gerando nova revisão da minuta
      await api.post(`/condominiums/${activeCondominiumId}/suggestions/${id}/incorporate`, {
        target_provision_id: suggestion.target_provision_id,
        new_text: incorporateText.trim(),
        description: `Incorporação da sugestão ${suggestion.public_protocol}.`,
      });
      toast.success('Sugestão incorporada atomicamente à minuta normativa!');
      fetchDetail();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao incorporar sugestão na minuta.');
    } finally {
      setIsIncorporating(false);
    }
  };

  const handleRevealIdentity = async (justification: string) => {
    if (!activeCondominiumId || !id) return;
    setIsRevealing(true);
    try {
      // CA-33: Consulta justificada e auditada de identidade
      const res = await api.post<any>(
        `/condominiums/${activeCondominiumId}/moderation/suggestions/${id}/identity?role=sindico`,
        { justification }
      );
      setRevealedIdentity(res.data);
    } finally {
      setIsRevealing(false);
    }
  };

  const handleRegisterDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !id || publicSharedReason.trim().length < 5) {
      toast.error('A resposta compartilhável é obrigatória (mínimo 5 caracteres).');
      return;
    }
    setIsSubmittingDecision(true);
    try {
      // CA-27: Decisão editorial acolhida NÃO publica automaticamente
      await api.post(`/condominiums/${activeCondominiumId}/moderation/suggestions/${id}/decision`, {
        decision: editorialDecision,
        public_shared_reason: publicSharedReason.trim(),
        internal_note: internalNote.trim() || undefined,
      });
      toast.success('Decisão editorial registrada com sucesso!');
      fetchDetail();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao registrar decisão.');
    } finally {
      setIsSubmittingDecision(false);
    }
  };

  const handleAuthorizePublication = async () => {
    if (!activeCondominiumId || !id) return;
    if (!isSindico) {
      toast.error('Apenas o síndico ativo com mandato pode autorizar a publicação pública (CA-28).');
      return;
    }
    setIsPublishing(true);
    try {
      // CA-28 / S18: Mesa de publicação do síndico
      await api.post(
        `/condominiums/${activeCondominiumId}/moderation/suggestions/${id}/publish?role=sindico`,
        {
          sanitized_text: sanitizedText.trim(),
          sanitized_justification: sanitizedJustification.trim(),
        }
      );
      toast.success('Sugestão sanitizada publicada com sucesso no mural público!');
      fetchDetail();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao publicar sugestão.');
    } finally {
      setIsPublishing(false);
    }
  };

  if (!suggestion) {
    return (
      <div className="space-y-4 max-w-4xl mx-auto">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <Breadcrumb
        items={[
          { label: 'Participação & Moderação' },
          { label: 'Fila de Moderação', href: '/painel/sugestoes' },
          { label: `Protocolo ${suggestion.public_protocol}` },
        ]}
        showHome
      />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight font-mono">
              {suggestion.public_protocol}
            </h1>
            <Badge variant="outline" className="text-xs uppercase">
              {suggestion.category}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">Campanha: {suggestion.campaign_name}</p>
        </div>

        {/* Botão de Revelação Auditada de Identidade (CA-33) */}
        <div>
          {revealedIdentity ? (
            <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900">
              <p className="font-bold flex items-center gap-1">
                <User className="w-3.5 h-3.5" />
                <span>Autor: {revealedIdentity.full_name}</span>
              </p>
              <p className="text-xs text-emerald-700 mt-0.5">
                Unidade: <strong>{revealedIdentity.unit_code}</strong> • {revealedIdentity.email}
              </p>
            </div>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsIdentityModalOpen(true)}
              className="text-amber-800 border-amber-300 hover:bg-amber-50"
            >
              <Lock className="w-3.5 h-3.5 mr-1 text-amber-600" />
              <span>Consultar Identidade do Autor</span>
            </Button>
          )}
        </div>
      </div>

      {/* Grid de 2 Colunas: Contribuição vs Decisão & Publicação */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Coluna 1: Contribuição do Morador */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Teor da Proposta Submetida</CardTitle>
              <CardDescription>Texto original submetido pelo morador com protocolo.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div>
                <span className="font-bold text-slate-700 block mb-1 uppercase tracking-wider text-xs">
                  Redação Proposta:
                </span>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 font-medium leading-relaxed">
                  {suggestion.text}
                </div>
              </div>
              <div>
                <span className="font-bold text-slate-700 block mb-1 uppercase tracking-wider text-xs">
                  Justificativa / Motivação:
                </span>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-700 leading-relaxed">
                  {suggestion.justification}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Decisão Editorial (CA-27: não publica automaticamente) */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Dimensão 2: Decisão Editorial</CardTitle>
              <CardDescription>
                Acolhimento técnico com resposta compartilhável obrigatória ao morador.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleRegisterDecision} className="space-y-4 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 uppercase mb-1">Deliberação da Comissão *</label>
                  <select
                    className="w-full border border-slate-300 rounded-lg p-2 text-xs outline-none"
                    value={editorialDecision}
                    onChange={(e) => setEditorialDecision(e.target.value)}
                  >
                    <option value="acolhida">Acolhida Integralmente</option>
                    <option value="acolhida_parcial">Acolhida Parcialmente (com adaptação)</option>
                    <option value="rejeitada">Não Acolhida</option>
                    <option value="duplicada">Duplicada (já contemplada em outra sugestão)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 uppercase mb-1">
                    Resposta Compartilhável Pública (Visível ao morador) *
                  </label>
                  <textarea
                    required
                    rows={3}
                    className="w-full border border-slate-300 rounded-lg p-2 text-xs outline-none"
                    placeholder="Ex: A comissão técnica acolheu a sugestão para aprimorar os horários de convivência..."
                    value={publicSharedReason}
                    onChange={(e) => setPublicSharedReason(e.target.value)}
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 uppercase mb-1">
                    Nota Interna Restrita (Oculta de moradores - CA-24)
                  </label>
                  <textarea
                    rows={2}
                    className="w-full border border-slate-300 rounded-lg p-2 text-xs outline-none bg-amber-50/40"
                    placeholder="Anotações confidenciais entre comissão e jurídico..."
                    value={internalNote}
                    onChange={(e) => setInternalNote(e.target.value)}
                  />
                </div>

                <Button type="submit" size="sm" isLoading={isSubmittingDecision}>
                  Gravar Decisão Editorial
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Coluna 2: Mesa de Publicação Sanitizada do Síndico (S18, CA-28) */}
        <div className="space-y-4">
          <Card className="border-indigo-200 bg-indigo-50/10">
            <CardHeader>
              <CardTitle className="text-base flex items-center justify-between">
                <span>Dimensão 3: Mesa de Publicação Sanitizada</span>
                <Badge variant={suggestion.publication_status === 'publicada' ? 'success' : 'outline'}>
                  {suggestion.publication_status === 'publicada' ? 'Publicada no Mural' : 'Não Publicada'}
                </Badge>
              </CardTitle>
              <CardDescription>
                Apenas o síndico ativo com mandato pode autorizar a publicação pública (CA-28, UI-24).
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <Alert variant="info" title="Checklist de Sanitização Obrigatório">
                Certifique-se de que nenhum dado pessoal, nome de morador, acusação ou unidade conste no texto público
                antes de assinar a publicação (UI-25).
              </Alert>

              <div>
                <label className="block font-semibold text-slate-700 uppercase mb-1">
                  Texto Normativo Sanitizado (Público) *
                </label>
                <textarea
                  rows={4}
                  className="w-full border border-slate-300 rounded-lg p-2 text-xs outline-none font-medium bg-white"
                  value={sanitizedText}
                  onChange={(e) => setSanitizedText(e.target.value)}
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 uppercase mb-1">
                  Justificativa Sanitizada (Pública) *
                </label>
                <textarea
                  rows={3}
                  className="w-full border border-slate-300 rounded-lg p-2 text-xs outline-none bg-white"
                  value={sanitizedJustification}
                  onChange={(e) => setSanitizedJustification(e.target.value)}
                />
              </div>

              <div className="pt-2">
                <Button
                  className="w-full"
                  onClick={handleAuthorizePublication}
                  isLoading={isPublishing}
                  disabled={!isSindico}
                >
                  <Send className="w-4 h-4 mr-1.5" />
                  <span>
                    {isSindico ? 'Autorizar Publicação no Mural Público' : 'Autorização Restrita ao Síndico'}
                  </span>
                </Button>
                {!isSindico && (
                  <p className="text-xs text-rose-600 mt-1.5 text-center font-medium">
                    Seu papel atual não possui autoridade para assinar publicação de conteúdo.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Dimensão 4: Incorporação na Minuta de Trabalho (CA-40) */}
          <Card className="border-emerald-200 bg-emerald-50/15">
            <CardHeader>
              <CardTitle className="text-base flex items-center justify-between">
                <span>Dimensão 4: Incorporação na Minuta</span>
                <Badge
                  variant={suggestion.incorporation_status === 'incorporada' ? 'success' : 'outline'}
                >
                  {suggestion.incorporation_status === 'incorporada' ? 'Incorporada na Minuta' : 'Não Incorporada'}
                </Badge>
              </CardTitle>
              <CardDescription>
                Consolida atomicamente a contribuição na minuta, gerando nova revisão no editor (CA-40).
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <Alert variant="info" title="Transação Atômica Vinculada">
                A incorporação exige que a sugestão tenha sido acolhida pela comissão. A redação abaixo substituirá o
                dispositivo normativo e criará uma nova revisão formal.
              </Alert>

              <div>
                <label className="block font-semibold text-slate-700 uppercase mb-1">
                  Redação Final para Incorporação *
                </label>
                <textarea
                  rows={4}
                  className="w-full border border-slate-300 rounded-lg p-2 text-xs outline-none font-serif bg-white text-slate-900"
                  value={incorporateText}
                  onChange={(e) => setIncorporateText(e.target.value)}
                  disabled={suggestion.incorporation_status === 'incorporada'}
                />
              </div>

              {suggestion.incorporation_status !== 'incorporada' && (
                <Button
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                  onClick={handleIncorporate}
                  isLoading={isIncorporating}
                  disabled={suggestion.editorial_decision !== 'acolhida' && suggestion.editorial_decision !== 'acolhida_parcial'}
                >
                  <FileCheck2 className="w-4 h-4 mr-1.5" />
                  <span>Incorporar à Minuta Normativa</span>
                </Button>
              )}
              {suggestion.editorial_decision !== 'acolhida' && suggestion.editorial_decision !== 'acolhida_parcial' && (
                <p className="text-xs text-amber-700 text-center font-medium">
                  Apenas sugestões acolhidas ou acolhidas parcialmente podem ser incorporadas à minuta.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Modal de Revelação Auditada */}
      <IdentityRevealModal
        isOpen={isIdentityModalOpen}
        onClose={() => setIsIdentityModalOpen(false)}
        publicProtocol={suggestion.public_protocol}
        onConfirm={handleRevealIdentity}
        isLoading={isRevealing}
      />
    </div>
  );
};
