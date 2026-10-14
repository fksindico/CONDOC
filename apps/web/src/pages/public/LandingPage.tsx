import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Building2,
  FileText,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  BookOpen,
  Calendar,
  Lock,
  Phone,
  Mail,
  Home,
  Sparkles,
  Users,
} from 'lucide-react';
import { consultationService, PublicLandingInfo } from '@/services/consultationService';

export const LandingPage: React.FC = () => {
  const [landingData, setLandingData] = useState<PublicLandingInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    consultationService
      .getPublicLandingInfo()
      .then((data) => setLandingData(data))
      .catch((err) => {
        console.error('Falha ao carregar informações da landing page:', err);
      })
      .finally(() => setLoading(false));
  }, []);

  const condoName = landingData?.name || 'CONDOC';
  const title = landingData?.landing_title || `${condoName} — Gestão Participativa`;
  const subtitle =
    landingData?.landing_subtitle ||
    'Ambiente Oficial de Modernização Normativa, Convenção e Regimento Interno';
  const description =
    landingData?.landing_description ||
    'Bem-vindo à plataforma oficial de governança colaborativa. Participe ativamente da revisão das regras do condomínio com comodidade, transparência e segurança jurídica.';

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Topbar Institucional */}
      <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Building2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-white block leading-none">
                {condoName}
              </span>
              <span className="text-[11px] font-medium tracking-wide uppercase text-indigo-400 font-mono mt-1 block">
                Governança & Legislação Interna
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            <a
              href="#consultas"
              className="text-xs sm:text-sm font-semibold text-slate-300 hover:text-white px-3 sm:px-4 py-2 rounded-lg hover:bg-slate-800/80 transition-all flex items-center gap-1.5"
            >
              <BookOpen className="w-4 h-4 text-indigo-400" />
              <span>Consultas Abertas</span>
            </a>

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

      {/* Hero Section */}
      <main className="flex-1">
        <section className="relative overflow-hidden pt-12 pb-16 sm:pt-20 sm:pb-24 border-b border-slate-800/60">
          {/* Luz de Fundo Decorativa */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-5xl h-96 bg-indigo-500/10 blur-[120px] rounded-full pointer-events-none -z-10" />

          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-950/70 border border-indigo-700/60 text-indigo-300 text-xs font-semibold mb-6 shadow-xs">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span>Processo de Consulta Oficial do Condomínio</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white mb-6 leading-tight sm:leading-tight">
              {title}
            </h1>

            <p className="text-lg sm:text-xl font-medium text-indigo-200/90 max-w-2xl mx-auto mb-4 leading-relaxed">
              {subtitle}
            </p>

            <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto leading-relaxed mb-10">
              {description}
            </p>

            {landingData?.open_consultations && landingData.open_consultations.length > 0 && (
              <div className="inline-block">
                <a
                  href="#consultas"
                  className="inline-flex items-center gap-2 bg-white text-slate-950 hover:bg-slate-100 font-bold px-6 py-3.5 rounded-xl shadow-lg transition-all active:scale-95 text-sm"
                >
                  <BookOpen className="w-4 h-4 text-indigo-600" />
                  <span>Ver Consultas Públicas Abertas</span>
                  <ArrowRight className="w-4 h-4 ml-1" />
                </a>
              </div>
            )}
          </div>
        </section>

        {/* Consultas Abertas para Moradores */}
        <section id="consultas" className="py-16 sm:py-20 bg-slate-950/40">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-10 gap-4">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 block mb-1">
                  Participação Cidadã
                </span>
                <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                  Consultas Públicas Ativas
                </h2>
              </div>
              <p className="text-xs sm:text-sm text-slate-400 max-w-md">
                Leia o documento oficial diretamente no visualizador interativo e envie suas sugestões de redação.
              </p>
            </div>

            {loading ? (
              <div className="flex flex-col items-center justify-center p-12 bg-slate-800/40 rounded-3xl border border-slate-800">
                <div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3" />
                <p className="text-xs text-slate-400">Verificando consultas abertas...</p>
              </div>
            ) : landingData?.open_consultations && landingData.open_consultations.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {landingData.open_consultations.map((c) => (
                  <div
                    key={c.id}
                    className="bg-slate-800/60 hover:bg-slate-800/80 border border-slate-700/80 hover:border-indigo-500/60 rounded-3xl p-6 sm:p-7 shadow-xl transition-all flex flex-col justify-between group"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-3 mb-4">
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-700/60">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          Aberta para Sugestões
                        </span>
                        <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-slate-700/60 text-slate-300">
                          {c.document_type === 'regimento' ? 'Regimento Interno' : 'Convenção'}
                        </span>
                      </div>

                      <h3 className="text-xl font-bold text-white group-hover:text-indigo-300 transition-colors mb-2">
                        {c.title}
                      </h3>

                      <p className="text-xs sm:text-sm text-slate-300 line-clamp-3 mb-5 leading-relaxed">
                        {c.description ||
                          'O síndico e a comissão disponibilizaram o documento para análise de todos os condôminos.'}
                      </p>

                      <div className="flex items-center gap-2 text-xs text-slate-400 mb-6 bg-slate-900/60 px-3 py-2 rounded-xl border border-slate-800">
                        <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                        <span className="truncate">{c.pdf_original_name}</span>
                      </div>
                    </div>

                    <Link
                      to={`/participar/${c.public_token}`}
                      className="w-full inline-flex items-center justify-center gap-2 py-3.5 px-5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm shadow-md shadow-indigo-600/30 transition-all active:scale-98"
                    >
                      <BookOpen className="w-4 h-4" />
                      <span>Folhear Documento & Sugerir</span>
                      <ArrowRight className="w-4 h-4 ml-1" />
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-16 px-6 bg-slate-800/30 rounded-3xl border border-slate-800/80 max-w-xl mx-auto">
                <div className="w-12 h-12 rounded-2xl bg-slate-800 text-slate-400 flex items-center justify-center mx-auto mb-3">
                  <FileText className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-white mb-1">Nenhuma consulta aberta no momento</h3>
                <p className="text-xs text-slate-400">
                  Todas as minutas estão em fase de consolidação pela gestão. Fique atento aos comunicados oficiais do condomínio.
                </p>
              </div>
            )}
          </div>
        </section>

        {/* Pilares de Segurança & Usabilidade */}
        <section className="py-16 sm:py-20 border-t border-slate-800/60">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-2xl mx-auto mb-12">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 block mb-1">
                Confiabilidade & Privacidade
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                Como Funciona a Revisão no CONDOC
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
                  <ShieldCheck className="w-5 h-5" />
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

      {/* Rodapé Oficial */}
      <footer className="border-t border-slate-800 bg-slate-950 text-xs text-slate-400 py-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <Building2 className="w-5 h-5 text-indigo-500" />
            <span className="font-semibold text-white">{condoName}</span>
            <span className="text-slate-600">|</span>
            <span>Plataforma CONDOC</span>
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
            <span>Preservação de registros conforme diretrizes do PRD Mestre CONDOC.</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
