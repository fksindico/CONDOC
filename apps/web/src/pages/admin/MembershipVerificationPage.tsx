import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/lib/api';
import { UserCheck, ShieldCheck, CheckCircle2, XCircle, AlertCircle, FileText } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';
import { TableSkeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';

export const MembershipVerificationPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const { toast } = useToast();
  const [pendingMemberships, setPendingMemberships] = useState<any[]>([]);
  const [selectedMembership, setSelectedMembership] = useState<any | null>(null);
  const [actionType, setActionType] = useState<'validado' | 'recusado'>('validado');
  const [method, setMethod] = useState<'documento' | 'declaracao_sindico' | 'presencial'>('documento');
  const [reason, setReason] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const fetchPending = async () => {
    if (!activeCondominiumId) return;
    setIsLoading(true);
    setError('');
    try {
      const res = await api.get<any[]>(`/condominiums/${activeCondominiumId}/memberships`);
      // Filtra os vínculos pendentes de validação documental
      const pending = (res.data || []).filter((m: any) => m.verification_status === 'pendente' || m.verification_status === 'em_analise');
      setPendingMemberships(pending);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar fila de validação.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPending();
  }, [activeCondominiumId]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !selectedMembership) return;
    if (reason.trim().length < 5) {
      toast.error('A justificativa deve conter pelo menos 5 caracteres.');
      return;
    }
    setIsSubmitting(true);

    try {
      // CA-12 / CA-15: Validação auditada com método e motivo obrigatórios
      await api.post(`/condominiums/${activeCondominiumId}/memberships/${selectedMembership.id}/verify`, {
        new_status: actionType,
        method,
        reason: reason.trim(),
      });
      setSelectedMembership(null);
      setReason('');
      toast.success(`Vínculo ${actionType === 'validado' ? 'validado' : 'recusado'} com sucesso!`);
      fetchPending();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao processar validação.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
          Validação Documental de Vínculos
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Confira e valide formalmente os vínculos declarados de residência antes de liberar participação (CA-12, CA-15).
        </p>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center justify-between">
            <span>Vínculos Aguardando Verificação ({pendingMemberships.length})</span>
            <Badge variant="warning">{pendingMemberships.length} Pendentes</Badge>
          </CardTitle>
          <CardDescription>
            A verificação gera evento imutável na trilha de auditoria contendo o método e o parecer da gestão.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <TableSkeleton rows={3} />
          ) : pendingMemberships.length === 0 ? (
            <div className="p-6">
              <EmptyState
                icon={UserCheck}
                title="Fila de validação limpa"
                description="Não há vínculos de residência pendentes de conferência no momento. Todos os cadastros submetidos foram processados."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-3">Morador</th>
                    <th className="px-6 py-3">Unidade</th>
                    <th className="px-6 py-3">Relação Declarada</th>
                    <th className="px-6 py-3">Status Atual</th>
                    <th className="px-6 py-3 text-right">Ação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {pendingMemberships.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-3.5 font-semibold text-slate-900 text-sm">
                        {m.resident_name || 'Morador'}
                      </td>
                      <td className="px-6 py-3.5">
                        <span className="font-mono font-semibold text-slate-800 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                          {m.unit_code || '—'}
                        </span>
                      </td>
                      <td className="px-6 py-3.5 capitalize text-slate-600">
                        {(m.category || 'proprietario_residente').replace('_', ' ')}
                      </td>
                      <td className="px-6 py-3.5">
                        <Badge variant="warning">Pendente</Badge>
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedMembership(m);
                            setActionType('validado');
                          }}
                        >
                          <ShieldCheck className="w-4 h-4 mr-1 text-emerald-600" />
                          <span>Verificar</span>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal de Verificação / Parecer */}
      {selectedMembership && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedMembership(null)}
          title="Verificação de Vínculo Residencial"
          description={`Morador: ${selectedMembership.resident_name} — Unidade ${selectedMembership.unit_code}`}
        >
          <form onSubmit={handleVerify} className="space-y-4">
            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
                <input
                  type="radio"
                  name="actionType"
                  value="validado"
                  checked={actionType === 'validado'}
                  onChange={() => setActionType('validado')}
                />
                <span className="text-emerald-700 font-bold">Validar Vínculo</span>
              </label>
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
                <input
                  type="radio"
                  name="actionType"
                  value="recusado"
                  checked={actionType === 'recusado'}
                  onChange={() => setActionType('recusado')}
                />
                <span className="text-rose-700 font-bold">Recusar Vínculo</span>
              </label>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Método de Verificação Utilizado *
              </label>
              <select
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                value={method}
                onChange={(e: any) => setMethod(e.target.value)}
              >
                <option value="documento">Análise Documental (Escritura, IPTU, Contrato de Locação)</option>
                <option value="declaracao_sindico">Declaração Direta do Síndico / Gestão</option>
                <option value="presencial">Conferência Presencial na Administração</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Parecer / Justificativa Obrigatória (Mínimo 5 caracteres) *
              </label>
              <textarea
                required
                rows={3}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="Ex: Contrato de locação verificado e confrontado com matrícula do imóvel..."
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setSelectedMembership(null)}>
                Cancelar
              </Button>
              <Button type="submit" isLoading={isSubmitting}>
                Confirmar Verificação
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
