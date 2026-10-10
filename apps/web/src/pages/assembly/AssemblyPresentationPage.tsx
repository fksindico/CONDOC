import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { BookOpen, ShieldAlert, FileText, CheckCircle2 } from 'lucide-react';

export const AssemblyPresentationPage: React.FC = () => {
  const { docId } = useParams<{ docId: string }>();
  const { activeCondominiumId } = useTenant();

  const [assemblyData, setAssemblyData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!activeCondominiumId || !docId) return;
    setIsLoading(true);
    api
      .get<any>(`/condominiums/${activeCondominiumId}/documents/${docId}/assembly-reading`)
      .then((res) => {
        setAssemblyData(res.data);
      })
      .catch((err) => {
        setError(err.message || 'Erro ao carregar minuta para projeção.');
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [activeCondominiumId, docId]);

  if (isLoading) {
    return (
      <div className="py-20 text-center space-y-3">
        <BookOpen className="w-10 h-10 animate-pulse text-brand-400 mx-auto" />
        <p className="text-sm font-medium text-slate-400">Carregando minuta para apresentação em assembleia...</p>
      </div>
    );
  }

  if (error || !assemblyData) {
    return (
      <div className="py-20 text-center text-rose-400">
        <p>{error || 'Minuta não encontrada para apresentação.'}</p>
      </div>
    );
  }

  return (
    <article className="space-y-8 font-serif leading-relaxed">
      {/* Título do Documento */}
      <div className="text-center pb-8 border-b border-slate-800 space-y-2">
        <span className="text-xs uppercase font-sans font-mono tracking-widest text-brand-400">
          {assemblyData.document_type?.replace('_', ' ')}
        </span>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
          {assemblyData.title}
        </h1>
        <p className="text-xs font-sans text-slate-400 max-w-xl mx-auto">
          Minuta final consolidada pela comissão de revisão para apreciação dos condôminos.
        </p>
      </div>

      {/* Dispositivos Normativos */}
      <div className="space-y-6">
        {assemblyData.provisions?.map((prov: any, idx: number) => (
          <section key={idx} className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 space-y-2">
            <span className="font-sans font-bold text-base text-brand-300 block tracking-wide">
              {prov.label || `Artigo ${idx + 1}`}
            </span>
            <p className="text-base sm:text-lg text-slate-200 leading-relaxed font-serif pl-2 border-l-2 border-brand-500/50">
              {prov.text}
            </p>
          </section>
        ))}
      </div>
    </article>
  );
};
