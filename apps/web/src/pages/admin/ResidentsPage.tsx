import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/lib/api';
import type { UnitMembership } from '@condc/api-contracts';
import { Users, UserPlus, Search, Phone, Mail, Home, ShieldAlert } from 'lucide-react';
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
      // CA-02: Cria pré-cadastro manual sem criar credencial de acesso nem enviar convite
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
            Cadastros prévios e validações de residência (CA-02, CA-13, CA-14).
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
                    <th className="px-6 py-3">Morador</th>
                    <th className="px-6 py-3">Unidade</th>
                    <th className="px-6 py-3">Relação / Vínculo</th>
                    <th className="px-6 py-3">Status de Verificação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filtered.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-3.5">
                        <span className="font-semibold text-slate-900 text-sm block">
                          {m.resident_name || 'Morador'}
                        </span>
                      </td>
                      <td className="px-6 py-3.5">
                        <span className="font-mono font-semibold text-slate-800 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                          {m.unit_code || '—'}
                        </span>
                      </td>
                      <td className="px-6 py-3.5 text-slate-600 capitalize">
                        {(m.category || 'proprietario_residente').replace('_', ' ')}
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
                    </tr>
                  ))}
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
    </div>
  );
};
