import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { api, setApiTenantId, getApiTenantId } from '@/lib/api';
import type { Condominium } from '@condc/api-contracts';

interface TenantContextType {
  condominiums: Condominium[];
  activeCondominiumId: string | null;
  activeCondominium: Condominium | null;
  isLoading: boolean;
  selectCondominium: (condoId: string) => void;
  refetchCondominiums: () => Promise<void>;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export const TenantProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = useQueryClient();
  const [condominiums, setCondominiums] = useState<Condominium[]>([]);
  const [activeCondominiumId, setActiveCondominiumIdState] = useState<string | null>(getApiTenantId());
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchCondos = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await api.get<Condominium[]>('/condominiums');
      const list = res.data || [];
      setCondominiums(list);

      // Se não houver condomínio selecionado e a lista tiver itens, seleciona o primeiro
      const currentStored = getApiTenantId();
      if (!currentStored && list.length > 0) {
        const firstId = list[0].id;
        setActiveCondominiumIdState(firstId);
        setApiTenantId(firstId);
      } else if (currentStored && !list.some((c) => c.id === currentStored) && list.length > 0) {
        const firstId = list[0].id;
        setActiveCondominiumIdState(firstId);
        setApiTenantId(firstId);
      }
    } catch {
      setCondominiums([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCondos();
  }, [fetchCondos]);

  const selectCondominium = (condoId: string) => {
    if (condoId === activeCondominiumId) return;

    // UI-01: Troca de condomínio limpa contexto e expurga todo o cache do TanStack Query
    queryClient.clear();

    setActiveCondominiumIdState(condoId);
    setApiTenantId(condoId);
  };

  const activeCondominium = condominiums.find((c) => c.id === activeCondominiumId) || null;

  return (
    <TenantContext.Provider
      value={{
        condominiums,
        activeCondominiumId,
        activeCondominium,
        isLoading,
        selectCondominium,
        refetchCondominiums: fetchCondos,
      }}
    >
      {children}
    </TenantContext.Provider>
  );
};

export const useTenant = (): TenantContextType => {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant deve ser utilizado dentro de um TenantProvider');
  }
  return context;
};
