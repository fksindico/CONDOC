import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { Link, useNavigate } from 'react-router-dom';
import { BookOpen, Search, Send, Lock, ArrowRight, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { LegalDisclaimerBanner } from '@/components/ui/LegalDisclaimerBanner';

export const DocumentReaderPage: React.FC = () => {
  const { activeCondominiumId } = useTenant();
  const navigate = useNavigate();

  const [articles, setArticles] = useState<any[]>([]);
  const [activeCampaign, setActiveCampaign] = useState<any | null>(null);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!activeCondominiumId) return;
    setIsLoading(true);
    api.get<any[]>(`/condominiums/${activeCondominiumId}/campaigns`).then(async (resC) => {
      const list = resC.data || [];
      const openCamp = list.find((c) => c.state === 'aberta') || list[0] || null;
      setActiveCampaign(openCamp);

      if (openCamp) {
        try {
          // UI-19: O portal do morador consome estritamente o SNAPSHOT congelado da campanha
          const resSnap = await api.get<any[]>(`/condominiums/${activeCondominiumId}/campaigns/${openCamp.id}/document-snapshot`);
          setArticles(resSnap.data || []);
        } catch (err: any) {
          setError('Erro ao carregar artigos do snapshot da campanha.');
        }
      }
      setIsLoading(false);
    });
  }, [activeCondominiumId]);

  const filtered = articles.filter(
    (a) =>
      !search ||
      (a.label && a.label.toLowerCase().includes(search.toLowerCase())) ||
      (a.text && a.text.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Minuta em Consulta Pública</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Versão congelada no snapshot oficial da campanha (UI-19).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs font-mono uppercase bg-white">
            <Lock className="w-3 h-3 mr-1 text-slate-400" />
            <span>Versão Congelada</span>
          </Badge>
        </div>
      </div>

      <LegalDisclaimerBanner compact />

      {/* Barra de Busca de Artigos */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        <input
          type="text"
          className="w-full text-xs sm:text-sm bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 outline-none focus:ring-2 focus:ring-brand-500 shadow-2xs"
          placeholder="Pesquisar por palavras-chave (ex: animais, barulho, piscina, garagem)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {/* Listagem Estruturada de Artigos do Snapshot */}
      <div className="space-y-4">
        {isLoading ? (
          <p className="text-xs text-slate-400 text-center py-8">Carregando artigos da minuta...</p>
        ) : filtered.length === 0 ? (
          <Card className="text-center py-10 text-slate-500">
            <BookOpen className="w-8 h-8 mx-auto text-slate-300 mb-2" />
            <p className="text-sm font-medium">Nenhum artigo encontrado para a pesquisa.</p>
          </Card>
        ) : (
          filtered.map((item, idx) => (
            <Card key={idx} className="hover:border-slate-300 transition-colors">
              <CardContent className="p-5 flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="space-y-1.5 flex-1">
                  <span className="font-bold text-slate-900 text-sm block tracking-tight">
                    {item.label || `Artigo ${idx + 1}`}
                  </span>
                  <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-serif">
                    {item.text}
                  </p>
                </div>
                <div className="shrink-0 pt-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      navigate(
                        `/portal/sugerir?target_provision_id=${item.provision_id}&target_label=${encodeURIComponent(
                          item.label || ''
                        )}`
                      )
                    }
                  >
                    <Send className="w-3.5 h-3.5 mr-1 text-brand-600" />
                    <span>Sugerir neste artigo</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};
