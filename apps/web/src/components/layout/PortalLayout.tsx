import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useTenant } from '@/contexts/TenantContext';
import { LegalDisclaimerBanner } from '@/components/ui/LegalDisclaimerBanner';
import {
  Building2,
  BookOpen,
  MessageSquare,
  BookmarkCheck,
  User,
  LogOut,
  Home,
  FileText,
  ShieldCheck,
  LogIn,
  Eye,
} from 'lucide-react';

export const PortalLayout: React.FC = () => {
  const { user, logout, isSindico, isAdmin, isAuthenticated } = useAuth();
  const { activeCondominium } = useTenant();
  const location = useLocation();

  const navLinks = [
    { label: 'Início', path: '/portal', icon: Home },
    { label: 'Minuta em Consulta', path: '/portal/documento', icon: BookOpen },
    { label: 'Mural de Sugestões', path: '/portal/mural', icon: MessageSquare },
    { label: 'Minhas Sugestões', path: '/portal/minhas-sugestoes', icon: FileText },
    { label: 'Minhas Concordâncias', path: '/portal/minhas-concordancias', icon: BookmarkCheck },
    { label: 'Meu Cadastro', path: '/portal/meu-cadastro', icon: User },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Banner de Simulação no Portal do Morador */}
      {(isSindico || isAdmin) && (
        <div className="bg-amber-400 border-b border-amber-500 text-slate-950 px-4 py-2 text-xs font-semibold flex items-center justify-between shadow-2xs">
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-slate-950 shrink-0" />
            <span>
              <strong>Modo Simulação Ativo:</strong> Você está visualizando o Portal do Morador com a experiência do condômino.
            </span>
          </div>
          <Link
            to="/painel"
            className="ml-3 px-3 py-1 bg-slate-950 hover:bg-slate-900 text-white font-bold rounded-lg transition active:scale-95 shrink-0"
          >
            👑 Retornar ao Painel do Síndico
          </Link>
        </div>
      )}
      {/* Topbar Institucional do Morador */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo / Condomínio */}
            <div className="flex items-center gap-3">
              <Link to="/portal" className="flex items-center gap-2 text-brand-700 font-bold text-lg tracking-tight">
                <Building2 className="w-6 h-6 text-brand-600" aria-hidden="true" />
                <span>CONDOC</span>
              </Link>
              <div className="h-4 w-px bg-slate-200 hidden sm:block" />
              <span className="text-xs font-semibold text-slate-700 truncate max-w-[200px] sm:max-w-xs">
                {activeCondominium?.name || 'Portal do Morador'}
              </span>
            </div>

            {/* Usuário / Alternador de Perfil / Sair */}
            <div className="flex items-center gap-3 text-xs">
              {/* Botão de Alternância para o Painel do Síndico / Gestão */}
              {isSindico || isAdmin ? (
                <Link
                  to="/painel"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold transition-all shadow-xs"
                  title="Acessar o Painel Administrativo de Gestão"
                >
                  <ShieldCheck className="w-4 h-4 text-slate-950" aria-hidden="true" />
                  <span>Painel do Síndico</span>
                </Link>
              ) : !isAuthenticated ? (
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 font-semibold transition-all shadow-2xs"
                  title="Acesso de síndicos, comissões e gestão"
                >
                  <LogIn className="w-3.5 h-3.5 text-brand-600" aria-hidden="true" />
                  <span>Área do Síndico</span>
                </Link>
              ) : null}

              {isAuthenticated ? (
                <>
                  <span className="text-slate-600 hidden md:inline">
                    Olá, <strong className="text-slate-900">{user?.full_name || 'Morador'}</strong>
                  </span>
                  <button
                    onClick={logout}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:text-rose-600 hover:bg-slate-50 transition-colors cursor-pointer"
                    title="Sair do portal"
                  >
                    <LogOut className="w-3.5 h-3.5" aria-hidden="true" />
                    <span>Sair</span>
                  </button>
                </>
              ) : null}
            </div>
          </div>

          {/* Abas Horizontais de Navegação */}
          <nav className="flex space-x-1 sm:space-x-4 overflow-x-auto border-t border-slate-100 py-1 text-xs sm:text-sm no-scrollbar">
            {navLinks.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || (item.path !== '/portal' && location.pathname.startsWith(item.path));
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg font-medium whitespace-nowrap transition-all text-xs sm:text-sm ${
                    isActive
                      ? 'bg-brand-50 text-brand-700 font-semibold border border-brand-200/60 shadow-2xs'
                      : 'text-slate-700 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
                  }`}
                >
                  <Icon className="w-4 h-4 shrink-0 text-current" aria-hidden="true" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Conteúdo Central */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col gap-6">
        <Outlet />
      </main>

      {/* Rodapé Obrigatório Permanente */}
      <footer className="bg-white border-t border-slate-200 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
          <LegalDisclaimerBanner compact className="w-full sm:w-auto" />
          <p className="text-center sm:text-right shrink-0">
            CONDOC — Plataforma de Gestão Normativa Condominial
          </p>
        </div>
      </footer>
    </div>
  );
};
