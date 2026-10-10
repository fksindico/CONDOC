import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/lib/api';
import type { Project } from '@condc/api-contracts';
import { Link } from 'react-router-dom';
import { FolderGit2, Plus, FileText, ArrowRight, ShieldCheck, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';
import { CardSkeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatDatePtBr } from '@/lib/utils';

export const ProjectsPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const { toast } = useToast();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Modal Novo Projeto
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [purpose, setPurpose] = useState('');
  const [kind, setKind] = useState<'revisao' | 'criacao' | 'conjunta'>('revisao');
  const [isCreating, setIsCreating] = useState(false);

  const fetchProjects = async () => {
    if (!activeCondominiumId) return;
    setIsLoading(true);
    setError('');
    try {
      const res = await api.get<Project[]>(`/condominiums/${activeCondominiumId}/projects`);
      setProjects(res.data || []);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar projetos.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [activeCondominiumId]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId) return;
    setIsCreating(true);

    try {
      await api.post(`/condominiums/${activeCondominiumId}/projects`, {
        name: name.trim(),
        purpose: purpose.trim() || undefined,
        kind,
      });
      setIsModalOpen(false);
      setName('');
      setPurpose('');
      toast.success('Projeto normativo criado com sucesso!');
      fetchProjects();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao criar projeto.');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Projetos Normativos</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Gestão de criação, modernização e revisão de Convenções e Regimentos Internos (S08).
          </p>
        </div>
        <Button size="sm" onClick={() => setIsModalOpen(true)}>
          <Plus className="w-4 h-4 mr-1.5" />
          <span>Novo Projeto</span>
        </Button>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {isLoading ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : projects.length === 0 ? (
          <div className="col-span-full">
            <EmptyState
              icon={FolderGit2}
              title="Nenhum projeto normativo iniciado"
              description="Crie um projeto para elaborar ou revisar o Regimento Interno ou Convenção do condomínio."
              actionLabel="Criar Primeiro Projeto"
              onAction={() => setIsModalOpen(true)}
            />
          </div>
        ) : (
          projects.map((p) => (
            <Card key={p.id} className="flex flex-col justify-between hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <Badge variant="info" className="uppercase font-mono text-[10px]">
                    {p.kind}
                  </Badge>
                  <span className="text-[11px] text-slate-600 font-medium capitalize">
                    {p.status}
                  </span>
                </div>
                <CardTitle className="text-base mt-2 text-slate-900">{p.name}</CardTitle>
                {p.purpose && <CardDescription className="line-clamp-2 mt-1">{p.purpose}</CardDescription>}
              </CardHeader>
              <CardContent className="pt-0 pb-4">
                <div className="flex items-center gap-1.5 text-[11px] text-slate-600 mb-4 font-medium">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Iniciado em {formatDatePtBr(p.created_at)}</span>
                </div>
                <Link to={`/painel/projetos/${p.id}/documentos`}>
                  <Button variant="outline" size="sm" className="w-full justify-between">
                    <span>Acessar Documentos</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Modal Novo Projeto */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Criar Novo Projeto Normativo"
        description="Define o escopo de revisão ou modernização documental."
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Nome do Projeto *
            </label>
            <input
              type="text"
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Ex: Revisão Geral do Regimento Interno 2026"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Tipo / Natureza *
            </label>
            <select
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={kind}
              onChange={(e: any) => setKind(e.target.value)}
            >
              <option value="revisao">Revisão / Modernização de Norma Existente</option>
              <option value="criacao">Criação de Novo Documento Normativo</option>
              <option value="conjunta">Revisão Conjunta (Convenção + Regimento)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Finalidade / Justificativa
            </label>
            <textarea
              rows={3}
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Ex: Atualização das normas sobre áreas comuns, convivência de pets e veículos elétricos..."
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" isLoading={isCreating}>
              Criar Projeto
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
