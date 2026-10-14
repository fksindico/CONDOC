import React, { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import {
  FileText,
  Send,
  CheckCircle2,
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
  ListFilter,
  Sparkles,
  Columns,
  Maximize2,
  Minimize2,
  ExternalLink,
} from 'lucide-react';
import {
  consultationService,
  PublicConsultation,
  ConsultationSuggestionItem,
  SuggestionSubmission,
  StructureUnit,
  StructureBuilding,
} from '@/services/consultationService';
import { FlipbookViewer } from '@/components/viewer/FlipbookViewer';

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

  // Layout Desktop: 'split' (dividido lado a lado) | 'pdf_only' | 'form_only'
  const [desktopView, setDesktopView] = useState<'split' | 'pdf_only' | 'form_only'>('split');

  // Form State
  const [residentName, setResidentName] = useState('');
  const [residentPhone, setResidentPhone] = useState('');
  const [residentEmail, setResidentEmail] = useState('');
  const [blockTower, setBlockTower] = useState('');
  const [selectedFloor, setSelectedFloor] = useState('');
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
  const [isEditingIdentity, setIsEditingIdentity] = useState(false);
  const [manualUnitEntry, setManualUnitEntry] = useState(false);

  const buildings: StructureBuilding[] = consultation?.structure?.buildings || [];
  const totalUnits = consultation?.structure?.total_units || 0;
  const hasBuildings = buildings.length > 0;
  const hasStructure = hasBuildings && totalUnits > 0;

  // Auto-seleciona a torre se houver apenas uma cadastrada
  useEffect(() => {
    if (buildings.length === 1 && !blockTower) {
      setBlockTower(buildings[0].name);
    }
  }, [buildings, blockTower]);

  // Função utilitária para inferir/obter o rótulo do andar da unidade
  const getFloorLabel = (unit: StructureUnit): string => {
    if (unit.floor_label && unit.floor_label.trim()) {
      return unit.floor_label.trim();
    }
    const digits = unit.code.replace(/\D/g, '');
    if (digits.length >= 3) {
      const floorNum = digits.slice(0, -2);
      return `${floorNum}º Andar`;
    }
    return 'Térreo / Outro';
  };

  // Prédio atualmente selecionado e suas unidades
  const selectedBuilding = useMemo(() => {
    return buildings.find((b) => b.name === blockTower) || null;
  }, [buildings, blockTower]);

  const buildingUnits = useMemo(() => {
    return selectedBuilding ? selectedBuilding.units : [];
  }, [selectedBuilding]);

  // Lista única e ordenada de andares disponíveis na torre selecionada
  const availableFloors = useMemo(() => {
    if (!selectedBuilding) return [];
    const floorMap = new Map<string, string>();
    buildingUnits.forEach((u) => {
      const label = getFloorLabel(u);
      floorMap.set(label, label);
    });
    return Array.from(floorMap.keys()).sort((a, b) => {
      const numA = parseInt(a.replace(/\D/g, ''), 10) || 0;
      const numB = parseInt(b.replace(/\D/g, ''), 10) || 0;
      return numA - numB;
    });
  }, [selectedBuilding, buildingUnits]);

  // Unidades pertencentes estritamente ao andar selecionado
  const unitsOnSelectedFloor = useMemo(() => {
    if (!selectedFloor) return [];
    return buildingUnits.filter((u) => getFloorLabel(u) === selectedFloor);
  }, [buildingUnits, selectedFloor]);

  // Auto-detecção de andar caso a unidade já exista (por exemplo, restaurada do localStorage)
  useEffect(() => {
    if (selectedBuilding && unitCode && !selectedFloor) {
      const matched = buildingUnits.find((u) => u.code === unitCode);
      if (matched) {
        setSelectedFloor(getFloorLabel(matched));
      }
    }
  }, [selectedBuilding, unitCode, selectedFloor, buildingUnits]);

  const handlePhoneChange = (val: string) => {
    const raw = val.replace(/\D/g, '').slice(0, 11);
    if (raw.length <= 2) {
      setResidentPhone(raw);
    } else if (raw.length <= 6) {
      setResidentPhone(`(${raw.slice(0, 2)}) ${raw.slice(2)}`);
    } else if (raw.length <= 10) {
      setResidentPhone(`(${raw.slice(0, 2)}) ${raw.slice(2, 6)}-${raw.slice(6)}`);
    } else {
      setResidentPhone(`(${raw.slice(0, 2)}) ${raw.slice(2, 7)}-${raw.slice(7)}`);
    }
  };

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

  // Carrega histórico de sugestões enviadas exclusivamente neste dispositivo (Segurança Anti-IDOR)
  useEffect(() => {
    if (!token) return;
    try {
      const saved = localStorage.getItem(`condoc_my_suggestions_${token}`);
      if (saved) {
        setMySuggestions(JSON.parse(saved));
      }
    } catch {
      // Ignora erro de parse
    }
  }, [token]);

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
    if (!residentEmail.trim()) {
      setSubmitError('Por favor, informe seu e-mail (obrigatório).');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(residentEmail.trim())) {
      setSubmitError('Por favor, informe um endereço de e-mail válido (exemplo: morador@email.com).');
      return;
    }
    if (!unitCode.trim()) {
      setSubmitError('Por favor, selecione ou informe o número da sua unidade/apartamento.');
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

    // Salva identidade do morador no localStorage para evitar redigitação em envios futuros
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
      resident_email: residentEmail.trim(),
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
      // Atualiza histórico localmente e persiste no localStorage deste dispositivo
      setMySuggestions((prev) => {
        const next = [result, ...prev.filter((s) => s.id !== result.id)];
        try {
          localStorage.setItem(`condoc_my_suggestions_${token}`, JSON.stringify(next));
        } catch {}
        return next;
      });
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
          <p className="text-sm text-slate-500">Preparando o documento oficial para sua análise...</p>
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
    <div className="min-h-screen lg:h-screen bg-slate-100 flex flex-col font-sans lg:overflow-hidden">
      {/* Barra de Cabeçalho Superior */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
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

          {/* Ações do Cabeçalho: Baixar Documento + Alternância de Visualização */}
          <div className="flex items-center gap-2">
            <a
              href={consultation.pdf_download_url}
              download={consultation.pdf_original_name}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded-xl shadow-xs transition"
              title="Baixar documento oficial em PDF"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Baixar PDF</span>
            </a>

            {/* Controles Desktop de Alternância de Visualização (Desktop & Tablet Paisagem >= 1024px) */}
            <div className="hidden lg:flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl border border-slate-200">
              <button
                type="button"
                onClick={() => setDesktopView('split')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                  desktopView === 'split'
                    ? 'bg-white text-indigo-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                title="Exibir documento e formulário lado a lado"
              >
                <Columns className="w-3.5 h-3.5" />
                <span>Dividido</span>
              </button>
              <button
                type="button"
                onClick={() => setDesktopView('pdf_only')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                  desktopView === 'pdf_only'
                    ? 'bg-white text-indigo-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                title="Expandir documento em tela cheia"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Foco no Documento</span>
              </button>
              <button
                type="button"
                onClick={() => setDesktopView('form_only')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                  desktopView === 'form_only'
                    ? 'bg-white text-indigo-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                title="Focar no formulário de sugestão"
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span>Foco na Sugestão</span>
              </button>
            </div>
          </div>
        </div>

        {/* Alternador de Abas Mobile & Tablet Retrato (< 1024px) */}
        <div className="flex border-t border-slate-200 lg:hidden bg-slate-50">
          <button
            onClick={() => setActiveTab('document')}
            className={`flex-1 py-3 text-xs font-medium flex items-center justify-center gap-1.5 border-b-2 transition ${
              activeTab === 'document'
                ? 'border-indigo-600 text-indigo-600 bg-white font-bold'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <FileText className="w-4 h-4" />
            1. Ver Documento (PDF)
          </button>
          <button
            onClick={() => setActiveTab('form')}
            className={`flex-1 py-3 text-xs font-medium flex items-center justify-center gap-1.5 border-b-2 transition ${
              activeTab === 'form'
                ? 'border-indigo-600 text-indigo-600 bg-white font-bold'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <Edit3 className="w-4 h-4" />
            2. Minha Sugestão
          </button>
          {mySuggestions.length > 0 && (
            <button
              onClick={() => setActiveTab('history')}
              className={`py-3 px-3 text-xs font-medium flex items-center justify-center gap-1 border-b-2 transition ${
                activeTab === 'history'
                  ? 'border-indigo-600 text-indigo-600 bg-white font-bold'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <ListFilter className="w-4 h-4" />
              Envios ({mySuggestions.length})
            </button>
          )}
        </div>
      </header>

      {/* Conteúdo Principal */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-2 sm:p-4 flex flex-col lg:flex-row gap-5 lg:h-[calc(100vh-68px)] lg:overflow-hidden min-h-0">
        {/* Painel Esquerdo: Visualizador de PDF Embutido na Própria Página */}
        <section
          className={`flex-col bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden transition-all lg:h-full min-h-0 ${
            // Controle Mobile / Tablet Retrato
            activeTab === 'document' ? 'flex flex-1 min-h-[calc(100vh-140px)]' : 'hidden lg:flex'
          } ${
            // Controle Desktop / Tablet Paisagem
            desktopView === 'form_only'
              ? 'lg:hidden'
              : desktopView === 'pdf_only'
              ? 'flex-1'
              : 'flex-1 min-w-0'
          }`}
        >
          {/* Barra de Controle de Visualização no Topo (Desktop) */}
          <div className="px-4 py-2 bg-slate-100/90 border-b border-slate-200 flex items-center justify-between text-xs shrink-0">
            <div className="flex items-center gap-2 truncate">
              <span className="font-bold text-slate-700 truncate">📖 Leitor Interativo do Documento</span>
            </div>
            <div className="flex items-center gap-2">
              {desktopView === 'split' && (
                <button
                  type="button"
                  onClick={() => setDesktopView('pdf_only')}
                  className="hidden lg:inline-flex items-center gap-1 text-xs text-slate-600 hover:text-indigo-600 font-medium transition"
                  title="Ampliar documento para tela cheia (ocultar formulário)"
                >
                  <Maximize2 className="w-3.5 h-3.5" />
                  <span>Expandir Livro</span>
                </button>
              )}
              {desktopView === 'pdf_only' && (
                <button
                  type="button"
                  onClick={() => setDesktopView('split')}
                  className="hidden lg:inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 font-bold transition"
                  title="Voltar para visualização dividida com formulário"
                >
                  <Minimize2 className="w-3.5 h-3.5" />
                  <span>Dividir com Formulário</span>
                </button>
              )}
            </div>
          </div>

          {/* Visualizador Flipbook Interativo 3D (100% OSS MIT) */}
          <div className="flex-1 w-full relative h-full flex flex-col min-h-0 overflow-hidden">
            <FlipbookViewer
              pdfUrl={consultation.pdf_download_url}
              documentTitle={consultation.pdf_original_name}
              onDownloadPdf={() => {
                const link = document.createElement('a');
                link.href = consultation.pdf_download_url;
                link.download = consultation.pdf_original_name;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
              }}
              className="flex-1 rounded-none border-0 h-full"
            />
          </div>

          {/* Rodapé Mobile: Botão em destaque para ir ao formulário */}
          <div className="p-3 bg-indigo-50/70 border-t border-indigo-100 flex items-center justify-between gap-2 lg:hidden shrink-0">
            <span className="text-xs text-indigo-900 font-medium">Leu o trecho que quer alterar?</span>
            <button
              type="button"
              onClick={() => setActiveTab('form')}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1.5 transition"
            >
              <Edit3 className="w-4 h-4" /> 2. Fazer Minha Sugestão
            </button>
          </div>

          {/* Rodapé Desktop Discreto com Opção de Download Secundária */}
          <div className="hidden lg:flex px-4 py-2 bg-slate-50 border-t border-slate-200 items-center justify-between text-xs text-slate-500 shrink-0">
            <span>Dica: Consulte os artigos ao lado antes de registrar sua sugestão.</span>
            <a
              href={consultation.pdf_download_url}
              download={consultation.pdf_original_name}
              className="text-slate-600 hover:text-indigo-600 flex items-center gap-1 font-medium transition"
              title="Baixar cópia para leitura offline"
            >
              <Download className="w-3.5 h-3.5" /> Baixar cópia em PDF
            </a>
          </div>
        </section>

        {/* Painel Direito: Formulário de Sugestões Zero-Atrito com Scroll Isolado */}
        <section
          className={`flex-col gap-4 transition-all lg:h-full lg:overflow-y-auto overscroll-contain pr-1 custom-scrollbar min-h-0 ${
            // Controle Mobile / Tablet Retrato
            activeTab === 'form' || activeTab === 'history' ? 'flex w-full' : 'hidden lg:flex'
          } ${
            // Controle Desktop / Tablet Paisagem
            desktopView === 'pdf_only'
              ? 'lg:hidden'
              : desktopView === 'form_only'
              ? 'w-full max-w-3xl mx-auto'
              : 'w-full lg:w-[460px] xl:w-[500px] shrink-0'
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
                  Nenhuma sugestão enviada neste dispositivo ainda.
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
            <>
              {/* Botão de Atalho no Mobile para Consultar o Documento */}
              <div className="md:hidden flex items-center justify-between p-3 bg-indigo-50 border border-indigo-200 rounded-xl shadow-xs mb-1 text-xs">
                <span className="text-indigo-900 font-medium">Dúvida no número do artigo?</span>
                <button
                  type="button"
                  onClick={() => setActiveTab('document')}
                  className="font-bold text-indigo-700 bg-white px-3 py-1.5 rounded-lg border border-indigo-200 flex items-center gap-1.5 hover:bg-indigo-50 transition"
                >
                  <FileText className="w-3.5 h-3.5" /> 1. Consultar PDF
                </button>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 sm:p-6">
                <div className="mb-4">
                  <div className="flex items-center gap-2 text-indigo-600 text-xs font-bold uppercase tracking-wider mb-1">
                    <Sparkles className="w-4 h-4" /> Participação de Moradores
                  </div>
                  <h2 className="text-lg font-bold text-slate-900">Formulário de Sugestão</h2>
                  <p className="text-xs text-slate-500 mt-1">
                    Preenchimento simples e direto. Suas sugestões serão analisadas pelo síndico para a versão final.
                  </p>
                </div>

                {isClosed ? (
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs flex items-center gap-2">
                    <Clock className="w-5 h-5 shrink-0" />
                    <span>Esta consulta pública foi encerrada e não está aceitando novos envios no momento.</span>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-4">
                    {submitError && (
                      <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        {submitError}
                      </div>
                    )}

                    {/* Bloco 1: Identificação do Morador */}
                    {residentName && residentPhone && residentEmail && unitCode && !isEditingIdentity ? (
                      <div className="p-3.5 bg-indigo-50/70 border border-indigo-200/80 rounded-xl flex items-center justify-between transition-all">
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="w-9 h-9 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-xs">
                            {residentName.charAt(0).toUpperCase()}
                          </div>
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-slate-900 truncate">{residentName}</span>
                              <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-indigo-100 text-indigo-700 rounded-md shrink-0">
                                Identificado
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-600 mt-0.5 truncate">
                              {blockTower ? `${blockTower} • ` : ''}Apto {unitCode} • WhatsApp: {residentPhone} • {residentEmail}
                            </p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => setIsEditingIdentity(true)}
                          className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold px-2 py-1 rounded-lg hover:bg-indigo-100/60 transition shrink-0 ml-2"
                        >
                          Alterar Dados
                        </button>
                      </div>
                    ) : (
                      <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                            1. Seus Dados de Identificação
                          </span>
                          {isEditingIdentity && (
                            <button
                              type="button"
                              onClick={() => setIsEditingIdentity(false)}
                              className="text-[11px] text-indigo-600 hover:text-indigo-800 font-semibold"
                            >
                              Concluir Edição
                            </button>
                          )}
                        </div>

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
                                onChange={(e) => handlePhoneChange(e.target.value)}
                                placeholder="(11) 99999-9999"
                                className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                              />
                            </div>
                          </div>

                          <div>
                            <label className="block text-xs font-medium text-slate-700 mb-1">E-mail *</label>
                            <div className="relative">
                              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                              <input
                                type="email"
                                required
                                value={residentEmail}
                                onChange={(e) => setResidentEmail(e.target.value)}
                                placeholder="seu@email.com"
                                className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                              />
                            </div>
                          </div>
                        </div>

                        {/* Bloco de Localização Predial com Filtro Encadeado: Torre -> Andar -> Apartamento */}
                        <div className="pt-2 border-t border-slate-200">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-[11px] font-semibold text-slate-600">Localização da Unidade</span>
                            {hasStructure && (
                              <button
                                type="button"
                                onClick={() => setManualUnitEntry(!manualUnitEntry)}
                                className="text-[10px] text-indigo-600 hover:text-indigo-800 font-medium"
                              >
                                {manualUnitEntry ? 'Selecionar da estrutura' : 'Digitar manual'}
                              </button>
                            )}
                          </div>

                          {hasBuildings && !manualUnitEntry ? (
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                              {/* 1. Seleção da Torre */}
                              <div>
                                <label className="block text-[11px] font-medium text-slate-600 mb-1">Torre / Bloco *</label>
                                <div className="relative">
                                  <Layers className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                                  <select
                                    required
                                    value={blockTower}
                                    onChange={(e) => {
                                      const newTower = e.target.value;
                                      setBlockTower(newTower);
                                      setSelectedFloor('');
                                      setUnitCode('');
                                    }}
                                    className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                  >
                                    <option value="">Selecione...</option>
                                    {buildings.map((b) => (
                                      <option key={b.id} value={b.name}>
                                        {b.name}
                                      </option>
                                    ))}
                                  </select>
                                </div>
                              </div>

                              {/* 2. Seleção do Andar para filtrar */}
                              <div>
                                <label className="block text-[11px] font-medium text-slate-600 mb-1">Andar *</label>
                                <select
                                  required
                                  disabled={!blockTower}
                                  value={selectedFloor}
                                  onChange={(e) => {
                                    const newFloor = e.target.value;
                                    setSelectedFloor(newFloor);
                                    setUnitCode('');
                                  }}
                                  className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-slate-100 disabled:text-slate-400"
                                >
                                  <option value="">
                                    {blockTower ? 'Selecione o Andar...' : 'Escolha a torre primeiro'}
                                  </option>
                                  {availableFloors.map((floor) => (
                                    <option key={floor} value={floor}>
                                      {floor}
                                    </option>
                                  ))}
                                </select>
                              </div>

                              {/* 3. Seleção do Apartamento Filtrado pelo Andar */}
                              <div>
                                <label className="block text-[11px] font-medium text-slate-600 mb-1">Apartamento *</label>
                                <div className="relative">
                                  <Home className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                                  <select
                                    required
                                    disabled={!selectedFloor}
                                    value={unitCode}
                                    onChange={(e) => setUnitCode(e.target.value)}
                                    className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-slate-100 disabled:text-slate-400"
                                  >
                                    <option value="">
                                      {selectedFloor ? 'Selecione o Apto...' : 'Escolha o andar'}
                                    </option>
                                    {unitsOnSelectedFloor.map((u) => (
                                      <option key={u.id} value={u.code}>
                                        Apto {u.code}
                                      </option>
                                    ))}
                                    {/* Fallback se a unidade já salva não estiver na lista filtrada */}
                                    {unitCode && !unitsOnSelectedFloor.some((u) => u.code === unitCode) && (
                                      <option value={unitCode}>Apto {unitCode} (salvo)</option>
                                    )}
                                  </select>
                                </div>
                              </div>
                            </div>
                          ) : (
                            /* Modo Manual / Fallback sem estrutura cadastrada */
                            <div className="grid grid-cols-2 gap-2.5">
                              <div>
                                <label className="block text-[11px] font-medium text-slate-600 mb-1">Torre / Bloco</label>
                                <div className="relative">
                                  <Layers className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                                  <input
                                    type="text"
                                    value={blockTower}
                                    onChange={(e) => setBlockTower(e.target.value)}
                                    placeholder="Ex: Bloco A"
                                    className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                  />
                                </div>
                              </div>

                              <div>
                                <label className="block text-[11px] font-medium text-slate-600 mb-1">Unidade / Apto *</label>
                                <div className="relative">
                                  <Home className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
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
                          )}
                        </div>
                      </div>
                    )}

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
                        Consulte o documento em exibição para verificar a numeração exata do artigo.
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
                      Sua contribuição será analisada pela comissão e síndico para a redação da minuta final.
                    </p>
                  </form>
                )}
              </div>
            </>
          )}

          {/* Histórico Resumido no Desktop */}
          {mySuggestions.length > 0 && activeTab !== 'history' && desktopView !== 'pdf_only' && (
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <ListFilter className="w-4 h-4 text-indigo-600" />
                  Minhas Sugestões Enviadas ({mySuggestions.length})
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Unidade {unitCode}</span>
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
