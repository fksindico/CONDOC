import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { Send, Plus, KeyRound, Copy, Check, Ban, QrCode } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';

export const InvitationsPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const [invitations, setInvitations] = useState<any[]>([]);
  const [units, setUnits] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Modal Novo Convite
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [kind, setKind] = useState<'individual_padrao' | 'unidade_fixa' | 'amplo'>('unidade_fixa');
  const [targetUnitId, setTargetUnitId] = useState('');
  const [expectedContact, setExpectedContact] = useState('');
  const [expiresInDays, setExpiresInDays] = useState(7);
  const [maxRedemptions, setMaxRedemptions] = useState(1);
  const [isCreating, setIsCreating] = useState(false);
  const [createdInviteUrl, setCreatedInviteUrl] = useState('');

  // Modal Revogação
  const [revokeInviteId, setRevokeInviteId] = useState<string | null>(null);
  const [revokeReason, setRevokeReason] = useState('');
  const [isRevoking, setIsRevoking] = useState(false);

  const fetchInvitations = async () => {
    if (!activeCondominiumId) return;
    setIsLoading(true);
    setError('');
    try {
      const [resI, resU] = await Promise.all([
        api.get<any[]>(`/condominiums/${activeCondominiumId}/invitations`),
        api.get<any[]>(`/condominiums/${activeCondominiumId}/units`),
      ]);
      setInvitations(resI.data || []);
      setUnits(resU.data || []);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar convites.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInvitations();
  }, [activeCondominiumId]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId) return;
    setIsCreating(true);

    try {
      const res = await api.post<any>(`/condominiums/${activeCondominiumId}/invitations`, {
        kind,
        target_unit_id: targetUnitId || null,
        expected_contact: expectedContact.trim() || undefined,
        expires_in_days: expiresInDays,
        max_redemptions: maxRedemptions,
      });

      const invite = res.data;
      if (invite.invite_url) {
        setCreatedInviteUrl(invite.invite_url);
      }
      setIsModalOpen(false);
      fetchInvitations();
    } catch (err: any) {
      alert(err.message || 'Erro ao emitir convite.');
    } finally {
      setIsCreating(false);
    }
  };

  const handleRevoke = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !revokeInviteId) return;
    if (revokeReason.trim().length < 5) {
      alert('O motivo deve conter no mínimo 5 caracteres.');
      return;
    }
    setIsRevoking(true);

    try {
      // CA-11: Revogação bloqueia resgate sem apagar histórico
      await api.post(`/condominiums/${activeCondominiumId}/invitations/${revokeInviteId}/revoke`, {
        reason: revokeReason.trim(),
      });
      setRevokeInviteId(null);
      setRevokeReason('');
      fetchInvitations();
    } catch (err: any) {
      alert(err.message || 'Erro ao revogar convite.');
    } finally {
      setIsRevoking(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Convites de Acesso</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Emissão e controle de tokens de convite para participação dos moradores (CA-07 a CA-11).
          </p>
        </div>
        <Button size="sm" onClick={() => setIsModalOpen(true)}>
          <Plus className="w-4 h-4 mr-1.5" />
          <span>Novo Convite</span>
        </Button>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {createdInviteUrl && (
        <Alert variant="success" title="Convite Emitido com Sucesso!">
          <div className="space-y-2 mt-1">
            <p className="text-xs">Copie o link abaixo para enviar ao morador:</p>
            <div className="flex items-center gap-2 bg-white/80 p-2 rounded-lg border border-emerald-300">
              <input
                type="text"
                readOnly
                value={createdInviteUrl}
                className="flex-1 text-xs bg-transparent outline-none font-mono text-slate-800"
              />
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  navigator.clipboard.writeText(createdInviteUrl);
                  alert('Link copiado para a área de transferência!');
                }}
              >
                <Copy className="w-3.5 h-3.5 mr-1" />
                <span>Copiar</span>
              </Button>
            </div>
          </div>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Convites Emitidos ({invitations.length})</CardTitle>
          <CardDescription>
            Acompanhe resgates, validade e revogações com trilha de auditoria.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Modalidade</th>
                  <th className="px-6 py-3">Unidade Alvo</th>
                  <th className="px-6 py-3">Contato Esperado</th>
                  <th className="px-6 py-3">Resgates</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3 text-right">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {invitations.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                      Nenhum convite emitido até o momento.
                    </td>
                  </tr>
                ) : (
                  invitations.map((inv) => (
                    <tr key={inv.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-3.5 font-semibold text-slate-800 capitalize">
                        {(inv.kind || 'padrao').replace('_', ' ')}
                      </td>
                      <td className="px-6 py-3.5 font-mono text-slate-700">
                        {inv.unit_code ? `Unidade ${inv.unit_code}` : 'Qualquer Unidade'}
                      </td>
                      <td className="px-6 py-3.5 text-slate-600">{inv.expected_contact || '—'}</td>
                      <td className="px-6 py-3.5 font-medium">
                        {inv.redemption_count || 0} / {inv.max_redemptions || 1}
                      </td>
                      <td className="px-6 py-3.5">
                        <Badge
                          variant={
                            inv.status === 'active'
                              ? 'success'
                              : inv.status === 'revoked'
                              ? 'danger'
                              : 'default'
                          }
                        >
                          {inv.status === 'active' ? 'Ativo' : inv.status === 'revoked' ? 'Revogado' : 'Expirado'}
                        </Badge>
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        {inv.status === 'active' && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-rose-600 hover:text-rose-700 hover:bg-rose-50"
                            onClick={() => setRevokeInviteId(inv.id)}
                          >
                            <Ban className="w-3.5 h-3.5 mr-1" />
                            <span>Revogar</span>
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Modal Novo Convite */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Emitir Novo Convite de Acesso"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Modalidade do Convite *
            </label>
            <select
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              value={kind}
              onChange={(e: any) => setKind(e.target.value)}
            >
              <option value="unidade_fixa">Por Unidade Fixa (Convite restrito a um apartamento)</option>
              <option value="individual_padrao">Individual Pré-Conferido (Exige contato previsto)</option>
              <option value="amplo">Amplo (Divulgação geral com validação posterior)</option>
            </select>
          </div>

          {kind === 'unidade_fixa' && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Unidade de Destino *
              </label>
              <select
                required
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                value={targetUnitId}
                onChange={(e) => setTargetUnitId(e.target.value)}
              >
                <option value="">Selecione a unidade...</option>
                {units.map((u) => (
                  <option key={u.id} value={u.id}>
                    Unidade {u.code || u.unit_number}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Contato Previsto / Esperado (Opcional)
            </label>
            <input
              type="text"
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="E-mail ou Telefone do morador"
              value={expectedContact}
              onChange={(e) => setExpectedContact(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Validade (Dias)
              </label>
              <input
                type="number"
                min={1}
                max={90}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                value={expiresInDays}
                onChange={(e) => setExpiresInDays(parseInt(e.target.value) || 7)}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Máximo de Resgates
              </label>
              <input
                type="number"
                min={1}
                max={5000}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                value={maxRedemptions}
                onChange={(e) => setMaxRedemptions(parseInt(e.target.value) || 1)}
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" isLoading={isCreating}>
              Gerar Convite
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal Revogação */}
      {revokeInviteId && (
        <Modal
          isOpen={true}
          onClose={() => setRevokeInviteId(null)}
          title="Revogar Convite de Acesso"
          description="A revogação impede novos resgates mas preserva o histórico de contas já ativadas (CA-11)."
        >
          <form onSubmit={handleRevoke} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Motivo da Revogação (Mínimo 5 caracteres) *
              </label>
              <textarea
                required
                rows={3}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="Ex: Envio incorreto de token para unidade desocupada..."
                value={revokeReason}
                onChange={(e) => setRevokeReason(e.target.value)}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setRevokeInviteId(null)}>
                Cancelar
              </Button>
              <Button type="submit" variant="destructive" isLoading={isRevoking}>
                Confirmar Revogação
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
