import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Layouts
import { AdminLayout } from '@/components/layout/AdminLayout';
import { AssemblyLayout } from '@/components/layout/AssemblyLayout';

// Páginas de Autenticação & Onboarding
import { LoginPage } from '@/pages/auth/LoginPage';
import { InvitationRedeemPage } from '@/pages/auth/InvitationRedeemPage';

// Páginas Administrativas do Síndico (S02 a S21)
import { DashboardPage } from '@/pages/admin/DashboardPage';
import { CondominiumsPage } from '@/pages/admin/CondominiumsPage';
import { UnitsPage } from '@/pages/admin/UnitsPage';
import { ResidentsPage } from '@/pages/admin/ResidentsPage';
import { ImportWizardPage } from '@/pages/admin/ImportWizardPage';
import { MembershipVerificationPage } from '@/pages/admin/MembershipVerificationPage';
import { InvitationsPage } from '@/pages/admin/InvitationsPage';
import { ProjectsPage } from '@/pages/admin/ProjectsPage';
import { DocumentsPage } from '@/pages/admin/DocumentsPage';
import { TranscriptionReviewPage } from '@/pages/admin/TranscriptionReviewPage';
import { StructuredEditorPage } from '@/pages/admin/StructuredEditorPage';
import { CompareDeParaPage } from '@/pages/admin/CompareDeParaPage';
import { SnapshotsPage } from '@/pages/admin/SnapshotsPage';
import { ExportsPage } from '@/pages/admin/ExportsPage';
import { CampaignsPage } from '@/pages/admin/CampaignsPage';
import { ModerationQueuePage } from '@/pages/admin/ModerationQueuePage';
import { SuggestionDetailPage } from '@/pages/admin/SuggestionDetailPage';
import { CampaignStatsPage } from '@/pages/admin/CampaignStatsPage';
import { TeamPage } from '@/pages/admin/TeamPage';
import { AuditLogsPage } from '@/pages/admin/AuditLogsPage';

// Modo de Apresentação em Assembleia (Leitura)
import { AssemblyPresentationPage } from '@/pages/assembly/AssemblyPresentationPage';

// Consultas Públicas Simplificadas (PDF & Sugestões Ágeis)
import { PublicConsultationPage } from '@/pages/public/PublicConsultationPage';
import { SimplifiedConsultationsPage } from '@/pages/admin/SimplifiedConsultationsPage';
import { LandingPage } from '@/pages/public/LandingPage';
import { LandingConfigPage } from '@/pages/admin/LandingConfigPage';

export const App: React.FC = () => {
  return (
    <Routes>
      {/* Rota Raiz: Landing Page Institucional Pública */}
      <Route path="/" element={<LandingPage />} />

      {/* Rotas Públicas de Acesso */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/acesso/convite" element={<InvitationRedeemPage />} />
      <Route path="/participar/:token" element={<PublicConsultationPage />} />

      {/* Painel Administrativo da Gestão / Síndico (S01 a S21) */}
      <Route path="/painel" element={<AdminLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="consultas" element={<SimplifiedConsultationsPage />} />
        <Route path="apresentacao" element={<LandingConfigPage />} />
        <Route path="condominios" element={<CondominiumsPage />} />
        <Route path="unidades" element={<UnitsPage />} />
        <Route path="moradores" element={<ResidentsPage />} />
        <Route path="moradores/importar" element={<ImportWizardPage />} />
        <Route path="moradores/validacoes" element={<MembershipVerificationPage />} />
        <Route path="convites" element={<InvitationsPage />} />
        <Route path="projetos" element={<ProjectsPage />} />
        <Route path="projetos/:projectId/documentos" element={<DocumentsPage />} />
        <Route path="documentos/:docId/editor" element={<StructuredEditorPage />} />
        <Route path="documentos/:docId/compare" element={<CompareDeParaPage />} />
        <Route path="documentos/:docId/importacao" element={<TranscriptionReviewPage />} />
        <Route path="documentos/:docId/versoes" element={<SnapshotsPage />} />
        <Route path="exportacoes" element={<ExportsPage />} />
        <Route path="campanhas" element={<CampaignsPage />} />
        <Route path="sugestoes" element={<ModerationQueuePage />} />
        <Route path="sugestoes/:id" element={<SuggestionDetailPage />} />
        <Route path="estatisticas" element={<CampaignStatsPage />} />
        <Route path="equipe" element={<TeamPage />} />
        <Route path="auditoria" element={<AuditLogsPage />} />
      </Route>

      {/* Redirecionamento amigável de rotas legadas do Portal para a Landing Page pública (Sem senhas para moradores) */}
      <Route path="/portal/*" element={<Navigate to="/" replace />} />

      {/* Modo de Apresentação em Assembleia (Somente Leitura - UI-38, CA-45) */}
      <Route path="/assembleia/:docId" element={<AssemblyLayout />}>
        <Route index element={<AssemblyPresentationPage />} />
      </Route>

      {/* Fallback para páginas não encontradas */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
