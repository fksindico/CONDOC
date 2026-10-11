import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { Link } from 'react-router-dom';
import { FileText, Send, CheckCircle2, Clock, AlertCircle, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { CardSkeleton } from '@/components/ui/Skeleton';
import { formatDatePtBr } from '@/lib/utils';

export const MySuggestionsPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const [mySuggestions, setMySuggestions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!activeCondominiumId) return;
    setIsLoading(true);

    // Identifica o participante do morador
    api.get<any[]>(`/condominiums/${activeCondominiumId}/campaigns`).then(async (resC) => {
      const list = resC.data || [];
      if (list.length > 0) {
        const camp = list[0];
        const resP = await api.get<any[]>(`/condominiums/${activeCondominiumId}/campaigns/${camp.id}/participants`);
        if (resP.data && resP.data.length > 0) {
          const participant = resP.data[0];
          // M09: Lista sugestões do próprio morador (sem notas internas da equipe - CA-24)
          const resSugs = await api.get<any[]>(`/condominiums/${activeCondominiumId}/my-suggestions?participant_id=${participant.id}`);
          setMySuggestions(resSugs.data || []);
        }
      }
      setIsLoading(false);
    });
  }, [activeCondominiumId]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Minhas Sugestões</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Acompanhe o andamento das suas contribuições protocoladas (M09, M10).
          </p>
        </div>
        <Link to="/portal/sugerir">
          <Button size="sm">
            <Send className="w-4 h-4 mr-1.5" aria-hidden="true" />
            <span>Nova Sugestão</span>
          </Button>
        </Link>
      </div>

      <div className="space-y-4 animate-fade-in">
        {isLoading ? (
          <div className="space-y-4">
            <CardSkeleton />
            <CardSkeleton />
          </div>
        ) : mySuggestions.length === 0 ? (
          <Card className="text-center py-12 text-slate-500">
            <FileText className="w-10 h-10 mx-auto text-slate-300 mb-2" aria-hidden="true" />
            <p className="text-sm font-semibold text-slate-700">Você ainda não protocolou nenhuma sugestão.</p>
            <p className="text-xs text-slate-500 mt-0.5">
              Explore a minuta em discussão e envie propostas para melhorar o convívio no condomínio.
            </p>
            <div className="pt-4">
              <Link to="/portal/documento">
                <Button variant="outline" size="sm">
                  Explorar a Minuta
                </Button>
              </Link>
            </div>
          </Card>
        ) : (
          mySuggestions.map((sug) => (
            <Card key={sug.id} className="hover:border-slate-300 transition-colors">
              <CardContent className="p-5 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-xs font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                      {sug.public_protocol}
                    </span>
                    <Badge variant="outline" className="text-xs uppercase">
                      {sug.category}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={
                        sug.analysis_status === 'concluida'
                          ? 'success'
                          : sug.analysis_status === 'em_analise'
                          ? 'info'
                          : 'warning'
                      }
                      className="text-xs capitalize"
                    >
                      {sug.analysis_status}
                    </Badge>
                    <Badge
                      variant={
                        sug.editorial_decision === 'acolhida'
                          ? 'success'
                          : sug.editorial_decision === 'rejeitada'
                          ? 'danger'
                          : 'default'
                      }
                      className="text-xs capitalize"
                    >
                      {sug.editorial_decision.replace('_', ' ')}
                    </Badge>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-slate-900 text-sm font-serif">{sug.text}</h4>
                  <p className="text-xs text-slate-600 mt-1">{sug.justification}</p>
                </div>

                {/* Resposta Pública da Gestão (se houver) */}
                {sug.public_shared_reason && (
                  <div className="p-3 bg-emerald-50/70 border border-emerald-200 rounded-lg text-xs text-emerald-900 space-y-1">
                    <span className="font-semibold flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />
                      <span>Retorno Oficial da Comissão:</span>
                    </span>
                    <p className="leading-relaxed">{sug.public_shared_reason}</p>
                  </div>
                )}

                <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
                  <span>Enviada em {formatDatePtBr(sug.created_at)}</span>
                  <span>Versão {sug.version_number}</span>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};
