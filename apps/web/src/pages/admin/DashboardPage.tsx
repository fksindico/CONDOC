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
      detail: 'Convenção e Regimento em revisão ativa',
      icon: FolderGit2,
      color: 'text-brand-800 bg-brand-50 border-brand-200',
    },
    {
      label: 'Campanhas em Consulta',
      value: '1 Ativa',
      detail: 'Consulta Pública Marco v1.0',
      icon: Sliders,
      color: 'text-brand-700 bg-blue-50 border-blue-200',
    },
    {
      label: 'Participantes Habilitados',
      value: '142',
      detail: 'Moradores com vínculo validado',
      icon: Users,
      color: 'text-emerald-800 bg-emerald-50 border-emerald-200',
    },
    {
      label: 'Fila de Moderação (4D)',
      value: '8 Pendentes',
      detail: 'Sugestões aguardando análise',
      icon: MessageSquare,
      color: 'text-gold-700 bg-gold-50 border-gold-200',
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header do Painel */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Painel da Gestão</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            {activeCondominium?.name || 'Condomínio Selecionado'} — Governança documental e participação consultiva.
          </p>
        </div>
        <div className="flex items-center gap-2.5 flex-wrap">
          <Link to="/painel/consultas">
            <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white">
              <FileText className="w-4 h-4 mr-1.5" aria-hidden="true" />
              <span>Consultas em PDF</span>
            </Button>
          </Link>
          <Link to="/painel/projetos">
            <Button variant="outline" size="sm">
              <FolderGit2 className="w-4 h-4 mr-1.5" aria-hidden="true" />
              <span>Minutas</span>
            </Button>
          </Link>
          <Link to="/painel/exportacoes">
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4 mr-1.5" aria-hidden="true" />
              <span>Exportações</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Destaque: Fluxo Simplificado de Revisão Participativa em PDF */}
      <div className="bg-gradient-to-r from-indigo-900 via-slate-900 to-indigo-950 rounded-2xl p-5 text-white shadow-sm border border-indigo-800/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 uppercase tracking-wider inline-block">
            Novo Fluxo Ágil
          </span>
          <h2 className="text-base sm:text-lg font-bold text-white">
            Consultas Públicas em PDF & Coleta Direta de Sugestões
          </h2>
          <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
            Faça upload do Regimento ou Convenção em PDF e gere um link compartilhado para WhatsApp. Os moradores participam com visualização lado a lado e você exporta o relatório consolidado para Excel/CSV sem fricção de cadastros.
          </p>
        </div>
        <Link to="/painel/consultas" className="shrink-0">
          <button className="px-4 py-2.5 bg-indigo-500 hover:bg-indigo-400 text-white font-semibold text-xs rounded-xl shadow-xs transition flex items-center gap-2">
            <span>Acessar Consultas</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </Link>
      </div>

      {/* Grid de Métricas Principais (UI-05: sem PII ou contatos expostos) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((m, idx) => {
          const Icon = m.icon;
          return (
            <Card key={idx} className="animate-fade-in-up hover:border-slate-300 hover:shadow-md transition-all duration-200">
              <CardContent className="p-5 flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium text-slate-500">{m.label}</p>
                  <h3 className="text-2xl font-bold text-slate-900 mt-1">{m.value}</h3>
                  <p className="text-xs text-slate-500 mt-1">{m.detail}</p>
                </div>
                <div className={`p-2.5 rounded-xl border ${m.color}`}>
                  <Icon className="w-5 h-5 text-current" aria-hidden="true" />
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
            <CardDescription>Atalhos rápidos para fluxos de trabalho normativos e prediais.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5">
            <Link
              to="/painel/consultas"
              className="flex items-center justify-between p-3 rounded-lg border border-indigo-200 bg-indigo-50/50 hover:bg-indigo-100/60 transition-colors text-xs sm:text-sm group"
            >
              <div className="flex items-center gap-2.5">
                <FileText className="w-4 h-4 text-indigo-700" aria-hidden="true" />
                <span className="font-semibold text-indigo-950">Consultas em PDF (Links Compartilháveis)</span>
              </div>
              <ArrowRight className="w-4 h-4 text-indigo-500 group-hover:translate-x-0.5 transition-transform" aria-hidden="true" />
            </Link>
            <Link
              to="/painel/projetos"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-100 transition-colors text-xs sm:text-sm group"
            >
              <div className="flex items-center gap-2.5">
                <FolderGit2 className="w-4 h-4 text-brand-800" aria-hidden="true" />
                <span className="font-medium text-slate-800 group-hover:text-brand-900">Estação de Redação Normativa (Minutas)</span>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" aria-hidden="true" />
            </Link>
            <Link
              to="/painel/sugestoes"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-100 transition-colors text-xs sm:text-sm group"
            >
              <div className="flex items-center gap-2.5">
                <MessageSquare className="w-4 h-4 text-gold-700" aria-hidden="true" />
                <span className="font-medium text-slate-800 group-hover:text-gold-900">Moderação de Sugestões em 4 Dimensões</span>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" aria-hidden="true" />
            </Link>
            <Link
              to="/painel/condominios"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-100 transition-colors text-xs sm:text-sm group"
            >
              <div className="flex items-center gap-2.5">
                <Users className="w-4 h-4 text-emerald-700" aria-hidden="true" />
                <span className="font-medium text-slate-800 group-hover:text-emerald-900">Gestão Predial & Saneamento Cadastral</span>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" aria-hidden="true" />
            </Link>
            <Link
              to="/painel/exportacoes"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-100 transition-colors text-xs sm:text-sm group"
            >
              <div className="flex items-center gap-2.5">
                <Download className="w-4 h-4 text-blue-700" aria-hidden="true" />
                <span className="font-medium text-slate-800 group-hover:text-blue-900">Central de Exportações & Selo SHA-256</span>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" aria-hidden="true" />
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
              <ShieldAlert className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" aria-hidden="true" />
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
