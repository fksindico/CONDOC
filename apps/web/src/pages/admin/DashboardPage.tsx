import React from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { useAuth } from '@/contexts/AuthContext';
import { Link } from 'react-router-dom';
import {
  FileText,
  Sliders,
  Users,
  MessageSquare,
  ArrowRight,
  ShieldAlert,
  Download,
  FolderGit2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export const DashboardPage: React.FC = () => {
  const { activeCondominium } = useTenant();
  const { isSindico } = useAuth();

  const metrics = [
    {
      label: 'Projetos Normativos',
      value: '2',
      detail: 'Convenção e Regimento em revisão',
      icon: FolderGit2,
      color: 'text-blue-600 bg-blue-50 border-blue-200',
    },
    {
      label: 'Campanhas em Consulta',
      value: '1 Ativa',
      detail: 'Consulta Pública Marco v1.0',
      icon: Sliders,
      color: 'text-indigo-600 bg-indigo-50 border-indigo-200',
    },
    {
      label: 'Participantes Habilitados',
      value: '142',
      detail: 'Moradores com vínculo validado',
      icon: Users,
      color: 'text-emerald-600 bg-emerald-50 border-emerald-200',
    },
    {
      label: 'Fila de Moderação (4D)',
      value: '8 Pendentes',
      detail: 'Sugestões aguardando análise',
      icon: MessageSquare,
      color: 'text-amber-600 bg-amber-50 border-amber-200',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header do Painel */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Painel da Gestão</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            {activeCondominium?.name || 'Condomínio Selecionado'} — Governança documental e participação consultiva.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Link to="/painel/projetos">
            <Button size="sm">
              <FileText className="w-4 h-4 mr-1.5" />
              <span>Ver Minutas</span>
            </Button>
          </Link>
          <Link to="/painel/exportacoes">
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4 mr-1.5" />
              <span>Exportações</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Grid de Métricas Principais (UI-05: sem PII ou contatos expostos) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((m, idx) => {
          const Icon = m.icon;
          return (
            <Card key={idx}>
              <CardContent className="p-5 flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium text-slate-500">{m.label}</p>
                  <h3 className="text-2xl font-bold text-slate-900 mt-1">{m.value}</h3>
                  <p className="text-[11px] text-slate-500 mt-1">{m.detail}</p>
                </div>
                <div className={`p-2.5 rounded-xl border ${m.color}`}>
                  <Icon className="w-5 h-5 text-current" />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Ações e Módulos Rápidos */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Ações do Síndico e Gestão</CardTitle>
            <CardDescription>Atalhos rápidos para fluxos de trabalho frequentes.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5">
            <Link
              to="/painel/sugestoes"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-100 transition-colors text-xs sm:text-sm"
            >
              <span className="font-medium text-slate-800">Moderação de Sugestões em 4 Dimensões</span>
              <ArrowRight className="w-4 h-4 text-slate-400" />
            </Link>
            <Link
              to="/painel/moradores/validacoes"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-100 transition-colors text-xs sm:text-sm"
            >
              <span className="font-medium text-slate-800">Fila de Validação Documental de Moradores</span>
              <ArrowRight className="w-4 h-4 text-slate-400" />
            </Link>
            <Link
              to="/painel/convites"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-100 transition-colors text-xs sm:text-sm"
            >
              <span className="font-medium text-slate-800">Emissão e Gestão de Convites de Acesso</span>
              <ArrowRight className="w-4 h-4 text-slate-400" />
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Governança e Integridade</CardTitle>
            <CardDescription>Salvaguardas de conformidade com o PRD Mestre v3.0.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs text-slate-600 leading-relaxed">
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex gap-2.5">
              <ShieldAlert className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-slate-900">Vedações Deliberativas Ativas</p>
                <p className="mt-0.5">
                  A plataforma opera em regime estritamente consultivo. Recursos deliberativos e apurações vinculantes
                  são terminantemente desabilitados.
                </p>
              </div>
            </div>
            <p>
              Todos os acessos a dados de identificação pessoal de moradores em sugestões exigem justificativa e
              são auditados de forma permanente.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
