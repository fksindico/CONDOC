import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { History, Shield, Lock, Search, Filter, Loader2, Info } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { Breadcrumb } from '@/components/ui/Breadcrumb';
import { formatDatePtBr } from '@/lib/utils';

interface AuditEvent {
  id: string;
  condominium_id: string;
  actor_account_id: string;
  actor_name?: string;
  actor_email?: string;
  target_type: string;
  target_id: string;
  purpose: string;
  created_at: string;
}

export const AuditLogsPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const [logs, setLogs] = useState<AuditEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeCondominiumId) return;
    setIsLoading(true);
    setError(null);
    api.get<AuditEvent[]>(`/condominiums/${activeCondominiumId}/audit-logs`)
      .then((res) => {
        setLogs(res.data || []);
      })
      .catch((err) => {
        console.error('Falha ao carregar trilha de auditoria:', err);
        setError('Não foi possível carregar os registros de auditoria em tempo real.');
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [activeCondominiumId]);

  return (
    <div className="space-y-6 animate-fade-in">
      <Breadcrumb
        items={[
          { label: 'Administração' },
          { label: 'Trilha de Auditoria' },
        ]}
        showHome
      />

      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Trilha Imutável de Auditoria</h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Histórico perene e inviolável de todas as ações sensíveis, validações e consultas de identidade (S21A).
        </p>
      </div>

      <Alert variant="info" title="Inviolabilidade Arquitetural (ADR-004 / LGPD)">
        Os registros de auditoria são imutáveis e protegidos no banco de dados. Nenhuma ação administrativa permite
        edição ou expurgo de eventos gravados.
      </Alert>

      {error && (
        <Alert variant="error" title="Erro de Comunicação">
          {error}
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center justify-between">
            <span>Eventos de Auditoria Registrados</span>
            <Badge variant="outline" className="text-slate-600">
              Somente Leitura
            </Badge>
          </CardTitle>
          <CardDescription>
            Rastreamento de acessos a dados pessoais, decisões editoriais e eventos homologados.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center p-12 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin mb-3 text-brand-600" />
              <p className="text-sm font-medium">Carregando trilha de auditoria...</p>
            </div>
          ) : logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-slate-500">
              <Shield className="w-10 h-10 text-slate-300 mb-3" />
              <p className="text-sm font-semibold text-slate-700">Nenhum evento registrado até o momento</p>
              <p className="text-xs text-slate-400 mt-1 text-center max-w-sm">
                Eventos de auditoria aparecerão automaticamente nesta trilha conforme ações restritas forem executadas.
              </p>
            </div>
          ) : (
            <>
              {/* Visualização Desktop: Tabela */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider">
                    <tr>
                      <th className="px-6 py-3">Timestamp</th>
                      <th className="px-6 py-3">Ator / Usuário</th>
                      <th className="px-6 py-3">Tipo de Alvo</th>
                      <th className="px-6 py-3">Justificativa / Finalidade</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {logs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-3.5 text-slate-500 font-mono">
                          {formatDatePtBr(log.created_at)}
                        </td>
                        <td className="px-6 py-3.5 font-semibold text-slate-900">
                          {log.actor_name || log.actor_email || 'Dr. Síndico Geral'}
                        </td>
                        <td className="px-6 py-3.5">
                          <Badge variant="warning">{log.target_type || 'identity.access'}</Badge>
                        </td>
                        <td className="px-6 py-3.5 text-slate-700">
                          {log.purpose}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Visualização Mobile: Cards (M7.1) */}
              <div className="md:hidden divide-y divide-slate-100 p-4 space-y-3">
                {logs.map((log) => (
                  <div key={log.id} className="pt-3 first:pt-0 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-900">
                        {log.actor_name || log.actor_email || 'Dr. Síndico Geral'}
                      </span>
                      <Badge variant="warning">{log.target_type || 'identity.access'}</Badge>
                    </div>
                    <p className="text-slate-700">{log.purpose}</p>
                    <p className="text-slate-400 font-mono text-[11px]">
                      {formatDatePtBr(log.created_at)}
                    </p>
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
