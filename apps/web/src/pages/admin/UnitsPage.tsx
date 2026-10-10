import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import type { Building, Unit } from '@condc/api-contracts';
import { Layers, Plus, Building2, Check, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';

export const UnitsPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Modais de Criação
  const [isBuildingModalOpen, setIsBuildingModalOpen] = useState(false);
  const [isUnitModalOpen, setIsUnitModalOpen] = useState(false);
  const [newBuildingName, setNewBuildingName] = useState('');
  const [newBuildingCode, setNewBuildingCode] = useState('');
  const [newUnitCode, setNewUnitCode] = useState('');
  const [selectedBuildingId, setSelectedBuildingId] = useState('');
  const [newIdealFraction, setNewIdealFraction] = useState('0.0100');

  const fetchData = async () => {
    if (!activeCondominiumId) return;
    setIsLoading(true);
    setError('');
    try {
      const [resB, resU] = await Promise.all([
        api.get<Building[]>(`/condominiums/${activeCondominiumId}/buildings`),
        api.get<Unit[]>(`/condominiums/${activeCondominiumId}/units`),
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

  const handleCreateBuilding = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId) return;
    try {
      await api.post(`/condominiums/${activeCondominiumId}/buildings`, {
        name: newBuildingName.trim(),
        code: newBuildingCode.trim() || newBuildingName.trim().toUpperCase(),
        kind: 'tower',
      });
      setIsBuildingModalOpen(false);
      setNewBuildingName('');
      setNewBuildingCode('');
      fetchData();
    } catch (err: any) {
      alert(err.message || 'Erro ao criar torre/bloco.');
    }
  };

  const handleCreateUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId) return;
    try {
      await api.post(`/condominiums/${activeCondominiumId}/units`, {
        building_id: selectedBuildingId || null,
        code: newUnitCode.trim(),
        ideal_fraction: parseFloat(newIdealFraction) || 0.01,
      });
      setIsUnitModalOpen(false);
      setNewUnitCode('');
      fetchData();
    } catch (err: any) {
      alert(err.message || 'Erro ao criar unidade.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Torres & Unidades</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Estrutura física do condomínio para vinculação e auditoria de moradores.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setIsBuildingModalOpen(true)}>
            <Building2 className="w-4 h-4 mr-1.5" />
            <span>Nova Torre/Bloco</span>
          </Button>
          <Button size="sm" onClick={() => setIsUnitModalOpen(true)}>
            <Plus className="w-4 h-4 mr-1.5" />
            <span>Nova Unidade</span>
          </Button>
        </div>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {/* Grid de Torres / Blocos */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {buildings.map((b) => {
          const countUnits = units.filter((u) => u.building_id === b.id).length;
          return (
            <Card key={b.id}>
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-slate-900 text-sm">{b.name}</h4>
                  <p className="text-xs text-slate-500 font-mono mt-0.5">Código: {b.code || '—'}</p>
                  <p className="text-xs text-slate-600 mt-2 font-medium">
                    {countUnits} {countUnits === 1 ? 'unidade' : 'unidades'} cadastradas
                  </p>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-100 text-slate-600">
                  <Building2 className="w-5 h-5" />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Tabela de Unidades */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Unidades Autônomas ({units.length})</CardTitle>
          <CardDescription>
            Preservação de zeros à esquerda e frações ideais (sem peso eleitoral).
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Código / Unidade</th>
                  <th className="px-6 py-3">Torre / Bloco</th>
                  <th className="px-6 py-3">Fração Ideal</th>
                  <th className="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {units.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                      Nenhuma unidade cadastrada. Crie uma unidade ou use o assistente de importação.
                    </td>
                  </tr>
                ) : (
                  units.map((u) => {
                    const b = buildings.find((x) => x.id === u.building_id);
                    return (
                      <tr key={u.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-3 font-semibold text-slate-900 font-mono text-sm">
                          {u.code || u.unit_number}
                        </td>
                        <td className="px-6 py-3 text-slate-700">{b ? b.name : 'Geral'}</td>
                        <td className="px-6 py-3 text-slate-600 font-mono">
                          {u.ideal_fraction ? Number(u.ideal_fraction).toFixed(4) : '—'}
                        </td>
                        <td className="px-6 py-3">
                          <Badge variant="success">Ativa</Badge>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
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
            <Button type="submit">Cadastrar Torre</Button>
          </div>
        </form>
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
            <Button type="submit">Cadastrar Unidade</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
