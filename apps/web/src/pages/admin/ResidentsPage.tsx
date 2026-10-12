import React, { useState, useEffect, useMemo } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/lib/api';
import type { Unit, ResidentRegistration, UnitMembership } from '@condc/api-contracts';
import {
  Users,
  UserPlus,
  Search,
  Phone,
  Mail,
  Home,
  ShieldAlert,
  ShieldCheck,
  Edit2,
  Archive,
  Trash2,
  RotateCcw,
  AlertTriangle,
  UserCheck,
  Clock,
  Sparkles,
  Info,
  CheckCircle2,
  FileCheck,
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

interface UnifiedResidentItem {
  id: string;
  itemType: 'registration' | 'membership';
  name: string;
  unitCode: string;
  unitId: string;
  phone?: string | null;
  email?: string | null;
  category: string;
  verificationStatus: string;
  membershipStatus: string;
  source: 'manual' | 'import' | 'vinculado';
  notes?: string | null;
  createdAt: string;
  raw: any;
}

export const ResidentsPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const { toast } = useToast();

  const [memberships, setMemberships] = useState<any[]>([]);
  const [registrations, setRegistrations] = useState<any[]>([]);
  const [units, setUnits] = useState<any[]>([]);

  const [activeTab, setActiveTab] = useState<'todos' | 'pre_cadastros' | 'validados' | 'pendentes'>('todos');
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 1. Modal Novo Pré-cadastro Manual (CA-02)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newFullName, setNewFullName] = useState('');
  const [newPhone, setNewPhone] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newUnitId, setNewUnitId] = useState('');
  const [newRelationship, setNewRelationship] = useState('proprietario_residente');
  const [newNotes, setNewNotes] = useState('');

  // 2. Modal Editar Pré-cadastro
  const [isEditRegOpen, setIsEditRegOpen] = useState(false);
  const [selectedReg, setSelectedReg] = useState<any | null>(null);
  const [editRegFullName, setEditRegFullName] = useState('');
  const [editRegPhone, setEditRegPhone] = useState('');
  const [editRegEmail, setEditRegEmail] = useState('');
  const [editRegUnitId, setEditRegUnitId] = useState('');
  const [editRegRelationship, setEditRegRelationship] = useState('proprietario_residente');
  const [editRegNotes, setEditRegNotes] = useState('');

  // 3. Modal Excluir Pré-cadastro
  const [isDeleteRegOpen, setIsDeleteRegOpen] = useState(false);

  // 4. Modal Editar Vínculo (Membership)
  const [isEditMembershipOpen, setIsEditMembershipOpen] = useState(false);
  const [selectedMembership, setSelectedMembership] = useState<any | null>(null);
  const [editMemName, setEditMemName] = useState('');
  const [editMemPhone, setEditMemPhone] = useState('');
  const [editMemCategory, setEditMemCategory] = useState('proprietario_residente');
  const [editMemStatus, setEditMemStatus] = useState('active');

  // 5. Modal Validação Documental de Vínculo (CA-12, CA-15)
  const [isVerifyModalOpen, setIsVerifyModalOpen] = useState(false);
  const [verifyStatus, setVerifyStatus] = useState('validado');
  const [verifyMethod, setVerifyMethod] = useState('declaracao_sindico');
  const [verifyReason, setVerifyReason] = useState('');

  // 6. Modais Revogação e Saneamento de Vínculo
  const [isDeleteMembershipOpen, setIsDeleteMembershipOpen] = useState(false);
  const [isPurgeMembershipOpen, setIsPurgeMembershipOpen] = useState(false);

  // Carga paralela de memberships, registrations e units
  const fetchData = async () => {
    if (!activeCondominiumId) return;
    setIsLoading(true);
    setError('');
    try {
      const [resM, resR, resU] = await Promise.all([
        api.get<any[]>(`/condominiums/${activeCondominiumId}/memberships`),
        api.get<any[]>(`/condominiums/${activeCondominiumId}/registrations`),
        api.get<any[]>(`/condominiums/${activeCondominiumId}/units`),
      ]);
      setMemberships(resM.data || []);
      setRegistrations(resR.data || []);
      setUnits(resU.data || []);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar dados de moradores.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeCondominiumId]);

  // Mapa de unidades para busca rápida por id
  const unitsMap = useMemo(() => {
    const map = new Map<string, any>();
    units.forEach((u) => map.set(u.id, u));
    return map;
  }, [units]);

  // Lista unificada consolidando Pré-cadastros e Vínculos
  const unifiedList = useMemo<UnifiedResidentItem[]>(() => {
    const linkedMembershipIds = new Set(
      memberships.map((m) => m.id).filter(Boolean)
    );

    // 1. Pré-cadastros (ResidentRegistration)
    const regItems: UnifiedResidentItem[] = registrations
      .filter((r) => !r.linked_membership_id || !linkedMembershipIds.has(r.linked_membership_id))
      .map((r) => {
        const u = unitsMap.get(r.unit_id);
        const code = r.unit_code || (u ? u.code || u.unit_number : '—');
        return {
          id: r.id,
          itemType: 'registration',
          name: r.full_name || 'Morador sem nome',
          unitCode: code,
          unitId: r.unit_id,
          phone: r.phone_e164,
          email: r.email,
          category: r.relationship || 'proprietario_residente',
          verificationStatus: 'pendente',
          membershipStatus: 'pre_cadastro',
          source: (r.source === 'import' ? 'import' : 'manual'),
          notes: r.notes,
          createdAt: r.created_at,
          raw: r,
        };
      });

    // 2. Vínculos efetivos (UnitMembership)
    const memItems: UnifiedResidentItem[] = memberships.map((m) => {
      const u = unitsMap.get(m.unit_id);
      const code = m.unit_code || (u ? u.code || u.unit_number : '—');
      return {
        id: m.id,
        itemType: 'membership',
        name: m.resident_name || 'Morador',
        unitCode: code,
        unitId: m.unit_id,
        phone: m.phone_e164,
        email: m.email,
        category: m.category || 'proprietario_residente',
        verificationStatus: m.verification_status || 'pendente',
        membershipStatus: m.membership_status || 'active',
        source: 'vinculado',
        notes: null,
        createdAt: m.created_at,
        raw: m,
      };
    });

    return [...regItems, ...memItems];
  }, [registrations, memberships, unitsMap]);

  // Filtragem reativa por aba e por texto
  const filtered = useMemo(() => {
    return unifiedList.filter((item) => {
      let matchesTab = true;
      if (activeTab === 'pre_cadastros') {
        matchesTab = item.itemType === 'registration';
      } else if (activeTab === 'validados') {
        matchesTab = item.itemType === 'membership' && item.verificationStatus === 'validado';
      } else if (activeTab === 'pendentes') {
        matchesTab =
          item.itemType === 'registration' ||
          item.verificationStatus === 'pendente' ||
          item.verificationStatus === 'em_analise';
      }

      const q = search.trim().toLowerCase();
      const matchesSearch =
        !q ||
        item.name.toLowerCase().includes(q) ||
        item.unitCode.toLowerCase().includes(q) ||
        (item.phone && item.phone.toLowerCase().includes(q)) ||
        (item.email && item.email.toLowerCase().includes(q));

      return matchesTab && matchesSearch;
    });
  }, [unifiedList, activeTab, search]);

  // Contagens para os badges das abas
  const preCadastrosCount = useMemo(
    () => unifiedList.filter((i) => i.itemType === 'registration').length,
    [unifiedList]
  );
  const validadosCount = useMemo(
    () => unifiedList.filter((i) => i.itemType === 'membership' && i.verificationStatus === 'validado').length,
    [unifiedList]
  );
  const pendentesCount = useMemo(
    () =>
      unifiedList.filter(
        (i) =>
          i.itemType === 'registration' ||
          i.verificationStatus === 'pendente' ||
          i.verificationStatus === 'em_analise'
      ).length,
    [unifiedList]
  );

  const tabItems = [
    { key: 'todos', label: 'Todos', badge: unifiedList.length },
    { key: 'pre_cadastros', label: 'Pré-cadastros', badge: preCadastrosCount },
    { key: 'validados', label: 'Validados', badge: validadosCount },
    { key: 'pendentes', label: 'Pendentes', badge: pendentesCount },
  ];

  // ==========================================
  // HANDLERS: Pré-cadastro Manual (CA-02)
  // ==========================================

  const handleCreatePreRegistration = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !newUnitId) return;

    setIsSubmitting(true);
    try {
      await api.post(`/condominiums/${activeCondominiumId}/registrations`, {
        unit_id: newUnitId,
        full_name: newFullName.trim(),
        phone_e164: newPhone.trim() || null,
        email: newEmail.trim() || null,
        relationship: newRelationship,
        notes: newNotes.trim() || null,
      });

      setIsCreateModalOpen(false);
      setNewFullName('');
      setNewPhone('');
      setNewEmail('');
      setNewUnitId('');
      setNewRelationship('proprietario_residente');
      setNewNotes('');

      toast.success('Pré-cadastro de morador realizado com sucesso! O morador já está listado na tabela.');
      await fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao criar pré-cadastro de morador.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenEditReg = (rawReg: any) => {
    setSelectedReg(rawReg);
    setEditRegFullName(rawReg.full_name || '');
    setEditRegPhone(rawReg.phone_e164 || '');
    setEditRegEmail(rawReg.email || '');
    setEditRegUnitId(rawReg.unit_id || '');
    setEditRegRelationship(rawReg.relationship || 'proprietario_residente');
    setEditRegNotes(rawReg.notes || '');
    setIsEditRegOpen(true);
  };

  const handleUpdatePreRegistration = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !selectedReg) return;

    setIsSubmitting(true);
    try {
      await api.patch(
        `/condominiums/${activeCondominiumId}/registrations/${selectedReg.id}`,
        {
          full_name: editRegFullName.trim(),
          phone_e164: editRegPhone.trim() || null,
          email: editRegEmail.trim() || null,
          unit_id: editRegUnitId || undefined,
          relationship: editRegRelationship,
          notes: editRegNotes.trim() || null,
        }
      );

      toast.success('Pré-cadastro de morador atualizado com sucesso!');
      setIsEditRegOpen(false);
      await fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao atualizar pré-cadastro.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenDeleteReg = (rawReg: any) => {
    setSelectedReg(rawReg);
    setIsDeleteRegOpen(true);
  };

  const handleDeletePreRegistration = async () => {
    if (!activeCondominiumId || !selectedReg) return;

    setIsSubmitting(true);
    try {
      await api.delete(
        `/condominiums/${activeCondominiumId}/registrations/${selectedReg.id}`
      );
      toast.success(`Pré-cadastro de "${selectedReg.full_name}" removido com sucesso.`);
      setIsDeleteRegOpen(false);
      await fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao excluir pré-cadastro.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // ==========================================
  // HANDLERS: Vínculos com Conta (Membership)
  // ==========================================

  const handleOpenEditMembership = (m: any) => {
    setSelectedMembership(m);
    setEditMemName(m.resident_name || '');
    setEditMemPhone(m.phone_e164 || '');
    setEditMemCategory(m.category || 'proprietario_residente');
    setEditMemStatus(m.membership_status || 'active');
    setIsEditMembershipOpen(true);
  };

  const handleUpdateMembership = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !selectedMembership) return;

    setIsSubmitting(true);
    try {
      await api.patch(
        `/condominiums/${activeCondominiumId}/memberships/${selectedMembership.id}`,
        {
          resident_name: editMemName.trim(),
          phone_e164: editMemPhone.trim() || null,
          category: editMemCategory,
          membership_status: editMemStatus,
        }
      );
      toast.success('Cadastro do condômino atualizado com sucesso!');
      setIsEditMembershipOpen(false);
      await fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao atualizar dados do condômino.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleArchiveMembership = async (m: any) => {
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
      await fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao alterar situação do condômino.');
    }
  };

  const handleOpenVerifyModal = (m: any) => {
    setSelectedMembership(m);
    setVerifyStatus('validado');
    setVerifyMethod('declaracao_sindico');
    setVerifyReason('');
    setIsVerifyModalOpen(true);
  };

  const handleVerifyMembership = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !selectedMembership) return;
    if (verifyReason.trim().length < 5) {
      toast.error('O motivo da validação deve conter no mínimo 5 caracteres para fins de auditoria.');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post(
        `/condominiums/${activeCondominiumId}/memberships/${selectedMembership.id}/verify`,
        {
          new_status: verifyStatus,
          method: verifyMethod,
          reason: verifyReason.trim(),
        }
      );
      toast.success(`Validação documental registrada com sucesso (CA-12, CA-15)!`);
      setIsVerifyModalOpen(false);
      await fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao registrar validação de residência.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenDeleteMembership = (m: any) => {
    setSelectedMembership(m);
    setIsDeleteMembershipOpen(true);
  };

  const handleDeleteMembership = async () => {
    if (!activeCondominiumId || !selectedMembership) return;

    setIsSubmitting(true);
    try {
      await api.delete(`/condominiums/${activeCondominiumId}/memberships/${selectedMembership.id}`);
      toast.success(`Vínculo de "${selectedMembership.resident_name}" revogado com sucesso.`);
      setIsDeleteMembershipOpen(false);
      await fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao revogar vínculo do morador.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenPurge = (m: any) => {
    setSelectedMembership(m);
    setIsPurgeMembershipOpen(true);
  };

  const handlePurgeConfirm = async () => {
    if (!activeCondominiumId || !selectedMembership) return;

    setIsSubmitting(true);
    try {
      await api.delete(`/condominiums/${activeCondominiumId}/memberships/${selectedMembership.id}?permanent=true`);
      toast.success(`Vínculo de "${selectedMembership.resident_name}" excluído definitivamente no saneamento.`);
      setIsPurgeMembershipOpen(false);
      await fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao excluir definitivamente o vínculo do morador.');
    } finally {
      setIsSubmitting(false);
    }
  };

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
            Gestão integrada de pré-cadastros, convites e validações auditadas de residência (CA-02, CA-12, CA-13, CA-14).
          </p>
        </div>
        <Button size="sm" onClick={() => setIsCreateModalOpen(true)}>
          <UserPlus className="w-4 h-4 mr-1.5" aria-hidden="true" />
          <span>Novo Pré-cadastro</span>
        </Button>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      <Card>
        <CardHeader className="p-4 sm:p-6 pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            {/* Abas com contagem dinâmica */}
            <Tabs
              items={tabItems}
              activeKey={activeTab}
              onChange={(k) => setActiveTab(k as any)}
              size="sm"
            />

            {/* Busca textual */}
            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                className="w-full text-xs border border-slate-200 rounded-lg pl-9 pr-3 py-2 outline-none focus:ring-1 focus:ring-brand-500"
                placeholder="Buscar por nome, unidade, telefone..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <TableSkeleton rows={5} />
          ) : filtered.length === 0 ? (
            <div className="p-6">
              <EmptyState
                icon={Users}
                title={
                  search
                    ? 'Nenhum resultado encontrado'
                    : activeTab === 'pre_cadastros'
                    ? 'Nenhum pré-cadastro pendente'
                    : 'Nenhum morador cadastrado'
                }
                description={
                  search
                    ? 'Nenhum morador ou pré-cadastro corresponde à sua busca.'
                    : activeTab === 'pre_cadastros'
                    ? 'Todos os moradores já foram convidados ou vinculados.'
                    : 'Cadastre um novo morador manualmente ou importe uma planilha cadastral.'
                }
                actionLabel={search ? undefined : 'Novo Pré-cadastro'}
                onAction={search ? undefined : () => setIsCreateModalOpen(true)}
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
                    <th className="px-6 py-3">Tipo de Registro</th>
                    <th className="px-6 py-3">Verificação</th>
                    <th className="px-6 py-3">Situação</th>
                    <th className="px-6 py-3 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filtered.map((item) => {
                    const isArchived =
                      item.membershipStatus === 'ended' || item.membershipStatus === 'inactive';
                    const isPreCadastro = item.itemType === 'registration';

                    return (
                      <tr
                        key={`${item.itemType}-${item.id}`}
                        className={`hover:bg-slate-50/50 transition-colors ${
                          isArchived ? 'opacity-70 bg-slate-50/40' : ''
                        }`}
                      >
                        {/* 1. Nome e Contato */}
                        <td className="px-6 py-3.5">
                          <span className="font-semibold text-slate-900 text-sm block">
                            {item.name}
                          </span>
                          <div className="flex flex-wrap items-center gap-3 mt-0.5">
                            {item.phone && (
                              <span className="text-[11px] text-slate-500 flex items-center gap-1">
                                <Phone className="w-3 h-3 text-slate-400" />
                                {item.phone}
                              </span>
                            )}
                            {item.email && (
                              <span className="text-[11px] text-slate-500 flex items-center gap-1">
                                <Mail className="w-3 h-3 text-slate-400" />
                                {item.email}
                              </span>
                            )}
                          </div>
                        </td>

                        {/* 2. Unidade */}
                        <td className="px-6 py-3.5">
                          <span className="font-mono font-semibold text-slate-800 bg-slate-100 px-2.5 py-1 rounded border border-slate-200 inline-block">
                            {item.unitCode}
                          </span>
                        </td>

                        {/* 3. Categoria / Relação */}
                        <td className="px-6 py-3.5 text-slate-600 capitalize">
                          {item.category.replace(/_/g, ' ')}
                        </td>

                        {/* 4. Tipo de Registro */}
                        <td className="px-6 py-3.5">
                          {isPreCadastro ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-sky-700 bg-sky-50 px-2 py-0.5 rounded-full border border-sky-200">
                              <Sparkles className="w-3 h-3 text-sky-500" />
                              Pré-cadastro ({item.source === 'import' ? 'Planilha' : 'Manual'})
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                              <UserCheck className="w-3 h-3 text-emerald-600" />
                              Conta com Vínculo
                            </span>
                          )}
                        </td>

                        {/* 5. Status de Verificação */}
                        <td className="px-6 py-3.5">
                          {isPreCadastro ? (
                            <Badge variant="warning">
                              Aguardando Convite
                            </Badge>
                          ) : (
                            <Badge
                              variant={
                                item.verificationStatus === 'validado'
                                  ? 'success'
                                  : item.verificationStatus === 'pendente'
                                  ? 'warning'
                                  : item.verificationStatus === 'em_analise'
                                  ? 'default'
                                  : 'danger'
                              }
                            >
                              {item.verificationStatus === 'validado'
                                ? 'Validado'
                                : item.verificationStatus === 'em_analise'
                                ? 'Em Análise'
                                : item.verificationStatus === 'pendente'
                                ? 'Pendente'
                                : item.verificationStatus === 'recusado'
                                ? 'Recusado'
                                : 'Revogado'}
                            </Badge>
                          )}
                        </td>

                        {/* 6. Situação Geral */}
                        <td className="px-6 py-3.5">
                          {isArchived ? (
                            <span className="inline-flex items-center text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                              Desativado
                            </span>
                          ) : isPreCadastro ? (
                            <span className="inline-flex items-center text-[11px] font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                              Pré-cadastro
                            </span>
                          ) : (
                            <span className="inline-flex items-center text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
                              Ativo
                            </span>
                          )}
                        </td>

                        {/* 7. Ações */}
                        <td className="px-6 py-3.5 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {isPreCadastro ? (
                              <>
                                {/* Editar Pré-cadastro */}
                                <button
                                  onClick={() => handleOpenEditReg(item.raw)}
                                  className="p-1.5 text-slate-500 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors"
                                  title="Editar pré-cadastro"
                                  aria-label="Editar pré-cadastro"
                                >
                                  <Edit2 className="w-4 h-4" />
                                </button>

                                {/* Excluir Pré-cadastro */}
                                <button
                                  onClick={() => handleOpenDeleteReg(item.raw)}
                                  className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-slate-100 rounded-lg transition-colors"
                                  title="Excluir pré-cadastro"
                                  aria-label="Excluir pré-cadastro"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </>
                            ) : (
                              <>
                                {/* Validar Documentalmente Vínculo se pendente */}
                                {item.verificationStatus !== 'validado' && (
                                  <button
                                    onClick={() => handleOpenVerifyModal(item.raw)}
                                    className="p-1.5 text-emerald-600 hover:text-emerald-800 hover:bg-emerald-50 rounded-lg transition-colors"
                                    title="Validar residência documental (CA-12, CA-15)"
                                    aria-label="Validar residência documental"
                                  >
                                    <ShieldCheck className="w-4 h-4" />
                                  </button>
                                )}

                                {/* Editar Vínculo */}
                                <button
                                  onClick={() => handleOpenEditMembership(item.raw)}
                                  className="p-1.5 text-slate-500 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors"
                                  title="Editar condômino"
                                  aria-label="Editar condômino"
                                >
                                  <Edit2 className="w-4 h-4" />
                                </button>

                                {/* Arquivar / Reativar */}
                                <button
                                  onClick={() => handleToggleArchiveMembership(item.raw)}
                                  className="p-1.5 text-slate-500 hover:text-amber-600 hover:bg-slate-100 rounded-lg transition-colors"
                                  title={isArchived ? 'Reativar condômino' : 'Arquivar/Desativar condômino'}
                                  aria-label={isArchived ? 'Reativar condômino' : 'Arquivar/Desativar condômino'}
                                >
                                  {isArchived ? <RotateCcw className="w-4 h-4" /> : <Archive className="w-4 h-4" />}
                                </button>

                                {/* Revogar / Saneamento Definitivo */}
                                {isArchived ? (
                                  <button
                                    onClick={() => handleOpenPurge(item.raw)}
                                    className="p-1.5 text-rose-500 hover:text-rose-700 hover:bg-rose-50 rounded-lg transition-colors"
                                    title="Saneamento / Excluir Definitivamente"
                                    aria-label="Saneamento / Excluir Definitivamente"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                ) : (
                                  <button
                                    onClick={() => handleOpenDeleteMembership(item.raw)}
                                    className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-slate-100 rounded-lg transition-colors"
                                    title="Revogar / Encerrar vínculo"
                                    aria-label="Revogar / Encerrar vínculo"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                )}
                              </>
                            )}
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

      {/* ======================================================== */}
      {/* MODAL 1: Novo Pré-cadastro Manual (CA-02)               */}
      {/* ======================================================== */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Novo Pré-cadastro de Morador"
        description="Registra os dados cadastrais da unidade sem emitir credenciais automáticas (CA-02)."
      >
        <form onSubmit={handleCreatePreRegistration} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Unidade Autônoma *
            </label>
            <select
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={newUnitId}
              onChange={(e) => setNewUnitId(e.target.value)}
            >
              <option value="">Selecione a unidade...</option>
              {units.map((u) => (
                <option key={u.id} value={u.id}>
                  Unidade {u.code || u.unit_number} {u.block ? `(${u.block})` : ''}
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
              value={newFullName}
              onChange={(e) => setNewFullName(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Telefone (com DDD)
              </label>
              <input
                type="text"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="(11) 98888-7777"
                value={newPhone}
                onChange={(e) => setNewPhone(e.target.value)}
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
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Relação com a Unidade *
            </label>
            <select
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={newRelationship}
              onChange={(e) => setNewRelationship(e.target.value)}
            >
              <option value="proprietario_residente">Proprietário Residente</option>
              <option value="proprietario_nao_residente">Proprietário Não Residente</option>
              <option value="inquilino">Inquilino / Locatário</option>
              <option value="dependente">Dependente Familiar</option>
              <option value="procurador">Procurador / Representante</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Observações Internas (Opcional)
            </label>
            <textarea
              rows={2}
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Anotações para a administração do condomínio..."
              value={newNotes}
              onChange={(e) => setNewNotes(e.target.value)}
            />
          </div>

          <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <span>
              <strong>Garantia de Não-Emissão Automática:</strong> O pré-cadastro não gera login nem convida o
              morador imediatamente. O convite é emitido em etapa separada pelo assistente de convites.
            </span>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsCreateModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Salvando...' : 'Salvar Pré-cadastro'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* ======================================================== */}
      {/* MODAL 2: Editar Pré-cadastro                             */}
      {/* ======================================================== */}
      <Modal
        isOpen={isEditRegOpen}
        onClose={() => setIsEditRegOpen(false)}
        title="Editar Pré-cadastro de Morador"
        description="Atualize as informações cadastrais antes da emissão de convite."
      >
        <form onSubmit={handleUpdatePreRegistration} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Unidade Autônoma *
            </label>
            <select
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={editRegUnitId}
              onChange={(e) => setEditRegUnitId(e.target.value)}
            >
              <option value="">Selecione a unidade...</option>
              {units.map((u) => (
                <option key={u.id} value={u.id}>
                  Unidade {u.code || u.unit_number} {u.block ? `(${u.block})` : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Nome do Morador *
            </label>
            <input
              type="text"
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={editRegFullName}
              onChange={(e) => setEditRegFullName(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Telefone
              </label>
              <input
                type="text"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="(11) 98888-7777"
                value={editRegPhone}
                onChange={(e) => setEditRegPhone(e.target.value)}
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
                value={editRegEmail}
                onChange={(e) => setEditRegEmail(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Relação com a Unidade *
            </label>
            <select
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={editRegRelationship}
              onChange={(e) => setEditRegRelationship(e.target.value)}
            >
              <option value="proprietario_residente">Proprietário Residente</option>
              <option value="proprietario_nao_residente">Proprietário Não Residente</option>
              <option value="inquilino">Inquilino / Locatário</option>
              <option value="dependente">Dependente Familiar</option>
              <option value="procurador">Procurador / Representante</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Observações Internas
            </label>
            <textarea
              rows={2}
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={editRegNotes}
              onChange={(e) => setEditRegNotes(e.target.value)}
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsEditRegOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Salvando...' : 'Salvar Alterações'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* ======================================================== */}
      {/* MODAL 3: Excluir Pré-cadastro                            */}
      {/* ======================================================== */}
      <Modal
        isOpen={isDeleteRegOpen}
        onClose={() => setIsDeleteRegOpen(false)}
        title="Excluir Pré-cadastro de Morador"
      >
        <div className="space-y-4">
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="text-xs text-rose-900">
              <p className="font-semibold text-rose-950">Confirmar exclusão de pré-cadastro:</p>
              <p className="mt-1">
                Deseja remover o pré-cadastro de <strong>"{selectedReg?.full_name}"</strong> da unidade{' '}
                <strong>"{selectedReg?.unit_code || unitsMap.get(selectedReg?.unit_id)?.code || '—'}"</strong>?
              </p>
              <p className="mt-1 text-slate-600">
                Esta ação remove o registro prévio não convidado da base cadastral.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsDeleteRegOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              disabled={isSubmitting}
              onClick={handleDeletePreRegistration}
            >
              {isSubmitting ? 'Excluindo...' : 'Excluir Pré-cadastro'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* ======================================================== */}
      {/* MODAL 4: Editar Vínculo com Conta                        */}
      {/* ======================================================== */}
      <Modal
        isOpen={isEditMembershipOpen}
        onClose={() => setIsEditMembershipOpen(false)}
        title="Editar Dados do Condômino"
        description="Atualize as informações cadastrais e relação de vínculo do morador com a unidade."
      >
        <form onSubmit={handleUpdateMembership} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Nome do Morador *
            </label>
            <input
              type="text"
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={editMemName}
              onChange={(e) => setEditMemName(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Telefone
              </label>
              <input
                type="text"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="(11) 98888-7777"
                value={editMemPhone}
                onChange={(e) => setEditMemPhone(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Situação do Vínculo
              </label>
              <select
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                value={editMemStatus}
                onChange={(e) => setEditMemStatus(e.target.value)}
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
              value={editMemCategory}
              onChange={(e) => setEditMemCategory(e.target.value)}
            >
              <option value="proprietario_residente">Proprietário Residente</option>
              <option value="proprietario_nao_residente">Proprietário Não Residente</option>
              <option value="inquilino">Inquilino / Locatário</option>
              <option value="dependente">Dependente Familiar</option>
              <option value="procurador">Procurador / Representante</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsEditMembershipOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Salvando...' : 'Salvar Alterações'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* ======================================================== */}
      {/* MODAL 5: Validação Documental de Residência (CA-12, CA-15)*/}
      {/* ======================================================== */}
      <Modal
        isOpen={isVerifyModalOpen}
        onClose={() => setIsVerifyModalOpen(false)}
        title="Validar Residência e Titularidade"
        description="Registro auditado de conferência de vínculo conforme diretrizes CA-12 e CA-15."
      >
        <form onSubmit={handleVerifyMembership} className="space-y-4">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700">
            <p>
              Condômino: <strong>{selectedMembership?.resident_name}</strong>
            </p>
            <p className="mt-0.5">
              Unidade:{' '}
              <strong>
                {selectedMembership?.unit_code ||
                  unitsMap.get(selectedMembership?.unit_id)?.code ||
                  '—'}
              </strong>
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Novo Status de Verificação *
              </label>
              <select
                required
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                value={verifyStatus}
                onChange={(e) => setVerifyStatus(e.target.value)}
              >
                <option value="validado">Validado (Confirmado)</option>
                <option value="em_analise">Em Análise</option>
                <option value="recusado">Recusado</option>
                <option value="revogado">Revogado</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Método de Conferência *
              </label>
              <select
                required
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                value={verifyMethod}
                onChange={(e) => setVerifyMethod(e.target.value)}
              >
                <option value="documento">Documento Comprobatório</option>
                <option value="declaracao_sindico">Declaração do Síndico</option>
                <option value="presencial">Conferência Presencial</option>
                <option value="cadastro_legado">Cadastro Legado da Administração</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Motivo / Justificativa Auditada *
            </label>
            <textarea
              required
              rows={3}
              minLength={5}
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Ex: Escritura apresentada na administração e conferida com certidão de ônus."
              value={verifyReason}
              onChange={(e) => setVerifyReason(e.target.value)}
            />
            <p className="text-[11px] text-slate-400 mt-1">
              Mínimo de 5 caracteres. Registrado de forma imutável na trilha de auditoria.
            </p>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsVerifyModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Registrando...' : 'Confirmar Validação'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* ======================================================== */}
      {/* MODAL 6: Revogar Vínculo do Morador                      */}
      {/* ======================================================== */}
      <Modal
        isOpen={isDeleteMembershipOpen}
        onClose={() => setIsDeleteMembershipOpen(false)}
        title="Revogar Vínculo do Morador"
      >
        <div className="space-y-4">
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="text-xs text-rose-900">
              <p className="font-semibold text-rose-950">Atenção ao revogar este vínculo:</p>
              <p className="mt-1">
                Você está prestes a revogar o vínculo de <strong>{selectedMembership?.resident_name}</strong> com a
                unidade{' '}
                <strong>
                  {selectedMembership?.unit_code ||
                    unitsMap.get(selectedMembership?.unit_id)?.code ||
                    '—'}
                </strong>.
              </p>
              <p className="mt-1 text-slate-600">
                O histórico auditado será preservado (CA-12, CA-15), mas o morador perderá os acessos vinculados a esta unidade.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsDeleteMembershipOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              disabled={isSubmitting}
              onClick={handleDeleteMembership}
            >
              {isSubmitting ? 'Revogando...' : 'Confirmar Revogação'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* ======================================================== */}
      {/* MODAL 7: Saneamento Definitivo de Vínculo                */}
      {/* ======================================================== */}
      <Modal
        isOpen={isPurgeMembershipOpen}
        onClose={() => setIsPurgeMembershipOpen(false)}
        title="Saneamento Definitivo de Vínculo"
      >
        <div className="space-y-4">
          <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-3 text-rose-900 text-xs">
            <AlertTriangle className="w-5 h-5 shrink-0 text-rose-600 mt-0.5" />
            <div>
              <p className="font-bold uppercase tracking-wider text-rose-700">Ação Irreversível de Saneamento</p>
              <p className="mt-1 leading-relaxed">
                O vínculo de <strong>"{selectedMembership?.resident_name}"</strong> com a unidade{' '}
                <strong>
                  "{selectedMembership?.unit_code ||
                    unitsMap.get(selectedMembership?.unit_id)?.code ||
                    '—'}"
                </strong>{' '}
                já está inativo/revogado e será <strong>removido definitivamente</strong> da base de dados.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsPurgeMembershipOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              disabled={isSubmitting}
              onClick={handlePurgeConfirm}
            >
              {isSubmitting ? 'Expurgando...' : 'Excluir Definitivamente'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
