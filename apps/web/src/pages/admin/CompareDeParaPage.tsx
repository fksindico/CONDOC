import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { ArrowLeft, FileDiff, Download, ShieldCheck, CheckCircle2, XCircle, Edit3, History, Search, Filter } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { Breadcrumb } from '@/components/ui/Breadcrumb';

export const CompareDeParaPage: React.FC = () => {
  const { docId } = useParams<{ docId: string }>();
  const { activeCondominiumId } = useTenant();

  const [deparaReport, setDeparaReport] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterType, setFilterType] = useState('todos');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchDePara = async () => {
    if (!activeCondominiumId || !docId) return;
    setIsLoading(true);
    setError('');
    try {
      const res = await api.get<any>(`/condominiums/${activeCondominiumId}/documents/${docId}/depara`);
      setDeparaReport(res.data);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar relatório DePara.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDePara();
  }, [activeCondominiumId, docId]);

  const entries = deparaReport?.entries || [];
  const filteredEntries = entries.filter((entry: any) => {
    const matchesFilter = filterType === 'todos' || entry.entry_type === filterType;
    const matchesSearch =
      !searchTerm.trim() ||
      (entry.draft_label && entry.draft_label.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (entry.draft_text && entry.draft_text.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (entry.summary && entry.summary.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <Breadcrumb
        items={[
          { label: 'Projetos Normativos', href: '/painel/projetos' },
          { label: 'Minuta de Trabalho', href: docId ? `/painel/documentos/${docId}/editor` : undefined },
          { label: 'Relatório DePara' },
        ]}
        showHome
      />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Relatório Comparativo DePara & Origens
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Rastreabilidade de alterações entre a convenção/regimento anterior e a nova minuta (CA-19, CA-20, CA-21).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link to={`/painel/documentos/${docId}/editor`}>
            <Button size="sm" variant="outline">
              <Edit3 className="w-3.5 h-3.5 mr-1 text-brand-700" aria-hidden="true" />
              <span>Editor Estruturado</span>
            </Button>
          </Link>
          <Link to={`/painel/documentos/${docId}/versoes`}>
            <Button size="sm" variant="outline">
              <History className="w-3.5 h-3.5 mr-1 text-slate-500" aria-hidden="true" />
              <span>Snapshots</span>
            </Button>
          </Link>
        </div>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {/* Métricas Clicáveis / Filtros Rápidos (Padrão Pro Max) */}
      {deparaReport && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
          <button
            onClick={() => setFilterType('todos')}
            className={`p-3 rounded-xl border text-left transition-all ${
              filterType === 'todos'
                ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                : 'bg-white border-slate-200 hover:border-slate-300'
            }`}
          >
            <span className={`text-2xl font-bold block ${filterType === 'todos' ? 'text-white' : 'text-slate-900'}`}>
              {deparaReport.total_entries || 0}
            </span>
            <p className={`text-xs mt-0.5 ${filterType === 'todos' ? 'text-slate-300' : 'text-slate-500'}`}>
              Todos os Dispositivos
            </p>
          </button>

          <button
            onClick={() => setFilterType('incluido')}
            className={`p-3 rounded-xl border text-left transition-all ${
              filterType === 'incluido'
                ? 'bg-emerald-700 text-white border-emerald-700 shadow-sm'
                : 'bg-emerald-50/60 border-emerald-200 hover:border-emerald-300'
            }`}
          >
            <span className={`text-2xl font-bold block ${filterType === 'incluido' ? 'text-white' : 'text-emerald-800'}`}>
              {deparaReport.total_new_provisions || 0}
            </span>
            <p className={`text-xs mt-0.5 ${filterType === 'incluido' ? 'text-emerald-100' : 'text-emerald-700'}`}>
              Novos Incluídos (Sem Origem)
            </p>
          </button>

          <button
            onClick={() => setFilterType('excluido')}
            className={`p-3 rounded-xl border text-left transition-all ${
              filterType === 'excluido'
                ? 'bg-rose-700 text-white border-rose-700 shadow-sm'
                : 'bg-rose-50/60 border-rose-200 hover:border-rose-300'
            }`}
          >
            <span className={`text-2xl font-bold block ${filterType === 'excluido' ? 'text-white' : 'text-rose-800'}`}>
              {deparaReport.total_excluded_provisions || 0}
            </span>
            <p className={`text-xs mt-0.5 ${filterType === 'excluido' ? 'text-rose-100' : 'text-rose-700'}`}>
              Excluídos da Minuta
            </p>
          </button>

          <button
            onClick={() => setFilterType('alterado')}
            className={`p-3 rounded-xl border text-left transition-all ${
              filterType === 'alterado'
                ? 'bg-blue-700 text-white border-blue-700 shadow-sm'
                : 'bg-blue-50/60 border-blue-200 hover:border-blue-300'
            }`}
          >
            <span className={`text-2xl font-bold block ${filterType === 'alterado' ? 'text-white' : 'text-blue-800'}`}>
              {(deparaReport.total_entries || 0) -
                (deparaReport.total_new_provisions || 0) -
                (deparaReport.total_excluded_provisions || 0)}
            </span>
            <p className={`text-xs mt-0.5 ${filterType === 'alterado' ? 'text-blue-100' : 'text-blue-700'}`}>
              Mantidos / Alterados
            </p>
          </button>
        </div>
      )}

      {/* Mapeamento DePara: Desktop Table + Mobile Cards (M7.1) */}
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3">
          <div>
            <CardTitle className="text-base flex items-center gap-2">
              <span>Mapeamento DePara da Minuta</span>
              <Badge variant="outline" className="font-mono text-[10px]">
                {filteredEntries.length} de {entries.length}
              </Badge>
            </CardTitle>
            <CardDescription>
              Confronto entre a redação anterior e a nova redação proposta com justificativa e histórico.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" aria-hidden="true" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Filtrar por artigo ou texto..."
                className="text-xs pl-8 pr-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-brand-600 focus:bg-white w-48 transition-all"
              />
            </div>
            {filterType !== 'todos' && (
              <button
                onClick={() => setFilterType('todos')}
                className="text-[11px] text-brand-700 hover:underline whitespace-nowrap"
              >
                Limpar filtro
              </button>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {/* Visualização Desktop: Tabela */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3 w-1/4">Dispositivo na Minuta</th>
                  <th className="px-6 py-3 w-1/6">Classificação</th>
                  <th className="px-6 py-3 w-1/3">Origem(ns) na Convenção Anterior</th>
                  <th className="px-6 py-3">Resumo da Rastreabilidade</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredEntries.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                      Nenhum dispositivo encontrado para os filtros selecionados.
                    </td>
                  </tr>
                ) : (
                  filteredEntries.map((entry: any, idx: number) => {
                    const rowBg =
                      entry.entry_type === 'incluido'
                        ? 'bg-emerald-50/30 hover:bg-emerald-50/50'
                        : entry.entry_type === 'excluido'
                        ? 'bg-rose-50/30 hover:bg-rose-50/50'
                        : entry.entry_type === 'alterado'
                        ? 'bg-blue-50/20 hover:bg-blue-50/40'
                        : 'hover:bg-slate-50/60';

                    return (
                      <tr key={idx} className={`${rowBg} transition-colors`}>
                        <td className="px-6 py-3.5 align-top">
                          <span className="font-bold text-slate-900 block text-sm">{entry.draft_label}</span>
                          <p className={`text-slate-800 text-xs mt-1 leading-relaxed font-serif ${entry.entry_type === 'excluido' ? 'line-through text-slate-400' : ''}`}>
                            {entry.draft_text}
                          </p>
                        </td>
                        <td className="px-6 py-3.5 align-top">
                          <Badge variant={(entry.entry_type as any) || 'default'} dot>
                            {entry.entry_type}
                          </Badge>
                        </td>
                        <td className="px-6 py-3.5 align-top">
                          {entry.sources && entry.sources.length > 0 ? (
                            <div className="space-y-1.5">
                              {entry.sources.map((s: any, sIdx: number) => (
                                <div key={sIdx} className="p-2 bg-slate-50 border border-slate-200/80 rounded-lg text-xs text-slate-800 font-serif">
                                  <strong className="font-sans font-semibold text-slate-900">{s.source_label}:</strong> {s.source_text}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <span className="text-slate-400 italic text-xs">Sem correspondente anterior (Dispositivo Novo)</span>
                          )}
                        </td>
                        <td className="px-6 py-3.5 align-top text-slate-600 leading-relaxed text-xs">
                          {entry.summary || '—'}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Visualização Mobile: Cards Empilhados (M7.1) */}
          <div className="md:hidden divide-y divide-slate-100 p-3 space-y-3">
            {filteredEntries.length === 0 ? (
              <p className="text-center py-6 text-xs text-slate-500">
                Nenhum dispositivo encontrado para os filtros selecionados.
              </p>
            ) : (
              filteredEntries.map((entry: any, idx: number) => (
                <div key={idx} className="pt-3 first:pt-0 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 text-sm">{entry.draft_label}</span>
                    <Badge variant={(entry.entry_type as any) || 'default'} dot>{entry.entry_type}</Badge>
                  </div>
                  <p className="text-slate-800 leading-relaxed font-serif bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    {entry.draft_text}
                  </p>
                  {entry.sources && entry.sources.length > 0 ? (
                    <div className="space-y-1">
                      <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Origem Anterior:</span>
                      {entry.sources.map((s: any, sIdx: number) => (
                        <div key={sIdx} className="p-2 bg-slate-100/70 border rounded text-xs text-slate-700 font-serif">
                          <strong>{s.source_label}:</strong> {s.source_text}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-500 italic text-[11px]">Sem correspondente anterior (Novo)</p>
                  )}
                  {entry.summary && (
                    <p className="text-slate-500 text-[11px] pt-1">
                      <strong>Resumo:</strong> {entry.summary}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
