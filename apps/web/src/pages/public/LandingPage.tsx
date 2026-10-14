import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Building2,
  ShieldCheck,
  ArrowRight,
  BookOpen,
  Lock,
  Phone,
  Mail,
  KeyRound,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import { consultationService, PublicLandingInfo } from '@/services/consultationService';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [landingData, setLandingData] = useState<PublicLandingInfo | null>(null);
  const [tokenInput, setTokenInput] = useState('');
  const [tokenError, setTokenError] = useState<string | null>(null);

  useEffect(() => {
    document.title = 'FK Gestão Condominial';
    consultationService
      .getPublicLandingInfo()
      .then((data) => setLandingData(data))
      .catch((err) => {
        console.error('Falha ao carregar informações da landing page:', err);
      });
  }, []);

  const handleTokenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanToken = tokenInput.trim();
    if (!cleanToken) {
      setTokenError('Por favor, informe o código de acesso fornecido pela administração.');
      return;
    }
    if (cleanToken.length < 3) {
      setTokenError('O código de acesso deve conter ao menos 3 caracteres.');
      return;
    }
    setTokenError(null);
    navigate(`/participar/${encodeURIComponent(cleanToken)}`);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white font-sans">
      {/* Topbar White-Label */}
      <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Building2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-white block leading-none">
                FK Gestão Condominial
              </span>
              <span className="text-[11px] font-medium tracking-wide uppercase text-indigo-400 font-mono mt-1 block">
                Governança & Consultas Normativas
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            <Link
              to="/login"
              className="text-xs sm:text-sm font-semibold bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white px-4 sm:px-5 py-2.5 rounded-xl shadow-md shadow-indigo-600/25 transition-all flex items-center gap-1.5 active:scale-95"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Acesso da Gestão</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section & Card Central de Acesso por Código */}
      <main className="flex-1">
        <section className="relative overflow-hidden pt-12 pb-16 sm:pt-20 sm:pb-24 border-b border-slate-800/60">
          {/* Luz de Fundo Decorativa */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-5xl h-96 bg-indigo-500/10 blur-[120px] rounded-full pointer-events-none -z-10" />

          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-950/70 border border-indigo-700/60 text-indigo-300 text-xs font-semibold mb-6 shadow-xs">
              <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
              <span>Revisão e Modernização de Regras Condominiais</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white mb-6 leading-tight sm:leading-tight">
              FK Gestão Condominial
            </h1>

            <p className="text-lg sm:text-xl font-medium text-indigo-200/90 max-w-2xl mx-auto mb-4 leading-relaxed">
              Modernização Normativa, Convenção e Regimento Interno
            </p>

            <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto leading-relaxed mb-10">
              Participe da revisão das normas do seu condomínio com transparência, comodidade e segurança. Insira abaixo o código de acesso recebido da administração para visualizar o documento e enviar suas sugestões.
            </p>

            {/* Caixa Central de Inserção de Token / Código de Acesso */}
            <div className="max-w-xl mx-auto bg-slate-950/90 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-sm text-left relative">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-indigo-950 text-indigo-400 flex items-center justify-center border border-indigo-800/60">
                  <KeyRound className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">Acessar Consulta do Condomínio</h2>
                  <p className="text-xs text-slate-400">
                    Digite o código de acesso fornecido pela administração do condomínio:
                  </p>
                </div>
              </div>

              <form onSubmit={handleTokenSubmit} className="space-y-4">
                {tokenError && (
                  <div className="p-3 bg-rose-950/60 border border-rose-800 text-rose-300 text-xs rounded-xl flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                    <span>{tokenError}</span>
                  </div>
                )}

                <div className="flex flex-col sm:flex-row gap-2.5">
                  <div className="relative flex-1">
                    <input
                      type="text"
                      value={tokenInput}
                      onChange={(e) => {
                        setTokenInput(e.target.value.toUpperCase());
                        if (tokenError) setTokenError(null);
                      }}
                      placeholder="Ex: REG2026"
                      autoFocus
                      className="w-full px-4 py-3.5 bg-slate-900 border border-slate-700 rounded-xl text-white font-mono text-base tracking-wider placeholder:text-slate-500 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all uppercase"
                    />
                  </div>
                  <button
                    type="submit"
                    className="inline-flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-6 py-3.5 rounded-xl shadow-lg shadow-indigo-600/30 transition-all active:scale-95 text-sm cursor-pointer whitespace-nowrap"
                  >
                    <span>Acessar Consulta</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>

                <div className="flex items-start gap-2 pt-2 text-[11px] text-slate-400 leading-relaxed border-t border-slate-800/80">
                  <HelpCircle className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                  <span>
                    Caso tenha recebido um link direto (exemplo: <code className="text-indigo-300">.../participar/CODIGO</code>), basta clicar no link para abrir diretamente o documento e o formulário de sugestões.
                  </span>
                </div>
              </form>
            </div>
          </div>
        </section>

        {/* Pilares de Segurança & Usabilidade */}
        <section className="py-16 sm:py-20 border-t border-slate-800/60 bg-slate-950/30">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-2xl mx-auto mb-12">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 block mb-1">
                Confiabilidade & Privacidade
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                Como Funciona a Revisão de Normas
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-800/40 border border-slate-800 rounded-3xl p-6">
                <div className="w-10 h-10 rounded-xl bg-indigo-950 text-indigo-400 flex items-center justify-center mb-4">
                  <BookOpen className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white mb-2">Folheamento em 3D</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Experiência imersiva no computador ou celular estilo livro virtual (Flipbook), com zoom, busca e alternância de visualização.
                </p>
              </div>

              <div className="bg-slate-800/40 border border-slate-800 rounded-3xl p-6">
                <div className="w-10 h-10 rounded-xl bg-emerald-950 text-emerald-400 flex items-center justify-center mb-4">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white mb-2">Protocolo Seguro</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Cada sugestão enviada recebe um número de protocolo exclusivo unívoco (<span className="font-mono text-emerald-400">Torre-Apto-#####</span>) para total rastreabilidade.
                </p>
              </div>

              <div className="bg-slate-800/40 border border-slate-800 rounded-3xl p-6">
                <div className="w-10 h-10 rounded-xl bg-purple-950 text-purple-400 flex items-center justify-center mb-4">
                  <Lock className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white mb-2">Proteção & LGPD</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Seus dados pessoais permanecem protegidos. O sistema valida os registros para evitar falsidade e preserva a impessoalidade das decisões.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Rodapé White-Label */}
      <footer className="border-t border-slate-800 bg-slate-950 text-xs text-slate-400 py-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <Building2 className="w-5 h-5 text-indigo-500" />
            <span className="font-semibold text-white">FK Gestão Condominial</span>
            <span className="text-slate-600">|</span>
            <span>Governança & Consultas Normativas</span>
          </div>

          {(landingData?.landing_contact_email || landingData?.landing_contact_phone) && (
            <div className="flex flex-wrap items-center gap-4 text-slate-300">
              {landingData.landing_contact_phone && (
                <div className="flex items-center gap-1.5">
                  <Phone className="w-3.5 h-3.5 text-indigo-400" />
                  <span>{landingData.landing_contact_phone}</span>
                </div>
              )}
              {landingData.landing_contact_email && (
                <div className="flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5 text-indigo-400" />
                  <span>{landingData.landing_contact_email}</span>
                </div>
              )}
            </div>
          )}

          <div className="text-slate-500 text-[11px] text-center md:text-right">
            <span>© 2026 FK Gestão Condominial. Todos os direitos reservados.</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
