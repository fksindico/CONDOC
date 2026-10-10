import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { Send, CheckCircle2, ShieldAlert, ArrowLeft, FileText, Info } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';

export const SuggestionCreatePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { activeCondominiumId } = useTenant();

  const targetProvisionId = searchParams.get('target_provision_id') || '';
  const targetLabel = searchParams.get('target_label') || '';

  const [activeCampaign, setActiveCampaign] = useState<any | null>(null);
  const [category, setCategory] = useState<'redacao' | 'clareza' | 'supressao' | 'adicao' | 'adequacao_legal' | 'geral'>('redacao');
  const [text, setText] = useState('');
  const [justification, setJustification] = useState('');
  const [alternativeText, setAlternativeText] = useState('');

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [protocolResult, setProtocolResult] = useState<string | null>(null);

  useEffect(() => {
    if (!activeCondominiumId) return;
    api.get<any[]>(`/condominiums/${activeCondominiumId}/campaigns`).then((res) => {
      const list = res.data || [];
      const openCamp = list.find((c) => c.state === 'aberta') || list[0] || null;
      setActiveCampaign(openCamp);
    });
  }, [activeCondominiumId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !activeCampaign) {
      setError('Nenhuma campanha de consulta pública ativa encontrada.');
      return;
    }
    if (text.trim().length < 5 || justification.trim().length < 5) {
      setError('O texto da proposta e a justificativa devem conter pelo menos 5 caracteres.');
      return;
    }
    setIsLoading(true);
    setError('');

    try {
      // CA-25 / UI-20: Envio de sugestão privada gerando protocolo único imediato
      // Busca participante cadastrado para a campanha
      const resParts = await api.get<any[]>(`/condominiums/${activeCondominiumId}/campaigns/${activeCampaign.id}/participants`);
      const participant = (resParts.data || [])[0];

      if (!participant) {
        throw new Error('Você precisa ter seu vínculo de morador habilitado na campanha para sugerir.');
      }

      const res = await api.post<any>(`/condominiums/${activeCondominiumId}/campaigns/${activeCampaign.id}/suggestions`, {
        participant_id: participant.id,
        target_provision_id: targetProvisionId || null,
        text: text.trim(),
        justification: justification.trim(),
        alternative_text: alternativeText.trim() || undefined,
        category,
      });

      setProtocolResult(res.data.public_protocol);
    } catch (err: any) {
      setError(err.message || 'Erro ao enviar sugestão.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/portal/documento')}
          className="p-1.5 rounded-lg text-slate-500 hover:bg-slate-200 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Enviar Sugestão</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Sua contribuição nasce privada e será analisada pela comissão técnica (CA-25).
          </p>
        </div>
      </div>

      {protocolResult ? (
        <Card className="text-center p-8 space-y-4">
          <div className="inline-flex p-3 bg-emerald-100 rounded-full text-emerald-700 mx-auto">
            <CheckCircle2 className="w-10 h-10" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Sugestão Protocolada com Sucesso!</h2>
          <div className="p-3 bg-slate-100 rounded-lg max-w-sm mx-auto font-mono text-base font-bold text-slate-800 border">
            {protocolResult}
          </div>
          <p className="text-xs text-slate-600 max-w-md mx-auto">
            Guarde o número do protocolo acima. Você pode acompanhar a análise técnica e o parecer da comissão no painel
            "Minhas Sugestões".
          </p>
          <div className="flex justify-center gap-3 pt-4">
            <Button variant="outline" onClick={() => navigate('/portal/documento')}>
              Voltar à Minuta
            </Button>
            <Button onClick={() => navigate('/portal/minhas-sugestoes')}>
              Acompanhar Minhas Sugestões
            </Button>
          </div>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center justify-between">
              <span>Nova Proposta de Redação</span>
              {targetLabel && (
                <span className="text-xs bg-slate-100 px-2.5 py-1 rounded-md text-slate-700 font-mono">
                  Alvo: {targetLabel}
                </span>
              )}
            </CardTitle>
            <CardDescription>
              Descreva sua proposta com clareza para subsidiar a avaliação da comissão técnica.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4 text-xs sm:text-sm">
              {error && <Alert variant="error">{error}</Alert>}

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Categoria da Proposta *
                </label>
                <select
                  className="w-full text-xs sm:text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                  value={category}
                  onChange={(e: any) => setCategory(e.target.value)}
                >
                  <option value="redacao">Aprimoramento de Redação</option>
                  <option value="clareza">Clareza e Compreensão</option>
                  <option value="adicao">Inclusão de Nova Regra</option>
                  <option value="supressao">Supressão de Dispositivo</option>
                  <option value="adequacao_legal">Adequação à Legislação / Código Civil</option>
                  <option value="geral">Geral sobre o Documento</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Texto da Proposta de Redação *
                </label>
                <textarea
                  required
                  rows={4}
                  className="w-full text-xs sm:text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 leading-relaxed font-serif"
                  placeholder="Redija aqui como você sugere que o artigo seja escrito..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Justificativa e Motivação *
                </label>
                <textarea
                  required
                  rows={3}
                  className="w-full text-xs sm:text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 leading-relaxed"
                  placeholder="Explique o motivo da alteração e por que ela beneficia o convívio no condomínio..."
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Proposta Alternativa (Opcional)
                </label>
                <textarea
                  rows={2}
                  className="w-full text-xs sm:text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                  placeholder="Caso a proposta principal não seja acolhida, sugira uma segunda opção..."
                  value={alternativeText}
                  onChange={(e) => setAlternativeText(e.target.value)}
                />
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 flex items-start gap-2">
                <ShieldAlert className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                <span>
                  <strong>Aviso de Transparência (LGPD):</strong> Sua sugestão é registrada de forma privada com
                  protocolo único. A identidade do autor não é exposta a outros moradores.
                </span>
              </div>
            </CardContent>

            <CardFooter className="justify-end gap-3">
              <Button type="button" variant="outline" onClick={() => navigate('/portal/documento')}>
                Cancelar
              </Button>
              <Button type="submit" isLoading={isLoading}>
                <Send className="w-4 h-4 mr-1.5" />
                <span>Protocolar Sugestão</span>
              </Button>
            </CardFooter>
          </form>
        </Card>
      )}
    </div>
  );
};
