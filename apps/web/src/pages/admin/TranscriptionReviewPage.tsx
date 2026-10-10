import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTenant } from '@/contexts/TenantContext';
import { api } from '@/lib/api';
import { ArrowLeft, CheckCircle2, Edit3, Upload, FileText, ShieldAlert } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';

export const TranscriptionReviewPage: React.FC = () => {
  const { docId } = useParams<{ docId: string }>();
  const { activeCondominiumId } = useTenant();

  const [rawText, setRawText] = useState(
    'CAPITULO I - DO REGIMENTO INTERNO\nArt. 1º. O presente Regimento Interno regula o comportamento e as relacoes entre os moradores do Condominio.\nArt. 2º. E vedado aos moradores produzir barulho excessivo apos as 22h00.'
  );
  const [correctedText, setCorrectedText] = useState(
    'CAPÍTULO I - DO REGIMENTO INTERNO\nArt. 1º. O presente Regimento Interno regula o comportamento e as relações entre os moradores do Condomínio.\nArt. 2º. É vedado aos moradores produzir barulho excessivo após as 22h00.'
  );
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleConfirm = () => {
    setIsSubmitting(true);
    setTimeout(() => {
      setIsConfirmed(true);
      setIsSubmitting(false);
    }, 600);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Link
            to="/painel/projetos"
            className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 mb-1 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Voltar</span>
          </Link>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Conferência Humana de Transcrição (OCR)
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Conferência e correção de documento original escaneado (CA-17, CA-18).
          </p>
        </div>
        <Button onClick={handleConfirm} isLoading={isSubmitting} disabled={isConfirmed}>
          <CheckCircle2 className="w-4 h-4 mr-1.5" />
          <span>{isConfirmed ? 'Transcrição Confirmada' : 'Confirmar Conferência'}</span>
        </Button>
      </div>

      {isConfirmed && (
        <Alert variant="success" title="Conferência Humana Concluída!">
          A transcrição foi homologada e fixada como documento-base somente leitura para comparação e mapeamento de
          origens.
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Lado 1: Texto Bruto Extraído (OCR) */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="w-5 h-5 text-slate-500" />
              <span>Original Extraído (OCR)</span>
            </CardTitle>
            <CardDescription>Texto bruto gerado a partir do arquivo original PDF/Imagem.</CardDescription>
          </CardHeader>
          <CardContent>
            <textarea
              readOnly
              rows={16}
              className="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded-lg p-3 outline-none text-slate-700 leading-relaxed"
              value={rawText}
            />
          </CardContent>
        </Card>

        {/* Lado 2: Correção e Ajuste Humano */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Edit3 className="w-5 h-5 text-brand-600" />
              <span>Transcrição Corrigida</span>
            </CardTitle>
            <CardDescription>
              Corrija eventuais falhas de OCR. Não simula alteração normativa (CA-18).
            </CardDescription>
          </CardHeader>
          <CardContent>
            <textarea
              rows={16}
              disabled={isConfirmed}
              className="w-full text-xs font-mono border border-slate-300 rounded-lg p-3 outline-none focus:ring-2 focus:ring-brand-500 leading-relaxed text-slate-900"
              value={correctedText}
              onChange={(e) => setCorrectedText(e.target.value)}
            />
          </CardContent>
        </Card>
      </div>

      <Alert variant="info" title="Regra de Integridade Histórica (CA-18)">
        Corrigir a transcrição documental gera uma nova versão de fidelidade da transcrição, sem criar alteração
        normativa no documento. A versão base permanece como registro histórico inalterável.
      </Alert>
    </div>
  );
};
