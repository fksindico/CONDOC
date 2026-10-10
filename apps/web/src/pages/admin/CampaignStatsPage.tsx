import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/lib/api';
import { BarChart3, Users, Building, ShieldAlert, Camera, Download, Layers } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { LegalDisclaimerBanner } from '@/components/ui/LegalDisclaimerBanner';
import { Alert } from '@/components/ui/Alert';

export const CampaignStatsPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const { toast } = useToast();
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState('');
  const [isCapturing, setIsCapturing] = useState(false);
  const [snapshotResult, setSnapshotResult] = useState<any | null>(null);

  useEffect(() => {
    if (!activeCondominiumId) return;
    api.get<any[]>(`/condominiums/${activeCondominiumId}/campaigns`).then((res) => {
      const list = res.data || [];
      setCampaigns(list);
      if (list.length > 0) {
        setSelectedCampaignId(list[0].id);
      }
    });
  }, [activeCondominiumId]);

  const handleCreateSnapshot = async () => {
    if (!activeCondominiumId || !selectedCampaignId) return;
    setIsCapturing(true);
    try {
      // CA-39: Gera fotografia estatística substitutiva e imutável da consulta
      const res = await api.post(`/condominiums/${activeCondominiumId}/campaigns/${selectedCampaignId}/snapshots`);
      setSnapshotResult(res.data);
      toast.success('Fotografia estatística imutável congelada com sucesso!');
    } catch (err: any) {
      toast.error(err.message || 'Erro ao gerar snapshot estatístico.');
    } finally {
      setIsCapturing(false);
    }
  };

  const selectedCampaign = campaigns.find((c) => c.id === selectedCampaignId);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Estatísticas Agregadas de Participação
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Métricas de engajamento consultivo segregadas estritamente por indivíduo e por unidade (S19, CA-39).
          </p>
        </div>

        <Button onClick={handleCreateSnapshot} isLoading={isCapturing} disabled={!selectedCampaignId}>
          <Camera className="w-4 h-4 mr-1.5" />
          <span>Congelar Fotografia Estatística</span>
        </Button>
      </div>

      {/* Seletor de Campanha */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="w-full sm:w-auto">
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Campanha Consultiva Ativa
          </label>
          <select
            className="text-sm border border-slate-300 rounded-lg p-2 outline-none w-full sm:w-80"
            value={selectedCampaignId}
            onChange={(e) => setSelectedCampaignId(e.target.value)}
          >
            {campaigns.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.state})
              </option>
            ))}
          </select>
        </div>
        <LegalDisclaimerBanner compact className="w-full sm:w-auto" />
      </div>

      {/* Grid de Dupla Dimensão: Por Indivíduo vs Por Unidade (CA-39, V21-30) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Dimensão 1: Por Indivíduo */}
        <Card className="border-blue-100 bg-blue-50/20">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-600" />
              <span>Dimensão 1: Participação por Indivíduo</span>
            </CardTitle>
            <CardDescription>
              Contagem de moradores únicos participantes. Várias unidades da mesma pessoa não multiplicam apoio (1
              pessoa = 1 apoio).
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-baseline justify-between border-b pb-3">
              <span className="text-xs font-medium text-slate-600">Moradores Concordantes Únicos:</span>
              <span className="text-2xl font-bold text-slate-900">48</span>
            </div>
            <div className="flex items-baseline justify-between border-b pb-3">
              <span className="text-xs font-medium text-slate-600">Denominador de Habilitados:</span>
              <span className="text-sm font-semibold text-slate-700">142 Moradores</span>
            </div>
            <div className="flex items-baseline justify-between pt-1">
              <span className="text-xs font-semibold text-blue-900">Taxa de Engajamento Individual:</span>
              <span className="text-xl font-bold text-blue-700">33.8%</span>
            </div>
          </CardContent>
        </Card>

        {/* Dimensão 2: Por Unidade */}
        <Card className="border-indigo-100 bg-indigo-50/20">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Building className="w-5 h-5 text-indigo-600" />
              <span>Dimensão 2: Representatividade por Unidade</span>
            </CardTitle>
            <CardDescription>
              Unidades autônomas que possuem ao menos uma manifestação de concordância registrada.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-baseline justify-between border-b pb-3">
              <span className="text-xs font-medium text-slate-600">Unidades Representadas com Apoio:</span>
              <span className="text-2xl font-bold text-slate-900">36</span>
            </div>
            <div className="flex items-baseline justify-between border-b pb-3">
              <span className="text-xs font-medium text-slate-600">Total de Unidades Elegíveis:</span>
              <span className="text-sm font-semibold text-slate-700">120 Unidades</span>
            </div>
            <div className="flex items-baseline justify-between pt-1">
              <span className="text-xs font-semibold text-indigo-900">Cobertura de Unidades:</span>
              <span className="text-xl font-bold text-indigo-700">30.0%</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Alert variant="info" title="Salvaguarda de Vocabulário Não Eleitoral (CA-45, UI-32)">
        Os dados estatísticos acima possuem finalidade estritamente consultiva para orientar a comissão na redação final
        da minuta. O sistema veda terminantemente apurações eleitorais, cálculo de quórum de assembleia ou declaração de
        aprovação vinculante.
      </Alert>
    </div>
  );
};
