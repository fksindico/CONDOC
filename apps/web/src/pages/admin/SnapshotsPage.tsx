import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { History, Plus, ArrowLeft, Lock, CheckCircle2, Copy } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';
import { formatDatePtBr } from '@/lib/utils';

export const SnapshotsPage: React.FC = () => {
  const { docId } = useParams<{ docId: string }>();
  const { activeCondominiumId } = useTenant();

  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Modal Novo Snapshot
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [versionLabel, setVersionLabel] = useState('');
  const [purpose, setPurpose] = useState('consulta_publica');
  const [isCreating, setIsCreating] = useState(false);

  const fetchSnapshots = async () => {
    if (!activeCondominiumId || !docId) return;
    setIsLoading(true);
    setError('');
    try {
      const res = await api.get<any[]>(`/condominiums/${activeCondominiumId}/documents/${docId}/snapshots`);
      setSnapshots(res.data || []);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar snapshots.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSnapshots();
  }, [activeCondominiumId, docId]);

  const handleCreateSnapshot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !docId) return;
    setIsCreating(true);

    try {
      // CA-41: Congelamento atômico de revisões em snapshot imutável com cálculo SHA-256
      await api.post(`/condominiums/${activeCondominiumId}/documents/${docId}/snapshots`, {
        version_label: versionLabel.trim(),
        purpose,
      });
      setIsModalOpen(false);
      setVersionLabel('');
      fetchSnapshots();
    } catch (err: any) {
      alert(err.message || 'Erro ao congelar snapshot.');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Link
            to="/painel/projetos"
            className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 mb-1 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Voltar</span>
          </Link>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Snapshots & Versões Imutáveis
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Fotografias criptografadas e congeladas da minuta para consulta pública ou assembleia (CA-41, UI-17).
          </p>
        </div>
        <Button size="sm" onClick={() => setIsModalOpen(true)}>
          <Lock className="w-4 h-4 mr-1.5" />
          <span>Congelar Novo Snapshot</span>
        </Button>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      <div className="space-y-4">
        {snapshots.length === 0 ? (
          <Card className="text-center py-12 text-slate-500">
            <History className="w-10 h-10 mx-auto text-slate-400 mb-2" />
            <p className="text-sm font-semibold text-slate-700">Nenhum snapshot congelado.</p>
            <p className="text-xs text-slate-500 mt-0.5">
              Congele um snapshot para vincular à campanha de consulta pública dos moradores.
            </p>
          </Card>
        ) : (
          snapshots.map((snap) => (
            <Card key={snap.id} className="hover:border-slate-300 transition-colors">
              <CardContent className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-slate-900 text-sm">{snap.version_label}</h3>
                    <Badge variant="outline" className="text-[10px] uppercase font-mono">
                      {snap.purpose}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-500 flex items-center gap-1 font-mono">
                    <span>Hash SHA-256:</span>
                    <span className="text-slate-800 bg-slate-100 px-1.5 py-0.5 rounded text-[11px]">
                      {snap.content_hash || '—'}
                    </span>
                  </p>
                  <p className="text-[11px] text-slate-400">Congelado em {formatDatePtBr(snap.frozen_at)}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs text-emerald-700 font-semibold flex items-center gap-1 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Imutável</span>
                  </span>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Modal Novo Snapshot */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Congelar Novo Snapshot da Minuta"
        description="Gera uma versão congelada imutável e calcula o hash de integridade de todos os artigos."
      >
        <form onSubmit={handleCreateSnapshot} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Rótulo / Identificação da Versão *
            </label>
            <input
              type="text"
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Ex: Marco de Consulta Pública v1.0"
              value={versionLabel}
              onChange={(e) => setVersionLabel(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Finalidade do Marco *
            </label>
            <select
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
            >
              <option value="consulta_publica">Abertura de Consulta Pública</option>
              <option value="marco_revisao">Marco Interno de Revisão da Comissão</option>
              <option value="versao_final">Versão Final Consolidada para Assembleia</option>
            </select>
          </div>

          <Alert variant="info" title="Imutabilidade Garantida (UI-17)">
            Uma vez congelado, este snapshot não poderá ser editado diretamente. Futuras modificações deverão ocorrer
            na minuta de trabalho e gerar novos marcos.
          </Alert>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" isLoading={isCreating}>
              Confirmar Congelamento
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
