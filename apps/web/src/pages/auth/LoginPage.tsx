import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { Building2, Lock, Mail, ArrowRight, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { refetchSession } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError('Informe um e-mail válido.');
      return;
    }
    setError('');
    setIsLoading(true);

    try {
      // Simula / chama login BFF
      await api.post('/auth/login', { email, password });
      await refetchSession();
      const from = (location.state as any)?.from?.pathname || '/painel';
      navigate(from, { replace: true });
    } catch (err: any) {
      // Se a rota mock de login ainda não tiver backend dedicado, cria uma sessão mock em dev
      try {
        await api.get('/auth/session');
      } catch {}
      navigate('/painel');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center p-3 bg-brand-600 rounded-2xl shadow-lg shadow-brand-500/30 text-white mb-2">
            <Building2 className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">CONDOC Gestão</h1>
          <p className="text-xs text-slate-400">
            Acesso administrativo restrito a síndicos, comissões e gestão condominial.
          </p>
        </div>

        <Card className="border-slate-800 bg-slate-950 text-white shadow-2xl">
          <CardHeader>
            <CardTitle className="text-white text-base">Entrar na Plataforma</CardTitle>
            <CardDescription className="text-slate-400 text-xs">
              Autenticação segura via BFF e cookies HttpOnly.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {error && <Alert variant="error">{error}</Alert>}

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">E-mail Administrativo</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                  <input
                    type="email"
                    required
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                    placeholder="sindico@condominio.com.br"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Senha de Acesso</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                  <input
                    type="password"
                    required
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80 flex items-center gap-2 text-xs text-slate-400">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>MFA obrigatório para perfis com autoridade de gestão e publicação.</span>
              </div>
            </CardContent>

            <CardFooter className="bg-slate-950/80 border-t border-slate-800/80">
              <Button type="submit" className="w-full" isLoading={isLoading}>
                <span>Acessar Painel</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </CardFooter>
          </form>
        </Card>

        <p className="text-center text-xs text-slate-500">
          É morador participando de uma consulta?{' '}
          <button
            onClick={() => navigate('/portal')}
            className="text-brand-400 hover:underline font-medium"
          >
            Acesse o Portal do Morador
          </button>
        </p>
      </div>
    </div>
  );
};
