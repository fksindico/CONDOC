import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { ShieldCheck, UserPlus, Shield, UserX, Clock, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';
import { formatDateOnly } from '@/lib/utils';

export const TeamPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const [rolesList, setRolesList] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Modal Atribuir Papel
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [accountId, setAccountId] = useState('');
  const [role, setRole] = useState('comissao');
  const [isAssigning, setIsAssigning] = useState(false);

  const fetchRoles = async () => {
    if (!activeCondominiumId) return;
    setIsLoading(true);
    setError('');
    try {
      const res = await api.get<any[]>(`/condominiums/${activeCondominiumId}/roles`);
      setRolesList(res.data || []);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar equipe e permissões.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAssignRole = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !accountId.trim()) return;
    setIsAssigning(true);
    setError('');
    try {
      await api.post(`/condominiums/${activeCondominiumId}/roles`, {
        account_id: accountId.trim(),
        role,
      });
      setIsModalOpen(false);
      setAccountId('');
      await fetchRoles();
    } catch (err: any) {
      setError(err.message || 'Erro ao atribuir papel à equipe.');
    } finally {
      setIsAssigning(false);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, [activeCondominiumId]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Equipe & Permissões</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Gestão de papéis com mandatos delimitados e segregação de autoridade (S20, CA-28).
          </p>
        </div>
        <div>
          <Button
            variant="primary"
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2"
          >
            <UserPlus className="w-4 h-4" />
            <span>Atribuir Papel</span>
          </Button>
        </div>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center justify-between">
            <span>Atribuições de Papel Ativas ({rolesList.length})</span>
            <Badge variant="info">MFA Recomendado</Badge>
          </CardTitle>
          <CardDescription>
            A publicação de versões no portal é restrita com exclusividade ao papel ativo de Síndico.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Membro da Equipe</th>
                  <th className="px-6 py-3">Papel / Função</th>
                  <th className="px-6 py-3">Vigência Inicial</th>
                  <th className="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rolesList.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                      Nenhum papel administrativo configurado.
                    </td>
                  </tr>
                ) : (
                  rolesList.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-3.5">
                        <span className="font-semibold text-slate-900 text-sm block">{r.account_name || 'Usuário'}</span>
                        <span className="text-xs text-slate-500">{r.account_email || '—'}</span>
                      </td>
                      <td className="px-6 py-3.5">
                        <Badge
                          variant={r.role === 'sindico' ? 'warning' : 'outline'}
                          className="font-mono uppercase text-xs"
                        >
                          {r.role}
                        </Badge>
                      </td>
                      <td className="px-6 py-3.5 text-slate-600">{formatDateOnly(r.valid_from)}</td>
                      <td className="px-6 py-3.5">
                        <Badge variant={r.status === 'active' ? 'success' : 'default'}>
                          {r.status === 'active' ? 'Ativo' : 'Expirado'}
                        </Badge>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Atribuir Papel à Equipe"
      >
        <form onSubmit={handleAssignRole} className="space-y-4">
          <p className="text-xs text-slate-500">
            Conceda mandatos e responsabilidades a membros da gestão condominial.
          </p>
          <div>
            <label htmlFor="accountIdInput" className="block text-xs font-semibold text-slate-700 mb-1">
              ID da Conta (UUID do Usuário)
            </label>
            <input
              id="accountIdInput"
              type="text"
              required
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              placeholder="Ex: 550e8400-e29b-41d4-a716-446655440000"
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label htmlFor="roleSelect" className="block text-xs font-semibold text-slate-700 mb-1">
              Papel / Função
            </label>
            <select
              id="roleSelect"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
            >
              <option value="comissao">Membro da Comissão (comissao)</option>
              <option value="conselho">Conselheiro Fiscal / Consultivo (conselho)</option>
              <option value="subsindico">Subsíndico (subsindico)</option>
              <option value="sindico">Síndico (sindico)</option>
              <option value="juridico">Assessor Jurídico (juridico)</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsModalOpen(false)}
              disabled={isAssigning}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={isAssigning || !accountId.trim()}
            >
              {isAssigning ? 'Atribuindo...' : 'Confirmar Atribuição'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
