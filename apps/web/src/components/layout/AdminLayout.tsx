import React, { useState } from 'react';
import { Outlet, Link, useLocation, Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useTenant } from '@/contexts/TenantContext';
import {
  Building2,
  FileText,
  Users,
  MessageSquare,
  ShieldCheck,
  BarChart3,
  Settings,
  LogOut,
  ChevronDown,
  Layers,
  FileCheck2,
  Send,
  UserCheck,
  FolderGit2,
  History,
  Download,
  Sliders,
  FileSpreadsheet,
  Menu,
  X,
  Home,
  Eye,
  Sparkles,
} from 'lucide-react';

export const AdminLayout: React.FC = () => {
  const { user, logout, isSindico, activeRole, setActiveRole, isAuthenticated, isLoading } = useAuth();
  const { condominiums, activeCondominium, selectCondominium } = useTenant();
  const location = useLocation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-400 text-sm">Carregando painel administrativo...</p>
        </div>
      </div>
    );
  }

  // Se não autenticado no BFF, redireciona para login preservando URL de retorno
  if (!isAuthenticated && !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const menuSections = [
    {
      title: 'Revisão Participativa',
      items: [
        { label: 'Dashboard', path: '/painel', icon: BarChart3 },
        { label: 'Consultas em PDF', path: '/painel/consultas', icon: FileText },
        { label: 'Moradores Participantes', path: '/painel/moradores', icon: Users },
      ],
    },
    {
      title: 'Estrutura Predial',
      items: [
        { label: 'Condomínios', path: '/painel/condominios', icon: Building2 },
        { label: 'Torres & Unidades', path: '/painel/unidades', icon: Layers },
      ],
    },
    {
      title: 'Administração',
      items: [
        { label: 'Apresentação & Mensagens', path: '/painel/apresentacao', icon: Sparkles },
        { label: 'Equipe & Permissões', path: '/painel/equipe', icon: ShieldCheck },
        { label: 'Trilha de Auditoria', path: '/painel/auditoria', icon: History },
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar Mobile Backdrop */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 md:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar Principal */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-64 bg-slate-900 text-slate-300 flex flex-col transition-transform duration-200 ease-in-out ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Brand Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <Link to="/painel" className="flex items-center gap-2.5 text-white font-bold text-base tracking-tight">
            <Building2 className="w-6 h-6 text-brand-400" aria-hidden="true" />
            <span>CONDOC</span>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-brand-900/60 text-brand-300 border border-brand-700">
              Gestão
            </span>
          </Link>
          <button
            className="md:hidden text-slate-400 hover:text-white"
            onClick={() => setIsSidebarOpen(false)}
            aria-label="Fechar menu lateral"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        {/* Seletor de Condomínio Ativo */}
        <div className="p-3 border-b border-slate-800">
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Condomínio Ativo
            </label>
            <Link
              to="/painel/condominios"
              className="text-[10px] text-brand-400 hover:text-brand-300 transition-colors font-medium"
              title="Gerenciar todos os condomínios"
            >
              Gerenciar &rarr;
            </Link>
          </div>
          <select
            className="w-full text-xs bg-slate-800 border border-slate-700 text-white rounded-lg p-2 focus:ring-1 focus:ring-brand-400 outline-none truncate"
            value={activeCondominium?.id || ''}
            onChange={(e) => selectCondominium(e.target.value)}
          >
            {condominiums.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* Menu de Navegação */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-4 text-xs">
          {menuSections.map((sec, idx) => (
            <div key={idx}>
              <span className="block px-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                {sec.title}
              </span>
              <ul className="space-y-0.5">
                {sec.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path || location.pathname.startsWith(`${item.path}/`);
                  return (
                    <li key={item.path}>
                      <Link
                        to={item.path}
                        onClick={() => setIsSidebarOpen(false)}
                        className={`flex items-center gap-2.5 px-2.5 py-2 rounded-lg font-medium transition-colors ${
                          isActive
                            ? 'bg-brand-600 text-white shadow-sm'
                            : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                        }`}
                      >
                        <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
                        <span className="truncate">{item.label}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Alternador de Visão para o Síndico (Modo Simulação) */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/40">
          <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
            <Eye className="w-3.5 h-3.5 text-indigo-400" />
            <span>Alternar Modo de Visão</span>
          </label>
          <select
            value={activeRole}
            onChange={(e) => {
              const val = e.target.value;
              if (val === 'morador') {
                window.location.href = '/portal';
              } else {
                setActiveRole(val);
              }
            }}
            className="w-full text-xs bg-slate-800 border border-slate-700 text-slate-200 rounded-lg p-2 focus:ring-1 focus:ring-indigo-400 outline-none"
          >
            <option value="sindico">👑 Visão Síndico (Acesso Geral)</option>
            <option value="conselho">🛡️ Visão Conselho / Comissão</option>
            <option value="morador">🏠 Ver como Morador (/portal)</option>
          </select>
        </div>

        {/* Perfil & Logout */}
        <div className="p-3 border-t border-slate-800 flex items-center justify-between text-xs">
          <div className="truncate pr-2">
            <p className="font-semibold text-white truncate">{user?.full_name || 'Usuário Gestão'}</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span
                className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border ${
                  activeRole === 'sindico'
                    ? 'bg-amber-950/80 text-amber-300 border-amber-700/80 font-bold'
                    : 'bg-indigo-950/80 text-indigo-300 border-indigo-700/80 font-bold'
                }`}
              >
                {activeRole === 'sindico' ? 'Síndico Ativo' : `Simulando: ${activeRole}`}
              </span>
            </div>
          </div>
          <button
            onClick={logout}
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
            title="Encerrar Sessão"
            aria-label="Encerrar Sessão"
          >
            <LogOut className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>
      </aside>

      {/* Conteúdo Principal */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Banner de Simulação da Visão do Conselho / Comissão */}
        {activeRole === 'conselho' && (
          <div className="bg-amber-500/15 border-b border-amber-300 text-amber-900 px-4 py-2.5 text-xs font-medium flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-amber-700 shrink-0" />
              <span>
                <strong>Modo Simulação Ativo:</strong> Você está navegando com a visão do <strong>Conselho Fiscal / Comissão</strong>. Dados pessoais de contato estão anonimizados e ações de publicação restritas ao síndico ativo.
              </span>
            </div>
            <button
              onClick={() => setActiveRole('sindico')}
              className="ml-3 px-2.5 py-1 bg-amber-600 hover:bg-amber-700 text-white font-bold rounded-lg transition active:scale-95 shrink-0 cursor-pointer"
            >
              Voltar para Síndico
            </button>
          </div>
        )}

        {/* Topbar Mobile */}
        <header className="md:hidden bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="text-slate-600 hover:text-slate-900"
            aria-label="Abrir menu de navegação"
          >
            <Menu className="w-6 h-6" aria-hidden="true" />
          </button>
          <span className="font-semibold text-sm text-slate-900 truncate">
            {activeCondominium?.name || 'CONDOC'}
          </span>
          <div className="w-6" />
        </header>

        {/* Viewport Principal */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
