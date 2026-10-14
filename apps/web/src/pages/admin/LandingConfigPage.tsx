import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import {
  Building2,
  Save,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  MessageSquare,
  Mail,
  Phone,
  Sparkles,
  HeartHandshake,
  Layers,
} from 'lucide-react';

export const LandingConfigPage: React.FC = () => {
  const { activeCondominium, refetchCondominiums } = useTenant();

  const [landingTitle, setLandingTitle] = useState('');
  const [landingSubtitle, setLandingSubtitle] = useState('');
  const [landingDescription, setLandingDescription] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [defaultThankYou, setDefaultThankYou] = useState('');

  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (activeCondominium) {
      setLandingTitle((activeCondominium as any).landing_title || '');
      setLandingSubtitle((activeCondominium as any).landing_subtitle || '');
      setLandingDescription((activeCondominium as any).landing_description || '');
      setContactEmail((activeCondominium as any).landing_contact_email || '');
      setContactPhone((activeCondominium as any).landing_contact_phone || '');
      setDefaultThankYou((activeCondominium as any).default_thank_you_message || '');
    }
  }, [activeCondominium]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominium) return;

    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      await api.patch(`/condominiums/${activeCondominium.id}`, {
        landing_title: landingTitle.trim() || null,
        landing_subtitle: landingSubtitle.trim() || null,
        landing_description: landingDescription.trim() || null,
        landing_contact_email: contactEmail.trim() || null,
        landing_contact_phone: contactPhone.trim() || null,
        default_thank_you_message: defaultThankYou.trim() || null,
      });

      setSuccess(true);
      await refetchCondominiums();
      setTimeout(() => setSuccess(false), 3500);
    } catch (err: any) {
      setError(err?.response?.data?.error || err.message || 'Falha ao salvar configurações.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Cabeçalho */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Sparkles className="w-6 h-6 text-indigo-600" />
            <span>Apresentação & Mensagens da Gestão</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Personalize os textos da Landing Page pública e a mensagem oficial de agradecimento enviada aos moradores.
          </p>
        </div>

        <a
          href="/"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors shadow-2xs w-fit"
        >
          <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
          <span>Visualizar Landing Page</span>
        </a>
      </div>

      {success && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-2xl p-4 flex items-center gap-3 animate-in fade-in duration-200">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <span className="text-xs sm:text-sm font-medium">
            Configurações da apresentação e mensagens salvas com sucesso!
          </span>
        </div>
      )}

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span className="text-xs sm:text-sm font-medium">{error}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Seção 1: Landing Page */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-5">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <Building2 className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-bold text-slate-900">
              Apresentação Institucional (Tela Inicial do Domínio)
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Título Principal da Gestão
              </label>
              <input
                type="text"
                value={landingTitle}
                onChange={(e) => setLandingTitle(e.target.value)}
                placeholder={`Exemplo: ${activeCondominium?.name || 'Condomínio'} — Governança Participativa 2026`}
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Aparece em destaque no topo da página inicial de apresentação.
              </p>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Subtítulo / Slogan de Modernização
              </label>
              <input
                type="text"
                value={landingSubtitle}
                onChange={(e) => setLandingSubtitle(e.target.value)}
                placeholder="Exemplo: Processo oficial de revisão e modernização das normas internas do condomínio"
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Mensagem Institucional do Síndico aos Moradores
              </label>
              <textarea
                rows={4}
                value={landingDescription}
                onChange={(e) => setLandingDescription(e.target.value)}
                placeholder="Exemplo: Convidamos todos os proprietários e residentes a participarem ativamente das consultas públicas abertas. Sua colaboração é essencial para elaborarmos regras que reflitam a harmonia e o respeito mútuo em nossa comunidade."
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition resize-y"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-slate-400" />
                <span>E-mail Oficial de Contato da Administração</span>
              </label>
              <input
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                placeholder="sindico@condominio.com.br"
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Phone className="w-3.5 h-3.5 text-slate-400" />
                <span>Telefone / WhatsApp Oficial</span>
              </label>
              <input
                type="text"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                placeholder="(11) 99999-8888"
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition"
              />
            </div>
          </div>
        </div>

        {/* Seção 2: Mensagem Padrão de Agradecimento */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <HeartHandshake className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-bold text-slate-900">
              Mensagem de Agradecimento Pós-Envio
            </h2>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Texto de Agradecimento Exibido ao Morador
            </label>
            <textarea
              rows={3}
              value={defaultThankYou}
              onChange={(e) => setDefaultThankYou(e.target.value)}
              placeholder="Exemplo: Agradecemos imensamente sua contribuição! A participação dos moradores é fundamental para construirmos regras que reflitam a harmonia e o respeito mútuo em nosso condomínio."
              className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition resize-y"
            />
            <p className="text-[11px] text-slate-400 mt-1">
              Esta mensagem é exibida na tela de confirmação após o morador registrar uma sugestão.
              Caso uma consulta tenha mensagem específica definida, ela terá prioridade sobre esta.
            </p>
          </div>
        </div>

        {/* Botão de Salvar */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm shadow-sm transition active:scale-95 disabled:opacity-50 cursor-pointer"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Salvando...' : 'Salvar Alterações'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
