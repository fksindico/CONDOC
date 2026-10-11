import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { ArrowLeft, FileDiff, Download, ShieldCheck, CheckCircle2, XCircle, Edit3, History } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';

export const CompareDeParaPage: React.FC = () => {
  const { docId } = useParams<{ docId: string }>();
  const { activeCondominiumId } = useTenant();

  const [deparaReport, setDeparaReport] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

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

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Link
            to="/painel/projetos"
            className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 mb-1 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Voltar aos Projetos</span>
          </Link>
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
              <Edit3 className="w-3.5 h-3.5 mr-1 text-brand-600" />
              <span>Editor Estruturado</span>
            </Button>
          </Link>
          <Link to={`/painel/documentos/${docId}/versoes`}>
            <Button size="sm" variant="outline">
              <History className="w-3.5 h-3.5 mr-1 text-slate-500" />
              <span>Snapshots</span>
            </Button>
          </Link>
        </div>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {deparaReport && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
          <div className="p-3 bg-white border rounded-xl shadow-xs">
            <span className="text-2xl font-bold text-slate-900">{deparaReport.total_entries || 0}</span>
            <p className="text-xs text-slate-500 mt-0.5">Dispositivos Avaliados</p>
          </div>
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl shadow-xs">
            <span className="text-2xl font-bold text-emerald-800">{deparaReport.total_new_provisions || 0}</span>
            <p className="text-xs text-emerald-700 mt-0.5">Novos Incluídos (Sem Origem)</p>
          </div>
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl shadow-xs">
            <span className="text-2xl font-bold text-rose-800">{deparaReport.total_excluded_provisions || 0}</span>
            <p className="text-xs text-rose-700 mt-0.5">Excluídos da Minuta</p>
          </div>
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl shadow-xs">
            <span className="text-2xl font-bold text-blue-800">
              {(deparaReport.total_entries || 0) -
                (deparaReport.total_new_provisions || 0) -
                (deparaReport.total_excluded_provisions || 0)}
            </span>
            <p className="text-xs text-blue-700 mt-0.5">Mantidos / Alterados</p>
          </div>
        </div>
      )}

      {/* Tabela DePara Granular */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Mapeamento DePara da Minuta</CardTitle>
          <CardDescription>
            Confronto entre a redação anterior e a nova redação proposta com justificativa e histórico.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
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
                {!deparaReport || !deparaReport.entries || deparaReport.entries.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                      Nenhum dispositivo mapeado neste documento.
                    </td>
                  </tr>
                ) : (
                  deparaReport.entries.map((entry: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-3.5 align-top">
                        <span className="font-bold text-slate-900 block text-sm">{entry.draft_label}</span>
                        <p className="text-slate-600 text-xs mt-1 leading-relaxed">{entry.draft_text}</p>
                      </td>
                      <td className="px-6 py-3.5 align-top">
                        <Badge variant={(entry.entry_type as any) || 'default'}>{entry.entry_type}</Badge>
                      </td>
                      <td className="px-6 py-3.5 align-top">
                        {entry.sources && entry.sources.length > 0 ? (
                          <div className="space-y-1.5">
                            {entry.sources.map((s: any, sIdx: number) => (
                              <div key={sIdx} className="p-2 bg-slate-50 border rounded text-[11px] text-slate-700">
                                <strong>{s.source_label}:</strong> {s.source_text}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">Sem correspondente anterior (Dispositivo Novo)</span>
                        )}
                      </td>
                      <td className="px-6 py-3.5 align-top text-slate-600 leading-relaxed">
                        {entry.summary || '—'}
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
