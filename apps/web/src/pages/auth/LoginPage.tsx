import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useTenant } from '@/contexts/TenantContext';
import { Building2, Lock, Mail, ArrowRight, ShieldCheck, UserCheck, User } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const { selectCondominium } = useTenant();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const performLogin = async (userEmail: string, userPassword = '') => {
    setError('');
    setIsLoading(true);
    try {
      const account = await login(userEmail, userPassword);
      if (account.tenant_id) {
        selectCondominium(account.tenant_id);
      }
      const isManager = account.roles?.some((r) => ['sindico', 'admin', 'comissao', 'juridico'].includes(r.toLowerCase()));
      const from = (location.state as any)?.from?.pathname;
      const target = from || (isManager ? '/painel' : '/portal');
      navigate(target, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Falha ao autenticar.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError('Informe um e-mail válido.');
      return;
    }
    performLogin(email, password);
  };

  const demoProfiles = [
    {
      name: 'Dr. Carlos Silva',
      role: 'Síndico Ativo',
      email: 'sindico@parquedasflores.com',
      desc: 'Acesso total a minutas, moderação, mesa de publicação e equipe',
      icon: ShieldCheck,
      badgeColor: 'bg-amber-900/60 text-amber-300 border-amber-700',
    },
    {
      name: 'Mariana Oliveira',
      role: 'Moradora (Apto 101)',
      email: 'mariana.oliveira@exemplo.com',
      desc: 'Portal do morador, envio de sugestões privadas e concordâncias',
      icon: User,
      badgeColor: 'bg-emerald-900/60 text-emerald-300 border-emerald-700',
    },
    {
      name: 'Roberto Santos',
      role: 'Proprietário (B201)',
      email: 'roberto.santos@exemplo.com',
      desc: 'Morador com múltiplas unidades e consulta ativa',
      icon: UserCheck,
      badgeColor: 'bg-blue-900/60 text-blue-300 border-blue-700',
    },
  ];

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center p-3 bg-brand-600 rounded-2xl shadow-lg shadow-brand-500/30 text-white mb-2">
            <Building2 className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">CONDOC — Acesso ao Sistema</h1>
          <p className="text-xs text-slate-400">
            Plataforma de gestão normativa condominial, consultas públicas e participação.
          </p>
        </div>

        {/* Perfis de Acesso Rápido de Demonstração (1 Clique) */}
        <div className="space-y-2.5">
          <span className="block text-center text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Acesso Rápido — Escolha seu Perfil
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            {demoProfiles.map((prof) => {
              const Icon = prof.icon;
              return (
                <button
                  key={prof.email}
                  type="button"
                  onClick={() => performLogin(prof.email)}
                  disabled={isLoading}
                  className="p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-brand-500 hover:bg-slate-900 text-left transition-all duration-150 flex flex-col justify-between group cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                >
                  <div>
                    <span className={`inline-block text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border mb-2 ${prof.badgeColor}`}>
                      {prof.role}
                    </span>
                    <h4 className="text-xs font-bold text-white group-hover:text-brand-300 transition-colors">
                      {prof.name}
                    </h4>
                    <p className="text-[11px] text-slate-500 line-clamp-2 mt-1 leading-tight">
                      {prof.desc}
                    </p>
                  </div>
                  <span className="text-[10px] text-brand-400 font-semibold mt-3 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                    <span>Entrar</span>
                    <ArrowRight className="w-3 h-3" />
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Formulário Manual com E-mail */}
        <Card className="border-slate-800 bg-slate-950 text-white shadow-2xl">
          <CardHeader>
            <CardTitle className="text-white text-base">Entrar com Outro E-mail</CardTitle>
            <CardDescription className="text-slate-400 text-xs">
              Autenticação segura via BFF e cookies HttpOnly.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {error && <Alert variant="error">{error}</Alert>}

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">E-mail Cadastrado</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                  <input
                    type="email"
                    required
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                    placeholder="seu.email@condominio.com.br"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Senha de Acesso (Opcional em Dev)</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                  <input
                    type="password"
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              </div>
            </CardContent>

            <CardFooter className="bg-slate-950/80 border-t border-slate-800/80">
              <Button type="submit" className="w-full" isLoading={isLoading}>
                <span>Acessar</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </CardFooter>
          </form>
        </Card>

        <p className="text-center text-xs text-slate-500">
          Deseja ir diretamente para o portal sem login?{' '}
          <button
            onClick={() => navigate('/portal')}
            className="text-brand-400 hover:underline font-medium cursor-pointer"
          >
            Acessar como Morador Visitante
          </button>
        </p>
      </div>
    </div>
  );
};
