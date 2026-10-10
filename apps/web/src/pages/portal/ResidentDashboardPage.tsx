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
      <div className="bg-gradient-to-r from-brand-700 to-indigo-800 text-white rounded-2xl p-6 sm:p-8 shadow-md">
        <div className="max-w-3xl space-y-3">
          <Badge variant="outline" className="text-white border-white/40 text-[11px] uppercase tracking-wider">
            Consulta Pública Ativa
          </Badge>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Participe da Modernização das Normas do Seu Condomínio
          </h1>
          <p className="text-xs sm:text-sm text-brand-100 leading-relaxed">
            Leia a minuta em discussão, envie sugestões privadas de aprimoramento e apoie propostas de interesse coletivo.
          </p>
          <div className="pt-2 flex flex-wrap gap-3">
            <Link to="/portal/documento">
              <Button className="bg-white text-brand-900 hover:bg-brand-50 border-0 shadow-sm">
                <BookOpen className="w-4 h-4 mr-1.5 text-brand-700" />
                <span>Ler Minuta em Consulta</span>
              </Button>
            </Link>
            <Link to="/portal/sugerir">
              <Button variant="outline" className="text-white border-white/30 hover:bg-white/10">
                <Send className="w-4 h-4 mr-1.5" />
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
        <Card className="hover:border-slate-300 transition-colors">
          <CardHeader>
            <div className="p-2.5 w-fit rounded-xl bg-blue-50 text-blue-700 mb-2">
              <BookOpen className="w-5 h-5" />
            </div>
            <CardTitle className="text-base">Documento Normativo</CardTitle>
            <CardDescription>
              Acesse os artigos congelados na versão oficial de consulta pública (snapshot imutável).
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/portal/documento">
              <Button variant="ghost" size="sm" className="w-full justify-between text-brand-600">
                <span>Explorar Artigos</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:border-slate-300 transition-colors">
          <CardHeader>
            <div className="p-2.5 w-fit rounded-xl bg-indigo-50 text-indigo-700 mb-2">
              <MessageSquare className="w-5 h-5" />
            </div>
            <CardTitle className="text-base">Mural de Sugestões</CardTitle>
            <CardDescription>
              Veja as contribuições autorizadas pela gestão, 100% anônimas e livres de identificação pessoal.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/portal/mural">
              <Button variant="ghost" size="sm" className="w-full justify-between text-brand-600">
                <span>Ver Propostas Públicas</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:border-slate-300 transition-colors">
          <CardHeader>
            <div className="p-2.5 w-fit rounded-xl bg-emerald-50 text-emerald-700 mb-2">
              <BookmarkCheck className="w-5 h-5" />
            </div>
            <CardTitle className="text-base">Minhas Concordâncias</CardTitle>
            <CardDescription>
              Acompanhe as propostas com as quais você manifestou apoio consultivo ou retire-as quando desejar.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/portal/minhas-concordancias">
              <Button variant="ghost" size="sm" className="w-full justify-between text-brand-600">
                <span>Minhas Manifestações</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
