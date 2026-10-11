import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { Link } from 'react-router-dom';
import { MessageSquare, ArrowRight, Filter, Search, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';

export const ModerationQueuePage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const [queue, setQueue] = useState<any[]>([]);
  const [filterAnalysis, setFilterAnalysis] = useState('');
  const [filterPublication, setFilterPublication] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchQueue = async () => {
    if (!activeCondominiumId) return;
    setIsLoading(true);
    setError('');
    try {
      let endpoint = `/condominiums/${activeCondominiumId}/moderation/queue?`;
      if (filterAnalysis) endpoint += `analysis_status=${filterAnalysis}&`;
      if (filterPublication) endpoint += `publication_status=${filterPublication}&`;
      const res = await api.get<any[]>(endpoint);
      setQueue(res.data || []);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar fila de moderação.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [activeCondominiumId, filterAnalysis, filterPublication]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Fila de Moderação em 4 Dimensões
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Análise técnica, decisão editorial, publicação e incorporação tratadas de forma independente (S16, UI-22).
          </p>
        </div>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      <Card>
        <CardHeader className="p-4 sm:p-6 pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                <Filter className="w-3.5 h-3.5 text-slate-400" />
                <span>Filtros:</span>
              </span>
              <select
                className="text-xs border border-slate-200 rounded-lg p-2 outline-none font-medium text-slate-700"
                value={filterAnalysis}
                onChange={(e) => setFilterAnalysis(e.target.value)}
              >
                <option value="">Todas as Análises</option>
                <option value="pendente">Pendente de Análise</option>
                <option value="concluida">Análise Concluída</option>
              </select>
              <select
                className="text-xs border border-slate-200 rounded-lg p-2 outline-none font-medium text-slate-700"
                value={filterPublication}
                onChange={(e) => setFilterPublication(e.target.value)}
              >
                <option value="">Todas as Publicações</option>
                <option value="nao_publicada">Não Publicadas</option>
                <option value="publicada">Publicadas</option>
                <option value="oculta">Ocultas</option>
              </select>
            </div>
            <span className="text-xs text-slate-500 font-medium">
              {queue.length} {queue.length === 1 ? 'sugestão encontrada' : 'sugestões encontradas'}
            </span>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Protocolo</th>
                  <th className="px-6 py-3 w-1/3">Teor da Proposta</th>
                  <th className="px-6 py-3">Dimensão 1: Análise</th>
                  <th className="px-6 py-3">Dimensão 2: Decisão</th>
                  <th className="px-6 py-3">Dimensão 3: Publicação</th>
                  <th className="px-6 py-3">Dimensão 4: Incorporação</th>
                  <th className="px-6 py-3 text-right">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {queue.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                      Nenhuma sugestão encontrada para os filtros selecionados.
                    </td>
                  </tr>
                ) : (
                  queue.map((sug) => (
                    <tr key={sug.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-3.5 font-mono font-bold text-slate-900">
                        {sug.public_protocol}
                      </td>
                      <td className="px-6 py-3.5">
                        <p className="line-clamp-2 text-slate-800 font-medium">{sug.text}</p>
                        <p className="line-clamp-1 text-slate-400 text-[11px] mt-0.5">{sug.justification}</p>
                      </td>
                      <td className="px-6 py-3.5">
                        <Badge
                          variant={sug.analysis_status === 'concluida' ? 'success' : 'warning'}
                          className="capitalize text-[10px]"
                        >
                          {sug.analysis_status}
                        </Badge>
                      </td>
                      <td className="px-6 py-3.5">
                        <Badge
                          variant={sug.editorial_decision === 'acolhida' ? 'success' : 'default'}
                          className="capitalize text-[10px]"
                        >
                          {sug.editorial_decision.replace('_', ' ')}
                        </Badge>
                      </td>
                      <td className="px-6 py-3.5">
                        <Badge
                          variant={
                            sug.publication_status === 'publicada'
                              ? 'info'
                              : sug.publication_status === 'oculta'
                              ? 'danger'
                              : 'default'
                          }
                          className="capitalize text-[10px]"
                        >
                          {sug.publication_status.replace('_', ' ')}
                        </Badge>
                      </td>
                      <td className="px-6 py-3.5">
                        <Badge
                          variant={sug.incorporation_status === 'incorporada' ? 'success' : 'outline'}
                          className="capitalize text-[10px]"
                        >
                          {sug.incorporation_status === 'incorporada' ? 'Incorporada' : 'Pendente'}
                        </Badge>
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <Link to={`/painel/sugestoes/${sug.id}`}>
                          <Button size="sm" variant="outline">
                            <span>Moderar</span>
                            <ArrowRight className="w-3.5 h-3.5 ml-1" />
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
