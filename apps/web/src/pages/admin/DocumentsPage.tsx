import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTenant } from '@/contexts/TenantContext';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/lib/api';
import type { Document } from '@condc/api-contracts';
import { FileText, Plus, ArrowLeft, ArrowRight, Edit3, Camera, FileDiff, History, Maximize2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';
import { CardSkeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';

export const DocumentsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { activeCondominiumId } = useTenant();
  const { toast } = useToast();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Modal Novo Documento
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [docType, setDocType] = useState<'regimento_interno' | 'convencao' | 'anexo_normativo'>('regimento_interno');
  const [isCreating, setIsCreating] = useState(false);

  const fetchDocuments = async () => {
    if (!activeCondominiumId || !projectId) return;
    setIsLoading(true);
    setError('');
    try {
      const res = await api.get<Document[]>(`/condominiums/${activeCondominiumId}/projects/${projectId}/documents`);
      setDocuments(res.data || []);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar minutas do projeto.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [activeCondominiumId, projectId]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !projectId) return;
    setIsCreating(true);

    try {
      await api.post(`/condominiums/${activeCondominiumId}/projects/${projectId}/documents`, {
        title: title.trim(),
        type: docType,
        numbering_policy: 'preservar_original',
      });
      setIsModalOpen(false);
      setTitle('');
      toast.success('Minuta normativa criada com sucesso!');
      fetchDocuments();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao criar documento.');
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
            <span>Voltar aos Projetos</span>
          </Link>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Minutas Normativas</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Minutas de trabalho, histórico de versões e dispositivos normativos estruturados (S09).
          </p>
        </div>
        <Button size="sm" onClick={() => setIsModalOpen(true)}>
          <Plus className="w-4 h-4 mr-1.5" />
          <span>Nova Minuta</span>
        </Button>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {isLoading ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : documents.length === 0 ? (
          <div className="col-span-full">
            <EmptyState
              icon={FileText}
              title="Nenhum documento normativo cadastrado"
              description="Crie uma minuta de Regimento Interno ou Convenção para iniciar a redação dos dispositivos."
              actionLabel="Criar Primeira Minuta"
              onAction={() => setIsModalOpen(true)}
            />
          </div>
        ) : (
          documents.map((d) => (
            <Card key={d.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <Badge variant="info" className="uppercase font-mono text-[10px]">
                    {d.type.replace('_', ' ')}
                  </Badge>
                  <span className="text-[11px] font-semibold text-slate-600 capitalize bg-slate-100 px-2 py-0.5 rounded">
                    {d.editorial_status.replace('_', ' ')}
                  </span>
                </div>
                <CardTitle className="text-base mt-2 text-slate-900">{d.title}</CardTitle>
                <CardDescription>Política de Numeração: {d.numbering_policy}</CardDescription>
              </CardHeader>
              <CardContent className="pt-0 space-y-2">
                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 text-xs">
                  <Link to={`/painel/documentos/${d.id}/editor`}>
                    <Button variant="primary" size="sm" className="w-full justify-center">
                      <Edit3 className="w-3.5 h-3.5 mr-1" />
                      <span>Editor Estruturado</span>
                    </Button>
                  </Link>
                  <Link to={`/painel/documentos/${d.id}/compare`}>
                    <Button variant="outline" size="sm" className="w-full justify-center">
                      <FileDiff className="w-3.5 h-3.5 mr-1" />
                      <span>DePara & Diff</span>
                    </Button>
                  </Link>
                  <Link to={`/painel/documentos/${d.id}/importacao`}>
                    <Button variant="outline" size="sm" className="w-full justify-center">
                      <Camera className="w-3.5 h-3.5 mr-1" />
                      <span>OCR Original</span>
                    </Button>
                  </Link>
                  <Link to={`/painel/documentos/${d.id}/versoes`}>
                    <Button variant="outline" size="sm" className="w-full justify-center">
                      <History className="w-3.5 h-3.5 mr-1" />
                      <span>Snapshots</span>
                    </Button>
                  </Link>
                  <Link to={`/assembleia/${d.id}`} className="col-span-2">
                    <Button variant="outline" size="sm" className="w-full justify-center text-slate-800 border-slate-300 hover:bg-slate-100">
                      <Maximize2 className="w-3.5 h-3.5 mr-1 text-indigo-600" />
                      <span>Projetar em Assembleia</span>
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Modal Nova Minuta */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Criar Nova Minuta Normativa"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Título da Minuta *
            </label>
            <input
              type="text"
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Ex: Minuta de Regimento Interno 2026"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Tipo do Documento *
            </label>
            <select
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={docType}
              onChange={(e: any) => setDocType(e.target.value)}
            >
              <option value="regimento_interno">Regimento Interno</option>
              <option value="convencao">Convenção de Condomínio</option>
              <option value="anexo_normativo">Anexo Normativo (Manual de Obras, Salão de Festas, etc.)</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" isLoading={isCreating}>
              Criar Minuta
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
