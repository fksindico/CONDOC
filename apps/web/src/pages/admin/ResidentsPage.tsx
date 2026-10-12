import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/lib/api';
import type { UnitMembership } from '@condc/api-contracts';
import {
  Users,
  UserPlus,
  Search,
  Phone,
  Mail,
  Home,
  ShieldAlert,
  Edit2,
  Archive,
  Trash2,
  RotateCcw,
  AlertTriangle,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { Modal } from '@/components/ui/Modal';
import { TableSkeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { Tabs } from '@/components/ui/Tabs';
import { Breadcrumb } from '@/components/ui/Breadcrumb';

export const ResidentsPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const { toast } = useToast();
  const [memberships, setMemberships] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'todos' | 'validado' | 'pendente' | 'em_analise'>('todos');
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Modal Pré-cadastro Manual (CA-02)
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [unitId, setUnitId] = useState('');
  const [units, setUnits] = useState<any[]>([]);

  // Modais de Edição e Exclusão / Revogação
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedMembership, setSelectedMembership] = useState<any | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [editFormData, setEditFormData] = useState({
    resident_name: '',
    phone_e164: '',
    category: 'proprietario_residente',
    membership_status: 'active',
  });

  const fetchData = async () => {
    if (!activeCondominiumId) return;
    setIsLoading(true);
    setError('');
    try {
      const [resM, resU] = await Promise.all([
        api.get<any[]>(`/condominiums/${activeCondominiumId}/memberships`),
        api.get<any[]>(`/condominiums/${activeCondominiumId}/units`),
      ]);
      setMemberships(resM.data || []);
      setUnits(resU.data || []);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar lista de moradores.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeCondominiumId]);

  const handleCreatePreRegistration = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !unitId) return;
    try {
      await api.post(`/condominiums/${activeCondominiumId}/registrations`, {
        unit_id: unitId,
        full_name: fullName.trim(),
        phone_e164: phone.trim() || null,
        email: email.trim() || null,
        relationship: 'proprietario_residente',
      });
      setIsModalOpen(false);
      setFullName('');
      setPhone('');
      setEmail('');
      setUnitId('');
      toast.success('Pré-cadastro de morador salvo com sucesso!');
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao criar pré-cadastro.');
    }
  };

  const handleOpenEdit = (m: any) => {
    setSelectedMembership(m);
    setEditFormData({
      resident_name: m.resident_name || '',
      phone_e164: m.phone_e164 || '',
      category: m.category || 'proprietario_residente',
      membership_status: m.membership_status || 'active',
    });
    setIsEditOpen(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !selectedMembership) return;

    setIsSubmitting(true);
    try {
      await api.patch(
        `/condominiums/${activeCondominiumId}/memberships/${selectedMembership.id}`,
        {
          resident_name: editFormData.resident_name.trim(),
          phone_e164: editFormData.phone_e164.trim() || null,
          category: editFormData.category,
          membership_status: editFormData.membership_status,
        }
      );
      toast.success('Cadastro do condômino atualizado com sucesso!');
      setIsEditOpen(false);
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao atualizar dados do condômino.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleArchive = async (m: any) => {
    if (!activeCondominiumId) return;
    const isEnded = m.membership_status === 'ended' || m.membership_status === 'inactive';
    const newStatus = isEnded ? 'active' : 'ended';
    const actionLabel = newStatus === 'active' ? 'reativado com sucesso' : 'arquivado/desativado com sucesso';

    try {
      await api.patch(
        `/condominiums/${activeCondominiumId}/memberships/${m.id}`,
        { membership_status: newStatus }
      );
      toast.success(`Condômino "${m.resident_name}" ${actionLabel}.`);
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao alterar status do condômino.');
    }
  };

  const handleOpenDelete = (m: any) => {
    setSelectedMembership(m);
    setIsDeleteOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!activeCondominiumId || !selectedMembership) return;

    setIsSubmitting(true);
    try {
      await api.delete(`/condominiums/${activeCondominiumId}/memberships/${selectedMembership.id}`);
      toast.success(`Vínculo de "${selectedMembership.resident_name}" revogado/excluído com sucesso.`);
      setIsDeleteOpen(false);
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao revogar vínculo do morador.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filtered = memberships.filter((m) => {
    const matchesTab = activeTab === 'todos' || m.verification_status === activeTab;
    const matchesSearch =
      !search ||
      (m.resident_name && m.resident_name.toLowerCase().includes(search.toLowerCase())) ||
      (m.unit_code && m.unit_code.toLowerCase().includes(search.toLowerCase()));
    return matchesTab && matchesSearch;
  });

  const tabItems = [
    { key: 'todos', label: 'Todos', badge: memberships.length },
    { key: 'validado', label: 'Validados' },
    { key: 'pendente', label: 'Pendentes' },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <Breadcrumb
        items={[
          { label: 'Estrutura & Moradores' },
          { label: 'Moradores & Vínculos' },
        ]}
        showHome
      />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Moradores & Vínculos</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Gestão completa, cadastros prévios e validações de residência (CA-02, CA-13, CA-14).
          </p>
        </div>
        <Button size="sm" onClick={() => setIsModalOpen(true)}>
          <UserPlus className="w-4 h-4 mr-1.5" aria-hidden="true" />
          <span>Novo Pré-cadastro</span>
        </Button>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      <Card>
        <CardHeader className="p-4 sm:p-6 pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            {/* Abas de Status com Tabs Component */}
            <Tabs
              items={tabItems}
              activeKey={activeTab}
              onChange={(k) => setActiveTab(k as any)}
              size="sm"
            />

            {/* Busca */}
            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                className="w-full text-xs border border-slate-200 rounded-lg pl-9 pr-3 py-2 outline-none focus:ring-1 focus:ring-brand-500"
                placeholder="Buscar por nome ou unidade..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <TableSkeleton rows={4} />
          ) : filtered.length === 0 ? (
            <div className="p-6">
              <EmptyState
                icon={Users}
                title="Nenhum morador encontrado"
                description={search ? "Nenhum resultado corresponde à sua busca." : "Nenhum morador com este status. Cadastre um novo morador ou importe uma planilha."}
                actionLabel={search ? undefined : "Novo Pré-cadastro"}
                onAction={search ? undefined : () => setIsModalOpen(true)}
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-3">Condômino / Morador</th>
                    <th className="px-6 py-3">Unidade</th>
                    <th className="px-6 py-3">Relação / Vínculo</th>
                    <th className="px-6 py-3">Status de Verificação</th>
                    <th className="px-6 py-3">Situação</th>
                    <th className="px-6 py-3 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filtered.map((m) => {
                    const isArchived = m.membership_status === 'ended' || m.membership_status === 'inactive';

                    return (
                      <tr key={m.id} className={`hover:bg-slate-50/50 transition-colors ${isArchived ? 'opacity-70 bg-slate-50/40' : ''}`}>
                        <td className="px-6 py-3.5">
                          <span className="font-semibold text-slate-900 text-sm block">
                            {m.resident_name || 'Morador'}
                          </span>
                          {m.phone_e164 && (
                            <span className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                              <Phone className="w-3 h-3 text-slate-400" />
                              {m.phone_e164}
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-3.5">
                          <span className="font-mono font-semibold text-slate-800 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                            {m.unit_code || '—'}
                          </span>
                        </td>
                        <td className="px-6 py-3.5 text-slate-600 capitalize">
                          {(m.category || 'proprietario_residente').replace(/_/g, ' ')}
                        </td>
                        <td className="px-6 py-3.5">
                          <Badge
                            variant={
                              m.verification_status === 'validado'
                                ? 'success'
                                : m.verification_status === 'pendente'
                                ? 'warning'
                                : 'default'
                            }
                          >
                            {m.verification_status || 'Pendente'}
                          </Badge>
                        </td>
                        <td className="px-6 py-3.5">
                          {isArchived ? (
                            <span className="inline-flex items-center text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                              Desativado
                            </span>
                          ) : (
                            <span className="inline-flex items-center text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
                              Ativo
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-3.5 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              onClick={() => handleOpenEdit(m)}
                              className="p-1.5 text-slate-500 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors"
                              title="Editar morador"
                              aria-label="Editar morador"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>

                            <button
                              onClick={() => handleToggleArchive(m)}
                              className="p-1.5 text-slate-500 hover:text-amber-600 hover:bg-slate-100 rounded-lg transition-colors"
                              title={isArchived ? 'Reativar condômino' : 'Arquivar/Desativar condômino'}
                              aria-label={isArchived ? 'Reativar condômino' : 'Arquivar/Desativar condômino'}
                            >
                              {isArchived ? <RotateCcw className="w-4 h-4" /> : <Archive className="w-4 h-4" />}
                            </button>

                            <button
                              onClick={() => handleOpenDelete(m)}
                              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-slate-100 rounded-lg transition-colors"
                              title="Revogar / Excluir vínculo"
                              aria-label="Revogar / Excluir vínculo"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal Pré-cadastro Manual (CA-02) */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Novo Pré-cadastro de Morador"
        description="Registra os dados prévios sem emitir credenciais ou enviar convite."
      >
        <form onSubmit={handleCreatePreRegistration} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Unidade Autônoma *
            </label>
            <select
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={unitId}
              onChange={(e) => setUnitId(e.target.value)}
            >
              <option value="">Selecione a unidade...</option>
              {units.map((u) => (
                <option key={u.id} value={u.id}>
                  Unidade {u.code || u.unit_number}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Nome Completo do Morador *
            </label>
            <input
              type="text"
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Ex: Mariana Oliveira"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Telefone (com DDD)
              </label>
              <input
                type="text"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="(11) 98888-7777"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                E-mail
              </label>
              <input
                type="email"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="morador@exemplo.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <span>
              <strong>Garantia de Não-Emissão Automática:</strong> Salvar o pré-cadastro não gera login nem convida o
              morador. O convite é emitido em etapa separada pelo assistente de convites.
            </span>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit">Salvar Pré-cadastro</Button>
          </div>
        </form>
      </Modal>

      {/* Modal Editar Condômino / Morador */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Editar Dados do Condômino"
        description="Atualize as informações cadastrais e relação de vínculo do morador com a unidade."
      >
        <form onSubmit={handleEditSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Nome do Morador *
            </label>
            <input
              type="text"
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={editFormData.resident_name}
              onChange={(e) => setEditFormData({ ...editFormData, resident_name: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Telefone
              </label>
              <input
                type="text"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="(11) 98888-7777"
                value={editFormData.phone_e164}
                onChange={(e) => setEditFormData({ ...editFormData, phone_e164: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Situação do Vínculo
              </label>
              <select
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                value={editFormData.membership_status}
                onChange={(e) => setEditFormData({ ...editFormData, membership_status: e.target.value })}
              >
                <option value="active">Ativo</option>
                <option value="ended">Encerrado / Desativado</option>
                <option value="inactive">Inativo</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Relação / Categoria de Vínculo *
            </label>
            <select
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={editFormData.category}
              onChange={(e) => setEditFormData({ ...editFormData, category: e.target.value })}
            >
              <option value="proprietario_residente">Proprietário Residente</option>
              <option value="proprietario_nao_residente">Proprietário Não Residente</option>
              <option value="inquilino">Inquilino / Locatário</option>
              <option value="dependente">Dependente Familiar</option>
              <option value="procurador">Procurador / Representante</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsEditOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Salvando...' : 'Salvar Alterações'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal Confirmar Exclusão / Revogação de Vínculo */}
      <Modal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title="Revogar Vínculo do Morador"
      >
        <div className="space-y-4">
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="text-xs text-rose-900">
              <p className="font-semibold text-rose-950">Atenção ao revogar este vínculo:</p>
              <p className="mt-1">
                Você está prestes a revogar o vínculo de <strong>{selectedMembership?.resident_name}</strong> com a
                unidade <strong>{selectedMembership?.unit_code}</strong>.
              </p>
              <p className="mt-1 text-slate-600">
                O histórico auditado será preservado (CA-12, CA-15), mas o morador perderá os acessos vinculados a esta unidade.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsDeleteOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              disabled={isSubmitting}
              onClick={handleDeleteConfirm}
            >
              {isSubmitting ? 'Revogando...' : 'Confirmar Revogação'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
