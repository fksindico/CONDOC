import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { Link } from 'react-router-dom';
import { BookmarkCheck, RotateCcw, ArrowRight, ShieldAlert } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { LegalDisclaimerBanner } from '@/components/ui/LegalDisclaimerBanner';
import { CardSkeleton } from '@/components/ui/Skeleton';
import { formatDatePtBr } from '@/lib/utils';

export const MyAgreementsPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const [agreements, setAgreements] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchAgreements = async () => {
    if (!activeCondominiumId) return;
    setIsLoading(true);

    api.get<any[]>(`/condominiums/${activeCondominiumId}/campaigns`).then(async (resC) => {
      const list = resC.data || [];
      if (list.length > 0) {
        const camp = list[0];
        const resP = await api.get<any[]>(`/condominiums/${activeCondominiumId}/campaigns/${camp.id}/participants`);
        if (resP.data && resP.data.length > 0) {
          const participant = resP.data[0];
          // M11: Lista concordâncias ativas do morador
          const resAgrs = await api.get<any[]>(`/condominiums/${activeCondominiumId}/my-agreements?participant_id=${participant.id}`);
          setAgreements(resAgrs.data || []);
        }
      }
      setIsLoading(false);
    });
  };

  useEffect(() => {
    fetchAgreements();
  }, [activeCondominiumId]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Minhas Concordâncias</h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Propostas normativas com as quais você registrou apoio consultivo (M11, CA-36).
        </p>
      </div>

      <LegalDisclaimerBanner />

      <div className="space-y-4 animate-fade-in">
        {isLoading ? (
          <div className="space-y-4">
            <CardSkeleton />
            <CardSkeleton />
          </div>
        ) : agreements.length === 0 ? (
          <Card className="text-center py-12 text-slate-500">
            <BookmarkCheck className="w-10 h-10 mx-auto text-slate-300 mb-2" aria-hidden="true" />
            <p className="text-sm font-semibold text-slate-700">Você não possui concordâncias ativas registradas.</p>
            <p className="text-xs text-slate-500 mt-0.5">
              Explore o mural de sugestões públicas e registre seu apoio nas propostas que considerar pertinentes.
            </p>
            <div className="pt-4">
              <Link to="/portal/mural">
                <Button variant="outline" size="sm">
                  Ver Mural Público
                </Button>
              </Link>
            </div>
          </Card>
        ) : (
          agreements.map((agr) => (
            <Card key={agr.agreement_id} className="hover:border-slate-300 transition-colors">
              <CardContent className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <span className="font-mono text-xs font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded border">
                    {agr.public_protocol}
                  </span>
                  <h4 className="font-serif text-sm font-semibold text-slate-900 mt-1">
                    {agr.sanitized_public_text}
                  </h4>
                  <p className="text-xs text-slate-500">Registrada em {formatDatePtBr(agr.created_at)}</p>
                </div>
                <div className="shrink-0 flex items-center gap-2.5">
                  <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                    Apoio Ativo
                  </span>
                  <Link to={`/portal/mural/${agr.published_suggestion_revision_id}`}>
                    <Button size="sm" variant="outline" className="font-semibold text-slate-800 hover:text-brand-700">
                      <span>Ver Proposta</span>
                      <ArrowRight className="w-3.5 h-3.5 ml-1" aria-hidden="true" />
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};
