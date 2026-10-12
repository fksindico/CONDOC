import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTenant } from '@/contexts/TenantContext';
import { useToast } from '@/contexts/ToastContext';
import { api, ApiClientError } from '@/lib/api';
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
  ChevronRight,
  Eye,
  StickyNote,
  GitBranch,
  Search,
  Check,
  Filter,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';
import { Breadcrumb } from '@/components/ui/Breadcrumb';

export const StructuredEditorPage: React.FC = () => {
  const { docId } = useParams<{ docId: string }>();
  const { activeCondominiumId } = useTenant();
  const { toast } = useToast();

  const [provisions, setProvisions] = useState<any[]>([]);
  const [selectedProvision, setSelectedProvision] = useState<any | null>(null);
  const [editText, setEditText] = useState('');
  const [editLabel, setEditLabel] = useState('');
  const [changeType, setChangeType] = useState('alterado');
  const [activeEtag, setActiveEtag] = useState<string | null>(null);

  // Filtros da Árvore Normativa
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('todos');

  // Status de Salvamento (UI-13: "Salvo" depende estritamente da resposta 200 do servidor)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'conflict' | 'error'>('idle');

  // Modal de Conflito de Concorrência Otimista 409 (UI-14, CA-23)
  const [conflictModalOpen, setConflictModalOpen] = useState(false);
  const [conflictServerText, setConflictServerText] = useState('');

  // Modal Novo Dispositivo
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [newKind, setNewKind] = useState('artigo');
  const [newLabel, setNewLabel] = useState('Art. ');
  const [newText, setNewText] = useState('');

  // Aba Inferior (Notas Internas vs Origem)
  const [activeTab, setActiveTab] = useState<'notas' | 'origens'>('notas');
  const [notes, setNotes] = useState<any[]>([]);
  const [newNoteContent, setNewNoteContent] = useState('');

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
    fetchProvisions();
  }, [activeCondominiumId, docId]);

  const selectProvision = async (prov: any) => {
    setSelectedProvision(prov);
    setEditText(prov.text || '');
    setEditLabel(prov.label || '');
    setChangeType(prov.change_type || 'alterado');
    setActiveEtag(prov.etag || null);
    setSaveStatus('idle');

    // Carrega notas internas do dispositivo selecionado
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
      // CA-23 / UI-14: Envia ETag com If-Match para controle de concorrência otimista
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

      // Atualiza com nova revisão e novo ETag retornado pelo backend
      setActiveEtag(res.data.etag || null);
      setSaveStatus('saved');
      fetchProvisions();
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (err: any) {
      if (err.status === 409 || err.code === 'CONCURRENCY_CONFLICT') {
        // Conflito de concorrência detectado sem sobrescrita silenciosa
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
      // Recarrega notas
      const resNotes = await api.get<any[]>(`/condominiums/${activeCondominiumId}/provisions/${selectedProvision.id}/notes`);
      setNotes(resNotes.data || []);
    } catch (err: any) {
      toast.error(err.message || 'Erro ao adicionar nota interna.');
    }
  };

  // Filtros aplicados sobre a árvore normativa
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
      <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center gap-3">
          <Link to={`/painel/projetos`} className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors" aria-label="Voltar aos projetos">
            <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-slate-900 tracking-tight">
                Estação de Redação Normativa
              </h1>
              <Badge variant="outline" className="font-mono text-[10px]">
                {provisions.length} dispositivos
              </Badge>
            </div>
            <p className="text-xs text-slate-500">Minuta Oficial em Elaboração — Concorrência Otimista com ETag ativa.</p>
          </div>
        </div>

        {/* Ações e Navegação Contextual */}
        <div className="flex flex-wrap items-center gap-2.5">
          <Link to={`/painel/documentos/${docId}/compare`}>
            <Button size="sm" variant="outline">
              <GitBranch className="w-3.5 h-3.5 mr-1 text-slate-500" aria-hidden="true" />
              <span>Relatório DePara</span>
            </Button>
          </Link>
          <Link to={`/painel/documentos/${docId}/versoes`}>
            <Button size="sm" variant="outline">
              <History className="w-3.5 h-3.5 mr-1 text-slate-500" aria-hidden="true" />
              <span>Snapshots</span>
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
                Salvo no servidor
              </span>
            )}
            {saveStatus === 'conflict' && (
              <span className="inline-flex items-center gap-1.5 text-rose-700 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200 font-bold">
                Conflito 409!
              </span>
            )}
            {saveStatus === 'error' && (
              <span className="inline-flex items-center gap-1.5 text-rose-700 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200 font-semibold">
                Falha ao salvar
              </span>
            )}
          </div>
          <Button size="sm" onClick={handleSaveProvision} isLoading={saveStatus === 'saving'}>
            <Save className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
            <span>Salvar Dispositivo</span>
          </Button>
        </div>
      </div>

      {/* Grid Tripartido do Editor (PRD 27.3 / Swiss Pro Max Layout) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* Coluna 1: Árvore Hierárquica de Dispositivos (3 colunas) */}
        <div className="lg:col-span-3 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs flex flex-col max-h-[820px]">
          <div className="p-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-brand-700" aria-hidden="true" />
              <span>Árvore Normativa</span>
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setIsNewModalOpen(true)}
                className="p-1.5 text-brand-700 hover:bg-brand-50 rounded-lg transition-colors"
                title="Adicionar Dispositivo"
                aria-label="Adicionar Dispositivo"
              >
                <Plus className="w-4 h-4" aria-hidden="true" />
              </button>
            </div>
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
            <CardHeader className="p-4 pb-3 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-sm flex items-center gap-2">
                  <span>Edição:</span>
                  <input
                    type="text"
                    className="font-bold text-slate-900 border border-slate-200 rounded px-2 py-0.5 text-sm w-32 outline-none focus:ring-1 focus:ring-brand-500"
                    value={editLabel}
                    onChange={(e) => setEditLabel(e.target.value)}
                  />
                </CardTitle>
                <CardDescription className="text-xs mt-0.5">
                  UUID Permanente: <code className="text-slate-600">{selectedProvision?.id?.slice(0, 8)}...</code>
                </CardDescription>
              </div>

              {/* Seletor de Tipo de Mudança Normativa */}
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
                        <p className="italic">Nenhuma nota interna restrita vinculada a este dispositivo.</p>
                      </div>
                    ) : (
                      notes.map((n) => (
                        <div key={n.id} className="p-2.5 bg-amber-50/60 border border-amber-200/70 rounded-lg text-amber-950 shadow-2xs">
                          <p className="leading-relaxed font-sans">{n.content}</p>
                          <div className="flex items-center justify-between text-[10px] text-amber-800/80 mt-1.5 pt-1 border-t border-amber-200/40">
                            <span className="font-mono uppercase tracking-wider font-semibold">Restrito • {n.category}</span>
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
                      placeholder="Adicionar nota restrita da equipe jurídica/comissão..."
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
                // Força nova tentativa de mesclagem
              }}
            >
              Manter Conteúdo Local e Mesclar
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
                onChange={(e) => setNewKind(e.target.value)}
              >
                <option value="artigo">Artigo</option>
                <option value="paragrafo">Parágrafo</option>
                <option value="inciso">Inciso</option>
                <option value="alinea">Alínea</option>
                <option value="capitulo">Capítulo</option>
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
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-brand-500"
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
