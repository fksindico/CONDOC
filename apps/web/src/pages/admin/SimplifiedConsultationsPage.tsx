import React, { useState, useEffect } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import {
  FileText,
  Plus,
  Share2,
  Copy,
  Check,
  Download,
  Printer,
  Trash2,
  Clock,
  Search,
  Filter,
  ExternalLink,
  MessageCircle,
  FileSpreadsheet,
  AlertCircle,
  Building,
  CheckCircle2,
  Calendar,
  Layers,
  ChevronRight,
  Eye,
} from 'lucide-react';
import {
  consultationService,
  AdminConsultation,
  ConsultationSuggestionItem,
} from '@/services/consultationService';

export const SimplifiedConsultationsPage: React.FC = () => {
  const { activeCondominium } = useTenant();

  const [consultations, setConsultations] = useState<AdminConsultation[]>([]);
  const [selectedConsultation, setSelectedConsultation] = useState<AdminConsultation | null>(null);
  const [suggestions, setSuggestions] = useState<ConsultationSuggestionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  // Filtros de Sugestões
  const [actionFilter, setActionFilter] = useState('todos');
  const [searchText, setSearchText] = useState('');
  const [unitFilter, setUnitFilter] = useState('');

  // Modal de Criação
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDocType, setNewDocType] = useState<'regimento' | 'convencao'>('regimento');
  const [newDescription, setNewDescription] = useState('');
  const [newDeadline, setNewDeadline] = useState('');
  const [newPdfFile, setNewPdfFile] = useState<File | null>(null);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Notificação de Cópia
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  const condoId = activeCondominium?.id;

  // Carrega Consultas
  const loadConsultations = () => {
    if (!condoId) return;
    setLoading(true);
    consultationService
      .getAdminConsultations(condoId)
      .then((data) => {
        setConsultations(data);
        if (data.length > 0 && !selectedConsultation) {
          setSelectedConsultation(data[0]);
        } else if (selectedConsultation) {
          const updated = data.find((c) => c.id === selectedConsultation.id);
          if (updated) setSelectedConsultation(updated);
        }
      })
      .catch((err) => {
        console.error('Erro ao carregar consultas:', err);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    loadConsultations();
  }, [condoId]);

  // Carrega Sugestões da Consulta Selecionada
  const loadSuggestions = () => {
    if (!condoId || !selectedConsultation) return;
    setLoadingSuggestions(true);
    consultationService
      .getAdminSuggestions(condoId, selectedConsultation.id, {
        action_type: actionFilter,
        search: searchText,
        unit_code: unitFilter,
      })
      .then((data) => {
        setSuggestions(data);
      })
      .catch((err) => {
        console.error('Erro ao carregar sugestões:', err);
      })
      .finally(() => {
        setLoadingSuggestions(false);
      });
  };

  useEffect(() => {
    loadSuggestions();
  }, [condoId, selectedConsultation, actionFilter, searchText, unitFilter]);

  // Criação de Nova Consulta
  const handleCreateConsultation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!condoId) return;

    if (!newTitle.trim()) {
      setCreateError('Título da consulta é obrigatório.');
      return;
    }
    if (!newPdfFile) {
      setCreateError('Por favor, selecione o arquivo PDF do documento.');
      return;
    }

    setCreating(true);
    setCreateError(null);

    const formData = new FormData();
    formData.append('title', newTitle.trim());
    formData.append('document_type', newDocType);
    if (newDescription.trim()) formData.append('description', newDescription.trim());
    if (newDeadline) formData.append('deadline', newDeadline);
    formData.append('pdf_file', newPdfFile);

    try {
      const created = await consultationService.createAdminConsultation(condoId, formData);
      setIsModalOpen(false);
      setNewTitle('');
      setNewDescription('');
      setNewDeadline('');
      setNewPdfFile(null);
      loadConsultations();
      setSelectedConsultation(created);
    } catch (err: any) {
      setCreateError(err.message || 'Erro ao criar consulta.');
    } finally {
      setCreating(false);
    }
  };

  // Alteração de Status da Consulta
  const handleStatusChange = async (consultationId: string, status: 'aberta' | 'pausada' | 'encerrada') => {
    if (!condoId) return;
    try {
      await consultationService.updateAdminConsultation(condoId, consultationId, { status });
      loadConsultations();
    } catch (err) {
      console.error('Erro ao atualizar status:', err);
    }
  };

  // Exclusão de Consulta
  const handleDeleteConsultation = async (consultationId: string) => {
    if (!condoId) return;
    if (!window.confirm('Tem certeza que deseja excluir esta consulta e suas sugestões associadas?')) return;
    try {
      await consultationService.deleteAdminConsultation(condoId, consultationId);
      setSelectedConsultation(null);
      loadConsultations();
    } catch (err) {
      console.error('Erro ao excluir consulta:', err);
    }
  };

  // Copia o link público
  const copyPublicLink = (token: string) => {
    const fullUrl = `${window.location.origin}/participar/${token}`;
    navigator.clipboard.writeText(fullUrl);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 2500);
  };

  // Disparo de mensagem no WhatsApp
  const shareWhatsApp = (consultation: AdminConsultation) => {
    const fullUrl = `${window.location.origin}/participar/${consultation.public_token}`;
    const docName = consultation.document_type === 'convencao' ? 'Convenção Condominial' : 'Regimento Interno';
    const text = `Olá, vizinhos do ${activeCondominium?.name || 'Condomínio'}! 🏢\n\nEstá aberta a revisão participativa do nosso ${docName}: "${consultation.title}".\n\nParticipe e envie suas sugestões de melhoria acessando o link:\n👉 ${fullUrl}\n\nSua colaboração é muito importante!`;
    const waUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(text)}`;
    window.open(waUrl, '_blank');
  };

  // Imprimir relatório
  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* Cabeçalho da Página */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-indigo-600 text-xs font-bold uppercase tracking-wider mb-1">
            <FileText className="w-4 h-4" /> Gestão Ágil de Documentos
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Consultas de Regimento & Convenção (PDF)</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Publique o documento original em PDF e gere links simples para os moradores enviarem sugestões de revisão.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl shadow-xs transition"
        >
          <Plus className="w-4 h-4" /> Nova Consulta em PDF
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-500">Carregando consultas públicas...</p>
        </div>
      ) : consultations.length === 0 ? (
        /* Estado Vazio */
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 max-w-xl mx-auto space-y-4">
          <div className="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto">
            <FileText className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Nenhuma Consulta em Andamento</h2>
          <p className="text-sm text-slate-500 leading-relaxed">
            Faça o upload do seu Regimento Interno ou Convenção em formato PDF para iniciar a coleta de sugestões dos condôminos de forma simples e desburocratizada.
          </p>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl shadow-xs transition"
          >
            <Plus className="w-4 h-4" /> Criar Primeira Consulta
          </button>
        </div>
      ) : (
        /* Grade de Consultas e Painel de Sugestões */
        <div className="space-y-6">
          {/* Seletor de Consultas Ativas */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {consultations.map((c) => {
              const isSelected = selectedConsultation?.id === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => setSelectedConsultation(c)}
                  className={`p-4 rounded-2xl border transition cursor-pointer relative ${
                    isSelected
                      ? 'bg-white border-indigo-600 shadow-md ring-2 ring-indigo-500/10'
                      : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider ${
                        c.document_type === 'convencao'
                          ? 'bg-purple-50 text-purple-700'
                          : 'bg-indigo-50 text-indigo-700'
                      }`}
                    >
                      {c.document_type === 'convencao' ? 'Convenção' : 'Regimento Interno'}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider ${
                        c.status === 'aberta'
                          ? 'bg-emerald-50 text-emerald-700'
                          : c.status === 'pausada'
                          ? 'bg-amber-50 text-amber-700'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {c.status}
                    </span>
                  </div>

                  <h3 className="font-bold text-slate-900 text-sm line-clamp-1 mb-1">{c.title}</h3>
                  <p className="text-xs text-slate-500 line-clamp-1 mb-3">
                    Arquivo: {c.pdf_original_name} ({(c.pdf_size_bytes / 1024 / 1024).toFixed(1)} MB)
                  </p>

                  <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs">
                    <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-indigo-600" />
                      {c.suggestions_count} sugestões
                    </span>
                    <span className="text-indigo-600 font-medium flex items-center gap-1">
                      Gerenciar <ChevronRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Detalhes da Consulta Selecionada */}
          {selectedConsultation && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
              {/* Barra de Ações & Link Compartilhável */}
              <div className="p-5 bg-gradient-to-r from-slate-50 to-indigo-50/30 border-b border-slate-200 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h2 className="text-lg font-bold text-slate-900">{selectedConsultation.title}</h2>
                    <select
                      value={selectedConsultation.status}
                      onChange={(e) =>
                        handleStatusChange(
                          selectedConsultation.id,
                          e.target.value as 'aberta' | 'pausada' | 'encerrada'
                        )
                      }
                      className="text-xs font-semibold px-2 py-1 bg-white border border-slate-300 rounded-lg focus:outline-hidden"
                    >
                      <option value="aberta">🟢 Aberta para Envios</option>
                      <option value="pausada">🟡 Pausada Temporariamente</option>
                      <option value="encerrada">🔴 Encerrada</option>
                    </select>
                  </div>
                  <p className="text-xs text-slate-500">
                    PDF Original: <strong>{selectedConsultation.pdf_original_name}</strong> | Prazo:{' '}
                    {selectedConsultation.deadline
                      ? new Date(selectedConsultation.deadline).toLocaleDateString('pt-BR')
                      : 'Indeterminado'}
                  </p>
                </div>

                {/* Bloco de Compartilhamento Direto */}
                <div className="flex items-center gap-2 flex-wrap">
                  <button
                    onClick={() => copyPublicLink(selectedConsultation.public_token)}
                    className="inline-flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 text-xs font-medium rounded-xl shadow-2xs transition"
                  >
                    {copiedToken === selectedConsultation.public_token ? (
                      <Check className="w-4 h-4 text-emerald-600" />
                    ) : (
                      <Copy className="w-4 h-4 text-slate-500" />
                    )}
                    {copiedToken === selectedConsultation.public_token ? 'Link Copiado!' : 'Copiar Link'}
                  </button>

                  <button
                    onClick={() => shareWhatsApp(selectedConsultation)}
                    className="inline-flex items-center gap-1.5 px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow-2xs transition"
                  >
                    <MessageCircle className="w-4 h-4" /> WhatsApp
                  </button>

                  <a
                    href={`/participar/${selectedConsultation.public_token}`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold rounded-xl transition"
                  >
                    <ExternalLink className="w-4 h-4" /> Ver Como Morador
                  </a>

                  <button
                    onClick={() => handleDeleteConsultation(selectedConsultation.id)}
                    className="p-2 text-rose-600 hover:bg-rose-50 rounded-xl transition"
                    title="Excluir Consulta"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Barra de Filtros e Exportação */}
              <div className="p-4 border-b border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-3 bg-white">
                <div className="flex items-center gap-2 flex-wrap flex-1">
                  {/* Busca Textual */}
                  <div className="relative min-w-[200px] flex-1 sm:flex-initial">
                    <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      value={searchText}
                      onChange={(e) => setSearchText(e.target.value)}
                      placeholder="Buscar por artigo, texto ou morador..."
                      className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>

                  {/* Filtro por Ação */}
                  <select
                    value={actionFilter}
                    onChange={(e) => setActionFilter(e.target.value)}
                    className="px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg font-medium text-slate-700 focus:outline-hidden"
                  >
                    <option value="todos">Todas as Ações</option>
                    <option value="alterar">✏️ Alterar Redação</option>
                    <option value="remover">🗑️ Remover Dispositivo</option>
                    <option value="incluir">➕ Incluir Nova Regra</option>
                  </select>

                  {/* Filtro por Unidade */}
                  <input
                    type="text"
                    value={unitFilter}
                    onChange={(e) => setUnitFilter(e.target.value)}
                    placeholder="Filtrar Unidade (ex: 402)"
                    className="w-32 px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden"
                  />
                </div>

                {/* Botões de Exportação */}
                <div className="flex items-center gap-2 shrink-0">
                  <a
                    href={condoId ? consultationService.getExportUrl(condoId, selectedConsultation.id) : '#'}
                    download
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-semibold rounded-lg transition"
                    title="Exportar para Excel (CSV UTF-8)"
                  >
                    <FileSpreadsheet className="w-4 h-4" /> Exportar Excel (CSV)
                  </a>
                  <button
                    onClick={handlePrint}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition"
                  >
                    <Printer className="w-4 h-4" /> Imprimir Relatório
                  </button>
                </div>
              </div>

              {/* Tabela de Sugestões Recebidas */}
              <div className="overflow-x-auto">
                {loadingSuggestions ? (
                  <div className="p-8 text-center text-slate-500 text-xs">Carregando sugestões...</div>
                ) : suggestions.length === 0 ? (
                  <div className="p-8 text-center text-slate-500 text-sm">
                    Nenhuma sugestão encontrada com os filtros selecionados.
                  </div>
                ) : (
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase text-[10px] tracking-wider">
                        <th className="py-3 px-4">Protocolo</th>
                        <th className="py-3 px-4">Morador & Contato</th>
                        <th className="py-3 px-4">Unidade</th>
                        <th className="py-3 px-4">Dispositivo</th>
                        <th className="py-3 px-4">Ação</th>
                        <th className="py-3 px-4 min-w-[280px]">Sugestão / Redação</th>
                        <th className="py-3 px-4 min-w-[200px]">Justificativa</th>
                        <th className="py-3 px-4">Data</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {suggestions.map((sug) => {
                        const actionStyle =
                          sug.action_type === 'alterar'
                            ? 'bg-blue-50 text-blue-700 border-blue-200'
                            : sug.action_type === 'remover'
                            ? 'bg-rose-50 text-rose-700 border-rose-200'
                            : 'bg-emerald-50 text-emerald-700 border-emerald-200';

                        const waClean = sug.resident_phone.replace(/\D/g, '');

                        return (
                          <tr key={sug.id} className="hover:bg-slate-50/80 transition">
                            <td className="py-3 px-4 font-mono font-bold text-indigo-700 whitespace-nowrap">
                              {sug.protocol}
                            </td>
                            <td className="py-3 px-4">
                              <div className="font-semibold text-slate-900">{sug.resident_name}</div>
                              <div className="flex items-center gap-2 mt-0.5">
                                <a
                                  href={`https://wa.me/55${waClean}`}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-[11px] text-emerald-600 hover:underline flex items-center gap-0.5"
                                  title="Conversar no WhatsApp"
                                >
                                  <MessageCircle className="w-3 h-3" /> {sug.resident_phone}
                                </a>
                              </div>
                              {sug.resident_email && (
                                <div className="text-[11px] text-slate-400">{sug.resident_email}</div>
                              )}
                            </td>
                            <td className="py-3 px-4 whitespace-nowrap">
                              <span className="font-semibold text-slate-800">Unidade {sug.unit_code}</span>
                              {sug.block_tower && (
                                <div className="text-[11px] text-slate-500">{sug.block_tower}</div>
                              )}
                            </td>
                            <td className="py-3 px-4 font-semibold text-slate-800">{sug.target_reference}</td>
                            <td className="py-3 px-4 whitespace-nowrap">
                              <span
                                className={`px-2 py-0.5 rounded-md border text-[10px] font-bold uppercase ${actionStyle}`}
                              >
                                {sug.action_type}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-slate-700 leading-relaxed">{sug.suggestion_text}</td>
                            <td className="py-3 px-4 text-slate-500 italic leading-relaxed">
                              {sug.justification || '—'}
                            </td>
                            <td className="py-3 px-4 text-slate-400 whitespace-nowrap text-[11px]">
                              {new Date(sug.created_at).toLocaleDateString('pt-BR')}{' '}
                              {new Date(sug.created_at).toLocaleTimeString('pt-BR', {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Modal: Nova Consulta de Documento com Upload de PDF */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full p-6 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-4">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <FileText className="w-5 h-5 text-indigo-600" /> Nova Consulta em PDF
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold p-1"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateConsultation} className="space-y-4">
              {createError && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {createError}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Título da Consulta *
                </label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="Ex: Revisão Anual do Regimento Interno 2026"
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Tipo de Documento *
                  </label>
                  <select
                    value={newDocType}
                    onChange={(e) => setNewDocType(e.target.value as 'regimento' | 'convencao')}
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-hidden font-medium"
                  >
                    <option value="regimento">Regimento Interno</option>
                    <option value="convencao">Convenção Condominial</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Prazo Final (Opcional)
                  </label>
                  <input
                    type="date"
                    value={newDeadline}
                    onChange={(e) => setNewDeadline(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Arquivo do Documento (PDF Obrigatório) *
                </label>
                <input
                  type="file"
                  required
                  accept="application/pdf"
                  onChange={(e) => setNewPdfFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-hidden file:mr-3 file:py-1 file:px-2.5 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Este PDF ficará visível lado a lado para os moradores no formulário de sugestão.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Descrição ou Orientações aos Moradores
                </label>
                <textarea
                  rows={3}
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Ex: Caros moradores, enviem sugestões sobre áreas comuns e regras de convivência até o dia 30..."
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-5 py-2 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl shadow-xs transition flex items-center gap-1.5"
                >
                  {creating ? 'Fazendo Upload...' : 'Publicar Consulta'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
