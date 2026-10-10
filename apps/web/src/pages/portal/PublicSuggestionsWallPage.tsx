import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { Link } from 'react-router-dom';
import { MessageSquare, ArrowRight, ShieldCheck, Search, Filter } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { CardSkeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { LegalDisclaimerBanner } from '@/components/ui/LegalDisclaimerBanner';
import { Alert } from '@/components/ui/Alert';

export const PublicSuggestionsWallPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [activeCampaign, setActiveCampaign] = useState<any | null>(null);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!activeCondominiumId) return;
    setIsLoading(true);
    api.get<any[]>(`/condominiums/${activeCondominiumId}/campaigns`).then(async (resC) => {
      const list = resC.data || [];
      const openCamp = list.find((c) => c.state === 'aberta') || list[0] || null;
      setActiveCampaign(openCamp);

      if (openCamp) {
        try {
          // CA-29 / UI-25: Lista estritamente sugestões publicadas autorizadas pelo síndico (sem PII)
          const resSugs = await api.get<any[]>(`/condominiums/${activeCondominiumId}/campaigns/${openCamp.id}/suggestions`);
          setSuggestions(resSugs.data || []);
        } catch {
          setSuggestions([]);
        }
      }
      setIsLoading(false);
    });
  }, [activeCondominiumId]);

  const filtered = suggestions.filter(
    (s) =>
      !search ||
      (s.public_protocol && s.public_protocol.toLowerCase().includes(search.toLowerCase())) ||
      (s.sanitized_public_text && s.sanitized_public_text.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
          Mural de Sugestões Públicas
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Contribuições da comunidade autorizadas pelo síndico para conhecimento coletivo (CA-26, CA-29).
        </p>
      </div>

      <LegalDisclaimerBanner />

      {/* Busca */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        <input
          type="text"
          className="w-full text-xs sm:text-sm bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 outline-none focus:ring-2 focus:ring-brand-500 shadow-2xs"
          placeholder="Filtrar sugestões públicas autorizadas..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Grid de Cartões Públicos 100% Anônimos (UI-25) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {isLoading ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : filtered.length === 0 ? (
          <div className="col-span-full">
            <EmptyState
              icon={MessageSquare}
              title={search ? "Nenhuma sugestão encontrada" : "Nenhuma sugestão publicada no mural"}
              description={search ? "Tente buscar por outros termos ou categorias." : "As sugestões enviadas passam por análise técnica e sanitização antes de serem autorizadas pelo síndico."}
              actionLabel={search ? undefined : "Enviar uma Sugestão"}
              onAction={search ? undefined : () => (window.location.href = '/portal/sugerir')}
            />
          </div>
        ) : (
          filtered.map((s) => (
            <Card key={s.id} className="hover:border-brand-300 hover:shadow-md transition-all duration-200 flex flex-col justify-between">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-slate-800 bg-slate-100 px-2.5 py-1 rounded border border-slate-200">
                    {s.public_protocol}
                  </span>
                  <Badge variant="outline" className="text-[10px] uppercase font-mono">
                    {s.category}
                  </Badge>
                </div>
                <CardTitle className="text-sm mt-3 text-slate-900 leading-relaxed font-serif">
                  {s.sanitized_public_text}
                </CardTitle>
                {s.sanitized_justification && (
                  <CardDescription className="line-clamp-2 mt-1 text-slate-600 text-xs">
                    {s.sanitized_justification}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="pt-0">
                <Link to={`/portal/mural/${s.id}`}>
                  <Button variant="outline" size="sm" className="w-full justify-between mt-2 font-semibold text-slate-800 hover:text-brand-700 hover:border-brand-300 hover:bg-brand-50 transition-colors">
                    <span>Ver Detalhe & Apoiar</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-brand-600" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};
