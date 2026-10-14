declare module 'page-flip' {
  export interface FlipSetting {
    startPage?: number;
    size?: 'fixed' | 'stretch';
    width?: number;
    height?: number;
    minWidth?: number;
    maxWidth?: number;
    minHeight?: number;
    maxHeight?: number;
    drawShadow?: boolean;
    flippingTime?: number;
    usePortrait?: boolean;
    startZIndex?: number;
    autoSize?: boolean;
    maxShadowOpacity?: number;
    showCover?: boolean;
    mobileScrollSupport?: boolean;
    clickEventForward?: boolean;
    useMouseEvents?: boolean;
    swipeDistance?: number;
    showPageCorners?: boolean;
    disableFlipByClick?: boolean;
  }

  export interface FlipEvent {
    data: number;
    object: PageFlip;
  }

  export class PageFlip {
    constructor(element: HTMLElement, setting: FlipSetting);
    destroy(): void;
    update(): void;
    loadFromImages(imagesHref: string[]): void;
    loadFromHTML(items: NodeListOf<HTMLElement> | HTMLElement[]): void;
    updateFromImages(imagesHref: string[]): void;
    updateFromHtml(items: NodeListOf<HTMLElement> | HTMLElement[]): void;
    turnToPrevPage(): void;
    turnToNextPage(): void;
    turnToPage(page: number): void;
    flipNext(corner?: string): void;
    flipPrev(corner?: string): void;
    flip(page: number, corner?: string): void;
    getPageCount(): number;
    getCurrentPageIndex(): number;
    on(event: 'flip', callback: (e: FlipEvent) => void): PageFlip;
    on(event: 'changeState' | 'changeOrientation' | 'init' | 'update', callback: (e: any) => void): PageFlip;
    on(event: string, callback: (e: any) => void): PageFlip;
    off(event: string, callback?: (e: any) => void): PageFlip;
  }
}
