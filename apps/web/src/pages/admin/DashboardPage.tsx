import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { Link } from 'react-router-dom';
import {
  FileText,
  Sliders,
  Users,
  MessageSquare,
  ArrowRight,
  ShieldAlert,
  Building2,
  Layers,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export const DashboardPage: React.FC = () => {
  const { activeCondominium, activeCondominiumId } = useTenant();
  const { isSindico } = useAuth();

  const [metricsData, setMetricsData] = useState<{
    consultations_open: number;
    consultations_total: number;
    suggestions_count: number;
    suggestions_pending: number;
    residents_count: number;
    registrations_count: number;
    memberships_count: number;
    buildings_count: number;
    units_count: number;
    projects_count: number;
  } | null>(null);
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(false);

  useEffect(() => {
    if (!activeCondominiumId) return;
    setIsLoadingMetrics(true);
    api.get<any>(`/condominiums/${activeCondominiumId}/dashboard-metrics`)
      .then((res) => {
        setMetricsData(res.data);
      })
      .catch((err) => {
        console.error('Falha ao carregar métricas reais:', err);
        setMetricsData(null);
      })
      .finally(() => {
        setIsLoadingMetrics(false);
      });
  }, [activeCondominiumId]);

  const metrics = [
    {
      label: 'Consultas em Andamento (PDF)',
      value: isLoadingMetrics ? '...' : `${metricsData?.consultations_open ?? 0} Ativa${(metricsData?.consultations_open ?? 0) === 1 ? '' : 's'}`,
      detail: `${metricsData?.consultations_total ?? 0} consulta(s) no total`,
      icon: Sliders,
      color: 'text-indigo-700 bg-indigo-50 border-indigo-200',
      link: '/painel/consultas',
    },
    {
      label: 'Moradores Participantes',
      value: isLoadingMetrics ? '...' : `${metricsData?.residents_count ?? 0}`,
      detail: 'Cadastrados organicamente via sugestão',
      icon: Users,
      color: 'text-emerald-800 bg-emerald-50 border-emerald-200',
      link: '/painel/moradores',
    },
    {
      label: 'Sugestões Coletadas',
      value: isLoadingMetrics ? '...' : `${metricsData?.suggestions_count ?? 0}`,
      detail: `${metricsData?.suggestions_pending ?? 0} pendente(s) de análise`,
      icon: MessageSquare,
      color: 'text-amber-700 bg-amber-50 border-amber-200',
      link: '/painel/consultas',
    },
    {
      label: 'Unidades com Participação',
      value: isLoadingMetrics ? '...' : `${metricsData?.units_count ?? 0}`,
      detail: `Em ${metricsData?.buildings_count ?? 0} torre(s)/bloco(s)`,
      icon: Layers,
      color: 'text-brand-800 bg-brand-50 border-brand-200',
      link: '/painel/moradores',
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header do Painel */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Painel da Gestão</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            {activeCondominium?.name || 'Condomínio Selecionado'} — Revisão documental participativa e direta.
          </p>
        </div>
        <div className="flex items-center gap-2.5 flex-wrap">
          <Link to="/painel/consultas">
            <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white">
              <FileText className="w-4 h-4 mr-1.5" aria-hidden="true" />
              <span>Consultas em PDF</span>
            </Button>
          </Link>
          <Link to="/painel/moradores">
            <Button variant="outline" size="sm">
              <Users className="w-4 h-4 mr-1.5" aria-hidden="true" />
              <span>Moradores Participantes</span>
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
            <Link key={idx} to={m.link} className="block group">
              <Card className="h-full animate-fade-in-up group-hover:border-slate-400 group-hover:shadow-md transition-all duration-200 cursor-pointer">
                <CardContent className="p-5 flex items-start justify-between">
                  <div>
                    <p className="text-xs font-medium text-slate-500 group-hover:text-slate-700 transition-colors">{m.label}</p>
                    <h3 className="text-2xl font-bold text-slate-900 mt-1">{m.value}</h3>
                    <p className="text-xs text-slate-500 mt-1">{m.detail}</p>
                  </div>
                  <div className={`p-2.5 rounded-xl border ${m.color}`}>
                    <Icon className="w-5 h-5 text-current" aria-hidden="true" />
                  </div>
                </CardContent>
              </Card>
            </Link>
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
                <span className="font-semibold text-indigo-950">Consultas em PDF (Links Compartilháveis via WhatsApp)</span>
              </div>
              <ArrowRight className="w-4 h-4 text-indigo-500 group-hover:translate-x-0.5 transition-transform" aria-hidden="true" />
            </Link>
            <Link
              to="/painel/moradores"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-100 transition-colors text-xs sm:text-sm group"
            >
              <div className="flex items-center gap-2.5">
                <Users className="w-4 h-4 text-emerald-700" aria-hidden="true" />
                <span className="font-medium text-slate-800 group-hover:text-emerald-900">Moradores Participantes (Contatos & WhatsApp)</span>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" aria-hidden="true" />
            </Link>
            <Link
              to="/painel/unidades"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-100 transition-colors text-xs sm:text-sm group"
            >
              <div className="flex items-center gap-2.5">
                <Layers className="w-4 h-4 text-brand-800" aria-hidden="true" />
                <span className="font-medium text-slate-800 group-hover:text-brand-900">Estrutura Predial (Torres & Unidades)</span>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" aria-hidden="true" />
            </Link>
            <Link
              to="/painel/condominios"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-100 transition-colors text-xs sm:text-sm group"
            >
              <div className="flex items-center gap-2.5">
                <Building2 className="w-4 h-4 text-slate-700" aria-hidden="true" />
                <span className="font-medium text-slate-800 group-hover:text-slate-900">Configuração do Condomínio</span>
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
