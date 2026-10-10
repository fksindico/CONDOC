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
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';

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

  return (
    <div className="space-y-4">
      {/* Topbar do Editor */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center gap-3">
          <Link to={`/painel/projetos`} className="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-base font-bold text-slate-900 tracking-tight">
              Editor Estruturado de Dispositivos (Tiptap)
            </h1>
            <p className="text-xs text-slate-500">Minuta de Trabalho — Concorrência Otimista com ETag ativa.</p>
          </div>
        </div>

        {/* Indicador de Salvamento (UI-13) */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium">
            {saveStatus === 'saving' && <span className="text-amber-600 animate-pulse font-semibold">Salvando...</span>}
            {saveStatus === 'saved' && <span className="text-emerald-700 font-semibold">Salvo no servidor</span>}
            {saveStatus === 'conflict' && <span className="text-rose-600 font-bold">Conflito de Concorrência!</span>}
            {saveStatus === 'error' && <span className="text-rose-600 font-semibold">Falha ao salvar</span>}
          </span>
          <Button size="sm" onClick={handleSaveProvision} isLoading={saveStatus === 'saving'}>
            <Save className="w-3.5 h-3.5 mr-1" />
            <span>Salvar Dispositivo</span>
          </Button>
        </div>
      </div>

      {/* Grid Tripartido do Editor (PRD 27.3) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* Coluna 1: Árvore Hierárquica de Dispositivos (3 colunas) */}
        <div className="lg:col-span-3 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs flex flex-col max-h-[780px]">
          <div className="p-3 border-b border-slate-100 flex items-center justify-between bg-slate-50">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-brand-600" />
              <span>Árvore Normativa</span>
            </span>
            <button
              onClick={() => setIsNewModalOpen(true)}
              className="p-1 text-brand-600 hover:bg-brand-50 rounded"
              title="Adicionar Dispositivo"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          <div className="overflow-y-auto p-2 space-y-1 flex-1 text-xs">
            {provisions.length === 0 ? (
              <p className="p-4 text-center text-slate-400">Nenhum dispositivo cadastrado.</p>
            ) : (
              provisions.map((prov) => {
                const isSelected = selectedProvision?.id === prov.id;
                return (
                  <button
                    key={prov.id}
                    onClick={() => selectProvision(prov)}
                    className={`w-full text-left p-2.5 rounded-lg border transition-all flex items-center justify-between ${
                      isSelected
                        ? 'border-brand-500 bg-brand-50/50 shadow-xs'
                        : 'border-transparent hover:bg-slate-50'
                    }`}
                  >
                    <div className="truncate pr-2">
                      <span className="font-bold text-slate-900 block truncate">{prov.label || 'Sem rótulo'}</span>
                      <span className="text-[11px] text-slate-500 block truncate">{prov.text}</span>
                    </div>
                    <Badge variant={(prov.change_type as any) || 'default'} className="text-[10px] shrink-0">
                      {prov.change_type || 'mantido'}
                    </Badge>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Coluna 2: Documento-Base Original (Somente Leitura - UI-12) (4 colunas) */}
        <div className="lg:col-span-4 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs flex flex-col max-h-[780px]">
          <div className="p-3 border-b border-slate-100 flex items-center justify-between bg-slate-50">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-slate-500" />
              <span>Documento-Base Original</span>
            </span>
            <span className="text-[10px] text-slate-500 font-medium">Somente Leitura</span>
          </div>
          <div className="p-4 overflow-y-auto text-xs font-serif leading-relaxed text-slate-700 bg-slate-50/30 flex-1 space-y-3">
            <p className="italic text-slate-400 border-b pb-2">
              Texto da convenção/regimento anterior para confronto direto e rastreabilidade de origens.
            </p>
            <div className="p-3 bg-white border border-slate-200 rounded-lg shadow-2xs">
              <span className="font-bold text-slate-900 block mb-1">Redação Anterior de Referência</span>
              <p className="text-slate-600">
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
                <CardDescription className="text-[11px] mt-0.5">
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
            <div className="flex border-b border-slate-100 text-xs font-semibold bg-slate-50">
              <button
                onClick={() => setActiveTab('notas')}
                className={`flex-1 py-2.5 px-3 text-center border-b-2 flex items-center justify-center gap-1.5 transition-colors ${
                  activeTab === 'notas'
                    ? 'border-brand-600 text-brand-700 bg-white'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <StickyNote className="w-3.5 h-3.5" />
                <span>Notas Internas ({notes.length})</span>
              </button>
              <button
                onClick={() => setActiveTab('origens')}
                className={`flex-1 py-2.5 px-3 text-center border-b-2 flex items-center justify-center gap-1.5 transition-colors ${
                  activeTab === 'origens'
                    ? 'border-brand-600 text-brand-700 bg-white'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <GitBranch className="w-3.5 h-3.5" />
                <span>Mapeamento de Origem</span>
              </button>
            </div>

            <CardContent className="p-4 text-xs">
              {activeTab === 'notas' ? (
                <div className="space-y-3">
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {notes.length === 0 ? (
                      <p className="text-slate-400 italic">Nenhuma nota interna vinculada a este artigo.</p>
                    ) : (
                      notes.map((n) => (
                        <div key={n.id} className="p-2.5 bg-amber-50/70 border border-amber-200 rounded-lg text-amber-900">
                          <p>{n.content}</p>
                          <span className="text-[10px] text-amber-700/80 mt-1 block">
                            Visibilidade: {n.visibility} • Categoria: {n.category}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                  <form onSubmit={handleAddNote} className="flex gap-2 pt-2 border-t border-slate-100">
                    <input
                      type="text"
                      className="flex-1 text-xs border border-slate-200 rounded-lg p-2 outline-none focus:ring-1 focus:ring-brand-500"
                      placeholder="Adicionar nota restrita da equipe jurídica/comissão..."
                      value={newNoteContent}
                      onChange={(e) => setNewNoteContent(e.target.value)}
                    />
                    <Button type="submit" size="sm" variant="outline">
                      Adicionar
                    </Button>
                  </form>
                </div>
              ) : (
                <div className="space-y-2 text-slate-600 leading-relaxed">
                  <p>
                    Classificação: <strong className="capitalize">{changeType}</strong>
                  </p>
                  <p className="text-[11px] text-slate-500">
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
