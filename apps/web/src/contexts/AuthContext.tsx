import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import type { RoleType } from '@condc/api-contracts';

export interface UserAccount {
  account_id: string;
  email: string;
  full_name: string;
  tenant_id?: string | null;
  roles?: string[];
}

interface AuthContextType {
  user: UserAccount | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  activeRole: string;
  roles: string[];
  setActiveRole: (role: string) => void;
  isSindico: boolean;
  isAdmin: boolean;
  isMorador: boolean;
  refetchSession: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserAccount | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [roles, setRoles] = useState<string[]>([]);
  const [activeRole, setActiveRole] = useState<string>('morador');

  const fetchSession = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await api.get<{ authenticated: boolean; account: UserAccount | null }>('/auth/session');
      if (res.data.authenticated && res.data.account) {
        setUser(res.data.account);
        setIsAuthenticated(true);
        const userRoles = res.data.account.roles || [];
        setRoles(userRoles);
        if (userRoles.includes('sindico')) {
          setActiveRole('sindico');
        } else if (userRoles.includes('admin')) {
          setActiveRole('admin');
        } else if (userRoles.length > 0) {
          setActiveRole(userRoles[0]);
        }
      } else {
        setUser(null);
        setIsAuthenticated(false);
        setRoles([]);
      }
    } catch {
      setUser(null);
      setIsAuthenticated(false);
      setRoles([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignora erro no logout
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setRoles([]);
    }
  };

  const isSindico = activeRole === 'sindico' || roles.includes('sindico');
  const isAdmin = activeRole === 'admin' || isSindico || roles.includes('admin');
  const isMorador = !isAdmin;

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        activeRole,
        roles,
        setActiveRole,
        isSindico,
        isAdmin,
        isMorador,
        refetchSession: fetchSession,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser utilizado dentro de um AuthProvider');
  }
  return context;
};
