import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTenant } from '@/contexts/TenantContext';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { BookOpen, MessageSquare, Send, BookmarkCheck, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { LegalDisclaimerBanner } from '@/components/ui/LegalDisclaimerBanner';
import { Badge } from '@/components/ui/Badge';

export const ResidentDashboardPage: React.FC = () => {
  const { activeCondominium } = useTenant();
  const { user } = useAuth();
  const [activeCampaign, setActiveCampaign] = useState<any | null>(null);

  useEffect(() => {
    if (!activeCondominium?.id) return;
    api.get<any[]>(`/condominiums/${activeCondominium.id}/campaigns`).then((res) => {
      const list = res.data || [];
      const openCamp = list.find((c) => c.state === 'aberta') || list[0] || null;
      setActiveCampaign(openCamp);
    });
  }, [activeCondominium]);

  return (
    <div className="space-y-6">
      {/* Banner de Boas-Vindas */}
      <div className="bg-gradient-to-br from-brand-700 via-brand-800 to-indigo-900 text-white rounded-2xl p-6 sm:p-8 shadow-lg shadow-brand-950/20 relative overflow-hidden border border-brand-600/30">
        <div className="max-w-3xl space-y-3.5 relative z-10">
          <Badge variant="outline" className="text-white border-white/30 bg-white/10 text-[11px] uppercase tracking-wider backdrop-blur-sm">
            Consulta Pública Ativa
          </Badge>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white leading-tight">
            Participe da Modernização das Normas do Seu Condomínio
          </h1>
          <p className="text-xs sm:text-sm text-brand-100 leading-relaxed max-w-2xl">
            Leia a minuta em discussão, envie sugestões privadas de aprimoramento e apoie propostas de interesse coletivo.
          </p>
          <div className="pt-2 flex flex-wrap gap-3">
            <Link to="/portal/documento">
              <Button variant="white" className="font-semibold text-brand-950 hover:bg-slate-100 shadow-md">
                <BookOpen className="w-4 h-4 mr-2 text-brand-700" />
                <span>Ler Minuta em Consulta</span>
              </Button>
            </Link>
            <Link to="/portal/sugerir">
              <Button variant="outline-white" className="font-semibold">
                <Send className="w-4 h-4 mr-2 text-white" />
                <span>Enviar Sugestão</span>
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Aviso Permanente de Natureza Consultiva (UI-28, CA-45) */}
      <LegalDisclaimerBanner />

      {/* Cards de Atalhos e Recursos */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <Card className="group hover:border-brand-300 hover:shadow-md transition-all duration-200 flex flex-col justify-between">
          <CardHeader>
            <div className="p-2.5 w-fit rounded-xl bg-blue-100 text-blue-800 border border-blue-200/60 mb-2">
              <BookOpen className="w-5 h-5" />
            </div>
            <CardTitle className="text-base text-slate-900">Documento Normativo</CardTitle>
            <CardDescription className="text-xs text-slate-600 leading-relaxed">
              Acesse os artigos congelados na versão oficial de consulta pública (snapshot imutável).
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/portal/documento">
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-between text-slate-800 font-semibold group-hover:bg-brand-50 group-hover:text-brand-700 group-hover:border-brand-300 transition-colors"
              >
                <span>Explorar Artigos</span>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-brand-600 transition-transform group-hover:translate-x-0.5" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="group hover:border-brand-300 hover:shadow-md transition-all duration-200 flex flex-col justify-between">
          <CardHeader>
            <div className="p-2.5 w-fit rounded-xl bg-indigo-100 text-indigo-800 border border-indigo-200/60 mb-2">
              <MessageSquare className="w-5 h-5" />
            </div>
            <CardTitle className="text-base text-slate-900">Mural de Sugestões</CardTitle>
            <CardDescription className="text-xs text-slate-600 leading-relaxed">
              Veja as contribuições autorizadas pela gestão, 100% anônimas e livres de identificação pessoal.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/portal/mural">
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-between text-slate-800 font-semibold group-hover:bg-brand-50 group-hover:text-brand-700 group-hover:border-brand-300 transition-colors"
              >
                <span>Ver Propostas Públicas</span>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-brand-600 transition-transform group-hover:translate-x-0.5" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="group hover:border-brand-300 hover:shadow-md transition-all duration-200 flex flex-col justify-between">
          <CardHeader>
            <div className="p-2.5 w-fit rounded-xl bg-emerald-100 text-emerald-800 border border-emerald-200/60 mb-2">
              <BookmarkCheck className="w-5 h-5" />
            </div>
            <CardTitle className="text-base text-slate-900">Minhas Concordâncias</CardTitle>
            <CardDescription className="text-xs text-slate-600 leading-relaxed">
              Acompanhe as propostas com as quais você manifestou apoio consultivo ou retire-as quando desejar.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/portal/minhas-concordancias">
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-between text-slate-800 font-semibold group-hover:bg-brand-50 group-hover:text-brand-700 group-hover:border-brand-300 transition-colors"
              >
                <span>Minhas Manifestações</span>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-brand-600 transition-transform group-hover:translate-x-0.5" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
