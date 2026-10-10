import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { Download, ShieldCheck, FileCheck, FileText, CheckCircle2, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';

export const ExportsPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [packageResult, setPackageResult] = useState<any | null>(null);
  const [internalReportResult, setInternalReportResult] = useState<any | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!activeCondominiumId) return;
    api.get<any[]>(`/condominiums/${activeCondominiumId}/projects`).then(async (resP) => {
      const projs = resP.data || [];
      if (projs.length > 0) {
        const resDocs = await api.get<any[]>(`/condominiums/${activeCondominiumId}/projects/${projs[0].id}/documents`);
        const docs = resDocs.data || [];
        setDocuments(docs);
        if (docs.length > 0) {
          setSelectedDocId(docs[0].id);
        }
      }
    });
  }, [activeCondominiumId]);

  const handleGeneratePublicPackage = async () => {
    if (!activeCondominiumId || !selectedDocId) return;
    setIsLoading(true);
    setError('');
    try {
      // CA-41, CA-42, UI-33: Gera pacote externo público com manifesto SHA-256 e sem notas/PII
      const res = await api.post(`/condominiums/${activeCondominiumId}/documents/${selectedDocId}/export/package`);
      setPackageResult(res.data);
    } catch (err: any) {
      setError(err.message || 'Erro ao gerar pacote público.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateInternalReport = async () => {
    if (!activeCondominiumId || !selectedDocId) return;
    setIsLoading(true);
    setError('');
    try {
      // UI-33: Gera relatório interno da comissão (is_public=False) contendo histórico e notas
      const res = await api.post(`/condominiums/${activeCondominiumId}/documents/${selectedDocId}/export/commission-report`);
      setInternalReportResult(res.data);
    } catch (err: any) {
      setError(err.message || 'Erro ao gerar relatório interno.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Central de Exportações</h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Geração de pacotes normativos públicos com manifesto de integridade e relatórios confidenciais da comissão (UI-33, CA-42).
        </p>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      <div className="bg-white p-4 rounded-xl border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="w-full sm:w-auto">
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Minuta Normativa Selecionada
          </label>
          <select
            className="text-sm border border-slate-300 rounded-lg p-2 outline-none w-full sm:w-80"
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
          >
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                {d.title} ({d.type.replace('_', ' ')})
              </option>
            ))}
          </select>
        </div>

        <div className="flex gap-2 w-full sm:w-auto">
          <Button onClick={handleGeneratePublicPackage} isLoading={isLoading}>
            <Download className="w-4 h-4 mr-1.5" />
            <span>Gerar Pacote Externo Público</span>
          </Button>
          <Button variant="outline" onClick={handleGenerateInternalReport} isLoading={isLoading}>
            <FileText className="w-4 h-4 mr-1.5" />
            <span>Relatório Interno da Comissão</span>
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Card 1: Pacote Externo Público */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center justify-between">
              <span>Pacote Externo Público</span>
              <Badge variant="success">Público Sanitizado</Badge>
            </CardTitle>
            <CardDescription>
              Minuta limpa final, relatório DePara e manifesto SHA-256 para distribuição na assembleia.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs text-slate-600">
            <p>
              <strong>Garantias do Pacote:</strong>
            </p>
            <ul className="list-disc pl-4 space-y-1 text-slate-500">
              <li>Expurgo total de notas internas da equipe e pareceres jurídicos (CA-24).</li>
              <li>Ausência absoluta de nomes, e-mails, telefones ou dados de moradores (UI-33).</li>
              <li>Aviso obrigatório de que não constitui deliberação vinculante nem registro cartorial (UI-38).</li>
            </ul>

            {packageResult && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-900 space-y-2 mt-3">
                <span className="font-semibold block flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Pacote Gerado e Assinado!</span>
                </span>
                <p className="font-mono text-[11px] truncate">
                  Manifesto SHA-256: <code>{packageResult.manifest_hash}</code>
                </p>
                <div className="space-y-1 text-[11px]">
                  {packageResult.files_manifest?.map((f: any, i: number) => (
                    <div key={i} className="flex justify-between font-mono bg-white/70 p-1 rounded">
                      <span>{f.path}</span>
                      <span className="text-slate-500">{f.size_bytes} bytes</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Card 2: Relatório Interno da Comissão */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center justify-between">
              <span>Relatório Interno da Comissão</span>
              <Badge variant="warning">Confidencial</Badge>
            </CardTitle>
            <CardDescription>
              Relatório restrito com histórico de sugestões, pareceres, notas e incorporações.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs text-slate-600">
            <p>
              <strong>Conteúdo Restrito da Gestão:</strong>
            </p>
            <ul className="list-disc pl-4 space-y-1 text-slate-500">
              <li>Histórico de contribuições dos moradores e pareceres técnicos.</li>
              <li>Notas internas confidenciais registradas durante a redação.</li>
              <li>Trilha de incorporação de artigos na minuta normativa.</li>
            </ul>

            {internalReportResult && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 space-y-2 mt-3">
                <span className="font-semibold block flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-amber-600" />
                  <span>Relatório Confidencial Gerado!</span>
                </span>
                <p className="font-mono text-[11px] truncate">
                  Manifesto SHA-256: <code>{internalReportResult.manifest_hash}</code>
                </p>
                <p className="text-[11px]">
                  Total de contribuições documentadas:{' '}
                  <strong>{internalReportResult.report_content?.total_suggestions_analyzed || 0}</strong>
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
