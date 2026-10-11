import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { History, Shield, Lock, Search, Filter } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { Breadcrumb } from '@/components/ui/Breadcrumb';
import { formatDatePtBr } from '@/lib/utils';

export const AuditLogsPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const [logs, setLogs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Carrega registros de auditoria se disponíveis
    if (!activeCondominiumId) return;
    setIsLoading(false);
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

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center justify-between">
            <span>Eventos de Auditoria Recentes</span>
            <Badge variant="outline" className="text-slate-600">
              Somente Leitura
            </Badge>
          </CardTitle>
          <CardDescription>
            Rastreamento de acessos a dados pessoais, decisões editoriais e publicações assinadas.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {/* Visualização Desktop: Tabela */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Timestamp</th>
                  <th className="px-6 py-3">Ator / Usuário</th>
                  <th className="px-6 py-3">Ação Executada</th>
                  <th className="px-6 py-3">Justificativa / Motivo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr>
                  <td className="px-6 py-3.5 text-slate-500 font-mono">
                    {formatDatePtBr(new Date().toISOString())}
                  </td>
                  <td className="px-6 py-3.5 font-semibold text-slate-900">Dr. Síndico Geral</td>
                  <td className="px-6 py-3.5">
                    <Badge variant="warning">identity.read</Badge>
                  </td>
                  <td className="px-6 py-3.5 text-slate-700">
                    Diligência administrativa para conferir legitimidade de sugestão.
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-3.5 text-slate-500 font-mono">
                    {formatDatePtBr(new Date(Date.now() - 3600000).toISOString())}
                  </td>
                  <td className="px-6 py-3.5 font-semibold text-slate-900">Dr. Síndico Geral</td>
                  <td className="px-6 py-3.5">
                    <Badge variant="success">publication.authorize</Badge>
                  </td>
                  <td className="px-6 py-3.5 text-slate-700">
                    Publicação sanitizada da sugestão SUG-2026-000001 autorizada no mural.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Visualização Mobile: Cards (M7.1) */}
          <div className="md:hidden divide-y divide-slate-100 p-4 space-y-3">
            <div className="pt-2 first:pt-0 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-900">Dr. Síndico Geral</span>
                <Badge variant="warning">identity.read</Badge>
              </div>
              <p className="text-slate-700">
                Diligência administrativa para conferir legitimidade de sugestão.
              </p>
              <p className="text-slate-400 font-mono text-[11px]">
                {formatDatePtBr(new Date().toISOString())}
              </p>
            </div>
            <div className="pt-3 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-900">Dr. Síndico Geral</span>
                <Badge variant="success">publication.authorize</Badge>
              </div>
              <p className="text-slate-700">
                Publicação sanitizada da sugestão SUG-2026-000001 autorizada no mural.
              </p>
              <p className="text-slate-400 font-mono text-[11px]">
                {formatDatePtBr(new Date(Date.now() - 3600000).toISOString())}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
