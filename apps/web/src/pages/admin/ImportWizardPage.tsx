import React, { useState } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { FileSpreadsheet, Upload, CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';

export const ImportWizardPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const [step, setStep] = useState<number>(1);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [batchData, setBatchData] = useState<any>(null);
  const [previewData, setPreviewData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [file, setFile] = useState<File | null>(null);

  // Mapeamento padrão de colunas
  const [mapping, setMapping] = useState({
    nome: 'Nome do Morador',
    unidade: 'Apartamento / Unidade',
    torre_bloco: 'Bloco',
    telefone: 'Telefone',
    email: 'E-mail',
    relacao: 'Vínculo',
  });

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !file) {
      setError('Selecione um arquivo de planilha CSV ou XLSX.');
      return;
    }
    setIsLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_label', 'upload_manual');

    try {
      const res = await api.post<any>(`/condominiums/${activeCondominiumId}/resident-imports`, formData);
      setBatchId(res.data.id);
      setBatchData(res.data);
      setStep(2);
    } catch (err: any) {
      setError(err.message || 'Erro ao enviar planilha.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyMapping = async () => {
    if (!activeCondominiumId || !batchId) return;
    setIsLoading(true);
    setError('');

    try {
      await api.post(`/condominiums/${activeCondominiumId}/resident-imports/${batchId}/mapping`, {
        mapping,
      });

      // Busca prévia validada pelo Core
      const prevRes = await api.get(`/condominiums/${activeCondominiumId}/resident-imports/${batchId}/preview`);
      setPreviewData(prevRes.data);
      setStep(3);
    } catch (err: any) {
      setError(err.message || 'Erro ao processar mapeamento de colunas.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmBatch = async () => {
    if (!activeCondominiumId || !batchId || !previewData) return;
    setIsLoading(true);
    setError('');

    try {
      // Confirmação transacional com expected_revision (V21-13)
      await api.post(`/condominiums/${activeCondominiumId}/resident-imports/${batchId}/confirm`, {
        expected_revision: previewData.revision || 1,
        acknowledge_selected_operations: true,
      });
      setStep(4);
    } catch (err: any) {
      setError(err.message || 'Erro ao confirmar lote de importação.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
          Assistente de Importação Cadastral
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Importe cadastros de moradores preservando zeros à esquerda e sem emissão automática de credenciais.
        </p>
      </div>

      {/* Indicador de Etapas */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-3 text-xs font-semibold">
        <span className={step >= 1 ? 'text-brand-600' : 'text-slate-400'}>1. Upload da Planilha</span>
        <span className="text-slate-300">→</span>
        <span className={step >= 2 ? 'text-brand-600' : 'text-slate-400'}>2. Mapeamento de Colunas</span>
        <span className="text-slate-300">→</span>
        <span className={step >= 3 ? 'text-brand-600' : 'text-slate-400'}>3. Prévia & Conflitos</span>
        <span className="text-slate-300">→</span>
        <span className={step >= 4 ? 'text-emerald-600' : 'text-slate-400'}>4. Concluído</span>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {/* Passo 1: Upload */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Upload className="w-5 h-5 text-brand-600" />
              <span>Etapa 1: Selecionar Arquivo</span>
            </CardTitle>
            <CardDescription>Formatos suportados: CSV e XLSX (até 10MB).</CardDescription>
          </CardHeader>
          <form onSubmit={handleFileUpload}>
            <CardContent className="space-y-4">
              <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:bg-slate-50/50 transition-colors cursor-pointer">
                <FileSpreadsheet className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                <p className="text-sm font-semibold text-slate-700">Clique para selecionar ou arraste sua planilha</p>
                <p className="text-xs text-slate-500 mt-1">
                  Proteção automática contra injeção de fórmulas ativada (V21-07).
                </p>
                <input
                  type="file"
                  accept=".csv, .xlsx, .xls"
                  className="mt-4 text-xs text-slate-600"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
              </div>

              <Alert variant="info" title="Garantia de Isolamento (CA-03 / V21-17)">
                O upload de cadastros apenas registra propostas em lote prévio. Não envia convites, não cria contas e
                não altera a base ativa antes da confirmação explícita.
              </Alert>
            </CardContent>
            <CardFooter>
              <Button type="submit" isLoading={isLoading} disabled={!file}>
                <span>Continuar para Mapeamento</span>
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
            </CardFooter>
          </form>
        </Card>
      )}

      {/* Passo 2: Mapeamento de Colunas */}
      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Etapa 2: Mapeamento das Colunas</CardTitle>
            <CardDescription>Associe as colunas da sua planilha aos campos canônicos do CONDOC.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Coluna: Nome do Morador *</label>
                <input
                  type="text"
                  className="w-full border border-slate-300 rounded-lg p-2 outline-none"
                  value={mapping.nome}
                  onChange={(e) => setMapping({ ...mapping, nome: e.target.value })}
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Coluna: Unidade / Apartamento *</label>
                <input
                  type="text"
                  className="w-full border border-slate-300 rounded-lg p-2 outline-none"
                  value={mapping.unidade}
                  onChange={(e) => setMapping({ ...mapping, unidade: e.target.value })}
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Coluna: Bloco / Torre</label>
                <input
                  type="text"
                  className="w-full border border-slate-300 rounded-lg p-2 outline-none"
                  value={mapping.torre_bloco}
                  onChange={(e) => setMapping({ ...mapping, torre_bloco: e.target.value })}
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Coluna: Telefone</label>
                <input
                  type="text"
                  className="w-full border border-slate-300 rounded-lg p-2 outline-none"
                  value={mapping.telefone}
                  onChange={(e) => setMapping({ ...mapping, telefone: e.target.value })}
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Coluna: E-mail</label>
                <input
                  type="text"
                  className="w-full border border-slate-300 rounded-lg p-2 outline-none"
                  value={mapping.email}
                  onChange={(e) => setMapping({ ...mapping, email: e.target.value })}
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Coluna: Vínculo / Relação</label>
                <input
                  type="text"
                  className="w-full border border-slate-300 rounded-lg p-2 outline-none"
                  value={mapping.relacao}
                  onChange={(e) => setMapping({ ...mapping, relacao: e.target.value })}
                />
              </div>
            </div>
          </CardContent>
          <CardFooter className="justify-between">
            <Button variant="outline" onClick={() => setStep(1)}>
              Voltar
            </Button>
            <Button onClick={handleApplyMapping} isLoading={isLoading}>
              <span>Validar e Gerar Prévia</span>
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </Button>
          </CardFooter>
        </Card>
      )}

      {/* Passo 3: Prévia e Conflitos */}
      {step === 3 && previewData && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Etapa 3: Prévia de Operações e Conflitos</CardTitle>
            <CardDescription>
              Revise o impacto do lote antes de confirmar a transação atômica.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <div className="p-3 bg-slate-50 border rounded-lg">
                <span className="text-xl font-bold text-slate-900">{previewData.total_rows || 0}</span>
                <p className="text-[11px] text-slate-500 mt-0.5">Linhas Lidas</p>
              </div>
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                <span className="text-xl font-bold text-emerald-800">{previewData.proposed_creates || 0}</span>
                <p className="text-[11px] text-emerald-700 mt-0.5">Novos Cadastros</p>
              </div>
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <span className="text-xl font-bold text-blue-800">{previewData.proposed_updates || 0}</span>
                <p className="text-[11px] text-blue-700 mt-0.5">Atualizações</p>
              </div>
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <span className="text-xl font-bold text-amber-800">{previewData.conflicts_count || 0}</span>
                <p className="text-[11px] text-amber-700 mt-0.5">Conflitos</p>
              </div>
            </div>

            <Alert variant="warning" title="Confirmação Irreversível de Lote">
              Ao confirmar, os novos pré-cadastros serão inseridos atomicamente na base. Lembre-se: os convites devem
              ser emitidos posteriormente em S07 (Convites de Acesso).
            </Alert>
          </CardContent>
          <CardFooter className="justify-between">
            <Button variant="outline" onClick={() => setStep(2)}>
              Revisar Mapeamento
            </Button>
            <Button onClick={handleConfirmBatch} isLoading={isLoading}>
              <span>Confirmar e Aplicar Lote</span>
              <CheckCircle2 className="w-4 h-4 ml-1.5" />
            </Button>
          </CardFooter>
        </Card>
      )}

      {/* Passo 4: Concluído */}
      {step === 4 && (
        <Card className="text-center p-8 space-y-4">
          <div className="inline-flex p-3 bg-emerald-100 rounded-full text-emerald-700 mx-auto">
            <CheckCircle2 className="w-10 h-10" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Lote Processado com Sucesso!</h2>
          <p className="text-xs text-slate-600 max-w-md mx-auto">
            Os pré-cadastros foram consolidados no banco de dados. Agora você pode emitir convites controlados ou
            revisar a lista de moradores.
          </p>
          <div className="flex justify-center gap-3 pt-4">
            <Button variant="outline" onClick={() => (window.location.href = '/painel/moradores')}>
              Ver Moradores
            </Button>
            <Button onClick={() => (window.location.href = '/painel/convites')}>
              Ir para Convites de Acesso
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
};
