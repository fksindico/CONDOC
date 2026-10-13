import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  FileText,
  Send,
  CheckCircle2,
  ExternalLink,
  Download,
  AlertCircle,
  Clock,
  Building,
  User,
  Phone,
  Mail,
  Home,
  Layers,
  Edit3,
  Trash2,
  PlusCircle,
  Copy,
  Check,
  ChevronRight,
  ListFilter,
  Sparkles,
} from 'lucide-react';
import {
  consultationService,
  PublicConsultation,
  ConsultationSuggestionItem,
  SuggestionSubmission,
} from '@/services/consultationService';

interface StoredResidentIdentity {
  name: string;
  phone: string;
  email: string;
  block_tower: string;
  unit: string;
}

const STORAGE_KEY = 'condoc_resident_identity';

export const PublicConsultationPage: React.FC = () => {
  const { token } = useParams<{ token: string }>();

  const [consultation, setConsultation] = useState<PublicConsultation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Layout Mobile: 'document' | 'form' | 'history'
  const [activeTab, setActiveTab] = useState<'document' | 'form' | 'history'>('form');

  // Form State
  const [residentName, setResidentName] = useState('');
  const [residentPhone, setResidentPhone] = useState('');
  const [residentEmail, setResidentEmail] = useState('');
  const [blockTower, setBlockTower] = useState('');
  const [unitCode, setUnitCode] = useState('');

  const [targetReference, setTargetReference] = useState('');
  const [actionType, setActionType] = useState<'alterar' | 'remover' | 'incluir'>('alterar');
  const [suggestionText, setSuggestionText] = useState('');
  const [justification, setJustification] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [lastSubmission, setLastSubmission] = useState<ConsultationSuggestionItem | null>(null);
  const [mySuggestions, setMySuggestions] = useState<ConsultationSuggestionItem[]>([]);
  const [copiedProtocol, setCopiedProtocol] = useState(false);

  // Carrega dados salvos do morador do localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const id: StoredResidentIdentity = JSON.parse(saved);
        if (id.name) setResidentName(id.name);
        if (id.phone) setResidentPhone(id.phone);
        if (id.email) setResidentEmail(id.email);
        if (id.block_tower) setBlockTower(id.block_tower);
        if (id.unit) setUnitCode(id.unit);
      }
    } catch {
      // Ignora erro de parse
    }
  }, []);

  // Carrega a consulta do backend
  useEffect(() => {
    if (!token) return;
    setLoading(true);
    consultationService
      .getPublicConsultation(token)
      .then((data) => {
        setConsultation(data);
        setError(null);
      })
      .catch((err) => {
        setError(err.message || 'Consulta não encontrada ou link expirado.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [token]);

  // Carrega histórico de sugestões do morador para esta consulta
  const loadMyHistory = (phone: string, unit: string) => {
    if (!token || (!phone && !unit)) return;
    consultationService
      .getMySuggestions(token, { phone, unit })
      .then((list) => setMySuggestions(list))
      .catch(() => {});
  };

  useEffect(() => {
    if (residentPhone || unitCode) {
      loadMyHistory(residentPhone, unitCode);
    }
  }, [residentPhone, unitCode, token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    if (!residentName.trim()) {
      setSubmitError('Por favor, informe seu nome completo.');
      return;
    }
    if (!residentPhone.trim()) {
      setSubmitError('Por favor, informe seu telefone com WhatsApp.');
      return;
    }
    if (!unitCode.trim()) {
      setSubmitError('Por favor, informe o número da sua unidade/apartamento.');
      return;
    }
    if (!targetReference.trim()) {
      setSubmitError('Por favor, indique qual artigo, parágrafo ou dispositivo você quer revisar.');
      return;
    }
    if (!suggestionText.trim()) {
      setSubmitError('Por favor, descreva sua sugestão.');
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    // Salva identidade do morador no localStorage para evitar redigitação
    try {
      const identity: StoredResidentIdentity = {
        name: residentName.trim(),
        phone: residentPhone.trim(),
        email: residentEmail.trim(),
        block_tower: blockTower.trim(),
        unit: unitCode.trim(),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(identity));
    } catch {
      // Ignora falha de armazenamento
    }

    const payload: SuggestionSubmission = {
      resident_name: residentName.trim(),
      resident_phone: residentPhone.trim(),
      resident_email: residentEmail.trim() || undefined,
      block_tower: blockTower.trim() || undefined,
      unit_code: unitCode.trim(),
      target_reference: targetReference.trim(),
      action_type: actionType,
      suggestion_text: suggestionText.trim(),
      justification: justification.trim() || undefined,
    };

    try {
      const result = await consultationService.submitSuggestion(token, payload);
      setLastSubmission(result);
      // Limpa os campos da sugestão mantendo os dados pessoais do morador
      setTargetReference('');
      setSuggestionText('');
      setJustification('');
      // Atualiza histórico
      loadMyHistory(residentPhone, unitCode);
      // Rola para o topo do formulário
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err: any) {
      setSubmitError(err.message || 'Erro ao enviar sugestão. Verifique os dados e tente novamente.');
    } finally {
      setSubmitting(false);
    }
  };

  const copyProtocol = () => {
    if (lastSubmission?.protocol) {
      navigator.clipboard.writeText(lastSubmission.protocol);
      setCopiedProtocol(true);
      setTimeout(() => setCopiedProtocol(false), 2500);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 max-w-md w-full text-center">
          <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-slate-800 mb-1">Carregando Consulta Pública</h2>
          <p className="text-sm text-slate-500">Preparando o documento para sua análise...</p>
        </div>
      </div>
    );
  }

  if (error || !consultation) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 max-w-md w-full text-center">
          <div className="w-14 h-14 bg-rose-50 text-rose-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Consulta Não Encontrada</h2>
          <p className="text-sm text-slate-600 mb-6">{error || 'O link informado pode ter sido desativado ou não existe.'}</p>
          <a
            href="/"
            className="inline-flex items-center justify-center w-full px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-medium text-sm rounded-xl transition"
          >
            Voltar ao Início
          </a>
        </div>
      </div>
    );
  }

  const isClosed = consultation.status !== 'aberta';

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      {/* Barra de Cabeçalho Superior */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-sm shrink-0">
              <Building className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 uppercase tracking-wide">
                  {consultation.document_type === 'convencao' ? 'Convenção' : 'Regimento Interno'}
                </span>
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded-md ${
                    consultation.status === 'aberta'
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'bg-amber-50 text-amber-700'
                  }`}
                >
                  {consultation.status === 'aberta' ? 'Em Consulta Aberta' : 'Consulta Encerrada'}
                </span>
              </div>
              <h1 className="text-base sm:text-lg font-bold text-slate-900 truncate">
                {consultation.condominium_name} — {consultation.title}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <a
              href={consultation.pdf_download_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
              title="Abrir PDF em nova aba"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Nova Aba</span>
            </a>
            <a
              href={consultation.pdf_download_url}
              download={consultation.pdf_original_name}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition"
              title="Baixar documento original"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Baixar PDF</span>
            </a>
          </div>
        </div>

        {/* Alternador de Abas Mobile */}
        <div className="flex border-t border-slate-200 md:hidden bg-slate-50">
          <button
            onClick={() => setActiveTab('document')}
            className={`flex-1 py-2.5 text-xs font-medium flex items-center justify-center gap-1.5 border-b-2 transition ${
              activeTab === 'document'
                ? 'border-indigo-600 text-indigo-600 bg-white font-semibold'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <FileText className="w-4 h-4" />
            1. Ver Documento (PDF)
          </button>
          <button
            onClick={() => setActiveTab('form')}
            className={`flex-1 py-2.5 text-xs font-medium flex items-center justify-center gap-1.5 border-b-2 transition ${
              activeTab === 'form'
                ? 'border-indigo-600 text-indigo-600 bg-white font-semibold'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <Edit3 className="w-4 h-4" />
            2. Minha Sugestão
          </button>
          {mySuggestions.length > 0 && (
            <button
              onClick={() => setActiveTab('history')}
              className={`py-2.5 px-3 text-xs font-medium flex items-center justify-center gap-1 border-b-2 transition ${
                activeTab === 'history'
                  ? 'border-indigo-600 text-indigo-600 bg-white font-semibold'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <ListFilter className="w-4 h-4" />
              Envios ({mySuggestions.length})
            </button>
          )}
        </div>
      </header>

      {/* Conteúdo Principal — Split View Lado a Lado no Desktop */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-3 sm:p-5 flex flex-col md:flex-row gap-5">
        {/* Painel Esquerdo: Visualizador de PDF (Lado a Lado no Desktop) */}
        <section
          className={`flex-1 flex-col bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden min-h-[500px] md:min-h-[calc(100vh-140px)] ${
            activeTab === 'document' ? 'flex' : 'hidden md:flex'
          }`}
        >
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-indigo-600" />
              <span className="text-xs font-semibold text-slate-700">Documento Oficial em Revisão</span>
              <span className="text-xs text-slate-400">({consultation.pdf_original_name})</span>
            </div>
            <div className="flex items-center gap-2">
              <a
                href={consultation.pdf_download_url}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-indigo-600 hover:text-indigo-700 flex items-center gap-1 font-medium"
              >
                Tela Cheia <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          <div className="flex-1 w-full bg-slate-200 relative">
            <iframe
              src={`${consultation.pdf_download_url}#toolbar=1&navpanes=0`}
              className="w-full h-full min-h-[500px] border-none"
              title="Visualizador do Documento PDF"
            />
          </div>

          <div className="p-2.5 bg-slate-50 border-t border-slate-200 text-center text-xs text-slate-500">
            Dica: No celular ou tablet, caso prefira, clique em <strong>"Tela Cheia"</strong> para zoom touch.
          </div>
        </section>

        {/* Painel Direito: Formulário de Sugestões Zero-Atrito */}
        <section
          className={`w-full md:w-[460px] lg:w-[500px] flex-col gap-4 shrink-0 ${
            activeTab === 'form' || activeTab === 'history' ? 'flex' : 'hidden md:flex'
          }`}
        >
          {/* Card de Notificação de Sucesso com Protocolo */}
          {lastSubmission && (
            <div className="bg-emerald-50 border-2 border-emerald-500 rounded-2xl p-5 shadow-sm text-slate-800 animate-in fade-in zoom-in-95 duration-200">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-bold text-base text-emerald-900">Sugestão Registrada com Sucesso!</h3>
                  <p className="text-xs text-emerald-700 mt-1">
                    Sua contribuição foi salva e já está disponível para o síndico e comissão no relatório de revisão.
                  </p>

                  <div className="mt-3.5 bg-white rounded-xl p-3 border border-emerald-200 flex items-center justify-between">
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                        Número de Protocolo
                      </span>
                      <span className="text-sm font-mono font-bold text-slate-900">{lastSubmission.protocol}</span>
                    </div>
                    <button
                      onClick={copyProtocol}
                      className="px-2.5 py-1.5 text-xs font-medium text-emerald-700 hover:text-emerald-800 bg-emerald-50 rounded-lg flex items-center gap-1 transition"
                    >
                      {copiedProtocol ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                      {copiedProtocol ? 'Copiado!' : 'Copiar'}
                    </button>
                  </div>

                  <div className="mt-4 flex items-center justify-between pt-2 border-t border-emerald-200/60">
                    <button
                      onClick={() => setLastSubmission(null)}
                      className="text-xs font-semibold text-emerald-800 hover:text-emerald-900 flex items-center gap-1"
                    >
                      <PlusCircle className="w-4 h-4" /> Enviar outra sugestão agora
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Abas Mobile para Histórico de Envios */}
          {activeTab === 'history' ? (
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <ListFilter className="w-5 h-5 text-indigo-600" />
                  Minhas Sugestões ({mySuggestions.length})
                </h3>
                <button
                  onClick={() => setActiveTab('form')}
                  className="text-xs text-indigo-600 hover:underline font-medium"
                >
                  Nova Sugestão
                </button>
              </div>

              {mySuggestions.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-6">
                  Nenhuma sugestão enviada nesta sessão ainda.
                </p>
              ) : (
                <div className="space-y-3">
                  {mySuggestions.map((sug) => (
                    <div key={sug.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-mono font-bold text-indigo-700">{sug.protocol}</span>
                        <span className="px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 font-semibold uppercase text-[10px]">
                          {sug.action_type}
                        </span>
                      </div>
                      <p className="font-semibold text-slate-800 mb-1">{sug.target_reference}</p>
                      <p className="text-slate-600 italic line-clamp-2">"{sug.suggestion_text}"</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Card do Formulário de Sugestão */
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 sm:p-6">
              <div className="mb-4">
                <div className="flex items-center gap-2 text-indigo-600 text-xs font-bold uppercase tracking-wider mb-1">
                  <Sparkles className="w-4 h-4" /> Participação de Moradores
                </div>
                <h2 className="text-lg font-bold text-slate-900">Formulário de Sugestão</h2>
                <p className="text-xs text-slate-500 mt-1">
                  Sem necessidade de senha ou cadastro prévio. Indique qual dispositivo do documento deseja aprimorar.
                </p>
              </div>

              {isClosed ? (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs">
                  <Clock className="w-4 h-4 mb-1" />
                  Esta consulta pública foi encerrada pelo síndico e não está aceitando novos envios no momento.
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  {submitError && (
                    <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 shrink-0" />
                      {submitError}
                    </div>
                  )}

                  {/* Bloco 1: Identificação Leve do Morador */}
                  <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                      1. Seus Dados de Identificação
                    </span>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 mb-1">Nome Completo *</label>
                      <div className="relative">
                        <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                        <input
                          type="text"
                          required
                          value={residentName}
                          onChange={(e) => setResidentName(e.target.value)}
                          placeholder="Ex: João Ferreira de Paula"
                          className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      <div>
                        <label className="block text-xs font-medium text-slate-700 mb-1">WhatsApp / Celular *</label>
                        <div className="relative">
                          <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                          <input
                            type="tel"
                            required
                            value={residentPhone}
                            onChange={(e) => setResidentPhone(e.target.value)}
                            placeholder="(11) 99999-9999"
                            className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-slate-700 mb-1">E-mail (Opcional)</label>
                        <div className="relative">
                          <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                          <input
                            type="email"
                            value={residentEmail}
                            onChange={(e) => setResidentEmail(e.target.value)}
                            placeholder="seu@email.com"
                            className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2.5">
                      <div>
                        <label className="block text-xs font-medium text-slate-700 mb-1">Torre / Bloco</label>
                        <div className="relative">
                          <Layers className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                          <input
                            type="text"
                            value={blockTower}
                            onChange={(e) => setBlockTower(e.target.value)}
                            placeholder="Ex: Torre A"
                            className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-slate-700 mb-1">Unidade / Apto *</label>
                        <div className="relative">
                          <Home className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                          <input
                            type="text"
                            required
                            value={unitCode}
                            onChange={(e) => setUnitCode(e.target.value)}
                            placeholder="Ex: 504"
                            className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Bloco 2: Tipo de Ação Desejada */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-2">
                      2. Qual ação você sugere? *
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      <button
                        type="button"
                        onClick={() => setActionType('alterar')}
                        className={`p-3 rounded-xl border text-center transition flex flex-col items-center gap-1.5 ${
                          actionType === 'alterar'
                            ? 'border-indigo-600 bg-indigo-50/60 text-indigo-700 font-bold ring-2 ring-indigo-500/20'
                            : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        <Edit3 className="w-5 h-5 text-indigo-600" />
                        <span className="text-xs">Alterar</span>
                        <span className="text-[10px] text-slate-500 font-normal hidden sm:block">Mudar redação</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setActionType('remover')}
                        className={`p-3 rounded-xl border text-center transition flex flex-col items-center gap-1.5 ${
                          actionType === 'remover'
                            ? 'border-rose-600 bg-rose-50/60 text-rose-700 font-bold ring-2 ring-rose-500/20'
                            : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        <Trash2 className="w-5 h-5 text-rose-600" />
                        <span className="text-xs">Remover</span>
                        <span className="text-[10px] text-slate-500 font-normal hidden sm:block">Excluir regra</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setActionType('incluir')}
                        className={`p-3 rounded-xl border text-center transition flex flex-col items-center gap-1.5 ${
                          actionType === 'incluir'
                            ? 'border-emerald-600 bg-emerald-50/60 text-emerald-700 font-bold ring-2 ring-emerald-500/20'
                            : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        <PlusCircle className="w-5 h-5 text-emerald-600" />
                        <span className="text-xs">Incluir</span>
                        <span className="text-[10px] text-slate-500 font-normal hidden sm:block">Nova regra</span>
                      </button>
                    </div>
                  </div>

                  {/* Bloco 3: Dispositivo / Ponto do Documento */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      3. Artigo, Parágrafo ou Ponto do Documento *
                    </label>
                    <input
                      type="text"
                      required
                      value={targetReference}
                      onChange={(e) => setTargetReference(e.target.value)}
                      placeholder="Ex: Artigo 14, § 2º ou 'Horário da Piscina'"
                      className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    <p className="text-[11px] text-slate-500 mt-1">
                      Consulte o documento ao lado para indicar a numeração correta.
                    </p>
                  </div>

                  {/* Bloco 4: Texto Sugerido */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      4. Sua Sugestão / Nova Redação Proposta *
                    </label>
                    <textarea
                      required
                      rows={4}
                      value={suggestionText}
                      onChange={(e) => setSuggestionText(e.target.value)}
                      placeholder={
                        actionType === 'alterar'
                          ? 'Escreva como gostaria que ficasse o texto deste artigo...'
                          : actionType === 'remover'
                          ? 'Explique qual trecho exato deve ser retirado...'
                          : 'Escreva o texto da nova regra que você gostaria de incluir...'
                      }
                      className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 leading-relaxed"
                    />
                  </div>

                  {/* Bloco 5: Justificativa */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      5. Por que essa mudança é importante? (Justificativa)
                    </label>
                    <textarea
                      rows={2}
                      value={justification}
                      onChange={(e) => setJustification(e.target.value)}
                      placeholder="Ex: Traz mais segurança, melhora a convivência ou reduz ruídos..."
                      className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 leading-relaxed"
                    />
                  </div>

                  {/* Botão de Envio */}
                  <button
                    type="submit"
                    disabled={submitting}
                    className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-sm rounded-xl shadow-sm transition flex items-center justify-center gap-2"
                  >
                    {submitting ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Registrando sugestão...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4" /> Enviar Sugestão
                      </>
                    )}
                  </button>

                  <p className="text-[11px] text-center text-slate-400">
                    Sua contribuição será analisada pela comissão e síndico para a minuta final.
                  </p>
                </form>
              )}
            </div>
          )}

          {/* Histórico Resumido no Desktop */}
          {mySuggestions.length > 0 && activeTab !== 'history' && (
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <ListFilter className="w-4 h-4 text-indigo-600" />
                  Minhas Sugestões Enviadas ({mySuggestions.length})
                </span>
                <span className="text-[10px] text-slate-400">Unidade {unitCode}</span>
              </div>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {mySuggestions.map((sug) => (
                  <div key={sug.id} className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-indigo-700 text-[11px]">{sug.protocol}</span>
                      <span className="text-[10px] font-semibold uppercase text-slate-500">
                        {sug.action_type}
                      </span>
                    </div>
                    <p className="font-medium text-slate-800 truncate mt-0.5">{sug.target_reference}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
};
