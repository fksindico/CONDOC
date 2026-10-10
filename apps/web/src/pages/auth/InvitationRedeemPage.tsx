import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';
import { Building2, KeyRound, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';

interface InvitationInspectData {
  valid: boolean;
  status: string;
  kind: string;
  condominium_id: string;
  condominium_name: string;
  unit_label?: string | null;
  expires_at: string;
  requires_contact_confirmation: boolean;
}

export const InvitationRedeemPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const tokenParam = searchParams.get('token') || '';

  const [token, setToken] = useState(tokenParam);
  const [contact, setContact] = useState('');
  const [inspection, setInspection] = useState<InvitationInspectData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRedeeming, setIsRedeeming] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleInspect = async (tokenValue: string) => {
    if (!tokenValue) return;
    setIsLoading(true);
    setError('');
    try {
      // CA-10 / V21-19: GET no convite apenas inspeciona, sem consumir nem autenticar
      const res = await api.get<InvitationInspectData>(`/access/invitations/inspect?token=${encodeURIComponent(tokenValue)}`);
      setInspection(res.data);
    } catch (err: any) {
      setError(err.message || 'Convite inválido, expirado ou revogado.');
      setInspection(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (tokenParam) {
      handleInspect(tokenParam);
    }
  }, [tokenParam]);

  const handleRedeem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setError('Informe o código do convite.');
      return;
    }
    setIsRedeeming(true);
    setError('');

    try {
      await api.post('/access/invitations/redeem', {
        token,
        provided_contact: contact.trim(),
      });
      setSuccess(true);
      setTimeout(() => {
        navigate('/portal/situacao');
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Erro ao resgatar convite.');
    } finally {
      setIsRedeeming(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center space-y-1">
          <div className="inline-flex items-center justify-center p-3 bg-brand-600 rounded-2xl shadow-md text-white mb-2">
            <Building2 className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Acesso à Consulta Pública</h1>
          <p className="text-xs text-slate-600">
            Resgate seu convite de morador para participar da revisão das normas do condomínio.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-brand-600" />
              <span>Resgatar Convite de Acesso</span>
            </CardTitle>
            <CardDescription>
              Valide o código fornecido pela administração do seu condomínio.
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleRedeem}>
            <CardContent className="space-y-4">
              {error && <Alert variant="error">{error}</Alert>}
              {success && (
                <Alert variant="success" title="Convite Resgatado com Sucesso!">
                  Seu acesso foi vinculado. Redirecionando para a situação de acesso...
                </Alert>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Código do Convite (Token) *
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    required
                    className="flex-1 text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-brand-500 outline-none uppercase font-mono"
                    placeholder="Ex: CONDOC-INV-XXXX-YYYY"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => handleInspect(token)}
                    isLoading={isLoading}
                  >
                    Verificar
                  </Button>
                </div>
              </div>

              {/* Informações Inspecionadas (CA-10) */}
              {inspection && (
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
                  <div className="flex items-center justify-between font-semibold text-slate-900">
                    <span>{inspection.condominium_name}</span>
                    <span className="text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      Válido
                    </span>
                  </div>
                  {inspection.unit_label && (
                    <p className="text-slate-600">
                      Unidade de Destino: <strong>{inspection.unit_label}</strong>
                    </p>
                  )}
                  <p className="text-slate-500">
                    Modalidade: <span className="capitalize">{inspection.kind.replace('_', ' ')}</span>
                  </p>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Confirmação de Contato (E-mail ou Telefone com DDD) *
                </label>
                <input
                  type="text"
                  required
                  className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-brand-500 outline-none"
                  placeholder="seu.email@exemplo.com ou 11988887777"
                  value={contact}
                  onChange={(e) => setContact(e.target.value)}
                />
                <p className="text-[11px] text-slate-500 mt-1">
                  O canal informado será conferido com a lista da administração para liberar sua participação.
                </p>
              </div>
            </CardContent>

            <CardFooter>
              <Button type="submit" className="w-full" isLoading={isRedeeming} disabled={success}>
                <span>Confirmar e Entrar</span>
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
};
