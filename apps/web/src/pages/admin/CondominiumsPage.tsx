import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/lib/api';
import type { Condominium } from '@condc/api-contracts';
import {
  Building2,
  Plus,
  Search,
  MapPin,
  Clock,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Edit2,
  Archive,
  Trash2,
  RotateCcw,
  ShieldCheck,
  Check,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { TableSkeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { Breadcrumb } from '@/components/ui/Breadcrumb';

interface FormData {
  name: string;
  cnpj: string;
  timezone: string;
  address_street: string;
  address_number: string;
  address_complement: string;
  address_neighborhood: string;
  address_city: string;
  address_state: string;
  address_zip_code: string;
  status: string;
}

const initialForm: FormData = {
  name: '',
  cnpj: '',
  timezone: 'America/Sao_Paulo',
  address_street: '',
  address_number: '',
  address_complement: '',
  address_neighborhood: '',
  address_city: '',
  address_state: '',
  address_zip_code: '',
  status: 'active',
};

export const CondominiumsPage: React.FC = () => {
  const { condominiums, activeCondominiumId, selectCondominium, refetchCondominiums } = useTenant();
  const { toast } = useToast();

  const [condoList, setCondoList] = useState<Condominium[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');

  // Modais
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isPurgeOpen, setIsPurgeOpen] = useState(false);
  const [purgeConfirmName, setPurgeConfirmName] = useState('');
  const [selectedCondo, setSelectedCondo] = useState<Condominium | null>(null);

  const [formData, setFormData] = useState<FormData>(initialForm);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchCondos = async () => {
    setIsLoading(true);
    setError('');
    try {
      const res = await api.get<Condominium[]>('/condominiums?status=all');
      setCondoList(res.data || []);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar lista de condomínios.');
      setCondoList(condominiums);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCondos();
  }, []);

  const handleOpenCreate = () => {
    setFormData(initialForm);
    setIsCreateOpen(true);
  };

  const handleOpenEdit = (condo: Condominium) => {
    setSelectedCondo(condo);
    setFormData({
      name: condo.name || '',
      cnpj: condo.cnpj || '',
      timezone: condo.timezone || 'America/Sao_Paulo',
      address_street: condo.address_street || '',
      address_number: condo.address_number || '',
      address_complement: condo.address_complement || '',
      address_neighborhood: condo.address_neighborhood || '',
      address_city: condo.address_city || '',
      address_state: condo.address_state || '',
      address_zip_code: condo.address_zip_code || '',
      status: condo.status || 'active',
    });
    setIsEditOpen(true);
  };

  const handleOpenDelete = (condo: Condominium) => {
    setSelectedCondo(condo);
    setIsDeleteOpen(true);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('O nome do condomínio é obrigatório.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await api.post<Condominium>('/condominiums', {
        name: formData.name.trim(),
        cnpj: formData.cnpj.trim() || null,
        timezone: formData.timezone,
        address_street: formData.address_street.trim(),
        address_number: formData.address_number.trim(),
        address_complement: formData.address_complement.trim(),
        address_neighborhood: formData.address_neighborhood.trim(),
        address_city: formData.address_city.trim(),
        address_state: formData.address_state.trim().toUpperCase(),
        address_zip_code: formData.address_zip_code.trim(),
      });

      toast.success(`Condomínio "${formData.name}" cadastrado com sucesso!`);
      setIsCreateOpen(false);
      await refetchCondominiums();
      await fetchCondos();

      if (res.data?.id) {
        selectCondominium(res.data.id);
      }
    } catch (err: any) {
      toast.error(err.message || 'Erro ao cadastrar condomínio.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCondo) return;
    if (!formData.name.trim()) {
      toast.error('O nome do condomínio é obrigatório.');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.patch(`/condominiums/${selectedCondo.id}`, {
        name: formData.name.trim(),
        cnpj: formData.cnpj.trim() || null,
        timezone: formData.timezone,
        address_street: formData.address_street.trim(),
        address_number: formData.address_number.trim(),
        address_complement: formData.address_complement.trim(),
        address_neighborhood: formData.address_neighborhood.trim(),
        address_city: formData.address_city.trim(),
        address_state: formData.address_state.trim().toUpperCase(),
        address_zip_code: formData.address_zip_code.trim(),
        status: formData.status,
      });

      toast.success('Condomínio atualizado com sucesso!');
      setIsEditOpen(false);
      await refetchCondominiums();
      await fetchCondos();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao atualizar condomínio.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleArchive = async (condo: Condominium) => {
    const isArchived = condo.status === 'archived' || condo.status === 'inactive';
    const newStatus = isArchived ? 'active' : 'archived';
    const actionLabel = newStatus === 'active' ? 'reativado com sucesso' : 'arquivado com sucesso';

    try {
      await api.patch(`/condominiums/${condo.id}`, { status: newStatus });
      toast.success(`Condomínio "${condo.name}" ${actionLabel}.`);
      await refetchCondominiums();
      await fetchCondos();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao alterar status do condomínio.');
    }
  };

  const handleDeleteConfirm = async () => {
    if (!selectedCondo) return;

    setIsSubmitting(true);
    try {
      await api.delete(`/condominiums/${selectedCondo.id}`);
      toast.success(`Condomínio "${selectedCondo.name}" arquivado/desativado com sucesso.`);
      setIsDeleteOpen(false);
      await refetchCondominiums();
      await fetchCondos();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao arquivar/desativar condomínio.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenPurge = (condo: Condominium) => {
    setSelectedCondo(condo);
    setPurgeConfirmName('');
    setIsPurgeOpen(true);
  };

  const handlePurgeConfirm = async () => {
    if (!selectedCondo) return;
    const normalized = purgeConfirmName.trim().toUpperCase();
    if (normalized !== 'CONFIRMAR EXCLUSÃO' && normalized !== 'CONFIRMAR EXCLUSAO') {
      toast.error('Digite "CONFIRMAR EXCLUSÃO" para prosseguir com o saneamento definitivo.');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.delete(`/condominiums/${selectedCondo.id}?permanent=true`);
      toast.success(`Condomínio "${selectedCondo.name}" expurgado definitivamente.`);
      setIsPurgeOpen(false);
      await refetchCondominiums();
      await fetchCondos();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao realizar o saneamento do condomínio.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectActive = (condo: Condominium) => {
    selectCondominium(condo.id);
    toast.info(`Contexto alterado para "${condo.name}".`);
  };

  // Filtragem
  const filteredCondos = condoList.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.cnpj && c.cnpj.includes(searchQuery)) ||
      (c.address_city && c.address_city.toLowerCase().includes(searchQuery.toLowerCase()));

    const isArchived = c.status === 'archived' || c.status === 'inactive';
    const matchesStatus =
      statusFilter === 'all'
        ? true
        : statusFilter === 'active'
        ? !isArchived
        : isArchived;

    return matchesSearch && matchesStatus;
  });

  const totalCount = condoList.length;
  const activeCount = condoList.filter((c) => c.status !== 'archived' && c.status !== 'inactive').length;
  const inactiveCount = condoList.filter((c) => c.status === 'archived' || c.status === 'inactive').length;


  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          { label: 'Painel', href: '/painel' },
          { label: 'Condomínios', href: '/painel/condominios' },
        ]}
      />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Building2 className="w-6 h-6 text-brand-600" />
            <span>Gestão de Condomínios</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Cadastre, edite, arquive e alterne o contexto operacional multi-tenancy do sistema.
          </p>
        </div>
        <div>
          <Button size="sm" onClick={handleOpenCreate} className="shadow-xs">
            <Plus className="w-4 h-4 mr-1.5" />
            <span>Novo Condomínio</span>
          </Button>
        </div>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {/* Cartões de Indicadores */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total de Unidades Gestão</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{totalCount}</h3>
            </div>
            <div className="p-3 bg-brand-50 rounded-xl text-brand-600">
              <Building2 className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Condomínios Ativos</p>
              <h3 className="text-2xl font-bold text-emerald-600 mt-1">{activeCount}</h3>
            </div>
            <div className="p-3 bg-emerald-50 rounded-xl text-emerald-600">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Arquivados / Inativos</p>
              <h3 className="text-2xl font-bold text-slate-500 mt-1">{inactiveCount}</h3>
            </div>
            <div className="p-3 bg-slate-100 rounded-xl text-slate-600">
              <Archive className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-brand-200 bg-brand-50/30">
          <CardContent className="p-4 flex items-center justify-between">
            <div className="truncate pr-2">
              <p className="text-xs font-semibold text-brand-700 uppercase tracking-wider">Contexto em Operação</p>
              <h3 className="text-sm font-bold text-slate-900 mt-1 truncate">
                {condoList.find((c) => c.id === activeCondominiumId)?.name || 'Nenhum Selecionado'}
              </h3>
            </div>
            <div className="p-3 bg-brand-100 rounded-xl text-brand-700 shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Barra de Filtros e Busca */}
      <Card>
        <CardContent className="p-4 flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-96">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Buscar por nome, CNPJ ou cidade..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="flex items-center gap-1.5 w-full sm:w-auto">
            <span className="text-xs font-semibold text-slate-500 mr-2">Filtrar:</span>
            <Button
              variant={statusFilter === 'all' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('all')}
            >
              Todos ({totalCount})
            </Button>
            <Button
              variant={statusFilter === 'active' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('active')}
            >
              Ativos ({activeCount})
            </Button>
            <Button
              variant={statusFilter === 'inactive' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('inactive')}
            >
              Arquivados ({inactiveCount})
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Condomínios em Grade de Cards */}
      {isLoading ? (
        <Card>
          <CardContent className="p-6">
            <TableSkeleton rows={4} />
          </CardContent>
        </Card>
      ) : filteredCondos.length === 0 ? (
        <Card>
          <CardContent className="p-8">
            <EmptyState
              icon={Building2}
              title="Nenhum condomínio encontrado"
              description="Não foram encontrados registros para o filtro selecionado. Cadastre um novo condomínio para iniciar."
              actionLabel="Cadastrar Novo Condomínio"
              onAction={handleOpenCreate}
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredCondos.map((condo) => {
            const isActiveContext = condo.id === activeCondominiumId;
            const isInactive = condo.status === 'archived' || condo.status === 'inactive';


            return (
              <Card
                key={condo.id}
                className={`relative flex flex-col justify-between transition-all duration-150 hover:shadow-md ${
                  isActiveContext ? 'border-2 border-brand-500 shadow-xs ring-1 ring-brand-500/20' : ''
                } ${isInactive ? 'opacity-75 bg-slate-50/50' : 'bg-white'}`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                        {isActiveContext && (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-brand-100 text-brand-800">
                            <span className="w-1.5 h-1.5 rounded-full bg-brand-600 animate-pulse" />
                            Sessão Ativa
                          </span>
                        )}
                        {isInactive ? (
                          <Badge variant="default">Arquivado</Badge>
                        ) : (
                          <Badge variant="success">Ativo</Badge>
                        )}
                      </div>
                      <CardTitle className="text-base text-slate-900 leading-tight truncate">
                        {condo.name}
                      </CardTitle>
                      <p className="text-xs text-slate-500 font-mono mt-0.5">
                        {condo.cnpj ? `CNPJ: ${condo.cnpj}` : 'CNPJ: Não informado'}
                      </p>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-3.5 text-xs text-slate-600 pt-0 pb-4">
                  {/* Endereço */}
                  <div className="flex items-start gap-2 pt-2 border-t border-slate-100">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                    <span className="line-clamp-2">
                      {[
                        condo.address_street,
                        condo.address_number,
                        condo.address_complement,
                        condo.address_neighborhood,
                        condo.address_city && condo.address_state
                          ? `${condo.address_city}/${condo.address_state}`
                          : condo.address_city,
                        condo.address_zip_code ? `CEP: ${condo.address_zip_code}` : null,
                      ]
                        .filter(Boolean)
                        .join(', ') || 'Endereço não cadastrado'}
                    </span>
                  </div>

                  {/* Fuso Horário */}
                  <div className="flex items-center gap-2 text-slate-500">
                    <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>Fuso: {condo.timezone || 'America/Sao_Paulo'}</span>
                  </div>
                </CardContent>

                {/* Rodapé com Ações */}
                <div className="p-3.5 bg-slate-50 border-t border-slate-100 rounded-b-xl flex items-center justify-between gap-2">
                  {isActiveContext ? (
                    <span className="text-[11px] font-medium text-brand-700 flex items-center gap-1.5 px-2 py-1 bg-brand-100/50 rounded-lg">
                      <Check className="w-3.5 h-3.5 text-brand-600" />
                      Em Operação
                    </span>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSelectActive(condo)}
                      className="text-xs"
                    >
                      <span>Ativar Contexto</span>
                    </Button>
                  )}

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleOpenEdit(condo)}
                      className="p-1.5 text-slate-500 hover:text-brand-600 hover:bg-slate-200/60 rounded-lg transition-colors"
                      title="Editar condomínio"
                      aria-label="Editar condomínio"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>

                    <button
                      onClick={() => handleToggleArchive(condo)}
                      className="p-1.5 text-slate-500 hover:text-amber-600 hover:bg-slate-200/60 rounded-lg transition-colors"
                      title={isInactive ? 'Reativar condomínio' : 'Arquivar condomínio'}
                      aria-label={isInactive ? 'Reativar condomínio' : 'Arquivar condomínio'}
                    >
                      {isInactive ? <RotateCcw className="w-4 h-4" /> : <Archive className="w-4 h-4" />}
                    </button>

                    {isInactive ? (
                      <button
                        onClick={() => handleOpenPurge(condo)}
                        className="p-1.5 text-rose-500 hover:text-rose-700 hover:bg-rose-100 rounded-lg transition-colors"
                        title="Saneamento / Excluir Definitivamente"
                        aria-label="Saneamento / Excluir Definitivamente"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleOpenDelete(condo)}
                        className="p-1.5 text-slate-400 hover:text-amber-600 hover:bg-slate-200/60 rounded-lg transition-colors"
                        title="Arquivar / Desativar"
                        aria-label="Arquivar / Desativar"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Modal Novo Condomínio */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Cadastrar Novo Condomínio">
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Nome do Condomínio *
            </label>
            <input
              type="text"
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Ex: Condomínio Edifício Solar das Palmeiras"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                CNPJ
              </label>
              <input
                type="text"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 font-mono"
                placeholder="00.000.000/0001-00"
                value={formData.cnpj}
                onChange={(e) => setFormData({ ...formData, cnpj: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Fuso Horário
              </label>
              <select
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                value={formData.timezone}
                onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
              >
                <option value="America/Sao_Paulo">Brasília (America/Sao_Paulo)</option>
                <option value="America/Manaus">Manaus (America/Manaus)</option>
                <option value="America/Cuiaba">Cuiabá (America/Cuiaba)</option>
                <option value="America/Belem">Belém (America/Belem)</option>
                <option value="America/Fortaleza">Fortaleza (America/Fortaleza)</option>
              </select>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-200">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3">
              Endereço Físico do Condomínio
            </h4>
            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-slate-600 mb-1">Logradouro / Rua</label>
                  <input
                    type="text"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="Ex: Av. das Américas"
                    value={formData.address_street}
                    onChange={(e) => setFormData({ ...formData, address_street: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Número</label>
                  <input
                    type="text"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="1500"
                    value={formData.address_number}
                    onChange={(e) => setFormData({ ...formData, address_number: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Complemento</label>
                  <input
                    type="text"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="Bloco Único"
                    value={formData.address_complement}
                    onChange={(e) => setFormData({ ...formData, address_complement: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Bairro</label>
                  <input
                    type="text"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="Barra da Tijuca"
                    value={formData.address_neighborhood}
                    onChange={(e) => setFormData({ ...formData, address_neighborhood: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Cidade</label>
                  <input
                    type="text"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="Rio de Janeiro"
                    value={formData.address_city}
                    onChange={(e) => setFormData({ ...formData, address_city: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Estado (UF)</label>
                  <input
                    type="text"
                    maxLength={2}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 uppercase font-mono"
                    placeholder="RJ"
                    value={formData.address_state}
                    onChange={(e) => setFormData({ ...formData, address_state: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">CEP</label>
                  <input
                    type="text"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 font-mono"
                    placeholder="22640-100"
                    value={formData.address_zip_code}
                    onChange={(e) => setFormData({ ...formData, address_zip_code: e.target.value })}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-200">
            <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Cadastrando...' : 'Cadastrar Condomínio'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal Editar Condomínio */}
      <Modal isOpen={isEditOpen} onClose={() => setIsEditOpen(false)} title="Editar Condomínio">
        <form onSubmit={handleEditSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Nome do Condomínio *
            </label>
            <input
              type="text"
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                CNPJ
              </label>
              <input
                type="text"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 font-mono"
                value={formData.cnpj}
                onChange={(e) => setFormData({ ...formData, cnpj: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Status
              </label>
              <select
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              >
                <option value="active">Ativo</option>
                <option value="archived">Arquivado</option>
                <option value="suspended">Suspenso</option>

              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Fuso Horário
              </label>
              <select
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                value={formData.timezone}
                onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
              >
                <option value="America/Sao_Paulo">Brasília (America/Sao_Paulo)</option>
                <option value="America/Manaus">Manaus (America/Manaus)</option>
                <option value="America/Cuiaba">Cuiabá (America/Cuiaba)</option>
                <option value="America/Belem">Belém (America/Belem)</option>
                <option value="America/Fortaleza">Fortaleza (America/Fortaleza)</option>
              </select>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-200">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3">
              Endereço Físico
            </h4>
            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-slate-600 mb-1">Logradouro / Rua</label>
                  <input
                    type="text"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                    value={formData.address_street}
                    onChange={(e) => setFormData({ ...formData, address_street: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Número</label>
                  <input
                    type="text"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                    value={formData.address_number}
                    onChange={(e) => setFormData({ ...formData, address_number: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Complemento</label>
                  <input
                    type="text"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="Edifício / Bloco"
                    value={formData.address_complement}
                    onChange={(e) => setFormData({ ...formData, address_complement: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Bairro</label>
                  <input
                    type="text"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                    value={formData.address_neighborhood}
                    onChange={(e) => setFormData({ ...formData, address_neighborhood: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Cidade</label>
                  <input
                    type="text"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                    value={formData.address_city}
                    onChange={(e) => setFormData({ ...formData, address_city: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Estado (UF)</label>
                  <input
                    type="text"
                    maxLength={2}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 uppercase font-mono"
                    value={formData.address_state}
                    onChange={(e) => setFormData({ ...formData, address_state: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">CEP</label>
                  <input
                    type="text"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 font-mono"
                    value={formData.address_zip_code}
                    onChange={(e) => setFormData({ ...formData, address_zip_code: e.target.value })}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-200">
            <Button type="button" variant="outline" onClick={() => setIsEditOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Salvando...' : 'Salvar Alterações'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal Confirmar Exclusão / Desativação */}
      <Modal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title="Desativar Condomínio"
      >
        <div className="space-y-4">
          <div className="p-3 bg-amber-50 rounded-lg flex items-start gap-3 text-amber-800 text-xs">
            <AlertTriangle className="w-5 h-5 shrink-0 text-amber-600 mt-0.5" />
            <div>
              <p className="font-semibold">Atenção à integridade histórica:</p>
              <p className="mt-1">
                A desativação do condomínio <strong>"{selectedCondo?.name}"</strong> alterará seu status para inativo. Em cumprimento às regras de auditoria e preservação legal, dados históricos e minutas não são destruídos fisicamente.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsDeleteOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={isSubmitting}
              onClick={handleDeleteConfirm}
            >
              {isSubmitting ? 'Desativando...' : 'Confirmar Desativação'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal Saneamento / Exclusão Definitiva */}
      <Modal
        isOpen={isPurgeOpen}
        onClose={() => setIsPurgeOpen(false)}
        title="Saneamento Definitivo de Condomínio"
      >
        <div className="space-y-4">
          <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-3 text-rose-900 text-xs">
            <AlertTriangle className="w-5 h-5 shrink-0 text-rose-600 mt-0.5" />
            <div>
              <p className="font-bold uppercase tracking-wider text-rose-700">Ação Irreversível de Saneamento</p>
              <p className="mt-1 leading-relaxed">
                Este procedimento removerá permanentemente o condomínio e expurgará em cascata todas as suas torres, unidades, documentos, minutas e registros associados sem uso.
              </p>
            </div>
          </div>

          {/* Cartão de Identificação em Destaque do Condomínio */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-slate-200/80 text-slate-700 rounded-lg shrink-0">
                <Building2 className="w-5 h-5" aria-hidden="true" />
              </div>
              <div>
                <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                  Condomínio a ser Excluído
                </span>
                <span className="font-bold text-slate-900 text-sm block">
                  {selectedCondo?.name}
                </span>
                <span className="text-xs text-slate-500 font-mono block">
                  CNPJ: {selectedCondo?.cnpj || 'Não informado'}
                </span>
              </div>
            </div>
            <Badge variant="danger" dot>Arquivado</Badge>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700">
              Para confirmar a exclusão permanente, digite exatamente <span className="font-mono text-rose-700 font-bold bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">CONFIRMAR EXCLUSÃO</span>:
            </label>
            <input
              type="text"
              value={purgeConfirmName}
              onChange={(e) => setPurgeConfirmName(e.target.value)}
              placeholder="CONFIRMAR EXCLUSÃO"
              className="w-full text-xs font-mono p-2.5 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-rose-500 uppercase tracking-wider"
            />
            <p className="text-[11px] text-slate-500">
              A palavra-chave padrão em maiúsculas assegura a confirmação consciente sem exigir que você decore ou copie o nome completo do condomínio.
            </p>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsPurgeOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={
                isSubmitting ||
                (purgeConfirmName.trim().toUpperCase() !== 'CONFIRMAR EXCLUSÃO' &&
                 purgeConfirmName.trim().toUpperCase() !== 'CONFIRMAR EXCLUSAO')
              }
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
