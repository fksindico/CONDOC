import React, { useState } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { Alert } from './Alert';
import { Lock, ShieldAlert } from 'lucide-react';

interface IdentityRevealModalProps {
  isOpen: boolean;
  onClose: () => void;
  publicProtocol: string;
  onConfirm: (justification: string) => Promise<void>;
  isLoading?: boolean;
}

export const IdentityRevealModal: React.FC<IdentityRevealModalProps> = ({
  isOpen,
  onClose,
  publicProtocol,
  onConfirm,
  isLoading = false,
}) => {
  const [justification, setJustification] = useState('');
  const [error, setError] = useState('');

  const handleConfirm = async () => {
    if (justification.trim().length < 5) {
      setError('A justificativa deve conter no mínimo 5 caracteres conforme exigência legal.');
      return;
    }
    setError('');
    try {
      await onConfirm(justification.trim());
      setJustification('');
      onClose();
    } catch (e: any) {
      setError(e.message || 'Erro ao consultar identidade.');
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Acesso Auditado à Identidade do Autor"
      description={`Sugestão ${publicProtocol}`}
      footer={
        <>
          <Button variant="outline" onClick={onClose} disabled={isLoading}>
            Cancelar
          </Button>
          <Button
            variant="destructive"
            onClick={handleConfirm}
            isLoading={isLoading}
            disabled={justification.trim().length < 5}
          >
            Confirmar e Registrar Auditoria
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Alert variant="warning" title="Auditoria Obrigatória (LGPD / CA-33)">
          O acesso aos dados pessoais de contato e residência do morador autor é estritamente restrito e registrará um
          evento permanente na trilha de auditoria contendo seu usuário, data/hora e a justificativa fornecida.
        </Alert>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
            Motivo / Justificativa Administrativa Fundamentada (Mínimo 5 caracteres) *
          </label>
          <textarea
            className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            rows={3}
            placeholder="Ex: Diligência administrativa para conferir legitimidade e dirimir dúvida sobre vaga..."
            value={justification}
            onChange={(e) => {
              setJustification(e.target.value);
              if (error) setError('');
            }}
          />
          {error && <p className="text-xs text-rose-600 mt-1 font-medium">{error}</p>}
        </div>
      </div>
    </Modal>
  );
};
