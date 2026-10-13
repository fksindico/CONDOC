import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Layouts
import { AdminLayout } from '@/components/layout/AdminLayout';
import { PortalLayout } from '@/components/layout/PortalLayout';
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

// Páginas do Portal do Morador (M01 a M12)
import { ResidentDashboardPage } from '@/pages/portal/ResidentDashboardPage';
import { DocumentReaderPage } from '@/pages/portal/DocumentReaderPage';
import { SuggestionCreatePage } from '@/pages/portal/SuggestionCreatePage';
import { PublicSuggestionsWallPage } from '@/pages/portal/PublicSuggestionsWallPage';
import { PublicSuggestionDetailPage } from '@/pages/portal/PublicSuggestionDetailPage';
import { MySuggestionsPage } from '@/pages/portal/MySuggestionsPage';
import { MyAgreementsPage } from '@/pages/portal/MyAgreementsPage';
import { ResidentProfilePage } from '@/pages/portal/ResidentProfilePage';
import { AccessStatusPage } from '@/pages/portal/AccessStatusPage';

// Modo de Apresentação em Assembleia (Leitura)
import { AssemblyPresentationPage } from '@/pages/assembly/AssemblyPresentationPage';

// Consultas Públicas Simplificadas (PDF & Sugestões Ágeis)
import { PublicConsultationPage } from '@/pages/public/PublicConsultationPage';
import { SimplifiedConsultationsPage } from '@/pages/admin/SimplifiedConsultationsPage';

export const App: React.FC = () => {
  return (
    <Routes>
      {/* Rotas Públicas de Acesso */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/acesso/convite" element={<InvitationRedeemPage />} />
      <Route path="/participar/:token" element={<PublicConsultationPage />} />

      {/* Painel Administrativo da Gestão / Síndico (S01 a S21) */}
      <Route path="/painel" element={<AdminLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="consultas" element={<SimplifiedConsultationsPage />} />
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

      {/* Portal do Morador (M01 a M12) */}
      <Route path="/portal" element={<PortalLayout />}>
        <Route index element={<ResidentDashboardPage />} />
        <Route path="documento" element={<DocumentReaderPage />} />
        <Route path="sugerir" element={<SuggestionCreatePage />} />
        <Route path="mural" element={<PublicSuggestionsWallPage />} />
        <Route path="mural/:id" element={<PublicSuggestionDetailPage />} />
        <Route path="minhas-sugestoes" element={<MySuggestionsPage />} />
        <Route path="minhas-concordancias" element={<MyAgreementsPage />} />
        <Route path="meu-cadastro" element={<ResidentProfilePage />} />
        <Route path="situacao" element={<AccessStatusPage />} />
      </Route>

      {/* Modo de Apresentação em Assembleia (Somente Leitura - UI-38, CA-45) */}
      <Route path="/assembleia/:docId" element={<AssemblyLayout />}>
        <Route index element={<AssemblyPresentationPage />} />
      </Route>

      {/* Rota Raiz Padrão */}
      <Route path="/" element={<Navigate to="/portal" replace />} />
      <Route path="*" element={<Navigate to="/portal" replace />} />
    </Routes>
  );
};
