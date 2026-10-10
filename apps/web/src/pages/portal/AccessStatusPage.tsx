import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { CheckCircle2, Clock, AlertTriangle, ShieldCheck, ArrowRight } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export const AccessStatusPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const steps = [
    {
      title: '1. Contato Confirmado',
      description: 'E-mail ou telefone autenticado com sucesso.',
      status: 'completed',
    },
    {
      title: '2. Cadastro de Morador',
      description: 'Dados pessoais e declaração de unidade residencial.',
      status: 'completed',
    },
    {
      title: '3. Validação Documental de Vínculo',
      description: 'A administração confere a titularidade ou contrato de locação da unidade.',
      status: 'verified', // ou 'in_review'
    },
    {
      title: '4. Habilitação na Consulta Pública',
      description: 'Permissão ativa para ler minutas, enviar sugestões e concordâncias.',
      status: 'active',
    },
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Situação de Acesso à Consulta</h1>
        <p className="text-xs text-slate-500 mt-1">
          Acompanhe os requisitos de governança e validação para sua participação nas normas do condomínio.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Etapas de Habilitação</CardTitle>
          <CardDescription>
            Conforme regras de integridade do PRD Mestre v3.0, a mera confirmação de e-mail não comprova residência.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            {steps.map((st, i) => (
              <div key={i} className="flex items-start gap-3 p-3.5 rounded-xl border border-slate-100 bg-slate-50/50">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-slate-900">{st.title}</h4>
                  <p className="text-xs text-slate-600 mt-0.5">{st.description}</p>
                </div>
                <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                  Habilitado
                </span>
              </div>
            ))}
          </div>
        </CardContent>
        <CardFooter className="justify-between">
          <span className="text-xs text-slate-500">Seu acesso está pronto para uso.</span>
          <Button onClick={() => navigate('/portal')}>
            <span>Acessar a Minuta em Consulta</span>
            <ArrowRight className="w-4 h-4 ml-1.5" />
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};
