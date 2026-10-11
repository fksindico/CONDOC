import React, { useEffect } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Bold, Italic, List, ListOrdered, Undo, Redo } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TiptapEditorProps {
  content: string;
  onChange: (text: string) => void;
  disabled?: boolean;
  className?: string;
}

export const TiptapEditor: React.FC<TiptapEditorProps> = ({
  content,
  onChange,
  disabled = false,
  className,
}) => {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: false, // Proibição de headings livres que quebrem a semântica jurídica de artigos
      }),
    ],
    content,
    editable: !disabled,
    onUpdate: ({ editor }) => {
      onChange(editor.getText());
    },
  });

  useEffect(() => {
    if (editor && editor.getText() !== content) {
      editor.commands.setContent(content);
    }
  }, [content, editor]);

  if (!editor) {
    return <div className="p-4 text-xs text-slate-500">Carregando editor...</div>;
  }

  return (
    <div className={cn('border border-slate-200 rounded-lg overflow-hidden bg-white', className)}>
      {/* Barra de Formatação Semântica Jurídica */}
      <div className="flex items-center gap-1 p-1.5 border-b border-slate-100 bg-slate-50 text-xs">
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBold().run()}
          disabled={disabled}
          className={`p-1.5 rounded hover:bg-slate-200 transition-colors ${
            editor.isActive('bold') ? 'bg-slate-200 text-brand-700 font-bold' : 'text-slate-600'
          }`}
          title="Negrito"
        >
          <Bold className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleItalic().run()}
          disabled={disabled}
          className={`p-1.5 rounded hover:bg-slate-200 transition-colors ${
            editor.isActive('italic') ? 'bg-slate-200 text-brand-700 font-bold' : 'text-slate-600'
          }`}
          title="Itálico"
        >
          <Italic className="w-3.5 h-3.5" />
        </button>
        <div className="h-3.5 w-px bg-slate-300 mx-1" />
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          disabled={disabled}
          className={`p-1.5 rounded hover:bg-slate-200 transition-colors ${
            editor.isActive('bulletList') ? 'bg-slate-200 text-brand-700 font-bold' : 'text-slate-600'
          }`}
          title="Lista de Itens"
        >
          <List className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          disabled={disabled}
          className={`p-1.5 rounded hover:bg-slate-200 transition-colors ${
            editor.isActive('orderedList') ? 'bg-slate-200 text-brand-700 font-bold' : 'text-slate-600'
          }`}
          title="Lista Numerada"
        >
          <ListOrdered className="w-3.5 h-3.5" />
        </button>
        <div className="h-3.5 w-px bg-slate-300 mx-1" />
        <button
          type="button"
          onClick={() => editor.chain().focus().undo().run()}
          disabled={disabled || !editor.can().undo()}
          className="p-1.5 rounded hover:bg-slate-200 text-slate-600 disabled:opacity-40"
          title="Desfazer"
        >
          <Undo className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().redo().run()}
          disabled={disabled || !editor.can().redo()}
          className="p-1.5 rounded hover:bg-slate-200 text-slate-600 disabled:opacity-40"
          title="Refazer"
        >
          <Redo className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Área Editável ProseMirror */}
      <EditorContent editor={editor} className="p-3 text-sm leading-relaxed" />
    </div>
  );
};
