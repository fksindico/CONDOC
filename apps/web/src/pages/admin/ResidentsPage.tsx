import React, { useState, useEffect, useMemo } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/lib/api';
import {
  Users,
  Search,
  Phone,
  Mail,
  Home,
  MessageSquare,
  Download,
  Plus,
  Edit2,
  Trash2,
  ExternalLink,
  Calendar,
  Building2,
  FileText,
  AlertTriangle,
  Clock,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { Modal } from '@/components/ui/Modal';
import { TableSkeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { Breadcrumb } from '@/components/ui/Breadcrumb';

interface ResidentItem {
  id: string;
  unit_id: string | null;
  unit_code: string;
  building_name: string;
  building_code: string;
  full_name: string;
  phone_e164: string | null;
  email: string | null;
  relationship: string;
  source: string;
  status: string;
  notes: string | null;
  suggestions_count: number;
  last_suggestion_date: string | null;
  created_at: string;
  updated_at: string;
}

interface SuggestionItem {
  id: string;
  protocol: string;
  target_reference: string;
  action_type: 'alterar' | 'remover' | 'incluir';
  suggestion_text: string;
  justification?: string;
  status: string;
  created_at: string;
  consultation_title?: string;
}

export const ResidentsPage: React.FC = () => {
  const { activeCondominium, activeCondominiumId } = useTenant();
  const { toast } = useToast();

  const [residents, setResidents] = useState<ResidentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  // 1. Modal Novo Morador Manual
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newPhone, setNewPhone] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newTower, setNewTower] = useState('');
  const [newUnit, setNewUnit] = useState('');
  const [newNotes, setNewNotes] = useState('');
  const [isSubmittingCreate, setIsSubmittingCreate] = useState(false);

  // 2. Modal Editar Morador
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editingResident, setEditingResident] = useState<ResidentItem | null>(null);
  const [editName, setEditName] = useState('');
  const [editPhone, setEditPhone] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editNotes, setEditNotes] = useState('');
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false);

  // 3. Modal Excluir Morador
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [deletingResident, setDeletingResident] = useState<ResidentItem | null>(null);
  const [isSubmittingDelete, setIsSubmittingDelete] = useState(false);

  // 4. Modal Ver Sugestões do Morador
  const [isSuggestionsOpen, setIsSuggestionsOpen] = useState(false);
  const [selectedResidentForSugs, setSelectedResidentForSugs] = useState<ResidentItem | null>(null);
  const [residentSuggestions, setResidentSuggestions] = useState<SuggestionItem[]>([]);
  const [isLoadingSugs, setIsLoadingSugs] = useState(false);

  const fetchResidents = async () => {
    if (!activeCondominiumId) return;
    setIsLoading(true);
    setError('');
    try {
      const res = await api.get<ResidentItem[]>(`/condominiums/${activeCondominiumId}/registrations`);
      setResidents(res.data || []);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar lista de moradores.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchResidents();
  }, [activeCondominiumId]);

  // Filtro reativo por texto
  const filteredResidents = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return residents;
    return residents.filter((r) => {
      const nameMatch = r.full_name?.toLowerCase().includes(q);
      const unitMatch = r.unit_code?.toLowerCase().includes(q);
      const towerMatch = r.building_name?.toLowerCase().includes(q);
      const phoneMatch = r.phone_e164?.includes(q);
      const emailMatch = r.email?.toLowerCase().includes(q);
      return nameMatch || unitMatch || towerMatch || phoneMatch || emailMatch;
    });
  }, [residents, search]);

  // Contagens para os cards de destaque
  const totalMoradores = residents.length;
  const unidadesUnicas = useMemo(() => {
    const units = new Set(residents.map((r) => r.unit_code).filter((u) => u && u !== '—'));
    return units.size;
  }, [residents]);
  const totalSugestoes = useMemo(() => {
    return residents.reduce((acc, r) => acc + (r.suggestions_count || 0), 0);
  }, [residents]);

  // ==========================================
  // HANDLERS
  // ==========================================

  const handleOpenCreate = () => {
    setNewName('');
    setNewPhone('');
    setNewEmail('');
    setNewTower('');
    setNewUnit('');
    setNewNotes('');
    setIsCreateOpen(true);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId) return;
    if (!newName.trim() || !newUnit.trim()) {
      toast.error('Informe ao menos o nome do morador e o número da unidade.');
      return;
    }

    setIsSubmittingCreate(true);
    try {
      await api.post(`/condominiums/${activeCondominiumId}/registrations`, {
        full_name: newName.trim(),
        phone_e164: newPhone.replace(/\D/g, '') || null,
        email: newEmail.trim().toLowerCase() || null,
        block_tower: newTower.trim() || null,
        unit_code: newUnit.trim(),
        relationship: 'proprietario_residente',
        notes: newNotes.trim() || null,
      });
      toast.success('Morador registrado com sucesso!');
      setIsCreateOpen(false);
      fetchResidents();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao registrar morador.');
    } finally {
      setIsSubmittingCreate(false);
    }
  };

  const handleOpenEdit = (res: ResidentItem) => {
    setEditingResident(res);
    setEditName(res.full_name || '');
    setEditPhone(res.phone_e164 || '');
    setEditEmail(res.email || '');
    setEditNotes(res.notes || '');
    setIsEditOpen(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !editingResident) return;

    setIsSubmittingEdit(true);
    try {
      await api.patch(`/condominiums/${activeCondominiumId}/registrations/${editingResident.id}`, {
        full_name: editName.trim(),
        phone_e164: editPhone.replace(/\D/g, '') || null,
        email: editEmail.trim().toLowerCase() || null,
        notes: editNotes.trim() || null,
      });
      toast.success('Dados do morador atualizados com sucesso!');
      setIsEditOpen(false);
      fetchResidents();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao atualizar dados do morador.');
    } finally {
      setIsSubmittingEdit(false);
    }
  };

  const handleOpenDelete = (res: ResidentItem) => {
    setDeletingResident(res);
    setIsDeleteOpen(true);
  };

  const handleDeleteSubmit = async () => {
    if (!activeCondominiumId || !deletingResident) return;
    setIsSubmittingDelete(true);
    try {
      await api.delete(`/condominiums/${activeCondominiumId}/registrations/${deletingResident.id}`);
      toast.success('Morador removido do cadastro com sucesso.');
      setIsDeleteOpen(false);
      fetchResidents();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao remover morador.');
    } finally {
      setIsSubmittingDelete(false);
    }
  };

  const handleOpenSuggestions = async (res: ResidentItem) => {
    setSelectedResidentForSugs(res);
    setIsSuggestionsOpen(true);
    setIsLoadingSugs(true);
    try {
      const response = await api.get<SuggestionItem[]>(
        `/condominiums/${activeCondominiumId}/registrations/${res.id}/suggestions`
      );
      setResidentSuggestions(response.data || []);
    } catch {
      setResidentSuggestions([]);
    } finally {
      setIsLoadingSugs(false);
    }
  };

  // Abre conversa no WhatsApp direto com o morador
  const handleOpenWhatsApp = (resident: ResidentItem) => {
    if (!resident.phone_e164) {
      toast.error('Este morador não possui celular cadastrado.');
      return;
    }
    const cleanPhone = resident.phone_e164.replace(/\D/g, '');
    const fullPhone = cleanPhone.startsWith('55') ? cleanPhone : `55${cleanPhone}`;
    const condoName = activeCondominium?.name || 'nosso condomínio';
    const text = encodeURIComponent(
      `Olá ${resident.full_name}, sou o síndico do ${condoName}. Estou entrando em contato sobre a sua participação na revisão dos documentos condominiais.`
    );
    window.open(`https://wa.me/${fullPhone}?text=${text}`, '_blank');
  };

  // Exporta a lista de moradores para CSV formatado com BOM UTF-8 e ';'
  const handleExportCSV = () => {
    if (residents.length === 0) {
      toast.error('Nenhum morador registrado para exportar.');
      return;
    }

    const headers = ['Nome Completo', 'Torre/Bloco', 'Unidade', 'WhatsApp/Telefone', 'E-mail', 'Sugestões Enviadas', 'Data Cadastro'];
    const rows = residents.map((r) => [
      `"${r.full_name.replace(/"/g, '""')}"`,
      `"${(r.building_name || '').replace(/"/g, '""')}"`,
      `"${r.unit_code}"`,
      `"${r.phone_e164 || ''}"`,
      `"${r.email || ''}"`,
      r.suggestions_count || 0,
      r.created_at ? new Date(r.created_at).toLocaleDateString('pt-BR') : '',
    ]);

    const csvContent = '\uFEFF' + [headers.join(';'), ...rows.map((row) => row.join(';'))].join('\r\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `moradores_${activeCondominium?.name || 'condominio'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Lista de moradores exportada com sucesso!');
  };

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      <Breadcrumb
        items={[
          { label: 'Painel', href: '/painel' },
          { label: 'Cadastro de Moradores' },
        ]}
      />

      {/* Header do Módulo */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Users className="w-6 h-6 text-indigo-600" aria-hidden="true" />
            <span>Moradores Participantes</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            {activeCondominium?.name || 'Condomínio Selecionado'} — Cadastro unificado gerado automaticamente a cada sugestão enviada via link universal. Consulta exclusiva da gestão.
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportCSV}
            className="border-slate-300 text-slate-700 hover:bg-slate-50"
          >
            <Download className="w-4 h-4 mr-1.5 text-slate-600" aria-hidden="true" />
            <span>Exportar CSV</span>
          </Button>

          <Button
            size="sm"
            onClick={handleOpenCreate}
            className="bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            <Plus className="w-4 h-4 mr-1.5" aria-hidden="true" />
            <span>Novo Morador Manual</span>
          </Button>
        </div>
      </div>

      {/* Destaque Informativo: Ciclo Ágil Zero-Atrito */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-4 sm:p-5 text-white shadow-sm border border-indigo-800/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 uppercase tracking-wider inline-block">
            Cadastro Automático por Participação
          </span>
          <h2 className="text-sm sm:text-base font-bold text-white">
            Sem Pré-Cadastros Burocráticos ou Múltiplos Registros
          </h2>
          <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
            Quando os moradores acessam o link público compartilhado para sugerir alterações nos documentos, o sistema consolida seus contatos automaticamente. Múltiplos acessos pelo mesmo morador não duplicam cadastros.
          </p>
        </div>
        <div className="shrink-0 flex items-center gap-2">
          <Badge className="bg-indigo-600/30 text-indigo-200 border-indigo-500/40 px-3 py-1 text-xs">
            {totalMoradores} Morador{totalMoradores === 1 ? '' : 'es'} Único{totalMoradores === 1 ? '' : 's'}
          </Badge>
        </div>
      </div>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="animate-fade-in-up">
          <CardContent className="p-4 sm:p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Moradores Registrados</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{totalMoradores}</h3>
              <p className="text-xs text-slate-500 mt-1">Participantes identificados</p>
            </div>
            <div className="p-2.5 rounded-xl border border-indigo-200 bg-indigo-50 text-indigo-700">
              <Users className="w-5 h-5 text-current" aria-hidden="true" />
            </div>
          </CardContent>
        </Card>

        <Card className="animate-fade-in-up">
          <CardContent className="p-4 sm:p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Unidades com Participação</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{unidadesUnicas}</h3>
              <p className="text-xs text-slate-500 mt-1">Apartamentos representados</p>
            </div>
            <div className="p-2.5 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-800">
              <Home className="w-5 h-5 text-current" aria-hidden="true" />
            </div>
          </CardContent>
        </Card>

        <Card className="animate-fade-in-up">
          <CardContent className="p-4 sm:p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Sugestões Coletadas</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{totalSugestoes}</h3>
              <p className="text-xs text-slate-500 mt-1">Propostas normativas enviadas</p>
            </div>
            <div className="p-2.5 rounded-xl border border-amber-200 bg-amber-50 text-amber-700">
              <MessageSquare className="w-5 h-5 text-current" aria-hidden="true" />
            </div>
          </CardContent>
        </Card>
      </div>

      {error && (
        <Alert variant="error">
          <span>{error}</span>
        </Alert>
      )}

      {/* Barra de Filtro e Busca */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true" />
          <input
            type="text"
            placeholder="Buscar por nome, unidade, torre ou telefone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs sm:text-sm border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        {search && (
          <Button variant="ghost" size="sm" onClick={() => setSearch('')} className="text-xs text-slate-500">
            Limpar Busca
          </Button>
        )}
      </div>

      {/* Tabela de Moradores */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6">
              <TableSkeleton rows={4} />
            </div>
          ) : filteredResidents.length === 0 ? (
            <div className="py-12">
              <EmptyState
                icon={Users}
                title={search ? 'Nenhum morador encontrado' : 'Nenhum morador cadastrado ainda'}
                description={
                  search
                    ? 'Tente ajustar os termos da sua busca.'
                    : 'Assim que os moradores enviarem sugestões através do link da consulta pública, eles aparecerão aqui automaticamente.'
                }
                actionLabel={search ? 'Limpar filtro' : 'Cadastrar Manualmente'}
                onAction={search ? () => setSearch('') : handleOpenCreate}
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs sm:text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/75 text-slate-600 font-semibold text-[11px] uppercase tracking-wider">
                    <th className="py-3 px-4">Morador</th>
                    <th className="py-3 px-4">Unidade / Torre</th>
                    <th className="py-3 px-4">Contato (WhatsApp)</th>
                    <th className="py-3 px-4 text-center">Sugestões</th>
                    <th className="py-3 px-4">Última Atividade</th>
                    <th className="py-3 px-4 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredResidents.map((resident) => (
                    <tr key={resident.id} className="hover:bg-slate-50/60 transition-colors">
                      {/* Nome e Email */}
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900">{resident.full_name}</div>
                        {resident.email ? (
                          <div className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                            <Mail className="w-3 h-3 text-slate-400" />
                            <span>{resident.email}</span>
                          </div>
                        ) : (
                          <div className="text-[11px] text-slate-400 italic">E-mail não informado</div>
                        )}
                      </td>

                      {/* Unidade e Torre */}
                      <td className="py-3 px-4">
                        <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-slate-100 text-slate-800 font-medium text-xs">
                          <Home className="w-3 h-3 text-slate-500" />
                          <span>Unidade {resident.unit_code}</span>
                        </div>
                        {resident.building_name && resident.building_name !== '—' && (
                          <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
                            <Building2 className="w-3 h-3 text-slate-400" />
                            <span>{resident.building_name}</span>
                          </div>
                        )}
                      </td>

                      {/* WhatsApp / Celular */}
                      <td className="py-3 px-4">
                        {resident.phone_e164 ? (
                          <button
                            onClick={() => handleOpenWhatsApp(resident)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200 transition font-medium text-xs group"
                            title="Conversar com o morador no WhatsApp"
                          >
                            <Phone className="w-3.5 h-3.5 text-emerald-600 group-hover:scale-110 transition-transform" />
                            <span>{resident.phone_e164}</span>
                            <ExternalLink className="w-3 h-3 text-emerald-500 opacity-60" />
                          </button>
                        ) : (
                          <span className="text-xs text-slate-400 italic">Sem telefone</span>
                        )}
                      </td>

                      {/* Total de Sugestões */}
                      <td className="py-3 px-4 text-center">
                        {resident.suggestions_count > 0 ? (
                          <button
                            onClick={() => handleOpenSuggestions(resident)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 transition text-xs font-semibold"
                            title="Ver sugestões enviadas por este morador"
                          >
                            <MessageSquare className="w-3 h-3 text-indigo-600" />
                            <span>{resident.suggestions_count} envio{resident.suggestions_count === 1 ? '' : 's'}</span>
                          </button>
                        ) : (
                          <span className="text-xs text-slate-400">0 envios</span>
                        )}
                      </td>

                      {/* Última Atividade */}
                      <td className="py-3 px-4 text-xs text-slate-500">
                        {resident.last_suggestion_date ? (
                          <div className="flex items-center gap-1">
                            <Clock className="w-3 h-3 text-slate-400" />
                            <span>{new Date(resident.last_suggestion_date).toLocaleDateString('pt-BR')}</span>
                          </div>
                        ) : resident.created_at ? (
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-slate-400" />
                            <span>{new Date(resident.created_at).toLocaleDateString('pt-BR')}</span>
                          </div>
                        ) : (
                          '—'
                        )}
                      </td>

                      {/* Ações */}
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {resident.suggestions_count > 0 && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleOpenSuggestions(resident)}
                              className="h-8 px-2 text-indigo-700 hover:bg-indigo-50 text-xs"
                              title="Ver sugestões enviadas"
                            >
                              <FileText className="w-3.5 h-3.5 mr-1" />
                              <span className="hidden sm:inline">Sugestões</span>
                            </Button>
                          )}

                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleOpenEdit(resident)}
                            className="h-8 w-8 p-0 text-slate-600 hover:bg-slate-100"
                            title="Editar dados do morador"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </Button>

                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleOpenDelete(resident)}
                            className="h-8 w-8 p-0 text-rose-600 hover:bg-rose-50 hover:text-rose-700"
                            title="Excluir morador"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ======================================================== */}
      {/* 1. MODAL: NOVO MORADOR MANUAL                            */}
      {/* ======================================================== */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Novo Cadastro de Morador"
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <p className="text-xs text-slate-500">
            Cadastre manualmente um morador caso queira adiantar contatos antes do envio pelo link público universal.
          </p>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Nome Completo *</label>
            <input
              type="text"
              required
              placeholder="Ex: Fabiano Silva"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full px-3 py-2 text-xs sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">WhatsApp / Celular</label>
              <input
                type="text"
                placeholder="(27) 93500-9626"
                value={newPhone}
                onChange={(e) => setNewPhone(e.target.value)}
                className="w-full px-3 py-2 text-xs sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">E-mail (opcional)</label>
              <input
                type="email"
                placeholder="morador@email.com"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                className="w-full px-3 py-2 text-xs sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Torre / Bloco</label>
              <input
                type="text"
                placeholder="Ex: Torre VILLE"
                value={newTower}
                onChange={(e) => setNewTower(e.target.value)}
                className="w-full px-3 py-2 text-xs sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Unidade / Apto *</label>
              <input
                type="text"
                required
                placeholder="Ex: 1004"
                value={newUnit}
                onChange={(e) => setNewUnit(e.target.value)}
                className="w-full px-3 py-2 text-xs sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Observações Internas</label>
            <textarea
              rows={2}
              placeholder="Notas de consulta do síndico..."
              value={newNotes}
              onChange={(e) => setNewNotes(e.target.value)}
              className="w-full px-3 py-2 text-xs sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsCreateOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={isSubmittingCreate}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              {isSubmittingCreate ? 'Salvando...' : 'Salvar Cadastro'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* ======================================================== */}
      {/* 2. MODAL: EDITAR MORADOR                                 */}
      {/* ======================================================== */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Editar Dados do Morador"
      >
        <form onSubmit={handleEditSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Nome Completo</label>
            <input
              type="text"
              required
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              className="w-full px-3 py-2 text-xs sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">WhatsApp / Celular</label>
              <input
                type="text"
                value={editPhone}
                onChange={(e) => setEditPhone(e.target.value)}
                className="w-full px-3 py-2 text-xs sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">E-mail</label>
              <input
                type="email"
                value={editEmail}
                onChange={(e) => setEditEmail(e.target.value)}
                className="w-full px-3 py-2 text-xs sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Observações do Síndico</label>
            <textarea
              rows={2}
              value={editNotes}
              onChange={(e) => setEditNotes(e.target.value)}
              className="w-full px-3 py-2 text-xs sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsEditOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={isSubmittingEdit}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              {isSubmittingEdit ? 'Atualizando...' : 'Salvar Alterações'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* ======================================================== */}
      {/* 3. MODAL: EXCLUIR MORADOR                                */}
      {/* ======================================================== */}
      <Modal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title="Confirmar Exclusão de Morador"
      >
        <div className="space-y-4">
          <p className="text-xs sm:text-sm text-slate-600">
            Tem certeza que deseja remover o cadastro de <strong>{deletingResident?.full_name}</strong> (Unidade {deletingResident?.unit_code})?
          </p>
          <Alert variant="warning">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
              <span className="text-xs text-amber-800">
                Esta ação remove o contato do cadastro administrativo. As sugestões previamente registradas serão preservadas para histórico.
              </span>
            </div>
          </Alert>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsDeleteOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="button"
              size="sm"
              disabled={isSubmittingDelete}
              onClick={handleDeleteSubmit}
              className="bg-rose-600 hover:bg-rose-700 text-white"
            >
              {isSubmittingDelete ? 'Excluindo...' : 'Sim, Excluir Morador'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* ======================================================== */}
      {/* 4. MODAL: VER SUGESTÕES DO MORADOR                       */}
      {/* ======================================================== */}
      <Modal
        isOpen={isSuggestionsOpen}
        onClose={() => setIsSuggestionsOpen(false)}
        title={`Sugestões de ${selectedResidentForSugs?.full_name || 'Morador'}`}
      >
        <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
          <div className="flex items-center justify-between bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
            <div>
              <span className="text-slate-500">Unidade: </span>
              <strong className="text-slate-900">{selectedResidentForSugs?.unit_code}</strong>
              {selectedResidentForSugs?.building_name && selectedResidentForSugs.building_name !== '—' && (
                <span className="text-slate-500"> ({selectedResidentForSugs.building_name})</span>
              )}
            </div>
            {selectedResidentForSugs?.phone_e164 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => selectedResidentForSugs && handleOpenWhatsApp(selectedResidentForSugs)}
                className="text-emerald-700 border-emerald-300 hover:bg-emerald-50 h-7 text-xs"
              >
                <Phone className="w-3 h-3 mr-1" />
                <span>WhatsApp</span>
              </Button>
            )}
          </div>

          {isLoadingSugs ? (
            <div className="py-8 text-center text-xs text-slate-500">Carregando sugestões enviadas...</div>
          ) : residentSuggestions.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500">Nenhuma sugestão encontrada para este morador.</div>
          ) : (
            <div className="space-y-3">
              {residentSuggestions.map((sug) => (
                <div key={sug.id} className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-xs space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                      {sug.protocol}
                    </span>
                    <Badge
                      className={
                        sug.action_type === 'alterar'
                          ? 'bg-amber-50 text-amber-700 border-amber-200'
                          : sug.action_type === 'remover'
                          ? 'bg-rose-50 text-rose-700 border-rose-200'
                          : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      }
                    >
                      {sug.action_type.toUpperCase()}
                    </Badge>
                  </div>

                  <div className="text-xs font-semibold text-slate-900">
                    Dispositivo: {sug.target_reference}
                  </div>

                  <div className="text-xs text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-100 whitespace-pre-wrap leading-relaxed">
                    {sug.suggestion_text}
                  </div>

                  {sug.justification && (
                    <div className="text-[11px] text-slate-500 italic">
                      <strong>Motivação:</strong> {sug.justification}
                    </div>
                  )}

                  <div className="text-[10px] text-slate-400 pt-1 flex items-center justify-between border-t border-slate-100">
                    <span>Enviado em {new Date(sug.created_at).toLocaleString('pt-BR')}</span>
                    <span className="capitalize font-medium text-slate-600">Status: {sug.status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-end pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsSuggestionsOpen(false)}>
              Fechar
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
