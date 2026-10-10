import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
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
} from 'lucide-react';

export const AdminLayout: React.FC = () => {
  const { user, logout, isSindico, activeRole } = useAuth();
  const { condominiums, activeCondominium, selectCondominium } = useTenant();
  const location = useLocation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const menuSections = [
    {
      title: 'Visão Geral',
      items: [
        { label: 'Dashboard', path: '/painel', icon: BarChart3 },
      ],
    },
    {
      title: 'Estrutura & Moradores',
      items: [
        { label: 'Torres & Unidades', path: '/painel/unidades', icon: Layers },
        { label: 'Moradores', path: '/painel/moradores', icon: Users },
        { label: 'Importação Cadastral', path: '/painel/moradores/importar', icon: FileSpreadsheet },
        { label: 'Validação de Vínculos', path: '/painel/moradores/validacoes', icon: UserCheck },
        { label: 'Convites de Acesso', path: '/painel/convites', icon: Send },
      ],
    },
    {
      title: 'Núcleo Documental',
      items: [
        { label: 'Projetos Normativos', path: '/painel/projetos', icon: FolderGit2 },
        { label: 'Central de Exportações', path: '/painel/exportacoes', icon: Download },
      ],
    },
    {
      title: 'Participação & Moderação',
      items: [
        { label: 'Campanhas de Consulta', path: '/painel/campanhas', icon: Sliders },
        { label: 'Fila de Moderação (4D)', path: '/painel/sugestoes', icon: MessageSquare },
        { label: 'Estatísticas Agregadas', path: '/painel/estatisticas', icon: BarChart3 },
      ],
    },
    {
      title: 'Administração',
      items: [
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
            <Building2 className="w-6 h-6 text-brand-400" />
            <span>CONDOC</span>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-brand-900/60 text-brand-300 border border-brand-700">
              Gestão
            </span>
          </Link>
          <button
            className="md:hidden text-slate-400 hover:text-white"
            onClick={() => setIsSidebarOpen(false)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Seletor de Condomínio Ativo */}
        <div className="p-3 border-b border-slate-800">
          <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
            Condomínio Ativo
          </label>
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
                        <Icon className="w-4 h-4 shrink-0" />
                        <span className="truncate">{item.label}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Perfil & Logout */}
        <div className="p-3 border-t border-slate-800 flex items-center justify-between text-xs">
          <div className="truncate pr-2">
            <p className="font-semibold text-white truncate">{user?.full_name || 'Usuário Gestão'}</p>
            <p className="text-[11px] text-slate-400 capitalize">{activeRole}</p>
          </div>
          <button
            onClick={logout}
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
            title="Encerrar Sessão"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>

      {/* Conteúdo Principal */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Topbar Mobile */}
        <header className="md:hidden bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="text-slate-600 hover:text-slate-900"
          >
            <Menu className="w-6 h-6" />
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
