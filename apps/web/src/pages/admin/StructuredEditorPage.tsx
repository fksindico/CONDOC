import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTenant } from '@/contexts/TenantContext';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/lib/api';
import { TiptapEditor } from '@/components/editor/TiptapEditor';
import {
  FileText,
  Save,
  Plus,
  ArrowLeft,
  AlertTriangle,
  History,
  Lock,
  Layers,
  StickyNote,
  GitBranch,
  Search,
  Check,
  Download,
  ShieldCheck,
  FileCheck,
  RefreshCw,
  FileDown,
  Sparkles,
  Info,
  CheckCircle2,
  XCircle,
  FileSignature,
  BookOpen,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';
import { Breadcrumb } from '@/components/ui/Breadcrumb';

interface PreflightIssue {
  severity: 'blocking' | 'warning' | 'info';
  rule_code: string;
  message: string;
  node_id?: string;
  location_label?: string;
}

interface PreflightReportData {
  is_valid: boolean;
  total_nodes_checked: number;
  blocking_count: number;
  warning_count: number;
  issues: PreflightIssue[];
}

export const StructuredEditorPage: React.FC = () => {
  const { docId } = useParams<{ docId: string }>();
  const { activeCondominiumId } = useTenant();
  const { toast } = useToast();

  const [documentDetail, setDocumentDetail] = useState<any | null>(null);
  const [provisions, setProvisions] = useState<any[]>([]);
  const [selectedProvision, setSelectedProvision] = useState<any | null>(null);
  const [editText, setEditText] = useState('');
  const [editLabel, setEditLabel] = useState('');
  const [changeType, setChangeType] = useState('alterado');
  const [activeEtag, setActiveEtag] = useState<string | null>(null);

  // Filtros da Árvore Normativa
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('todos');

  // Status de Salvamento
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'conflict' | 'error'>('idle');

  // Modal Conflito 409
  const [conflictModalOpen, setConflictModalOpen] = useState(false);
  const [conflictServerText, setConflictServerText] = useState('');

  // Modal Novo Dispositivo
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [newKind, setNewKind] = useState('artigo');
  const [newLabel, setNewLabel] = useState('Art. ');
  const [newText, setNewText] = useState('');

  // Modal Preflight
  const [isPreflightModalOpen, setIsPreflightModalOpen] = useState(false);
  const [preflightProfile, setPreflightProfile] = useState('clean_working');
  const [preflightReport, setPreflightReport] = useState<PreflightReportData | null>(null);
  const [isPreflightLoading, setIsPreflightLoading] = useState(false);

  // Modal Exportação Canônica
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [exportProfile, setExportProfile] = useState<'clean_working' | 'final_presentation' | 'draft'>('clean_working');
  const [isExporting, setIsExporting] = useState(false);
  const [exportManifest, setExportManifest] = useState<any | null>(null);

  // Modal Renumeração LC 95
  const [isRenumberModalOpen, setIsRenumberModalOpen] = useState(false);
  const [renumberPreview, setRenumberPreview] = useState<any | null>(null);
  const [isRenumberLoading, setIsRenumberLoading] = useState(false);

  // Instanciação de Template
  const [isInstantiating, setIsInstantiating] = useState(false);

  // Aba Inferior
  const [activeTab, setActiveTab] = useState<'notas' | 'origens'>('notas');
  const [notes, setNotes] = useState<any[]>([]);
  const [newNoteContent, setNewNoteContent] = useState('');

  const fetchDocumentDetail = async () => {
    if (!activeCondominiumId || !docId) return;
    try {
      const res = await api.get<any>(`/condominiums/${activeCondominiumId}/documents/${docId}`);
      setDocumentDetail(res.data);
    } catch {
      // Document metadata optional
    }
  };

  const fetchProvisions = async () => {
    if (!activeCondominiumId || !docId) return;
    try {
      const res = await api.get<any[]>(`/condominiums/${activeCondominiumId}/documents/${docId}/provisions`);
      const list = res.data || [];
      setProvisions(list);
      if (list.length > 0 && !selectedProvision) {
        selectProvision(list[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchDocumentDetail();
    fetchProvisions();
  }, [activeCondominiumId, docId]);

  const selectProvision = async (prov: any) => {
    setSelectedProvision(prov);
    setEditText(prov.text || '');
    setEditLabel(prov.label || '');
    setChangeType(prov.change_type || 'alterado');
    setActiveEtag(prov.etag || null);
    setSaveStatus('idle');

    if (activeCondominiumId) {
      try {
        const resNotes = await api.get<any[]>(`/condominiums/${activeCondominiumId}/provisions/${prov.id}/notes`);
        setNotes(resNotes.data || []);
      } catch {
        setNotes([]);
      }
    }
  };

  const handleSaveProvision = async () => {
    if (!activeCondominiumId || !selectedProvision) return;
    setSaveStatus('saving');

    try {
      const res = await api.put<any>(
        `/condominiums/${activeCondominiumId}/provisions/${selectedProvision.id}`,
        {
          text: editText,
          label: editLabel,
          change_type: changeType,
        },
        {
          etag: activeEtag,
        }
      );

      setActiveEtag(res.data.etag || null);
      setSaveStatus('saved');
      fetchProvisions();
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (err: any) {
      if (err.status === 409 || err.code === 'CONCURRENCY_CONFLICT') {
        setSaveStatus('conflict');
        setConflictServerText(err.message || 'Outro usuário gravou uma revisão mais recente.');
        setConflictModalOpen(true);
      } else {
        setSaveStatus('error');
        toast.error(err.message || 'Erro ao salvar dispositivo.');
      }
    }
  };

  const handleCreateProvision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !docId) return;

    try {
      await api.post(`/condominiums/${activeCondominiumId}/documents/${docId}/provisions`, {
        kind: newKind,
        label: newLabel,
        text: newText,
        change_type: 'incluido',
      });
      setIsNewModalOpen(false);
      setNewText('');
      toast.success('Dispositivo normativo adicionado com sucesso!');
      fetchProvisions();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao criar dispositivo.');
    }
  };

  const handleQuickInsert = (kind: string, defaultLabel: string) => {
    setNewKind(kind);
    setNewLabel(defaultLabel);
    setNewText('');
    setIsNewModalOpen(true);
  };

  const handleRunPreflight = async () => {
    if (!activeCondominiumId || !docId) return;
    setIsPreflightLoading(true);
    try {
      const res = await api.post<PreflightReportData>(
        `/condominiums/${activeCondominiumId}/documents/${docId}/preflight`,
        { profile: preflightProfile }
      );
      setPreflightReport(res.data);
      setIsPreflightModalOpen(true);
    } catch (err: any) {
      toast.error(err.message || 'Erro ao executar preflight.');
    } finally {
      setIsPreflightLoading(false);
    }
  };

  const handleOpenExportModal = async () => {
    setIsExportModalOpen(true);
    handleRunPreflightSilently();
  };

  const handleRunPreflightSilently = async () => {
    if (!activeCondominiumId || !docId) return;
    try {
      const res = await api.post<PreflightReportData>(
        `/condominiums/${activeCondominiumId}/documents/${docId}/preflight`,
        { profile: exportProfile }
      );
      setPreflightReport(res.data);
    } catch {
      // Ignore silent preflight errors
    }
  };

  const handleDownloadCanonicalFile = async (format: 'pdf' | 'docx') => {
    if (!activeCondominiumId || !docId) return;
    setIsExporting(true);

    try {
      const endpoint = `/api/v1/condominiums/${activeCondominiumId}/documents/${docId}/export/canonical`;
      const res = await fetch(endpoint, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-ID': activeCondominiumId,
        },
        body: JSON.stringify({
          format,
          profile: exportProfile,
          force_without_soffice: false,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.error || 'Falha na exportação canônica.');
      }

      const blob = await res.blob();
      const filename = `${documentDetail?.title || 'Documento_Normativo'}_${exportProfile}.${format}`;
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);

      toast.success(`Download de ${format.toUpperCase()} canônico concluído com sucesso!`);
    } catch (err: any) {
      toast.error(err.message || `Erro ao exportar ${format.toUpperCase()}.`);
    } finally {
      setIsExporting(false);
    }
  };

  const handleGenerateManifestOnly = async () => {
    if (!activeCondominiumId || !docId) return;
    setIsExporting(true);
    try {
      const res = await api.post<any>(
        `/condominiums/${activeCondominiumId}/documents/${docId}/export/canonical`,
        {
          format: 'json',
          profile: exportProfile,
        }
      );
      setExportManifest(res.data.manifest);
      toast.success('Manifesto criptográfico SHA-256 gerado com sucesso!');
    } catch (err: any) {
      toast.error(err.message || 'Erro ao gerar manifesto.');
    } finally {
      setIsExporting(false);
    }
  };

  const handleOpenRenumberModal = async () => {
    if (!activeCondominiumId || !docId) return;
    setIsRenumberLoading(true);
    try {
      const res = await api.get<any>(
        `/condominiums/${activeCondominiumId}/documents/${docId}/renumber?strategy=renumeracao_automatica`
      );
      setRenumberPreview(res.data);
      setIsRenumberModalOpen(true);
    } catch (err: any) {
      toast.error(err.message || 'Erro ao carregar pré-visualização de renumeração.');
    } finally {
      setIsRenumberLoading(false);
    }
  };

  const handleApplyRenumbering = async () => {
    if (!activeCondominiumId || !docId) return;
    setIsRenumberLoading(true);
    try {
      await api.post(
        `/condominiums/${activeCondominiumId}/documents/${docId}/renumber`,
        { strategy: 'renumeracao_automatica' }
      );
      toast.success('Renumeração sequencial determinística LC 95 aplicada com sucesso!');
      setIsRenumberModalOpen(false);
      fetchProvisions();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao aplicar renumeração.');
    } finally {
      setIsRenumberLoading(false);
    }
  };

  const handleInstantiateFromTemplate = async (templateType: 'regimento' | 'convencao') => {
    if (!activeCondominiumId || !documentDetail?.project_id) return;
    setIsInstantiating(true);
    try {
      const title = templateType === 'regimento' ? 'Regimento Interno' : 'Convenção de Condomínio';
      const res = await api.post<any>(
        `/condominiums/${activeCondominiumId}/projects/${documentDetail.project_id}/documents/instantiate-template`,
        {
          template_type: templateType,
          title: `${title} — ${new Date().getFullYear()}`,
        }
      );
      toast.success(`Modelo de ${title} instanciado com ${res.data.provisions_count} dispositivos LC 95!`);
      fetchProvisions();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao instanciar modelo normativo.');
    } finally {
      setIsInstantiating(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCondominiumId || !selectedProvision || !newNoteContent.trim()) return;

    try {
      await api.post(`/condominiums/${activeCondominiumId}/provisions/${selectedProvision.id}/notes`, {
        content: newNoteContent.trim(),
        visibility: 'equipe',
        category: 'redacao',
      });
      setNewNoteContent('');
      toast.success('Nota interna confidencial registrada!');
      const resNotes = await api.get<any[]>(`/condominiums/${activeCondominiumId}/provisions/${selectedProvision.id}/notes`);
      setNotes(resNotes.data || []);
    } catch (err: any) {
      toast.error(err.message || 'Erro ao adicionar nota interna.');
    }
  };

  const filteredProvisions = provisions.filter((prov) => {
    const matchesSearch =
      !searchTerm.trim() ||
      (prov.label && prov.label.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (prov.text && prov.text.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = typeFilter === 'todos' || prov.change_type === typeFilter;
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-4 animate-fade-in">
      <Breadcrumb
        items={[
          { label: 'Projetos Normativos', href: '/painel/projetos' },
          { label: 'Minuta de Trabalho', href: docId ? `/painel/documentos/${docId}` : undefined },
          { label: 'Editor Estruturado' },
        ]}
        showHome
      />

      {/* Topbar do Editor */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center gap-3">
          <Link to={`/painel/projetos`} className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors" aria-label="Voltar aos projetos">
            <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-slate-900 tracking-tight">
                {documentDetail?.title || 'Estação de Redação Normativa'}
              </h1>
              <Badge variant="outline" className="font-mono text-[10px]">
                {provisions.length} dispositivos LC 95
              </Badge>
            </div>
            <p className="text-xs text-slate-500">Editor Contínuo Tiptap Open Source — Renderização Canônica Unificada python-docx + LibreOffice.</p>
          </div>
        </div>

        {/* Ações Estratégicas e Auditoria LC 95 */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Botão Preflight */}
          <Button size="sm" variant="outline" onClick={handleRunPreflight} isLoading={isPreflightLoading}>
            <FileCheck className="w-3.5 h-3.5 mr-1 text-brand-600" aria-hidden="true" />
            <span>Preflight</span>
          </Button>

          {/* Botão Renumeração LC 95 */}
          <Button size="sm" variant="outline" onClick={handleOpenRenumberModal} isLoading={isRenumberLoading}>
            <RefreshCw className="w-3.5 h-3.5 mr-1 text-slate-600" aria-hidden="true" />
            <span>Renumerar LC 95</span>
          </Button>

          {/* Botão Exportação Canônica */}
          <Button size="sm" variant="outline" onClick={handleOpenExportModal}>
            <Download className="w-3.5 h-3.5 mr-1 text-emerald-600" aria-hidden="true" />
            <span>Exportar Canônico</span>
          </Button>

          <Link to={`/painel/documentos/${docId}/compare`}>
            <Button size="sm" variant="outline">
              <GitBranch className="w-3.5 h-3.5 mr-1 text-slate-500" aria-hidden="true" />
              <span>DePara</span>
            </Button>
          </Link>

          <div className="text-xs font-medium px-2">
            {saveStatus === 'saving' && (
              <span className="inline-flex items-center gap-1.5 text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200 animate-pulse font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                Gravando...
              </span>
            )}
            {saveStatus === 'saved' && (
              <span className="inline-flex items-center gap-1.5 text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 font-semibold">
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                Salvo
              </span>
            )}
            {saveStatus === 'conflict' && (
              <span className="inline-flex items-center gap-1.5 text-rose-700 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200 font-bold">
                Conflito 409!
              </span>
            )}
            {saveStatus === 'error' && (
              <span className="inline-flex items-center gap-1.5 text-rose-700 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200 font-semibold">
                Erro
              </span>
            )}
          </div>

          <Button size="sm" onClick={handleSaveProvision} isLoading={saveStatus === 'saving'}>
            <Save className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
            <span>Salvar Dispositivo</span>
          </Button>
        </div>
      </div>

      {/* Banner de Template Rápido (Se o documento estiver vazio) */}
      {provisions.length === 0 && (
        <Card className="border-dashed border-2 border-brand-300 bg-brand-50/40 p-6 text-center">
          <BookOpen className="w-10 h-10 text-brand-600 mx-auto mb-2" />
          <h2 className="text-base font-bold text-slate-900 mb-1">Minuta em Branco — Iniciar com Esqueleto Normativo Aberto</h2>
          <p className="text-xs text-slate-600 max-w-xl mx-auto mb-4">
            Instancie o esqueleto completo em conformidade com a Lei Complementar 95/98 (Títulos, Capítulos, Artigos, Parágrafos e Incisos com novos UUIDs isolados).
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Button
              onClick={() => handleInstantiateFromTemplate('regimento')}
              isLoading={isInstantiating}
              className="bg-brand-700 hover:bg-brand-800"
            >
              <Sparkles className="w-4 h-4 mr-1.5" />
              Instanciar Regimento Interno OSS
            </Button>
            <Button
              variant="outline"
              onClick={() => handleInstantiateFromTemplate('convencao')}
              isLoading={isInstantiating}
            >
              <FileSignature className="w-4 h-4 mr-1.5 text-slate-600" />
              Instanciar Convenção de Condomínio OSS
            </Button>
          </div>
        </Card>
      )}

      {/* Grid Tripartido do Editor (PRD 27.3 / Swiss Pro Max Layout) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* Coluna 1: Árvore Hierárquica de Dispositivos (3 colunas) */}
        <div className="lg:col-span-3 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs flex flex-col max-h-[820px]">
          <div className="p-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-brand-700" aria-hidden="true" />
              <span>Árvore Normativa</span>
            </span>
            <button
              onClick={() => setIsNewModalOpen(true)}
              className="p-1.5 text-brand-700 hover:bg-brand-50 rounded-lg transition-colors"
              title="Adicionar Dispositivo"
              aria-label="Adicionar Dispositivo"
            >
              <Plus className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>

          {/* Barra de Busca e Filtro Rápido */}
          <div className="p-2 border-b border-slate-100 bg-white space-y-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" aria-hidden="true" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Buscar artigo ou termo..."
                className="w-full text-xs pl-8 pr-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-brand-500 focus:bg-white transition-all"
              />
            </div>
            <div className="flex items-center gap-1 overflow-x-auto pb-1 text-[11px]">
              {['todos', 'alterado', 'incluido', 'mantido', 'excluido'].map((type) => (
                <button
                  key={type}
                  onClick={() => setTypeFilter(type)}
                  className={`px-2 py-0.5 rounded-full capitalize whitespace-nowrap transition-colors ${
                    typeFilter === type
                      ? 'bg-brand-800 text-white font-medium shadow-2xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {/* Lista de Dispositivos */}
          <div className="overflow-y-auto p-2 space-y-1 flex-1 text-xs custom-scrollbar">
            {filteredProvisions.length === 0 ? (
              <div className="p-6 text-center text-slate-400">
                <p className="text-xs">Nenhum dispositivo encontrado.</p>
                {searchTerm && (
                  <button
                    onClick={() => setSearchTerm('')}
                    className="mt-1 text-[11px] text-brand-600 hover:underline"
                  >
                    Limpar busca
                  </button>
                )}
              </div>
            ) : (
              filteredProvisions.map((prov) => {
                const isSelected = selectedProvision?.id === prov.id;
                return (
                  <button
                    key={prov.id}
                    onClick={() => selectProvision(prov)}
                    className={`w-full text-left p-2.5 rounded-lg border transition-all flex items-center justify-between group ${
                      isSelected
                        ? 'border-brand-700 bg-brand-50/70 shadow-xs border-l-4 border-l-brand-800'
                        : 'border-transparent hover:bg-slate-50'
                    }`}
                  >
                    <div className="truncate pr-2">
                      <span className={`block truncate ${isSelected ? 'font-bold text-brand-900' : 'font-semibold text-slate-800'}`}>
                        {prov.label || 'Sem rótulo'}
                      </span>
                      <span className="text-[11px] text-slate-500 block truncate font-serif">{prov.text}</span>
                    </div>
                    <Badge variant={(prov.change_type as any) || 'default'} dot={isSelected} className="text-[10px] shrink-0">
                      {prov.change_type || 'mantido'}
                    </Badge>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Coluna 2: Documento-Base Original (Somente Leitura - UI-12) (4 colunas) */}
        <div className="lg:col-span-4 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs flex flex-col max-h-[820px]">
          <div className="p-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
              <span>Base Histórica de Referência</span>
            </span>
            <span className="text-[11px] px-2 py-0.5 rounded bg-slate-200/70 text-slate-700 font-medium">
              Somente Leitura
            </span>
          </div>
          <div className="p-4 overflow-y-auto text-xs font-serif leading-relaxed text-slate-700 bg-slate-50/30 flex-1 space-y-3 custom-scrollbar">
            <div className="p-3 bg-amber-50/50 border border-amber-200/60 rounded-lg text-amber-900 text-[11px]">
              <p className="font-sans font-semibold mb-0.5">Texto Anterior da Convenção / Regimento</p>
              <p className="font-serif">
                Utilizado para confronto direto e rastreabilidade estrita de origens (CA-19 / CA-20). Nenhuma alteração nesta coluna sobrescreve a base histórica.
              </p>
            </div>
            <div className="legal-sheet p-4 space-y-2">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <span className="font-sans font-bold text-slate-900 text-xs">
                  {selectedProvision?.label ? `Referência: ${selectedProvision.label}` : 'Dispositivo'}
                </span>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">Original</span>
              </div>
              <p className="text-slate-800 text-sm leading-relaxed font-serif pt-1">
                {selectedProvision?.text || 'Selecione um dispositivo na árvore à esquerda para conferência.'}
              </p>
            </div>
          </div>
        </div>

        {/* Coluna 3: Editor Ativo Tiptap + Painel de Contexto (5 colunas) */}
        <div className="lg:col-span-5 space-y-4">
          <Card>
            <CardHeader className="p-4 pb-2">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <CardTitle className="text-sm flex items-center gap-2">
                    <span>Edição:</span>
                    <input
                      type="text"
                      className="font-bold text-slate-900 border border-slate-200 rounded px-2 py-0.5 text-sm w-36 outline-none focus:ring-1 focus:ring-brand-500"
                      value={editLabel}
                      onChange={(e) => setEditLabel(e.target.value)}
                    />
                  </CardTitle>
                  <CardDescription className="text-xs mt-0.5">
                    UUID: <code className="text-slate-600">{selectedProvision?.id?.slice(0, 8)}...</code>
                  </CardDescription>
                </div>

                <select
                  className="text-xs border border-slate-200 rounded-lg p-1.5 font-medium outline-none"
                  value={changeType}
                  onChange={(e) => setChangeType(e.target.value)}
                >
                  <option value="mantido">Mantido</option>
                  <option value="alterado">Alterado</option>
                  <option value="incluido">Incluído (Novo)</option>
                  <option value="excluido">Excluído</option>
                  <option value="renumerado">Renumerado</option>
                  <option value="desmembrado">Desmembrado</option>
                  <option value="consolidado">Consolidado</option>
                </select>
              </div>

              {/* Barra de Inserção Rápida de Blocos Normativos LC 95 */}
              <div className="flex flex-wrap items-center gap-1 pt-2 border-t border-slate-100 text-[11px]">
                <span className="text-slate-500 font-semibold mr-1">Inserir:</span>
                <button
                  type="button"
                  onClick={() => handleQuickInsert('artigo', 'Art. ')}
                  className="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded transition-colors font-medium"
                >
                  + Artigo
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickInsert('caput', '')}
                  className="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded transition-colors font-medium"
                >
                  + Caput
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickInsert('paragrafo', '§ 1º ')}
                  className="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded transition-colors font-medium"
                >
                  + Parágrafo
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickInsert('inciso', 'I - ')}
                  className="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded transition-colors font-medium"
                >
                  + Inciso
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickInsert('alinea', 'a) ')}
                  className="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded transition-colors font-medium"
                >
                  + Alínea
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickInsert('anexo', '[Quebra de Página]')}
                  className="px-2 py-0.5 bg-brand-50 hover:bg-brand-100 text-brand-700 rounded transition-colors font-medium"
                >
                  + Quebra de Página
                </button>
              </div>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <TiptapEditor content={editText} onChange={setEditText} className="min-h-[220px]" />
            </CardContent>
          </Card>

          {/* Abas de Contexto: Notas Internas (CA-24) e Mapeamento de Origens */}
          <Card>
            <div className="flex border-b border-slate-100 text-xs font-semibold bg-slate-50/80">
              <button
                onClick={() => setActiveTab('notas')}
                className={`flex-1 py-2.5 px-3 text-center border-b-2 flex items-center justify-center gap-1.5 transition-colors ${
                  activeTab === 'notas'
                    ? 'border-brand-800 text-brand-900 bg-white font-bold shadow-2xs'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <StickyNote className="w-3.5 h-3.5 text-amber-600" aria-hidden="true" />
                <span>Notas Internas ({notes.length})</span>
              </button>
              <button
                onClick={() => setActiveTab('origens')}
                className={`flex-1 py-2.5 px-3 text-center border-b-2 flex items-center justify-center gap-1.5 transition-colors ${
                  activeTab === 'origens'
                    ? 'border-brand-800 text-brand-900 bg-white font-bold shadow-2xs'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <GitBranch className="w-3.5 h-3.5 text-brand-600" aria-hidden="true" />
                <span>Mapeamento de Origem</span>
              </button>
            </div>

            <CardContent className="p-4 text-xs">
              {activeTab === 'notas' ? (
                <div className="space-y-3">
                  <div className="space-y-2 max-h-48 overflow-y-auto custom-scrollbar">
                    {notes.length === 0 ? (
                      <div className="p-4 bg-slate-50 border border-dashed border-slate-200 rounded-lg text-center text-slate-400">
                        <p className="italic">Nenhuma nota interna confidencial registrada para este dispositivo.</p>
                      </div>
                    ) : (
                      notes.map((n) => (
                        <div key={n.id} className="p-2.5 bg-amber-50/60 border border-amber-200/70 rounded-lg text-amber-950 shadow-2xs">
                          <p className="leading-relaxed font-sans">{n.content}</p>
                          <div className="flex items-center justify-between text-[10px] text-amber-800/80 mt-1.5 pt-1 border-t border-amber-200/40">
                            <span className="font-mono uppercase tracking-wider font-semibold">Privado • {n.category}</span>
                            <span className="capitalize">{n.visibility}</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                  <form onSubmit={handleAddNote} className="flex gap-2 pt-2 border-t border-slate-100">
                    <input
                      type="text"
                      className="flex-1 text-xs border border-slate-200 rounded-lg p-2 outline-none focus:ring-1 focus:ring-brand-700 bg-slate-50 focus:bg-white transition-all"
                      placeholder="Registrar observação jurídica privada..."
                      value={newNoteContent}
                      onChange={(e) => setNewNoteContent(e.target.value)}
                    />
                    <Button type="submit" size="sm" variant="outline">
                      Registrar
                    </Button>
                  </form>
                </div>
              ) : (
                <div className="space-y-2 text-slate-600 leading-relaxed">
                  <p>
                    Classificação: <strong className="capitalize">{changeType}</strong>
                  </p>
                  <p className="text-xs text-slate-500">
                    Dispositivos novos (incluídos) são protegidos pela regra CA-19 contra vinculações fictícias a
                    artigos da base anterior.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Modal Preflight (Auditoria Prévia LC 95) */}
      <Modal
        isOpen={isPreflightModalOpen}
        onClose={() => setIsPreflightModalOpen(false)}
        title="Auditoria Estrutural Preflight (EDOSS-EX-04)"
      >
        <div className="space-y-4 text-xs">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div>
              <span className="text-xs font-semibold text-slate-700">Perfil de Validação:</span>
              <select
                className="ml-2 border border-slate-300 rounded px-2 py-1 text-xs font-medium"
                value={preflightProfile}
                onChange={(e) => setPreflightProfile(e.target.value)}
              >
                <option value="clean_working">Minuta de Trabalho Limpa</option>
                <option value="final_presentation">Apresentação Oficial Final</option>
                <option value="draft">Rascunho</option>
              </select>
            </div>
            <Button size="sm" variant="outline" onClick={handleRunPreflight} isLoading={isPreflightLoading}>
              <RefreshCw className="w-3.5 h-3.5 mr-1" />
              Revalidar
            </Button>
          </div>

          {preflightReport && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 p-3 rounded-lg border bg-slate-50">
                {preflightReport.is_valid ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                ) : (
                  <XCircle className="w-5 h-5 text-rose-600 shrink-0" />
                )}
                <div>
                  <div className="font-bold text-slate-900">
                    {preflightReport.is_valid
                      ? 'Árvore Normativa 100% Conforme com LC 95/98'
                      : `${preflightReport.blocking_count} Inconsistência(s) Impeditiva(s) Encontrada(s)`}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {preflightReport.total_nodes_checked} nós auditados • {preflightReport.warning_count} aviso(s)
                  </div>
                </div>
              </div>

              {/* Lista de Questões / Inconsistências */}
              <div className="max-h-60 overflow-y-auto space-y-2 custom-scrollbar">
                {preflightReport.issues.length === 0 ? (
                  <div className="text-center p-4 text-emerald-700 bg-emerald-50 rounded-lg">
                    Nenhuma violação de gramática normativa detectada. O documento está apto para exportação canônica.
                  </div>
                ) : (
                  preflightReport.issues.map((iss, idx) => (
                    <div
                      key={idx}
                      className={`p-2.5 rounded-lg border flex items-start gap-2 ${
                        iss.severity === 'blocking'
                          ? 'bg-rose-50 border-rose-200 text-rose-900'
                          : iss.severity === 'warning'
                          ? 'bg-amber-50 border-amber-200 text-amber-900'
                          : 'bg-blue-50 border-blue-200 text-blue-900'
                      }`}
                    >
                      <span className="font-mono text-[10px] uppercase font-bold shrink-0 mt-0.5 px-1 rounded bg-white/70">
                        {iss.rule_code}
                      </span>
                      <div className="flex-1">
                        <p className="font-medium">{iss.message}</p>
                        {iss.location_label && (
                          <span className="text-[10px] text-slate-500 block mt-0.5">
                            Localização: {iss.location_label}
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          <div className="flex justify-end pt-2 border-t border-slate-100">
            <Button onClick={() => setIsPreflightModalOpen(false)}>Fechar Auditoria</Button>
          </div>
        </div>
      </Modal>

      {/* Modal Exportação Canônica Open Source (DOCX + PDF) */}
      <Modal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        title="Exportação Canônica Dual Open Source (ED-OSS-2.0)"
      >
        <div className="space-y-4 text-xs">
          <Alert variant="info" title="Pipeline Canônico de Fonte Única">
            O documento é compilado localmente em DOCX (python-docx) e convertido pelo LibreOffice Headless em PDF gêmeo idêntico, com selagem criptográfica por hash SHA-256 no Manifesto de Integridade.
          </Alert>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Perfil de Exportação
            </label>
            <select
              className="w-full text-xs border border-slate-300 rounded-lg p-2 font-medium outline-none"
              value={exportProfile}
              onChange={(e) => {
                setExportProfile(e.target.value as any);
                handleRunPreflightSilently();
              }}
            >
              <option value="clean_working">Minuta de Trabalho Limpa (Sem notas privadas)</option>
              <option value="final_presentation">Apresentação Oficial (Conformidade estrita ABNT/LC 95)</option>
              <option value="draft">Rascunho Preliminar</option>
            </select>
          </div>

          {/* Status do Preflight antes de exportar */}
          {preflightReport && (
            <div className={`p-2.5 rounded-lg border flex items-center justify-between ${
              preflightReport.is_valid ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'
            }`}>
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 shrink-0" />
                <span className="font-semibold">
                  {preflightReport.is_valid
                    ? 'Preflight Aprovado — Pronto para Exportar'
                    : `Preflight com ${preflightReport.blocking_count} erro(s) impeditivo(s)`}
                </span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setIsExportModalOpen(false);
                  setIsPreflightModalOpen(true);
                }}
                className="underline text-[11px] font-bold"
              >
                Ver Detalhes
              </button>
            </div>
          )}

          {/* Ações de Download Dual */}
          <div className="grid grid-cols-2 gap-3 pt-2">
            <Button
              variant="outline"
              onClick={() => handleDownloadCanonicalFile('docx')}
              isLoading={isExporting}
              className="flex items-center justify-center gap-1.5"
            >
              <FileDown className="w-4 h-4 text-blue-600" />
              <span>Baixar DOCX Canônico</span>
            </Button>
            <Button
              onClick={() => handleDownloadCanonicalFile('pdf')}
              isLoading={isExporting}
              className="flex items-center justify-center gap-1.5 bg-emerald-700 hover:bg-emerald-800"
            >
              <Download className="w-4 h-4" />
              <span>Baixar PDF Oficial</span>
            </Button>
          </div>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
            <button
              type="button"
              onClick={handleGenerateManifestOnly}
              className="text-brand-700 hover:underline font-semibold"
            >
              Visualizar Manifesto Criptográfico SHA-256
            </button>
            <Button variant="ghost" onClick={() => setIsExportModalOpen(false)}>
              Fechar
            </Button>
          </div>

          {exportManifest && (
            <div className="p-3 bg-slate-900 text-slate-100 rounded-lg font-mono text-[11px] max-h-48 overflow-y-auto custom-scrollbar">
              <pre>{JSON.stringify(exportManifest, null, 2)}</pre>
            </div>
          )}
        </div>
      </Modal>

      {/* Modal Renumeração Sequencial Determinística LC 95 */}
      <Modal
        isOpen={isRenumberModalOpen}
        onClose={() => setIsRenumberModalOpen(false)}
        title="Renumeração Sequencial Determinística (LC 95/98)"
      >
        <div className="space-y-4 text-xs">
          <Alert variant="info" title="Preservação de Referências e UUIDs">
            A renumeração recalcula os rótulos de Artigos, Parágrafos, Incisos e Alíneas preservando estritamente os UUIDs e mantendo as referências cruzadas intactas.
          </Alert>

          {renumberPreview && (
            <div className="space-y-2">
              <div className="text-slate-700 font-semibold">
                Divergências detectadas: {renumberPreview.discrepancies_count || 0}
              </div>
              <div className="max-h-60 overflow-y-auto border rounded-lg custom-scrollbar">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b text-slate-600">
                      <th className="p-2">Posição</th>
                      <th className="p-2">Rótulo Atual</th>
                      <th className="p-2">Rótulo LC 95 Proposto</th>
                      <th className="p-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(renumberPreview.preview_items || []).slice(0, 30).map((it: any, idx: number) => (
                      <tr key={idx} className="border-b hover:bg-slate-50">
                        <td className="p-2 font-mono text-slate-500">{it.position}</td>
                        <td className="p-2 font-bold text-slate-700">{it.current_label}</td>
                        <td className="p-2 font-bold text-brand-800">{it.new_label}</td>
                        <td className="p-2">
                          {it.has_changed ? (
                            <Badge variant="warning" className="text-[10px]">Alterará</Badge>
                          ) : (
                            <Badge variant="outline" className="text-[10px]">Inalterado</Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button variant="outline" onClick={() => setIsRenumberModalOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleApplyRenumbering} isLoading={isRenumberLoading}>
              Aplicar Renumeração LC 95
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal Conflito de Concorrência 409 (UI-14, CA-23) */}
      <Modal
        isOpen={conflictModalOpen}
        onClose={() => setConflictModalOpen(false)}
        title="Conflito de Edição Concorrente (HTTP 409)"
        description="Outro usuário da gestão gravou uma nova revisão enquanto você editava este dispositivo."
      >
        <div className="space-y-4 text-xs">
          <Alert variant="warning" title="Resolução Explícita Obrigatória">
            Para garantir a integridade do histórico normativo, suas alterações locais não sobrescreveram a versão mais
            recente. Resolva a divergência antes de gravar.
          </Alert>

          <div>
            <span className="font-semibold text-slate-800 block mb-1">Versão Mais Recente Gravada no Servidor:</span>
            <div className="p-2.5 bg-slate-50 border rounded-lg font-mono text-slate-700 max-h-32 overflow-y-auto">
              {conflictServerText}
            </div>
          </div>

          <div>
            <span className="font-semibold text-slate-800 block mb-1">Sua Versão Local em Edição:</span>
            <div className="p-2.5 bg-blue-50/50 border border-blue-200 rounded-lg font-mono text-slate-800 max-h-32 overflow-y-auto">
              {editText}
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              onClick={() => {
                setConflictModalOpen(false);
                fetchProvisions();
              }}
            >
              Descartar Minhas Alterações
            </Button>
            <Button
              onClick={() => {
                setConflictModalOpen(false);
              }}
            >
              Fechar
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal Novo Dispositivo */}
      <Modal
        isOpen={isNewModalOpen}
        onClose={() => setIsNewModalOpen(false)}
        title="Incluir Novo Dispositivo Normativo"
      >
        <form onSubmit={handleCreateProvision} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Tipo Estrutural *
              </label>
              <select
                className="w-full text-sm border border-slate-300 rounded-lg p-2 outline-none"
                value={newKind}
                onChange={(e) => {
                  setNewKind(e.target.value);
                  if (e.target.value === 'artigo' && !newLabel.startsWith('Art.')) setNewLabel('Art. ');
                  if (e.target.value === 'paragrafo' && !newLabel.startsWith('§')) setNewLabel('§ 1º ');
                  if (e.target.value === 'inciso' && !newLabel.startsWith('I')) setNewLabel('I - ');
                  if (e.target.value === 'alinea' && !newLabel.startsWith('a)')) setNewLabel('a) ');
                }}
              >
                <option value="artigo">Artigo</option>
                <option value="caput">Caput</option>
                <option value="paragrafo">Parágrafo</option>
                <option value="inciso">Inciso</option>
                <option value="alinea">Alínea</option>
                <option value="capitulo">Capítulo</option>
                <option value="anexo">Anexo / Tabela</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Rótulo *
              </label>
              <input
                type="text"
                required
                className="w-full text-sm border border-slate-300 rounded-lg p-2 outline-none font-bold"
                value={newLabel}
                onChange={(e) => setNewLabel(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Texto do Dispositivo *
            </label>
            <textarea
              required
              rows={4}
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500 font-serif"
              placeholder="Digite o conteúdo normativo..."
              value={newText}
              onChange={(e) => setNewText(e.target.value)}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsNewModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit">Adicionar Dispositivo</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
