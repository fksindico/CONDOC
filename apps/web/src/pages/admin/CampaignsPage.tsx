import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTenant } from '@/contexts/TenantContext';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/lib/api';
import type { ConsultationCampaign } from '@condc/api-contracts';
import { Sliders, Plus, Play, Square, Eye, EyeOff, ShieldAlert, Calendar, MessageSquare, BarChart3 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';
import { CardSkeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatDatePtBr } from '@/lib/utils';

export const CampaignsPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const { toast } = useToast();
  const [campaigns, setCampaigns] = useState<ConsultationCampaign[]>([]);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Modal Nova Campanha
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [selectedSnapshotId, setSelectedSnapshotId] = useState('');
  const [allowSuggestions, setAllowSuggestions] = useState(true);
  const [allowComplements, setAllowComplements] = useState(true);
  const [allowAgreements, setAllowAgreements] = useState(true);
  const [hideCounts, setHideCounts] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  const fetchCampaigns = async () => {
    if (!activeCondominiumId) return;
    setIsLoading(true);
    setError('');
    try {
      const [resC, resP] = await Promise.all([
        api.get<ConsultationCampaign[]>(`/condominiums/${activeCondominiumId}/campaigns`),
        api.get<any[]>(`/condominiums/${activeCondominiumId}/projects`),
      ]);
      setCampaigns(resC.data || []);
      const projs = resP.data || [];
      setProjects(projs);
      if (projs.length > 0 && !selectedProjectId) {
        setSelectedProjectId(projs[0].id);
        // Busca snapshots do projeto
        const resDocs = await api.get<any[]>(`/condominiums/${activeCondominiumId}/projects/${projs[0].id}/documents`);
        const docs = resDocs.data || [];
        if (docs.length > 0) {
          const resSnaps = await api.get<any[]>(`/condominiums/${activeCondominiumId}/documents/${docs[0].id}/snapshots`);
          setSnapshots(resSnaps.data || []);
          if (resSnaps.data && resSnaps.data.length > 0) {
            setSelectedSnapshotId(resSnaps.data[0].id);
          }
        }
      }
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar campanhas.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, [activeCondominiumId]);

  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !selectedProjectId || !selectedSnapshotId) {
      toast.error('Selecione um projeto e um snapshot imutável para a campanha.');
      return;
    }
    setIsCreating(true);

    try {
      await api.post(`/condominiums/${activeCondominiumId}/campaigns`, {
        project_id: selectedProjectId,
        snapshot_id: selectedSnapshotId,
        name: name.trim(),
        settings: {
          allow_suggestions: allowSuggestions,
          allow_complements: allowComplements,
          allow_agreements: allowAgreements,
          hide_counts: hideCounts,
        },
      });
      setIsModalOpen(false);
      setName('');
      toast.success('Campanha de consulta criada com sucesso!');
      fetchCampaigns();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao criar campanha.');
    } finally {
      setIsCreating(false);
    }
  };

  const handleToggleState = async (campaignId: string, action: 'open' | 'close') => {
    if (!activeCondominiumId) return;
    try {
      await api.post(`/condominiums/${activeCondominiumId}/campaigns/${campaignId}/${action}`);
      toast.success(action === 'open' ? 'Consulta pública aberta aos moradores!' : 'Consulta pública encerrada com sucesso.');
      fetchCampaigns();
    } catch (err: any) {
      toast.error(err.message || `Erro ao ${action === 'open' ? 'abrir' : 'encerrar'} campanha.`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Campanhas de Consulta Pública
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Gestão de campanhas consultivas vinculadas a snapshots imutáveis (S15, CA-25).
          </p>
        </div>
        <Button size="sm" onClick={() => setIsModalOpen(true)}>
          <Plus className="w-4 h-4 mr-1.5" />
          <span>Nova Campanha</span>
        </Button>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      <div className="space-y-4">
        {isLoading ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : campaigns.length === 0 ? (
          <EmptyState
            icon={Sliders}
            title="Nenhuma campanha de consulta criada"
            description="Crie uma campanha vinculando a um snapshot congelado da minuta para abrir a participação aos moradores."
            actionLabel="Criar Primeira Campanha"
            onAction={() => setIsModalOpen(true)}
          />
        ) : (
          campaigns.map((camp: any) => {
            const isOpen = camp.state === 'aberta';
            return (
              <Card key={camp.id} className="hover:border-slate-300 transition-colors">
                <CardContent className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-slate-900 text-base">{camp.name}</h3>
                      <Badge variant={isOpen ? 'success' : camp.state === 'encerrada' ? 'danger' : 'default'}>
                        {camp.state || 'Rascunho'}
                      </Badge>
                      {camp.settings?.hide_counts && (
                        <Badge variant="outline" className="text-[10px]">
                          Contagens Ocultas
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-slate-500">
                      Criada em {formatDatePtBr(camp.created_at)} • Início:{' '}
                      {camp.start_date ? formatDatePtBr(camp.start_date) : 'Não iniciado'}
                    </p>
                    <div className="flex gap-4 text-xs text-slate-600 pt-1">
                      <span>Sugestões: {camp.settings?.allow_suggestions ? 'Ativadas' : 'Desativadas'}</span>
                      <span>•</span>
                      <span>Concordâncias: {camp.settings?.allow_agreements ? 'Ativadas' : 'Desativadas'}</span>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 shrink-0">
                    <Link to={`/painel/sugestoes?campaign_id=${camp.id}`}>
                      <Button size="sm" variant="outline">
                        <MessageSquare className="w-3.5 h-3.5 mr-1 text-brand-600" />
                        <span>Fila 4D</span>
                      </Button>
                    </Link>
                    <Link to={`/painel/estatisticas`}>
                      <Button size="sm" variant="outline">
                        <BarChart3 className="w-3.5 h-3.5 mr-1 text-slate-500" />
                        <span>Métricas</span>
                      </Button>
                    </Link>
                    {!isOpen && camp.state !== 'encerrada' && (
                      <Button size="sm" onClick={() => handleToggleState(camp.id, 'open')}>
                        <Play className="w-3.5 h-3.5 mr-1" />
                        <span>Abrir Consulta</span>
                      </Button>
                    )}
                    {isOpen && (
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleToggleState(camp.id, 'close')}
                      >
                        <Square className="w-3.5 h-3.5 mr-1" />
                        <span>Encerrar Consulta</span>
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      {/* Modal Nova Campanha */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Criar Nova Campanha de Consulta"
        description="A campanha deve ser vinculada a um snapshot congelado imutável (UI-19)."
      >
        <form onSubmit={handleCreateCampaign} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Nome da Campanha *
            </label>
            <input
              type="text"
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Ex: Consulta Pública — Minuta Regimento 2026"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Projeto Normativo *
              </label>
              <select
                className="w-full text-sm border border-slate-300 rounded-lg p-2 outline-none"
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Snapshot Congelado *
              </label>
              <select
                className="w-full text-sm border border-slate-300 rounded-lg p-2 outline-none"
                value={selectedSnapshotId}
                onChange={(e) => setSelectedSnapshotId(e.target.value)}
              >
                {snapshots.length === 0 ? (
                  <option value="">Nenhum snapshot disponível</option>
                ) : (
                  snapshots.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.version_label}
                    </option>
                  ))
                )}
              </select>
            </div>
          </div>

          {/* Toggles de Recursos da Campanha (S15) */}
          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2.5 text-xs text-slate-700">
            <span className="font-bold text-slate-900 block mb-1">Recursos Habilitados na Campanha</span>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={allowSuggestions}
                onChange={(e) => setAllowSuggestions(e.target.checked)}
              />
              <span>Permitir envio de sugestões privadas pelos moradores</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={allowComplements}
                onChange={(e) => setAllowComplements(e.target.checked)}
              />
              <span>Permitir complementos e melhorias sobre propostas públicas</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={allowAgreements}
                onChange={(e) => setAllowAgreements(e.target.checked)}
              />
              <span>Habilitar botão consultivo "Concordo com esta proposta"</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={hideCounts}
                onChange={(e) => setHideCounts(e.target.checked)}
              />
              <span>
                <strong>Ocultar contagens para os moradores</strong> (Evita efeito manada - CA-38, UI-30)
              </span>
            </label>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" isLoading={isCreating}>
              Criar Campanha
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
