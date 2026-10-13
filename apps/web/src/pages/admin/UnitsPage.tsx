import React, { useState, useEffect, useMemo } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/lib/api';
import type { Building, Unit } from '@condc/api-contracts';
import {
  Layers,
  Plus,
  Building2,
  Check,
  AlertCircle,
  Search,
  Filter,
  Edit2,
  Trash2,
  RotateCcw,
  AlertTriangle,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { TableSkeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { Breadcrumb } from '@/components/ui/Breadcrumb';

export const UnitsPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const { toast } = useToast();
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Filtros de busca
  const [searchCode, setSearchCode] = useState('');
  const [selectedTowerFilter, setSelectedTowerFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('active');

  // Modais de Criação
  const [isBuildingModalOpen, setIsBuildingModalOpen] = useState(false);
  const [isUnitModalOpen, setIsUnitModalOpen] = useState(false);
  const [newBuildingName, setNewBuildingName] = useState('');
  const [newBuildingCode, setNewBuildingCode] = useState('');
  const [newUnitCode, setNewUnitCode] = useState('');
  const [selectedBuildingId, setSelectedBuildingId] = useState('');
  const [newIdealFraction, setNewIdealFraction] = useState('0.0100');

  // Modais de Edição e Exclusão de Torre/Bloco
  const [isEditBuildingOpen, setIsEditBuildingOpen] = useState(false);
  const [isDeleteBuildingOpen, setIsDeleteBuildingOpen] = useState(false);
  const [isPurgeBuildingOpen, setIsPurgeBuildingOpen] = useState(false);
  const [editingBuilding, setEditingBuilding] = useState<Building | null>(null);
  const [editBuildingName, setEditBuildingName] = useState('');
  const [editBuildingCode, setEditBuildingCode] = useState('');

  // Modais de Edição e Exclusão de Unidade
  const [isEditUnitOpen, setIsEditUnitOpen] = useState(false);
  const [isDeleteUnitOpen, setIsDeleteUnitOpen] = useState(false);
  const [isPurgeUnitOpen, setIsPurgeUnitOpen] = useState(false);
  const [editingUnit, setEditingUnit] = useState<Unit | null>(null);
  const [editUnitCode, setEditUnitCode] = useState('');
  const [editUnitBuildingId, setEditUnitBuildingId] = useState('');
  const [editUnitFraction, setEditUnitFraction] = useState('');
  const [editUnitStatus, setEditUnitStatus] = useState('active');

  const [isSubmitting, setIsSubmitting] = useState(false);

  // 4. Modal Gerador de Apartamentos em Lote
  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false);
  const [batchMode, setBatchMode] = useState<'existing' | 'new'>('new');
  const [batchBuildingId, setBatchBuildingId] = useState('');
  const [batchNewBuildingName, setBatchNewBuildingName] = useState('');
  const [batchNewBuildingCode, setBatchNewBuildingCode] = useState('');
  const [batchStartFloor, setBatchStartFloor] = useState('3');
  const [batchEndFloor, setBatchEndFloor] = useState('15');
  const [batchUnitsPerFloor, setBatchUnitsPerFloor] = useState('6');
  const [batchSuffixDigits, setBatchSuffixDigits] = useState<'2' | '1'>('2');
  const [isSubmittingBatch, setIsSubmittingBatch] = useState(false);

  const startF = parseInt(batchStartFloor, 10) || 0;
  const endF = parseInt(batchEndFloor, 10) || 0;
  const perF = parseInt(batchUnitsPerFloor, 10) || 0;
  const totalBatchUnits = endF >= startF && perF > 0 ? (endF - startF + 1) * perF : 0;

  const previewCodes = useMemo(() => {
    if (totalBatchUnits <= 0) return [];
    const list: string[] = [];
    for (let f = startF; f <= endF; f++) {
      for (let u = 1; u <= perF; u++) {
        const suf = batchSuffixDigits === '2' ? String(u).padStart(2, '0') : String(u);
        list.push(`${f}${suf}`);
        if (list.length >= 12) break;
      }
      if (list.length >= 12) break;
    }
    return list;
  }, [startF, endF, perF, batchSuffixDigits, totalBatchUnits]);

  const fetchData = async () => {
    if (!activeCondominiumId) return;
    setIsLoading(true);
    setError('');
    try {
      const [resB, resU] = await Promise.all([
        api.get<Building[]>(`/condominiums/${activeCondominiumId}/buildings?status=all`),
        api.get<Unit[]>(`/condominiums/${activeCondominiumId}/units?status=all`),
      ]);
      setBuildings(resB.data || []);
      setUnits(resU.data || []);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar estrutura física.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeCondominiumId]);

  // Criação de Torre
  const handleCreateBuilding = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId) return;
    setIsSubmitting(true);
    try {
      await api.post(`/condominiums/${activeCondominiumId}/buildings`, {
        name: newBuildingName.trim(),
        code: newBuildingCode.trim() || newBuildingName.trim().toUpperCase(),
        kind: 'tower',
      });
      setIsBuildingModalOpen(false);
      setNewBuildingName('');
      setNewBuildingCode('');
      toast.success('Torre/Bloco cadastrado com sucesso!');
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao criar torre/bloco.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Edição de Torre
  const handleOpenEditBuilding = (b: Building) => {
    setEditingBuilding(b);
    setEditBuildingName(b.name);
    setEditBuildingCode(b.code || '');
    setIsEditBuildingOpen(true);
  };

  const handleUpdateBuilding = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !editingBuilding) return;
    setIsSubmitting(true);
    try {
      await api.patch(`/condominiums/${activeCondominiumId}/buildings/${editingBuilding.id}`, {
        name: editBuildingName.trim(),
        code: editBuildingCode.trim() || editBuildingName.trim().toUpperCase(),
      });
      setIsEditBuildingOpen(false);
      toast.success('Torre/Bloco atualizado com sucesso!');
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao atualizar torre/bloco.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Exclusão de Torre
  const handleOpenDeleteBuilding = (b: Building) => {
    setEditingBuilding(b);
    setIsDeleteBuildingOpen(true);
  };

  const handleDeleteBuilding = async () => {
    if (!activeCondominiumId || !editingBuilding) return;
    setIsSubmitting(true);
    try {
      await api.delete(`/condominiums/${activeCondominiumId}/buildings/${editingBuilding.id}`);
      setIsDeleteBuildingOpen(false);
      toast.success(`Torre/Bloco "${editingBuilding.name}" desativado.`);
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao desativar torre/bloco.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenPurgeBuilding = (b: Building) => {
    setEditingBuilding(b);
    setIsPurgeBuildingOpen(true);
  };

  const handlePurgeBuildingConfirm = async () => {
    if (!activeCondominiumId || !editingBuilding) return;
    setIsSubmitting(true);
    try {
      await api.delete(`/condominiums/${activeCondominiumId}/buildings/${editingBuilding.id}?permanent=true`);
      setIsPurgeBuildingOpen(false);
      toast.success(`Torre/Bloco "${editingBuilding.name}" excluído definitivamente no saneamento.`);
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao excluir definitivamente torre/bloco.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReactivateBuilding = async (b: Building) => {
    if (!activeCondominiumId) return;
    try {
      await api.patch(`/condominiums/${activeCondominiumId}/buildings/${b.id}`, { status: 'active' });
      toast.success(`Torre/Bloco "${b.name}" reativado com sucesso!`);
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao reativar torre/bloco.');
    }
  };

  // Criação de Unidade
  const handleCreateUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId) return;

    const trimmedCode = newUnitCode.trim();
    // Validação preventiva de duplicidade no frontend
    const exists = units.some(
      (u) =>
        u.code.toLowerCase() === trimmedCode.toLowerCase() &&
        (u.building_id || null) === (selectedBuildingId || null) &&
        u.status !== 'inactive'
    );
    if (exists) {
      toast.error(`A unidade "${trimmedCode}" já está cadastrada para esta torre/condomínio.`);
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post(`/condominiums/${activeCondominiumId}/units`, {
        building_id: selectedBuildingId || null,
        code: trimmedCode,
        ideal_fraction: parseFloat(newIdealFraction) || 0.01,
      });
      setIsUnitModalOpen(false);
      setNewUnitCode('');
      toast.success('Unidade autônoma cadastrada com sucesso!');
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao criar unidade.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Geração em Lote de Apartamentos
  const handleBatchGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId) return;

    if (batchMode === 'new' && !batchNewBuildingName.trim()) {
      toast.error('Informe o nome da nova torre ou bloco.');
      return;
    }
    if (batchMode === 'existing' && !batchBuildingId) {
      toast.error('Selecione uma torre existente ou escolha cadastrar uma nova.');
      return;
    }
    if (startF > endF) {
      toast.error('O andar inicial não pode ser maior que o andar final.');
      return;
    }
    if (perF <= 0 || perF > 50) {
      toast.error('A quantidade de apartamentos por andar deve ser entre 1 e 50.');
      return;
    }

    setIsSubmittingBatch(true);
    try {
      const payload = {
        building_id: batchMode === 'existing' ? batchBuildingId : undefined,
        new_building_name: batchMode === 'new' ? batchNewBuildingName.trim() : undefined,
        new_building_code: batchMode === 'new' ? (batchNewBuildingCode.trim() || batchNewBuildingName.trim().toUpperCase()) : undefined,
        start_floor: startF,
        end_floor: endF,
        units_per_floor: perF,
        suffix_digits: parseInt(batchSuffixDigits, 10),
      };

      const res = await api.post<any>(`/condominiums/${activeCondominiumId}/units/batch-generate`, payload);
      const data = res.data;
      toast.success(
        `Sucesso! ${data.created_count} apartamentos gerados com sucesso (${data.existing_count} já existiam). Total: ${data.total_units} unidades.`
      );
      setIsBatchModalOpen(false);
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao gerar apartamentos em lote.');
    } finally {
      setIsSubmittingBatch(false);
    }
  };

  // Edição de Unidade
  const handleOpenEditUnit = (unit: Unit) => {
    setEditingUnit(unit);
    setEditUnitCode(unit.code || unit.unit_number || '');
    setEditUnitBuildingId(unit.building_id || '');
    setEditUnitFraction(unit.ideal_fraction ? String(unit.ideal_fraction) : '0.0100');
    setEditUnitStatus(unit.status || 'active');
    setIsEditUnitOpen(true);
  };

  const handleUpdateUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !editingUnit) return;

    const trimmedCode = editUnitCode.trim();
    // Validação preventiva de duplicidade no frontend
    const exists = units.some(
      (u) =>
        u.id !== editingUnit.id &&
        u.code.toLowerCase() === trimmedCode.toLowerCase() &&
        (u.building_id || null) === (editUnitBuildingId || null) &&
        u.status !== 'inactive'
    );
    if (exists) {
      toast.error(`Já existe outra unidade com código "${trimmedCode}" nesta torre/condomínio.`);
      return;
    }

    setIsSubmitting(true);
    try {
      await api.patch(`/condominiums/${activeCondominiumId}/units/${editingUnit.id}`, {
        code: trimmedCode,
        building_id: editUnitBuildingId || null,
        ideal_fraction: parseFloat(editUnitFraction) || 0.01,
        status: editUnitStatus,
      });
      setIsEditUnitOpen(false);
      toast.success('Unidade autônoma atualizada com sucesso!');
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao atualizar unidade.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Exclusão / Desativação de Unidade
  const handleOpenDeleteUnit = (unit: Unit) => {
    setEditingUnit(unit);
    setIsDeleteUnitOpen(true);
  };

  const handleDeleteUnit = async () => {
    if (!activeCondominiumId || !editingUnit) return;
    setIsSubmitting(true);
    try {
      await api.delete(`/condominiums/${activeCondominiumId}/units/${editingUnit.id}`);
      setIsDeleteUnitOpen(false);
      toast.success(`Unidade "${editingUnit.code}" desativada.`);
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao desativar unidade.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Reativação rápida de unidade
  const handleReactivateUnit = async (unit: Unit) => {
    if (!activeCondominiumId) return;
    try {
      await api.patch(`/condominiums/${activeCondominiumId}/units/${unit.id}`, {
        status: 'active',
      });
      toast.success(`Unidade "${unit.code}" reativada com sucesso!`);
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao reativar unidade.');
    }
  };

  const handleOpenPurgeUnit = (unit: Unit) => {
    setEditingUnit(unit);
    setIsPurgeUnitOpen(true);
  };

  const handlePurgeUnitConfirm = async () => {
    if (!activeCondominiumId || !editingUnit) return;
    setIsSubmitting(true);
    try {
      await api.delete(`/condominiums/${activeCondominiumId}/units/${editingUnit.id}?permanent=true`);
      setIsPurgeUnitOpen(false);
      toast.success(`Unidade "${editingUnit.code}" excluída definitivamente no saneamento.`);
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao excluir definitivamente unidade.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Filtragem de Unidades
  const filteredUnits = units.filter((u) => {
    const code = (u.code || u.unit_number || '').toLowerCase();
    const matchesCode = searchCode ? code.includes(searchCode.toLowerCase()) : true;

    const matchesTower =
      selectedTowerFilter === 'all'
        ? true
        : selectedTowerFilter === 'none'
        ? !u.building_id
        : u.building_id === selectedTowerFilter;

    const matchesStatus =
      statusFilter === 'all'
        ? true
        : statusFilter === 'active'
        ? u.status !== 'inactive'
        : u.status === 'inactive';

    return matchesCode && matchesTower && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          { label: 'Painel', href: '/painel' },
          { label: 'Torres & Unidades', href: '/painel/unidades' },
        ]}
      />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Layers className="w-6 h-6 text-brand-600" />
            <span>Torres & Unidades Autônomas</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Estrutura física do condomínio para vinculação, preservação cadastral e auditoria de moradores.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            size="sm"
            onClick={() => setIsBatchModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs"
          >
            <Sparkles className="w-4 h-4 mr-1.5" />
            <span>Gerar Apartamentos em Lote</span>
          </Button>
          <Button variant="outline" size="sm" onClick={() => setIsBuildingModalOpen(true)}>
            <Building2 className="w-4 h-4 mr-1.5" />
            <span>Nova Torre/Bloco</span>
          </Button>
          <Button variant="outline" size="sm" onClick={() => setIsUnitModalOpen(true)}>
            <Plus className="w-4 h-4 mr-1.5" />
            <span>Nova Unidade</span>
          </Button>
        </div>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {/* Grid de Torres / Blocos */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            Torres & Blocos Cadastrados ({buildings.length})
          </h3>
        </div>
        {buildings.length === 0 ? (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500 text-center">
            Nenhuma torre ou bloco cadastrado. Use o botão acima para adicionar blocos ao condomínio.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {buildings.map((b) => {
              const countUnits = units.filter((u) => u.building_id === b.id && u.status !== 'inactive').length;
              return (
                <Card key={b.id} className="relative group">
                  <CardContent className="p-4 flex items-center justify-between">
                    <div className="min-w-0 flex-1">
                      <h4 className="font-semibold text-slate-900 text-sm truncate">{b.name}</h4>
                      <p className="text-xs text-slate-500 font-mono mt-0.5">Código: {b.code || '—'}</p>
                      <p className="text-xs text-slate-600 mt-2 font-medium">
                        {countUnits} {countUnits === 1 ? 'unidade ativa' : 'unidades ativas'}
                      </p>
                    </div>
                    <div className="flex items-center gap-1">
                      {b.status === 'inactive' ? (
                        <>
                          <button
                            onClick={() => handleReactivateBuilding(b)}
                            className="p-1.5 text-slate-500 hover:text-emerald-600 hover:bg-slate-100 rounded-lg transition-colors"
                            title="Reativar Torre/Bloco"
                            aria-label="Reativar Torre/Bloco"
                          >
                            <RotateCcw className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleOpenPurgeBuilding(b)}
                            className="p-1.5 text-rose-500 hover:text-rose-700 hover:bg-rose-100 rounded-lg transition-colors"
                            title="Saneamento / Excluir Definitivamente"
                            aria-label="Saneamento / Excluir Definitivamente"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => handleOpenEditBuilding(b)}
                            className="p-1.5 text-slate-400 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors"
                            title="Editar Torre/Bloco"
                            aria-label="Editar Torre/Bloco"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleOpenDeleteBuilding(b)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-slate-100 rounded-lg transition-colors"
                            title="Desativar Torre/Bloco"
                            aria-label="Desativar Torre/Bloco"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Barra de Filtros da Tabela de Unidades */}
      <Card>
        <CardContent className="p-4 flex flex-col md:flex-row gap-3 items-center justify-between">
          <div className="relative w-full md:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-brand-500 font-mono"
              placeholder="Buscar unidade (ex: 101, 002)..."
              value={searchCode}
              onChange={(e) => setSearchCode(e.target.value)}
            />
          </div>

          <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
            {/* Filtro por Torre */}
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-500 font-medium">Torre:</span>
              <select
                className="text-xs border border-slate-300 rounded-lg py-1.5 px-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                value={selectedTowerFilter}
                onChange={(e) => setSelectedTowerFilter(e.target.value)}
              >
                <option value="all">Todas as Torres</option>
                <option value="none">Sem Torre (Geral)</option>
                {buildings.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Filtro por Status */}
            <div className="flex items-center gap-1">
              <Button
                variant={statusFilter === 'active' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('active')}
              >
                Ativas
              </Button>
              <Button
                variant={statusFilter === 'inactive' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('inactive')}
              >
                Inativas
              </Button>
              <Button
                variant={statusFilter === 'all' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('all')}
              >
                Todas ({units.length})
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabela de Unidades */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">
                Unidades Autônomas ({filteredUnits.length} exibidas de {units.length})
              </CardTitle>
              <CardDescription>
                Preservação estrita de zeros à esquerda e frações ideais (sem peso eleitoral).
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <TableSkeleton rows={4} />
          ) : filteredUnits.length === 0 ? (
            <div className="p-6">
              <EmptyState
                icon={Layers}
                title="Nenhuma unidade autônoma encontrada"
                description="Cadastre as unidades do condomínio ou ajuste os filtros de busca para localizá-las."
                actionLabel="Cadastrar Nova Unidade"
                onAction={() => setIsUnitModalOpen(true)}
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-3">Código / Unidade</th>
                    <th className="px-6 py-3">Torre / Bloco</th>
                    <th className="px-6 py-3">Fração Ideal</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredUnits.map((u) => {
                    const b = buildings.find((x) => x.id === u.building_id);
                    const isInactive = u.status === 'inactive';
                    return (
                      <tr
                        key={u.id}
                        className={`hover:bg-slate-50/50 transition-colors ${
                          isInactive ? 'opacity-60 bg-slate-50/30' : ''
                        }`}
                      >
                        <td className="px-6 py-3 font-semibold text-slate-900 font-mono text-sm">
                          {u.code || u.unit_number}
                        </td>
                        <td className="px-6 py-3 text-slate-700">{b ? b.name : 'Geral'}</td>
                        <td className="px-6 py-3 text-slate-600 font-mono">
                          {u.ideal_fraction ? Number(u.ideal_fraction).toFixed(4) : '—'}
                        </td>
                        <td className="px-6 py-3">
                          {isInactive ? (
                            <Badge variant="default">Inativa</Badge>
                          ) : (
                            <Badge variant="success">Ativa</Badge>
                          )}
                        </td>
                        <td className="px-6 py-3 text-right">
                          <div className="inline-flex items-center gap-1">
                            <button
                              onClick={() => handleOpenEditUnit(u)}
                              className="p-1.5 text-slate-500 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors"
                              title="Editar unidade"
                              aria-label="Editar unidade"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </button>

                            {isInactive ? (
                              <>
                                <button
                                  onClick={() => handleReactivateUnit(u)}
                                  className="p-1.5 text-slate-500 hover:text-emerald-600 hover:bg-slate-100 rounded-lg transition-colors"
                                  title="Reativar unidade"
                                  aria-label="Reativar unidade"
                                >
                                  <RotateCcw className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={() => handleOpenPurgeUnit(u)}
                                  className="p-1.5 text-rose-500 hover:text-rose-700 hover:bg-rose-50 rounded-lg transition-colors"
                                  title="Saneamento / Excluir Definitivamente"
                                  aria-label="Saneamento / Excluir Definitivamente"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </>
                            ) : (
                              <button
                                onClick={() => handleOpenDeleteUnit(u)}
                                className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-slate-100 rounded-lg transition-colors"
                                title="Excluir / Desativar unidade"
                                aria-label="Excluir / Desativar unidade"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
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

      {/* Modal Nova Torre/Bloco */}
      <Modal
        isOpen={isBuildingModalOpen}
        onClose={() => setIsBuildingModalOpen(false)}
        title="Cadastrar Torre ou Bloco"
      >
        <form onSubmit={handleCreateBuilding} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Nome da Torre/Bloco *
            </label>
            <input
              type="text"
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Ex: Torre A, Bloco das Acácias"
              value={newBuildingName}
              onChange={(e) => setNewBuildingName(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Código Curto
            </label>
            <input
              type="text"
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 font-mono uppercase"
              placeholder="Ex: TORRE_A, BL_1"
              value={newBuildingCode}
              onChange={(e) => setNewBuildingCode(e.target.value)}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsBuildingModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Cadastrando...' : 'Cadastrar Torre'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal Editar Torre/Bloco */}
      <Modal
        isOpen={isEditBuildingOpen}
        onClose={() => setIsEditBuildingOpen(false)}
        title="Editar Torre ou Bloco"
      >
        <form onSubmit={handleUpdateBuilding} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Nome da Torre/Bloco *
            </label>
            <input
              type="text"
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={editBuildingName}
              onChange={(e) => setEditBuildingName(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Código Curto
            </label>
            <input
              type="text"
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 font-mono uppercase"
              value={editBuildingCode}
              onChange={(e) => setEditBuildingCode(e.target.value)}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsEditBuildingOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Salvando...' : 'Salvar Alterações'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal Desativar Torre/Bloco */}
      <Modal
        isOpen={isDeleteBuildingOpen}
        onClose={() => setIsDeleteBuildingOpen(false)}
        title="Desativar Torre ou Bloco"
      >
        <div className="space-y-4">
          <div className="p-3 bg-amber-50 rounded-lg flex items-start gap-3 text-amber-800 text-xs">
            <AlertTriangle className="w-5 h-5 shrink-0 text-amber-600 mt-0.5" />
            <div>
              <p className="font-semibold">Confirmação de desativação:</p>
              <p className="mt-1">
                Deseja desativar a torre <strong>"{editingBuilding?.name}"</strong>? Suas unidades cadastradas serão preservadas no histórico.
              </p>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsDeleteBuildingOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={isSubmitting}
              onClick={handleDeleteBuilding}
            >
              {isSubmitting ? 'Desativando...' : 'Confirmar Desativação'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal Nova Unidade */}
      <Modal
        isOpen={isUnitModalOpen}
        onClose={() => setIsUnitModalOpen(false)}
        title="Cadastrar Unidade Autônoma"
      >
        <form onSubmit={handleCreateUnit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Torre ou Bloco
            </label>
            <select
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={selectedBuildingId}
              onChange={(e) => setSelectedBuildingId(e.target.value)}
            >
              <option value="">Sem Torre (Geral)</option>
              {buildings.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Código / Número da Unidade (Zeros à esquerda preservados) *
            </label>
            <input
              type="text"
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 font-mono"
              placeholder="Ex: 101, 002, 12A"
              value={newUnitCode}
              onChange={(e) => setNewUnitCode(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Fração Ideal
            </label>
            <input
              type="number"
              step="0.0001"
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 font-mono"
              placeholder="0.0100"
              value={newIdealFraction}
              onChange={(e) => setNewIdealFraction(e.target.value)}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsUnitModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Cadastrando...' : 'Cadastrar Unidade'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal Editar Unidade */}
      <Modal
        isOpen={isEditUnitOpen}
        onClose={() => setIsEditUnitOpen(false)}
        title="Editar Unidade Autônoma"
      >
        <form onSubmit={handleUpdateUnit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Torre ou Bloco
            </label>
            <select
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={editUnitBuildingId}
              onChange={(e) => setEditUnitBuildingId(e.target.value)}
            >
              <option value="">Sem Torre (Geral)</option>
              {buildings.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Código / Número da Unidade *
            </label>
            <input
              type="text"
              required
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 font-mono"
              value={editUnitCode}
              onChange={(e) => setEditUnitCode(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Fração Ideal
              </label>
              <input
                type="number"
                step="0.0001"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 font-mono"
                value={editUnitFraction}
                onChange={(e) => setEditUnitFraction(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Status
              </label>
              <select
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                value={editUnitStatus}
                onChange={(e) => setEditUnitStatus(e.target.value)}
              >
                <option value="active">Ativa</option>
                <option value="inactive">Inativa</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsEditUnitOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Salvando...' : 'Salvar Alterações'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal Desativar Unidade */}
      <Modal
        isOpen={isDeleteUnitOpen}
        onClose={() => setIsDeleteUnitOpen(false)}
        title="Desativar Unidade Autônoma"
      >
        <div className="space-y-4">
          <div className="p-3 bg-amber-50 rounded-lg flex items-start gap-3 text-amber-800 text-xs">
            <AlertTriangle className="w-5 h-5 shrink-0 text-amber-600 mt-0.5" />
            <div>
              <p className="font-semibold">Confirmação de desativação:</p>
              <p className="mt-1">
                Deseja desativar a unidade <strong>"{editingUnit?.code}"</strong>? Ela será marcada como inativa preservando todo o histórico de vínculos e documentos.
              </p>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsDeleteUnitOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={isSubmitting}
              onClick={handleDeleteUnit}
            >
              {isSubmitting ? 'Desativando...' : 'Confirmar Desativação'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal Saneamento / Excluir Definitivamente Torre */}
      <Modal
        isOpen={isPurgeBuildingOpen}
        onClose={() => setIsPurgeBuildingOpen(false)}
        title="Saneamento Definitivo de Torre / Bloco"
      >
        <div className="space-y-4">
          <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-3 text-rose-900 text-xs">
            <AlertTriangle className="w-5 h-5 shrink-0 text-rose-600 mt-0.5" />
            <div>
              <p className="font-bold uppercase tracking-wider text-rose-700">Ação Irreversível de Saneamento</p>
              <p className="mt-1 leading-relaxed">
                A torre <strong>"{editingBuilding?.name}"</strong> está inativa e será <strong>removida permanentemente</strong> da base de dados.
              </p>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsPurgeBuildingOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={isSubmitting}
              onClick={handlePurgeBuildingConfirm}
            >
              {isSubmitting ? 'Expurgando...' : 'Excluir Definitivamente'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal Saneamento / Excluir Definitivamente Unidade */}
      <Modal
        isOpen={isPurgeUnitOpen}
        onClose={() => setIsPurgeUnitOpen(false)}
        title="Saneamento Definitivo de Unidade Autônoma"
      >
        <div className="space-y-4">
          <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-3 text-rose-900 text-xs">
            <AlertTriangle className="w-5 h-5 shrink-0 text-rose-600 mt-0.5" />
            <div>
              <p className="font-bold uppercase tracking-wider text-rose-700">Ação Irreversível de Saneamento</p>
              <p className="mt-1 leading-relaxed">
                A unidade <strong>"{editingUnit?.code}"</strong> está inativa e será <strong>removida permanentemente</strong> da base de dados.
              </p>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsPurgeUnitOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={isSubmitting}
              onClick={handlePurgeUnitConfirm}
            >
              {isSubmitting ? 'Expurgando...' : 'Excluir Definitivamente'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal Gerador de Apartamentos em Lote */}
      <Modal
        isOpen={isBatchModalOpen}
        onClose={() => setIsBatchModalOpen(false)}
        title="Gerador de Torres e Apartamentos em Lote"
      >
        <form onSubmit={handleBatchGenerate} className="space-y-4">
          <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-xl text-xs text-indigo-900 leading-relaxed">
            <div className="flex items-center gap-1.5 font-bold mb-1">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <span>Numeração Padronizada Inteligente</span>
            </div>
            Gere todos os apartamentos do prédio de uma só vez. O sistema usa o andar como prefixo e a sequência de apartamentos como sufixo (ex: 3º andar com 6 por andar cria <strong>301, 302, 303, 304, 305, 306</strong>).
          </div>

          {/* Seleção de Torre: Existente ou Nova */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Torre / Bloco de Destino *
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setBatchMode('new')}
                className={`py-2 px-3 text-xs font-semibold rounded-lg border transition ${
                  batchMode === 'new'
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                }`}
              >
                + Criar Nova Torre
              </button>
              <button
                type="button"
                disabled={buildings.length === 0}
                onClick={() => setBatchMode('existing')}
                className={`py-2 px-3 text-xs font-semibold rounded-lg border transition ${
                  batchMode === 'existing'
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50 disabled:opacity-50'
                }`}
              >
                Torre Já Existente {buildings.length > 0 ? `(${buildings.length})` : ''}
              </button>
            </div>

            {batchMode === 'new' ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Nome da Torre *</label>
                  <input
                    type="text"
                    required
                    placeholder="Ex: Torre Alpha, Bloco A"
                    className="w-full text-xs border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-indigo-500"
                    value={batchNewBuildingName}
                    onChange={(e) => setBatchNewBuildingName(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Código (Opcional)</label>
                  <input
                    type="text"
                    placeholder="Ex: ALPHA"
                    className="w-full text-xs border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                    value={batchNewBuildingCode}
                    onChange={(e) => setBatchNewBuildingCode(e.target.value)}
                  />
                </div>
              </div>
            ) : (
              <div className="pt-1">
                <label className="block text-[11px] font-medium text-slate-600 mb-1">Selecione a Torre Existente *</label>
                <select
                  required
                  className="w-full text-xs border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-indigo-500"
                  value={batchBuildingId}
                  onChange={(e) => setBatchBuildingId(e.target.value)}
                >
                  <option value="">Selecione uma torre cadastrada...</option>
                  {buildings.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name} (Código: {b.code})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Parâmetros dos Andares e Unidades */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Andar Inicial *
              </label>
              <input
                type="number"
                required
                min="0"
                max="100"
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-center"
                value={batchStartFloor}
                onChange={(e) => setBatchStartFloor(e.target.value)}
              />
              <span className="text-[10px] text-slate-400 block mt-0.5 text-center">Ex: 1 ou 3</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Andar Término *
              </label>
              <input
                type="number"
                required
                min="0"
                max="100"
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-center"
                value={batchEndFloor}
                onChange={(e) => setBatchEndFloor(e.target.value)}
              />
              <span className="text-[10px] text-slate-400 block mt-0.5 text-center">Ex: 15 ou 20</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Aptos p/ Andar *
              </label>
              <input
                type="number"
                required
                min="1"
                max="50"
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-center"
                value={batchUnitsPerFloor}
                onChange={(e) => setBatchUnitsPerFloor(e.target.value)}
              />
              <span className="text-[10px] text-slate-400 block mt-0.5 text-center">Ex: 4 ou 6</span>
            </div>
          </div>

          {/* Painel de Live Preview */}
          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-700">Total de Apartamentos a Gerar:</span>
              <span className="font-bold text-sm text-indigo-700 font-mono bg-indigo-50 px-2.5 py-0.5 rounded-md border border-indigo-200">
                {totalBatchUnits} Unidades
              </span>
            </div>

            {totalBatchUnits > 0 && previewCodes.length > 0 && (
              <div className="text-[11px] text-slate-500 pt-1 border-t border-slate-200/80">
                <span className="font-medium text-slate-700 block mb-1">Amostra de numeração gerada:</span>
                <div className="flex flex-wrap gap-1">
                  {previewCodes.map((code) => (
                    <span
                      key={code}
                      className="px-1.5 py-0.5 bg-white border border-slate-200 rounded text-slate-800 font-mono text-[10px]"
                    >
                      {code}
                    </span>
                  ))}
                  {totalBatchUnits > previewCodes.length && (
                    <span className="text-slate-400 text-[10px] self-center">... e mais {totalBatchUnits - previewCodes.length}</span>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsBatchModalOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={isSubmittingBatch || totalBatchUnits <= 0}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              {isSubmittingBatch ? 'Gerando Lote...' : `Criar ${totalBatchUnits} Apartamentos`}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
