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
  Book,
  Home,
  Sliders,
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

export type LayoutMode = 'auto' | 'single' | 'double' | 'scroll';

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

  // Estados de Interface e Modos de Visualização
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('auto');
  const [effectiveMode, setEffectiveMode] = useState<'single' | 'double' | 'scroll'>('single');
  const [zoomLevel, setZoomLevel] = useState(100); // 100%
  const [showThumbnails, setShowThumbnails] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [bookDimensions, setBookDimensions] = useState<{ bookWidth: number; pageHeight: number; pageWidth: number }>({
    bookWidth: 500,
    pageHeight: 700,
    pageWidth: 500,
  });

  // Referências de DOM e Instâncias
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLElement>(null);
  const bookMountRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const pageFlipInstance = useRef<PageFlip | null>(null);
  const currentPageRef = useRef(1);
  const isManualNavRef = useRef(false);

  // Sincroniza referência de página atual para evitar recriação desnecessária de efeitos
  useEffect(() => {
    currentPageRef.current = currentPage;
  }, [currentPage]);

  // 1. Carrega o documento e renderiza as páginas em imagens de alta fidelidade
  useEffect(() => {
    let isCancelled = false;
    const blobUrlsToRevoke: string[] = [];

    const loadPdf = async () => {
      try {
        setLoading(true);
        setError(null);
        setLoadingProgress(5);

        // 1.1 Normaliza URL para evitar Mixed Content e resolver rota
        let targetUrl = pdfUrl;
        if (typeof window !== 'undefined') {
          if (window.location.protocol === 'https:' && targetUrl.startsWith('http:')) {
            targetUrl = targetUrl.replace(/^http:/, 'https:');
          }
          try {
            const parsed = new URL(targetUrl, window.location.origin);
            if (parsed.host === window.location.host) {
              targetUrl = parsed.pathname + parsed.search;
            }
          } catch {}
        }

        // 1.2 Faz download direto dos bytes via Fetch API (ArrayBuffer)
        setLoadingStatus('Baixando documento...');
        const resp = await fetch(targetUrl);
        if (!resp.ok) {
          throw new Error(`Falha ao obter PDF do servidor (HTTP ${resp.status} ${resp.statusText})`);
        }
        const arrayBuffer = await resp.arrayBuffer();
        if (isCancelled) return;

        setLoadingProgress(30);
        setLoadingStatus('Decodificando páginas do PDF...');

        const uint8Array = new Uint8Array(arrayBuffer);
        const loadingTask = pdfjsLib.getDocument({
          data: uint8Array,
        });

        const pdfDoc = await loadingTask.promise;
        if (isCancelled) return;

        const count = pdfDoc.numPages;
        setTotalPages(count);
        setLoadingProgress(40);
        setLoadingStatus(`Processando ${count} páginas em alta resolução...`);

        const loadedPages: PageData[] = [];

        // Renderiza cada página com qualidade Retina/HiDPI (1.75x)
        for (let i = 1; i <= count; i++) {
          if (isCancelled) return;
          setLoadingStatus(`Renderizando página ${i} de ${count}...`);

          const page = await pdfDoc.getPage(i);
          const baseViewport = page.getViewport({ scale: 1.0 });
          const aspectRatio = baseViewport.width / baseViewport.height;

          // Resolução HiDPI para nitidez cristalina
          const scale = 1.75;
          const viewport = page.getViewport({ scale });

          const canvas = document.createElement('canvas');
          canvas.width = viewport.width;
          canvas.height = viewport.height;
          const ctx = canvas.getContext('2d');

          if (!ctx) throw new Error('Não foi possível obter contexto 2D do Canvas.');

          // Fundo branco sólido
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

          // Gera miniatura leve para barra lateral
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

          const currentPercent = 40 + Math.round((i / count) * 60);
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
      blobUrlsToRevoke.forEach((url) => URL.revokeObjectURL(url));
      if (pageFlipInstance.current) {
        try {
          pageFlipInstance.current.destroy();
        } catch {}
        pageFlipInstance.current = null;
      }
    };
  }, [pdfUrl]);

  // 2. Calcula as dimensões exatas e o modo efetivo para ajuste perfeito (Fit-to-Screen)
  const computeOptimalDimensions = useCallback(() => {
    if (!stageRef.current || pagesData.length === 0) return null;

    const stage = stageRef.current;
    const isMobile = stage.clientWidth < 640;
    const paddingH = isMobile ? 24 : 56;
    const paddingV = isMobile ? 24 : 56;

    // Área visível real disponível com folga de respiração
    const availableWidth = Math.max(240, stage.clientWidth - paddingH);
    const availableHeight = Math.max(320, stage.clientHeight - paddingV);
    const baseAspect = pagesData[0]?.aspectRatio || 0.707; // padrão A4 ~0.707

    // Determina o modo efetivo
    let mode: 'single' | 'double' | 'scroll';
    if (layoutMode === 'scroll') {
      mode = 'scroll';
    } else if (layoutMode === 'single') {
      mode = 'single';
    } else if (layoutMode === 'double') {
      mode = 'double';
    } else {
      // Modo 'auto': se a largura disponível for menor que 880px, usa 1 Página Centralizada
      mode = availableWidth < 880 ? 'single' : 'double';
    }

    setEffectiveMode(mode);

    if (mode === 'scroll') {
      return { mode, bookWidth: availableWidth, pageHeight: availableHeight, pageWidth: availableWidth };
    }

    let pageWidth: number;
    let pageHeight: number;
    let bookWidth: number;

    if (mode === 'single') {
      // MODO 1 PÁGINA CENTRALIZADA: proporção é a da própria folha (baseAspect)
      if (availableWidth / availableHeight > baseAspect) {
        // Altura é o fator limitante
        pageHeight = Math.floor(availableHeight);
        pageWidth = Math.floor(pageHeight * baseAspect);
      } else {
        // Largura é o fator limitante
        pageWidth = Math.floor(availableWidth);
        pageHeight = Math.floor(pageWidth / baseAspect);
      }
      bookWidth = pageWidth;
    } else {
      // MODO 2 PÁGINAS (LIVRO ABERTO): proporção é o dobro (2 * baseAspect)
      const spreadAspect = 2 * baseAspect;
      if (availableWidth / availableHeight > spreadAspect) {
        // Altura é o fator limitante
        pageHeight = Math.floor(availableHeight);
        bookWidth = Math.floor(pageHeight * spreadAspect);
        pageWidth = Math.floor(bookWidth / 2);
      } else {
        // Largura é o fator limitante
        bookWidth = Math.floor(availableWidth);
        pageWidth = Math.floor(bookWidth / 2);
        pageHeight = Math.floor(pageWidth / baseAspect);
        bookWidth = pageWidth * 2;
      }
    }

    const dims = { mode, bookWidth, pageHeight, pageWidth };
    setBookDimensions({ bookWidth, pageHeight, pageWidth });
    return dims;
  }, [layoutMode, pagesData]);

  // 3. Monta o PageFlip com dimensões fixas rigorosamente calculadas
  const initPageFlip = useCallback(() => {
    if (loading || pagesData.length === 0) return;

    const dims = computeOptimalDimensions();
    if (!dims || dims.mode === 'scroll') return;

    const mount = bookMountRef.current;
    if (!mount) return;

    // Destrói instância anterior se existir
    if (pageFlipInstance.current) {
      try {
        pageFlipInstance.current.destroy();
      } catch (err) {
        console.warn('Erro ao destruir PageFlip anterior:', err);
      }
      pageFlipInstance.current = null;
    }

    // Limpa o ponto de montagem estável
    mount.innerHTML = '';

    // Cria o container filho efêmero com o tamanho exato do livro
    const bookContainer = document.createElement('div');
    bookContainer.className = 'stf__parent-container flex items-center justify-center m-auto shadow-2xl';
    bookContainer.style.width = `${dims.bookWidth}px`;
    bookContainer.style.height = `${dims.pageHeight}px`;
    bookContainer.style.position = 'relative';
    bookContainer.style.margin = 'auto';
    mount.appendChild(bookContainer);

    const pageElements: HTMLElement[] = [];

    pagesData.forEach((page, idx) => {
      const pageDiv = document.createElement('div');
      pageDiv.className =
        'page bg-white shadow-xl overflow-hidden select-none flex items-center justify-center';
      pageDiv.style.width = `${dims.pageWidth}px`;
      pageDiv.style.height = `${dims.pageHeight}px`;

      // Capa e contracapa duras
      if (idx === 0 || idx === pagesData.length - 1) {
        pageDiv.setAttribute('data-density', 'hard');
      }

      const img = document.createElement('img');
      img.src = page.imageUrl;
      img.alt = `Página ${page.pageNumber}`;
      img.className = 'w-full h-full object-contain pointer-events-none block';
      img.loading = idx < 4 ? 'eager' : 'lazy';

      pageDiv.appendChild(img);
      bookContainer.appendChild(pageDiv);
      pageElements.push(pageDiv);
    });

    try {
      const flip = new PageFlip(bookContainer, {
        width: dims.pageWidth,
        height: dims.pageHeight,
        size: 'fixed', // FIXED garante enquadramento sem overflow
        minWidth: 200,
        maxWidth: 2000,
        minHeight: 250,
        maxHeight: 2000,
        drawShadow: true,
        flippingTime: 400,
        usePortrait: dims.mode === 'single',
        startPage: Math.max(0, currentPageRef.current - 1),
        showCover: false, // showCover: false garante alinhamento centralizado sem deslocamento
        mobileScrollSupport: false,
        useMouseEvents: true,
        showPageCorners: true,
        swipeDistance: 20,
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
  }, [loading, pagesData, computeOptimalDimensions]);

  // Inicializa quando dados estiverem prontos ou o modo mudar
  useEffect(() => {
    if (loading || pagesData.length === 0) return;

    let frameId: number;
    let timerId: any;

    const checkAndInit = () => {
      if (!stageRef.current || stageRef.current.clientWidth < 50) {
        frameId = requestAnimationFrame(checkAndInit);
        return;
      }
      initPageFlip();
    };

    timerId = setTimeout(() => {
      frameId = requestAnimationFrame(checkAndInit);
    }, 60);

    return () => {
      clearTimeout(timerId);
      cancelAnimationFrame(frameId);
    };
  }, [loading, pagesData, layoutMode, initPageFlip]);

  // 4. ResizeObserver para redimensionar automaticamente quando a janela ou o split mudar
  useEffect(() => {
    if (!stageRef.current) return;
    let timeoutId: any = null;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect.width < 50 || entry.contentRect.height < 50) return;
      }
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        initPageFlip();
      }, 150);
    });

    observer.observe(stageRef.current);
    return () => {
      observer.disconnect();
      clearTimeout(timeoutId);
    };
  }, [initPageFlip]);

  // 5. Atalhos de Teclado
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignora se o foco estiver em inputs de texto
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement)?.tagName)) {
        return;
      }

      if (e.key === 'ArrowRight' || e.key === 'PageDown') {
        e.preventDefault();
        handleNextPage();
      } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault();
        handlePrevPage();
      } else if (e.key === 'Home') {
        e.preventDefault();
        goToPage(1);
      } else if (e.key === 'End') {
        e.preventDefault();
        goToPage(totalPages);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [totalPages, effectiveMode]);

  // Monitoramento de Scroll Spy no Modo Rolagem Contínua
  const handleScrollModeScroll = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container || isManualNavRef.current || pagesData.length === 0) return;

    const scrollTop = container.scrollTop;
    const focusY = scrollTop + container.clientHeight * 0.25;

    let detectedPage = 1;
    for (let i = 0; i < pagesData.length; i++) {
      const page = pagesData[i];
      const el = document.getElementById(`scroll-page-${page.pageNumber}`);
      if (el) {
        const top = el.offsetTop - container.offsetTop;
        const bottom = top + el.offsetHeight;
        if (top <= focusY && bottom > focusY) {
          detectedPage = page.pageNumber;
          break;
        } else if (top > focusY) {
          detectedPage = Math.max(1, page.pageNumber - 1);
          break;
        } else {
          detectedPage = page.pageNumber;
        }
      }
    }

    if (detectedPage !== currentPageRef.current) {
      currentPageRef.current = detectedPage;
      setCurrentPage(detectedPage);
      setInputPage(String(detectedPage));
    }
  }, [pagesData]);

  // Navegação
  const handlePrevPage = () => {
    if (effectiveMode !== 'scroll' && pageFlipInstance.current) {
      pageFlipInstance.current.flipPrev();
    } else {
      const prev = Math.max(1, currentPage - 1);
      goToPage(prev);
    }
  };

  const handleNextPage = () => {
    if (effectiveMode !== 'scroll' && pageFlipInstance.current) {
      pageFlipInstance.current.flipNext();
    } else {
      const next = Math.min(totalPages, currentPage + 1);
      goToPage(next);
    }
  };

  const goToPage = (p: number) => {
    if (p < 1 || p > totalPages) return;
    setCurrentPage(p);
    setInputPage(String(p));
    currentPageRef.current = p;

    if (effectiveMode !== 'scroll' && pageFlipInstance.current) {
      pageFlipInstance.current.turnToPage(p - 1);
    } else if (scrollContainerRef.current) {
      const container = scrollContainerRef.current;
      const el = document.getElementById(`scroll-page-${p}`);
      if (el) {
        isManualNavRef.current = true;
        // Rola estritamente o container interno para o topo da folha selecionada sem rolar a janela externa
        const targetScrollTop = el.offsetTop - container.offsetTop - 16;
        container.scrollTo({
          top: Math.max(0, targetScrollTop),
          behavior: 'smooth',
        });
        setTimeout(() => {
          isManualNavRef.current = false;
        }, 550);
      }
    }
  };

  const handleGoToPageSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const p = parseInt(inputPage, 10);
    if (!isNaN(p)) {
      goToPage(p);
    } else {
      setInputPage(String(currentPage));
    }
  };

  // Zoom
  const handleZoomIn = () => setZoomLevel((z) => Math.min(175, z + 15));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(65, z - 15));
  const handleResetZoom = () => {
    setZoomLevel(100);
    initPageFlip();
  };

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
      setTimeout(initPageFlip, 200);
    };
    document.addEventListener('fullscreenchange', onFsChange);
    return () => document.removeEventListener('fullscreenchange', onFsChange);
  }, [initPageFlip]);

  return (
    <div
      ref={containerRef}
      className={`flex flex-col bg-slate-900 text-slate-100 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl select-none ${className} ${
        isFullscreen ? 'fixed inset-0 z-50 rounded-none border-0' : 'h-full min-h-[580px]'
      }`}
    >
      {/* 1. BARRA SUPERIOR DE FERRAMENTAS E CONTROLES */}
      <header className="px-3 sm:px-4 py-2.5 bg-slate-950 border-b border-slate-800 flex flex-wrap items-center justify-between gap-2 shrink-0 z-30">
        {/* Lado Esquerdo: Miniaturas e Título */}
        <div className="flex items-center gap-2 min-w-0">
          <button
            type="button"
            onClick={() => setShowThumbnails(!showThumbnails)}
            className={`p-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition ${
              showThumbnails
                ? 'bg-indigo-600 border-indigo-500 text-white shadow-xs'
                : 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800'
            }`}
            title="Abrir painel lateral de miniaturas de páginas"
          >
            <LayoutGrid className="w-4 h-4" />
            <span className="hidden sm:inline">Páginas</span>
          </button>

          <span
            className="text-xs font-bold text-slate-200 truncate max-w-[130px] sm:max-w-[200px]"
            title={documentTitle}
          >
            {documentTitle}
          </span>
        </div>

        {/* Centro: Controles de Paginação Direta */}
        <div className="flex items-center gap-1 bg-slate-900/90 px-2 py-1 rounded-xl border border-slate-800 text-xs">
          <button
            type="button"
            onClick={() => goToPage(1)}
            disabled={currentPage <= 1 || loading}
            className="p-1 hover:bg-slate-800 disabled:opacity-30 rounded-md transition text-slate-400 hover:text-white"
            title="Ir para a primeira página (Capa)"
          >
            <Home className="w-3.5 h-3.5" />
          </button>

          <button
            type="button"
            onClick={handlePrevPage}
            disabled={currentPage <= 1 || loading}
            className="p-1 hover:bg-slate-800 disabled:opacity-30 rounded-md transition text-slate-300 hover:text-white"
            title="Página anterior (←)"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <form onSubmit={handleGoToPageSubmit} className="flex items-center gap-1">
            <span className="text-slate-400 text-[11px] hidden sm:inline">Pág.</span>
            <input
              type="text"
              value={inputPage}
              onChange={(e) => setInputPage(e.target.value)}
              onBlur={handleGoToPageSubmit}
              disabled={loading || totalPages === 0}
              className="w-10 text-center bg-slate-950 border border-slate-700 rounded-md px-1 py-0.5 text-xs font-mono font-bold text-white focus:outline-hidden focus:border-indigo-500"
            />
            <span className="text-slate-400 text-[11px]">de {totalPages || '—'}</span>
          </form>

          <button
            type="button"
            onClick={handleNextPage}
            disabled={currentPage >= totalPages || loading}
            className="p-1 hover:bg-slate-800 disabled:opacity-30 rounded-md transition text-slate-300 hover:text-white"
            title="Próxima página (→)"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Lado Direito: Modos de Visualização, Enquadramento, Zoom e Ações */}
        <div className="flex items-center gap-1.5 sm:gap-2">
          {/* Seletor de Modos (1 Página, 2 Páginas, Rolagem) */}
          <div className="flex items-center bg-slate-900 p-0.5 rounded-xl border border-slate-800">
            <button
              type="button"
              onClick={() => setLayoutMode('single')}
              className={`px-2 py-1 rounded-lg text-xs font-semibold flex items-center gap-1 transition ${
                effectiveMode === 'single' && layoutMode !== 'scroll'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="1 Página Centralizada (Folhear 3D focado)"
            >
              <FileText className="w-3.5 h-3.5" />
              <span className="hidden md:inline">1 Pág</span>
            </button>

            <button
              type="button"
              onClick={() => setLayoutMode('double')}
              className={`px-2 py-1 rounded-lg text-xs font-semibold flex items-center gap-1 transition ${
                effectiveMode === 'double' && layoutMode !== 'scroll'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="2 Páginas (Livro Aberto lado a lado)"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span className="hidden md:inline">2 Págs</span>
            </button>

            <button
              type="button"
              onClick={() => setLayoutMode('scroll')}
              className={`px-2 py-1 rounded-lg text-xs font-semibold flex items-center gap-1 transition ${
                layoutMode === 'scroll'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Rolagem Contínua Vertical"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Rolagem</span>
            </button>
          </div>

          {/* Ajustar à Tela (Fit-to-Screen) */}
          <button
            type="button"
            onClick={handleResetZoom}
            className="p-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded-lg text-slate-300 transition"
            title="Ajustar automaticamente à altura e largura da tela"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          {/* Zoom */}
          <div className="hidden lg:flex items-center gap-0.5 bg-slate-900 px-1 py-0.5 rounded-xl border border-slate-800 text-xs">
            <button
              type="button"
              onClick={handleZoomOut}
              className="p-1 hover:bg-slate-800 rounded text-slate-300"
              title="Diminuir Zoom"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="px-1 text-[11px] font-mono text-slate-300 font-bold">{zoomLevel}%</span>
            <button
              type="button"
              onClick={handleZoomIn}
              className="p-1 hover:bg-slate-800 rounded text-slate-300"
              title="Aumentar Zoom"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Download */}
          {onDownloadPdf ? (
            <button
              type="button"
              onClick={onDownloadPdf}
              className="px-2.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1 transition"
              title="Baixar PDF Original"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Baixar</span>
            </button>
          ) : (
            <a
              href={pdfUrl}
              download
              className="px-2.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1 transition"
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
            className="p-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded-xl transition"
            title={isFullscreen ? 'Sair da tela cheia' : 'Modo Tela Cheia Imersiva'}
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </header>

      {/* 2. ÁREA CENTRAL: PALCO PRINCIPAL + GAVETA LATERAL DE MINIATURAS */}
      <div className="relative flex-1 flex overflow-hidden bg-slate-950">
        {/* Gaveta Lateral de Miniaturas */}
        {showThumbnails && (
          <aside className="w-48 sm:w-56 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 z-40 animate-in slide-in-from-left-4 duration-200 shadow-2xl">
            <div className="p-3 border-b border-slate-800 flex items-center justify-between text-xs">
              <span className="font-bold text-slate-200">Miniaturas ({totalPages})</span>
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
                  onClick={() => goToPage(p.pageNumber)}
                  className={`w-full text-left p-1.5 rounded-xl border transition flex flex-col items-center gap-1.5 ${
                    currentPage === p.pageNumber
                      ? 'bg-indigo-950/80 border-indigo-500 shadow-md ring-2 ring-indigo-500/40'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
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

        {/* PALCO PRINCIPAL COM CENTRALIZAÇÃO MATEMÁTICA E AJUSTE RIGOROSO */}
        <main
          ref={stageRef}
          className="flex-1 relative flex items-center justify-center overflow-hidden p-2 sm:p-6 bg-slate-950"
        >
          {/* Feedback de Carregamento Progressivo */}
          {loading && (
            <div className="flex flex-col items-center justify-center p-8 text-center max-w-sm m-auto">
              <Loader2 className="w-10 h-10 text-indigo-500 animate-spin mb-4" />
              <h3 className="text-sm font-bold text-slate-100 mb-1">Carregando Minuta em Alta Resolução</h3>
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
            <div className="p-6 bg-rose-950/40 border border-rose-800/80 rounded-2xl max-w-md text-center m-auto">
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

          {/* MODO 1 E 2: FLIPBOOK 3D (1 PÁGINA CENTRALIZADA OU 2 PÁGINAS SPREAD) */}
          {!loading && !error && effectiveMode !== 'scroll' && (
            <div
              className="w-full h-full flex items-center justify-center relative select-none"
              style={{
                transform: zoomLevel !== 100 ? `scale(${zoomLevel / 100})` : 'none',
                transformOrigin: 'center center',
              }}
            >
              {/* Botão Flutuante de Folhear para a Esquerda (<) */}
              <button
                type="button"
                onClick={handlePrevPage}
                disabled={currentPage <= 1}
                className="absolute left-2 sm:left-4 z-20 w-11 h-11 rounded-full bg-slate-900/80 hover:bg-indigo-600 border border-slate-700 text-white flex items-center justify-center shadow-2xl backdrop-blur-md transition-all hover:scale-110 disabled:opacity-0 disabled:pointer-events-none"
                title="Página anterior (←)"
              >
                <ChevronLeft className="w-6 h-6 -ml-0.5" />
              </button>

              {/* Ponto de Montagem Estável do React - NUNCA removido pelo destroy() do PageFlip */}
              <div
                ref={bookMountRef}
                className="flipbook-mount w-full h-full flex items-center justify-center m-auto relative"
              />

              {/* Botão Flutuante de Folhear para a Direita (>) */}
              <button
                type="button"
                onClick={handleNextPage}
                disabled={currentPage >= totalPages}
                className="absolute right-2 sm:right-4 z-20 w-11 h-11 rounded-full bg-slate-900/80 hover:bg-indigo-600 border border-slate-700 text-white flex items-center justify-center shadow-2xl backdrop-blur-md transition-all hover:scale-110 disabled:opacity-0 disabled:pointer-events-none"
                title="Próxima página (→)"
              >
                <ChevronRight className="w-6 h-6 -mr-0.5" />
              </button>
            </div>
          )}

          {/* MODO 3: ROLAGEM VERTICAL CONTÍNUA COM NAVEGAÇÃO SUAVE E ISOLAMENTO DE SCROLL */}
          {!loading && !error && effectiveMode === 'scroll' && (
            <div className="w-full h-full relative select-none flex items-center justify-center">
              {/* Botão Flutuante de Rolar para Página Anterior (<) */}
              <button
                type="button"
                onClick={handlePrevPage}
                disabled={currentPage <= 1}
                className="absolute left-2 sm:left-4 z-20 w-11 h-11 rounded-full bg-slate-900/85 hover:bg-indigo-600 border border-slate-700 text-white flex items-center justify-center shadow-2xl backdrop-blur-md transition-all hover:scale-110 disabled:opacity-0 disabled:pointer-events-none"
                title="Página anterior (←)"
              >
                <ChevronLeft className="w-6 h-6 -ml-0.5" />
              </button>

              {/* Container de Rolagem Estritamente Isolado - NUNCA rola o window externo */}
              <div
                ref={scrollContainerRef}
                onScroll={handleScrollModeScroll}
                className="w-full h-full overflow-y-auto px-2 sm:px-6 py-6 flex flex-col items-center gap-8 overscroll-contain scroll-smooth custom-scrollbar"
                style={{
                  transform: zoomLevel !== 100 ? `scale(${zoomLevel / 100})` : 'none',
                  transformOrigin: 'top center',
                }}
              >
                {pagesData.map((page) => (
                  <div
                    key={page.pageNumber}
                    id={`scroll-page-${page.pageNumber}`}
                    className="bg-white rounded-xl shadow-2xl overflow-hidden max-w-3xl w-full border border-slate-800/80 flex flex-col shrink-0 transition-shadow hover:shadow-indigo-950/40"
                  >
                    <div className="bg-slate-100/95 px-3.5 py-2 text-[11px] font-mono text-slate-500 border-b border-slate-200 flex items-center justify-between">
                      <span className="font-bold text-slate-800 flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5 text-indigo-600" />
                        Página {page.pageNumber} de {totalPages}
                      </span>
                      <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Minuta Oficial</span>
                    </div>
                    <img
                      src={page.imageUrl}
                      alt={`Página ${page.pageNumber}`}
                      className="w-full h-auto object-contain select-text block"
                      loading={page.pageNumber <= 3 ? 'eager' : 'lazy'}
                    />
                  </div>
                ))}
              </div>

              {/* Botão Flutuante de Rolar para Próxima Página (>) */}
              <button
                type="button"
                onClick={handleNextPage}
                disabled={currentPage >= totalPages}
                className="absolute right-2 sm:right-4 z-20 w-11 h-11 rounded-full bg-slate-900/85 hover:bg-indigo-600 border border-slate-700 text-white flex items-center justify-center shadow-2xl backdrop-blur-md transition-all hover:scale-110 disabled:opacity-0 disabled:pointer-events-none"
                title="Próxima página (→)"
              >
                <ChevronRight className="w-6 h-6 -mr-0.5" />
              </button>
            </div>
          )}
        </main>
      </div>

      {/* 3. BARRA INFERIOR / TIMELINE SLIDER INTERATIVO DE PÁGINAS */}
      <footer className="px-4 py-2 bg-slate-950 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-2 shrink-0 z-30">
        {/* Controle Deslizante (Timeline Scrubber) */}
        <div className="flex items-center gap-3 w-full sm:max-w-md">
          <span className="text-[11px] font-mono font-bold text-slate-400 shrink-0">
            {currentPage} / {totalPages || 1}
          </span>
          <input
            type="range"
            min="1"
            max={totalPages || 1}
            value={currentPage}
            onChange={(e) => goToPage(parseInt(e.target.value, 10))}
            disabled={loading || totalPages === 0}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500 hover:accent-indigo-400"
            title="Arraste para navegar rapidamente entre as páginas"
          />
          <span className="text-[10px] text-slate-500 shrink-0 font-mono hidden sm:inline">
            {totalPages ? `${Math.round((currentPage / totalPages) * 100)}%` : '0%'}
          </span>
        </div>

        {/* Dica de Navegabilidade e Status */}
        <div className="flex items-center gap-3 text-[11px] text-slate-400">
          <span className="hidden md:inline">
            💡 Dica: Use as setas do teclado <kbd className="px-1 py-0.5 bg-slate-800 rounded border border-slate-700 text-[10px] font-mono">←</kbd> <kbd className="px-1 py-0.5 bg-slate-800 rounded border border-slate-700 text-[10px] font-mono">→</kbd> para folhear.
          </span>
          <span className="px-2 py-0.5 rounded-full bg-slate-900 border border-slate-800 text-[10px] font-semibold uppercase text-indigo-400">
            {effectiveMode === 'single' ? '1 Página Centralizada' : effectiveMode === 'double' ? '2 Páginas (Livro Aberto)' : 'Rolagem Contínua'}
          </span>
        </div>
      </footer>
    </div>
  );
};
