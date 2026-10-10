import React, { useState } from 'react';
import { Outlet, Link } from 'react-router-dom';
import { Building2, ZoomIn, ZoomOut, Maximize2, ShieldAlert, ArrowLeft } from 'lucide-react';

export const AssemblyLayout: React.FC = () => {
  const [fontSize, setFontSize] = useState<number>(18);
  const [isHighContrast, setIsHighContrast] = useState<boolean>(false);

  const increaseFont = () => setFontSize((prev) => Math.min(prev + 2, 28));
  const decreaseFont = () => setFontSize((prev) => Math.max(prev - 2, 14));
  const toggleContrast = () => setIsHighContrast((prev) => !prev);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

  return (
    <div
      className={`min-h-screen flex flex-col transition-colors ${
        isHighContrast ? 'bg-black text-amber-300' : 'bg-slate-900 text-slate-100'
      }`}
      style={{ fontSize: `${fontSize}px` }}
    >
      {/* Barra de Controles de Projeção */}
      <header className="bg-slate-950/80 backdrop-blur-md border-b border-slate-800 px-6 py-3 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <Link
            to="/painel"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            title="Voltar ao Painel"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="flex items-center gap-2 font-bold text-white tracking-tight">
            <Building2 className="w-5 h-5 text-brand-400" />
            <span className="text-base">CONDOC</span>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-brand-900/80 text-brand-300 border border-brand-700 font-mono uppercase tracking-wider">
            Projeção em Assembleia — Somente Leitura
          </span>
        </div>

        {/* Controles de Apresentador */}
        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={decreaseFont}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Diminuir Fonte (A-)"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="font-mono text-slate-400 px-1">{fontSize}px</span>
          <button
            onClick={increaseFont}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Aumentar Fonte (A+)"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <div className="h-4 w-px bg-slate-800 mx-1" />
          <button
            onClick={toggleContrast}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition-colors"
          >
            {isHighContrast ? 'Contraste Normal' : 'Alto Contraste'}
          </button>
          <button
            onClick={toggleFullscreen}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Tela Cheia"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Faixa Legal Obrigatória Visível para Todos os Condôminos */}
      <div className="bg-amber-950/60 border-b border-amber-900/80 px-6 py-2 text-center text-xs text-amber-300 flex items-center justify-center gap-2">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
        <span>
          <strong>VISUALIZAÇÃO PROJETADA — DOCUMENTO NORMATIVO CONSOLIDADO.</strong> Sistema exclusivamente consultivo.
          NÃO realiza votação, cálculo de quórum de assembleia, aprovação vinculante ou registro cartorial.
        </span>
      </div>

      {/* Conteúdo da Minuta Projetada */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-6 sm:p-10 lg:p-12 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
};
