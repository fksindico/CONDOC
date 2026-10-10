import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useTenant } from '@/contexts/TenantContext';
import { User, Home, Mail, Phone, ShieldCheck } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

export const ResidentProfilePage: React.FC = () => {
  const { user } = useAuth();
  const { activeCondominium } = useTenant();

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">Meu Cadastro de Morador</h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Confira seus dados pessoais e vínculos declarados com as unidades autônomas (M12A).
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <User className="w-5 h-5 text-brand-600" />
            <span>Dados da Conta</span>
          </CardTitle>
          <CardDescription>Informações associadas à sua autenticação no condomínio.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-xs sm:text-sm">
          <div className="flex items-center justify-between border-b pb-3">
            <span className="text-slate-500">Nome Completo:</span>
            <strong className="text-slate-900">{user?.full_name || 'Morador'}</strong>
          </div>
          <div className="flex items-center justify-between border-b pb-3">
            <span className="text-slate-500">E-mail:</span>
            <span className="text-slate-800 font-mono">{user?.email || '—'}</span>
          </div>
          <div className="flex items-center justify-between border-b pb-3">
            <span className="text-slate-500">Condomínio Vinculado:</span>
            <span className="text-slate-900 font-semibold">{activeCondominium?.name || 'Condomínio'}</span>
          </div>
          <div className="flex items-center justify-between pt-1">
            <span className="text-slate-500">Status do Vínculo:</span>
            <Badge variant="success">Residência Validada</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
