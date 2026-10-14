import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import { PageFlip } from 'page-flip';
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  Download,
  BookOpen,
  FileText,
  LayoutGrid,
  RotateCcw,
  Loader2,
  AlertCircle,
  X,
} from 'lucide-react';

// Configura o worker do PDF.js localmente empacotado pelo Vite (100% OSS e offline)
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker;

export interface FlipbookViewerProps {
  pdfUrl: string;
  documentTitle?: string;
  onDownloadPdf?: () => void;
  className?: string;
}

interface PageData {
  pageNumber: number;
  imageUrl: string;
  thumbUrl: string;
  aspectRatio: number;
}

export const FlipbookViewer: React.FC<FlipbookViewerProps> = ({
  pdfUrl,
  documentTitle = 'Documento PDF',
  onDownloadPdf,
  className = '',
}) => {
  // Estados de Carregamento
  const [loading, setLoading] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingStatus, setLoadingStatus] = useState('Inicializando leitor...');
  const [error, setError] = useState<string | null>(null);

  // Estados de Dados do Documento
  const [totalPages, setTotalPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [inputPage, setInputPage] = useState('1');
  const [pagesData, setPagesData] = useState<PageData[]>([]);

  // Estados de Interface e Modos
  const [viewMode, setViewMode] = useState<'flipbook' | 'scroll'>('flipbook');
  const [zoomLevel, setZoomLevel] = useState(100); // 100%
  const [showThumbnails, setShowThumbnails] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Referências de DOM
  const containerRef = useRef<HTMLDivElement>(null);
  const bookContainerRef = useRef<HTMLDivElement>(null);
  const pageFlipInstance = useRef<PageFlip | null>(null);

  // Carrega o documento e renderiza as páginas em imagens de alta fidelidade
  useEffect(() => {
    let isCancelled = false;
    const blobUrlsToRevoke: string[] = [];

    const loadPdf = async () => {
      try {
        setLoading(true);
        setError(null);
        setLoadingProgress(5);
        setLoadingStatus('Baixando documento...');

        const loadingTask = pdfjsLib.getDocument({
          url: pdfUrl,
          cMapUrl: 'https://cdn.jsdelivr.net/npm/pdfjs-dist@' + pdfjsLib.version + '/cmaps/',
          cMapPacked: true,
        });

        loadingTask.onProgress = ({ loaded, total }: { loaded: number; total: number }) => {
          if (total > 0) {
            const percent = Math.min(40, Math.round((loaded / total) * 40));
            setLoadingProgress(percent);
          }
        };

        const pdfDoc = await loadingTask.promise;
        if (isCancelled) return;

        const count = pdfDoc.numPages;
        setTotalPages(count);
        setLoadingProgress(45);
        setLoadingStatus(`Processando ${count} páginas...`);

        const loadedPages: PageData[] = [];

        // Renderiza cada página com qualidade Retina/HiDPI
        for (let i = 1; i <= count; i++) {
          if (isCancelled) return;
          setLoadingStatus(`Renderizando página ${i} de ${count}...`);

          const page = await pdfDoc.getPage(i);
          const baseViewport = page.getViewport({ scale: 1.0 });
          const aspectRatio = baseViewport.width / baseViewport.height;

          // Resolução HiDPI para nitidez de texto
          const scale = 1.75;
          const viewport = page.getViewport({ scale });

          const canvas = document.createElement('canvas');
          canvas.width = viewport.width;
          canvas.height = viewport.height;
          const ctx = canvas.getContext('2d');

          if (!ctx) throw new Error('Não foi possível obter contexto 2D do Canvas.');

          // Fundo branco para garantir legibilidade perfeita
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, canvas.width, canvas.height);

          await page.render({
            canvas,
            canvasContext: ctx,
            viewport,
          }).promise;

          // Gera imagem em alta resolução (Blob)
          const blob = await new Promise<Blob | null>((resolve) =>
            canvas.toBlob((b) => resolve(b), 'image/jpeg', 0.92)
          );

          if (!blob) throw new Error(`Falha ao converter página ${i} em imagem.`);

          const imageUrl = URL.createObjectURL(blob);
          blobUrlsToRevoke.push(imageUrl);

          // Gera miniatura leve para gaveta
          const thumbCanvas = document.createElement('canvas');
          const thumbScale = 0.25;
          const thumbViewport = page.getViewport({ scale: thumbScale });
          thumbCanvas.width = thumbViewport.width;
          thumbCanvas.height = thumbViewport.height;
          const thumbCtx = thumbCanvas.getContext('2d');
          if (thumbCtx) {
            thumbCtx.fillStyle = '#ffffff';
            thumbCtx.fillRect(0, 0, thumbCanvas.width, thumbCanvas.height);
            await page.render({
              canvas: thumbCanvas,
              canvasContext: thumbCtx,
              viewport: thumbViewport,
            }).promise;
          }
          const thumbUrl = thumbCanvas.toDataURL('image/jpeg', 0.7);

          loadedPages.push({
            pageNumber: i,
            imageUrl,
            thumbUrl,
            aspectRatio,
          });

          const currentPercent = 45 + Math.round((i / count) * 55);
          setLoadingProgress(currentPercent);
        }

        if (isCancelled) return;
        setPagesData(loadedPages);
        setLoading(false);
      } catch (err: any) {
        if (isCancelled) return;
        console.error('Erro ao renderizar PDF:', err);
        setError(err.message || 'Falha ao processar o arquivo PDF.');
        setLoading(false);
      }
    };

    loadPdf();

    return () => {
      isCancelled = true;
      // Libera os Blob URLs da memória
      blobUrlsToRevoke.forEach((url) => URL.revokeObjectURL(url));
      if (pageFlipInstance.current) {
        try {
          pageFlipInstance.current.destroy();
        } catch {}
        pageFlipInstance.current = null;
      }
    };
  }, [pdfUrl]);

  // Inicializa o PageFlip quando os dados das páginas e o container estiverem prontos
  useEffect(() => {
    if (loading || pagesData.length === 0 || viewMode !== 'flipbook') {
      return;
    }

    const container = bookContainerRef.current;
    if (!container) return;

    // Destrói instância anterior se existir
    if (pageFlipInstance.current) {
      try {
        pageFlipInstance.current.destroy();
      } catch {}
      pageFlipInstance.current = null;
    }

    container.innerHTML = '';

    // Cria os elementos de página HTML para o PageFlip
    const pageElements: HTMLElement[] = [];
    const baseAspect = pagesData[0]?.aspectRatio || 0.707; // padrão A4

    // Dimensões responsivas base
    const containerWidth = container.clientWidth || 800;
    const isMobile = window.innerWidth < 768;

    // No desktop, o livro abre com 2 páginas lado a lado. No mobile, 1 página.
    const pageCalculatedWidth = isMobile
      ? Math.min(containerWidth - 32, 500)
      : Math.min(Math.floor((containerWidth - 64) / 2), 480);
    const pageCalculatedHeight = Math.round(pageCalculatedWidth / baseAspect);

    pagesData.forEach((page, idx) => {
      const pageDiv = document.createElement('div');
      pageDiv.className =
        'page bg-white shadow-md overflow-hidden select-none flex items-center justify-center';
      if (idx === 0 || idx === pagesData.length - 1) {
        pageDiv.setAttribute('data-density', 'hard'); // Capa e contracapa duras
      }

      const img = document.createElement('img');
      img.src = page.imageUrl;
      img.alt = `Página ${page.pageNumber}`;
      img.className = 'w-full h-full object-contain pointer-events-none';
      img.loading = idx < 4 ? 'eager' : 'lazy';

      pageDiv.appendChild(img);
      container.appendChild(pageDiv);
      pageElements.push(pageDiv);
    });

    try {
      const flip = new PageFlip(container, {
        width: pageCalculatedWidth,
        height: pageCalculatedHeight,
        size: 'stretch',
        minWidth: 280,
        maxWidth: 700,
        minHeight: 400,
        maxHeight: 1000,
        drawShadow: true,
        flippingTime: 500,
        usePortrait: true, // Modo retrato de 1 página automático em telas estreitas
        startPage: Math.max(0, currentPage - 1),
        showCover: true,
        mobileScrollSupport: false,
        useMouseEvents: true,
        showPageCorners: true,
        swipeDistance: 25,
      });

      flip.loadFromHTML(pageElements);

      flip.on('flip', (e) => {
        const newPage = e.data + 1;
        setCurrentPage(newPage);
        setInputPage(String(newPage));
      });

      pageFlipInstance.current = flip;
    } catch (err) {
      console.error('Erro ao inicializar PageFlip:', err);
    }

    return () => {
      if (pageFlipInstance.current) {
        try {
          pageFlipInstance.current.destroy();
        } catch {}
        pageFlipInstance.current = null;
      }
    };
  }, [loading, pagesData, viewMode]);

  // Navegação
  const handlePrevPage = () => {
    if (viewMode === 'flipbook' && pageFlipInstance.current) {
      pageFlipInstance.current.flipPrev();
    } else {
      const prev = Math.max(1, currentPage - 1);
      setCurrentPage(prev);
      setInputPage(String(prev));
      scrollToPage(prev);
    }
  };

  const handleNextPage = () => {
    if (viewMode === 'flipbook' && pageFlipInstance.current) {
      pageFlipInstance.current.flipNext();
    } else {
      const next = Math.min(totalPages, currentPage + 1);
      setCurrentPage(next);
      setInputPage(String(next));
      scrollToPage(next);
    }
  };

  const handleGoToPage = (e: React.FormEvent) => {
    e.preventDefault();
    const p = parseInt(inputPage, 10);
    if (!isNaN(p) && p >= 1 && p <= totalPages) {
      setCurrentPage(p);
      if (viewMode === 'flipbook' && pageFlipInstance.current) {
        pageFlipInstance.current.turnToPage(p - 1);
      } else {
        scrollToPage(p);
      }
    } else {
      setInputPage(String(currentPage));
    }
  };

  const scrollToPage = (pageNum: number) => {
    const el = document.getElementById(`scroll-page-${pageNum}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // Zoom
  const handleZoomIn = () => setZoomLevel((z) => Math.min(180, z + 15));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(60, z - 15));
  const handleResetZoom = () => setZoomLevel(100);

  // Fullscreen
  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  useEffect(() => {
    const onFsChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', onFsChange);
    return () => document.removeEventListener('fullscreenchange', onFsChange);
  }, []);

  return (
    <div
      ref={containerRef}
      className={`flex flex-col bg-slate-900 text-slate-100 rounded-2xl overflow-hidden border border-slate-800 shadow-xl select-none ${className} ${
        isFullscreen ? 'fixed inset-0 z-50 rounded-none border-0' : 'h-full min-h-[560px]'
      }`}
    >
      {/* Barra de Ferramentas Superior do Leitor */}
      <header className="px-3 sm:px-4 py-2.5 bg-slate-950 border-b border-slate-800 flex flex-wrap items-center justify-between gap-2 shrink-0">
        {/* Título e Miniaturas */}
        <div className="flex items-center gap-2 min-w-0">
          <button
            type="button"
            onClick={() => setShowThumbnails(!showThumbnails)}
            className={`p-1.5 rounded-lg border text-xs font-medium flex items-center gap-1.5 transition ${
              showThumbnails
                ? 'bg-indigo-600 border-indigo-500 text-white'
                : 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800'
            }`}
            title="Alternar painel de miniaturas de páginas"
          >
            <LayoutGrid className="w-4 h-4" />
            <span className="hidden sm:inline">Páginas</span>
          </button>

          <span className="text-xs font-semibold text-slate-300 truncate max-w-[140px] sm:max-w-[220px]" title={documentTitle}>
            {documentTitle}
          </span>
        </div>

        {/* Controles Centrais de Navegação e Paginação */}
        <div className="flex items-center gap-1.5 bg-slate-900/80 px-2 py-1 rounded-xl border border-slate-800 text-xs">
          <button
            type="button"
            onClick={handlePrevPage}
            disabled={currentPage <= 1 || loading}
            className="p-1 hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-transparent rounded-md transition"
            title="Página anterior"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <form onSubmit={handleGoToPage} className="flex items-center gap-1">
            <span className="text-slate-400 text-[11px] hidden sm:inline">Pág.</span>
            <input
              type="text"
              value={inputPage}
              onChange={(e) => setInputPage(e.target.value)}
              onBlur={handleGoToPage}
              disabled={loading || totalPages === 0}
              className="w-9 text-center bg-slate-950 border border-slate-700 rounded px-1 py-0.5 text-xs font-mono font-bold text-white focus:outline-hidden focus:border-indigo-500"
            />
            <span className="text-slate-400 text-[11px]">de {totalPages || '—'}</span>
          </form>

          <button
            type="button"
            onClick={handleNextPage}
            disabled={currentPage >= totalPages || loading}
            className="p-1 hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-transparent rounded-md transition"
            title="Próxima página"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Controles de Modo (Flipbook / Scroll), Zoom e Download */}
        <div className="flex items-center gap-1 sm:gap-2">
          {/* Alternador de Modo de Leitura */}
          <div className="flex items-center bg-slate-900 p-0.5 rounded-lg border border-slate-800">
            <button
              type="button"
              onClick={() => setViewMode('flipbook')}
              className={`px-2 py-1 rounded-md text-xs font-medium flex items-center gap-1 transition ${
                viewMode === 'flipbook'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Modo Livro (Flipbook interativo 3D)"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Livro</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('scroll')}
              className={`px-2 py-1 rounded-md text-xs font-medium flex items-center gap-1 transition ${
                viewMode === 'scroll'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Modo Rolagem Vertical Contínua"
            >
              <FileText className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Rolagem</span>
            </button>
          </div>

          {/* Zoom */}
          <div className="hidden lg:flex items-center gap-0.5 bg-slate-900 px-1 py-0.5 rounded-lg border border-slate-800 text-xs">
            <button
              type="button"
              onClick={handleZoomOut}
              className="p-1 hover:bg-slate-800 rounded text-slate-300"
              title="Diminuir Zoom"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="px-1 text-[11px] font-mono text-slate-400">{zoomLevel}%</span>
            <button
              type="button"
              onClick={handleZoomIn}
              className="p-1 hover:bg-slate-800 rounded text-slate-300"
              title="Aumentar Zoom"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            {zoomLevel !== 100 && (
              <button
                type="button"
                onClick={handleResetZoom}
                className="p-1 hover:bg-slate-800 rounded text-slate-400"
                title="Resetar Zoom para 100%"
              >
                <RotateCcw className="w-3 h-3" />
              </button>
            )}
          </div>

          {/* Botão de Download */}
          {onDownloadPdf ? (
            <button
              type="button"
              onClick={onDownloadPdf}
              className="px-2.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-lg shadow-xs flex items-center gap-1 transition"
              title="Baixar PDF Original"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Baixar</span>
            </button>
          ) : (
            <a
              href={pdfUrl}
              download
              className="px-2.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-lg shadow-xs flex items-center gap-1 transition"
              title="Baixar PDF Original"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Baixar</span>
            </a>
          )}

          {/* Tela Cheia */}
          <button
            type="button"
            onClick={toggleFullscreen}
            className="p-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded-lg transition"
            title={isFullscreen ? 'Sair da tela cheia' : 'Visualizar em tela cheia'}
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </header>

      {/* Área Central: Visualizador + Gaveta Lateral de Miniaturas */}
      <div className="relative flex-1 flex overflow-hidden bg-slate-900">
        {/* Gaveta Retrátil de Miniaturas */}
        {showThumbnails && (
          <aside className="w-48 sm:w-56 bg-slate-950 border-r border-slate-800 flex flex-col shrink-0 z-20 animate-in slide-in-from-left-4 duration-200">
            <div className="p-3 border-b border-slate-800 flex items-center justify-between text-xs">
              <span className="font-bold text-slate-300">Todas as Páginas</span>
              <button
                type="button"
                onClick={() => setShowThumbnails(false)}
                className="p-1 text-slate-400 hover:text-white rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              {pagesData.map((p) => (
                <button
                  key={p.pageNumber}
                  type="button"
                  onClick={() => {
                    setCurrentPage(p.pageNumber);
                    setInputPage(String(p.pageNumber));
                    if (viewMode === 'flipbook' && pageFlipInstance.current) {
                      pageFlipInstance.current.turnToPage(p.pageNumber - 1);
                    } else {
                      scrollToPage(p.pageNumber);
                    }
                  }}
                  className={`w-full text-left p-1.5 rounded-xl border transition flex flex-col items-center gap-1.5 ${
                    currentPage === p.pageNumber
                      ? 'bg-indigo-950/60 border-indigo-500 shadow-md ring-2 ring-indigo-500/30'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <img
                    src={p.thumbUrl}
                    alt={`Miniatura ${p.pageNumber}`}
                    className="w-full h-auto rounded shadow-xs object-contain bg-white"
                  />
                  <span className="text-[11px] font-mono font-bold text-slate-400">
                    Página {p.pageNumber}
                  </span>
                </button>
              ))}
            </div>
          </aside>
        )}

        {/* Palco Principal do Documento */}
        <main className="flex-1 relative flex items-center justify-center overflow-auto p-2 sm:p-4 bg-radial from-slate-850 to-slate-950">
          {/* Feedback de Carregamento Progressivo */}
          {loading && (
            <div className="flex flex-col items-center justify-center p-8 text-center max-w-sm">
              <Loader2 className="w-10 h-10 text-indigo-500 animate-spin mb-4" />
              <h3 className="text-sm font-bold text-slate-100 mb-1">Preparando Livro Digital</h3>
              <p className="text-xs text-slate-400 mb-4">{loadingStatus}</p>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700">
                <div
                  className="bg-indigo-600 h-full transition-all duration-300 rounded-full"
                  style={{ width: `${loadingProgress}%` }}
                />
              </div>
              <span className="text-[11px] font-mono text-indigo-400 mt-2 font-bold">
                {loadingProgress}% concluído
              </span>
            </div>
          )}

          {/* Feedback de Erro */}
          {error && !loading && (
            <div className="p-6 bg-rose-950/40 border border-rose-800/80 rounded-2xl max-w-md text-center">
              <AlertCircle className="w-10 h-10 text-rose-400 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-rose-200 mb-1">Não foi possível carregar o PDF</h3>
              <p className="text-xs text-rose-300/80 mb-4">{error}</p>
              {onDownloadPdf ? (
                <button
                  type="button"
                  onClick={onDownloadPdf}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl shadow-xs transition"
                >
                  <Download className="w-4 h-4" /> Baixar Cópia do Arquivo
                </button>
              ) : (
                <a
                  href={pdfUrl}
                  download
                  className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl shadow-xs transition"
                >
                  <Download className="w-4 h-4" /> Baixar Cópia do Arquivo
                </a>
              )}
            </div>
          )}

          {/* MODO 1: Flipbook 3D Interativo */}
          {!loading && !error && viewMode === 'flipbook' && (
            <div
              className="flex items-center justify-center w-full h-full transition-transform duration-200 ease-out"
              style={{
                transform: zoomLevel !== 100 ? `scale(${zoomLevel / 100})` : 'none',
                transformOrigin: 'center center',
              }}
            >
              {/* Container onde a biblioteca PageFlip orquestra o livro */}
              <div
                ref={bookContainerRef}
                className="flipbook-root flex items-center justify-center mx-auto"
              />
            </div>
          )}

          {/* MODO 2: Rolagem Vertical Contínua */}
          {!loading && !error && viewMode === 'scroll' && (
            <div
              className="w-full h-full overflow-y-auto px-2 py-4 flex flex-col items-center gap-6"
              style={{
                transform: zoomLevel !== 100 ? `scale(${zoomLevel / 100})` : 'none',
                transformOrigin: 'top center',
              }}
            >
              {pagesData.map((page) => (
                <div
                  key={page.pageNumber}
                  id={`scroll-page-${page.pageNumber}`}
                  className="bg-white rounded-lg shadow-xl overflow-hidden max-w-3xl w-full border border-slate-700/50 flex flex-col"
                >
                  <div className="bg-slate-100 px-3 py-1 text-[11px] font-mono text-slate-500 border-b border-slate-200 flex items-center justify-between">
                    <span>Página {page.pageNumber}</span>
                    <span className="text-[10px] text-slate-400 uppercase">Minuta Oficial</span>
                  </div>
                  <img
                    src={page.imageUrl}
                    alt={`Página ${page.pageNumber}`}
                    className="w-full h-auto object-contain select-text"
                  />
                </div>
              ))}
            </div>
          )}
        </main>
      </div>

      {/* Dica de Rodapé para o Morador */}
      <footer className="px-4 py-1.5 bg-slate-950 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between shrink-0">
        <span className="truncate">
          {viewMode === 'flipbook'
            ? '💡 Dica: Arraste o canto da página ou use as setas para folhear o livro.'
            : '💡 Dica: Role para baixo para ler os artigos de forma contínua.'}
        </span>
        <span className="font-mono text-slate-500 hidden sm:inline">100% Open Source (Mozilla PDF.js)</span>
      </footer>
    </div>
  );
};
