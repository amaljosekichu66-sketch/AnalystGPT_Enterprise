# React Migration Mapping & Frontend Architecture Blueprint

**Sprint:** Sprint 14 Phase 6 — OpenAPI / React Migration Readiness (implemented; released in v14.0.0)
**Target Release:** **v17.0.0 — Sprint 17, React Migration & Modern Presentation Layer** (planned, not started)
**Status:** Approved preliminary blueprint — to be re-validated by the Sprint 16 readiness audit and superseded where the Sprint 16 React architecture ADR decides otherwise

> **Scope note.** This blueprint is design guidance, not delivered work. The backend side of
> it — the frozen OpenAPI 3.1 contract and the technology-neutral frontend service layer —
> was released in v14.0.0. No React
> code exists in this repository.
>
> **Sequencing (ROADMAP.md is authoritative):** Sprint 15 — Enterprise Stabilization,
> Governance Completion & Product/UX Remediation (no React work) → Sprint 16 — AI Provider
> Abstraction & Complete React Readiness (final readiness audit; React architecture and design
> system defined, not built) → **Sprint 17 — React Migration** (React + TypeScript implemented).
> Earlier revisions named Sprint 15 as the React migration, and a later one called Sprint 15
> *Refactoring & Architectural Evolution*; both are superseded.
>
> This document is the Sprint 14 *initial* readiness foundation. Stack choices, state strategy
> and component decomposition below are provisional inputs to the Sprint 16 architecture
> decision, not final decisions.

---

## 1. Executive Summary & Migration Strategy

AnalystGPT Enterprise was engineered with a strict layered architecture to ensure that presentation concerns remain isolated from application core workflows. The intent is that the platform can migrate from the Streamlit presentation layer to a modern, production-ready React + TypeScript frontend without backend changes. The migration is planned for Sprint 17. The build tooling and styling approach (this blueprint originally assumed Vite + TailwindCSS) are decided in Sprint 16, which evaluates the design-system approach rather than adopting a library by default.

This document establishes the authoritative contract mapping and component decomposition required for React frontend engineers, guaranteeing that:
1. **Zero Backend Changes Required:** The FastAPI REST API is frozen and fully typed (OpenAPI 3.1). *This is the Sprint 14 design intent; it is proven only when the Sprint 16 readiness audit passes.*
2. **Coexistence Capability:** Both Streamlit and React frontends can operate simultaneously against the same backend services.
3. **Purity of Presentation:** No business logic, database queries, or authorization bypasses reside in the presentation layer.

---

## 2. Architectural Boundary & Coexistence Topology

```text
┌─────────────────────────────────────────────────────────────┐
│                      Client Browsers                        │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               │ (Port 8501)                   │ (Port 3000)
               ▼                               ▼
     ┌───────────────────┐           ┌───────────────────┐
     │ Streamlit UI (MVP)│           │  React Frontend   │
     │  Python / View    │           │ TypeScript / Vite │
     └─────────┬─────────┘           └─────────┬─────────┘
               │                               │
               │                               │ HTTP / JSON
               │                               │ Bearer Token
               ▼                               ▼
     ═════════════════════════════════════════════════════════
             OpenAPI 3.1 REST API Layer (FastAPI :8000)
     ═════════════════════════════════════════════════════════
                               │
                               ▼
                    Application Layer Core
                     (Pipeline Orchestrator)
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       Domain Engines / AI           Persistence & Database
```

---

## 3. Page-to-Route Migration Mapping

| Streamlit View | React Route Path | Navigation Label | Access Control | Purpose |
|---|---|---|---|---|
| `dashboard_page.py` | `/dashboard` | Dashboard | Authenticated (`ANALYST`, `ADMIN`, `VIEWER`) | Primary analytical overview, KPIs, dataset exploration, pipeline health. |
| `upload_page.py` | `/upload` | Upload Dataset | Authenticated (`ANALYST`, `ADMIN`) | Upload bytes (`POST /api/datasets`), non-destructive cleaning preview, cleaning-policy proposal and approval/rejection, pipeline execution with an approved policy. |
| `report_page.py` | `/reports` | Reports | Authenticated (`ANALYST`, `ADMIN`, `VIEWER`) | Interactive structured analytics, KPI cards, download triggers (Plain Text, Vector PDF). |
| `ai_insights_page.py` | `/ai-insights` | AI Insights | Authenticated (`ANALYST`, `ADMIN`, `VIEWER`) | Asynchronous AI job lifecycle monitoring, cancel and retry buttons, executive synthesis, recommendations. |
| `admin_page.py` | `/admin/users` | Administration | Restricted (`ADMIN` only) | User directory, role assignment, status toggling, login-lockout unlock, account deletion, audit trail. |
| `about_page.py` | `/about` | About | Public (No Auth Required) | System architecture overview, capabilities, compliance, documentation links. |
| *Sign In Dialog* | `/login` | Sign In | Public | Credential authentication, token issuance, session establishment. |
| *Register Dialog* | `/register` | Register | Public | User self-registration and credential provisioning. |

---

## 4. UI Component Decomposition & React Hierarchy

```text
<AppLayout>
  ├── <Navbar> (Brand, System Status, User Avatar / Role, Logout)
  ├── <Sidebar> (Role-Aware Navigation Links: Dashboard, Upload, Reports, AI Insights, Admin, About)
  └── <MainContentContainer>
        ├── [Route: /dashboard]
        │     ├── <DatasetContextBanner />
        │     ├── <KPIGrid>
        │     │     └── <KPICard title="..." value="..." trend="..." />
        │     ├── <PipelineStatusCard />
        │     └── <DataExplorationTabs>
        │           ├── <DataTableView />
        │           └── <ColumnProfileView />
        │
        ├── [Route: /upload]
        │     ├── <DropzoneUploader />
        │     ├── <CleaningPolicyConfigurator />
        │     ├── <CleaningPreviewModal />
        │     ├── <PolicyProposalReview />   (propose / approve / reject)
        │     └── <ExecutePipelineButton />
        │
        ├── [Route: /reports]
        │     ├── <ReportHeader />
        │     ├── <ExportControlGroup>
        │     │     ├── <ExportTextButton endpoint="/api/reports/{id}/export/text" />
        │     │     └── <ExportPdfButton endpoint="/api/reports/{id}/export/pdf" />
        │     ├── <StructuredReportSections />
        │     └── <LineageProvenanceCard />
        │
        ├── [Route: /ai-insights]
        │     ├── <AIJobStatusBanner (PENDING | GENERATING | READY | FAILED | CANCELLED) />
        │     ├── <AIExecutiveSynthesis />
        │     ├── <AIRecommendationsList />
        │     ├── <AIDiagnosticExplanations />
        │     ├── <CancelJobButton />
        │     └── <RetryJobButton />
        │
        └── [Route: /admin/users]
              ├── <UserDirectoryTable />
              ├── <UserEditModal />
              ├── <UserUnlockButton />
              ├── <UserDeleteConfirmDialog />
              └── <AuditEventLog />
```

---

## 5. Frontend Service Layer Mapping

The Python frontend service layer in `src/frontend/services/` (`APIClient`, `AuthService`,
`UploadService`, `AdminService` classes; `dashboard_service`, `report_service`, `ai_service` and
`session_manager` function modules) maps to TypeScript API client modules in React:

```typescript
// Example React TypeScript Service Architecture

// src/services/auth.service.ts
export class AuthService {
  static async login(credentials: UserLogin): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>('/api/auth/login', credentials);
  }
  static async getProfile(): Promise<UserResponse> {
    return apiClient.get<UserResponse>('/api/auth/me');
  }
  static async logout(): Promise<LogoutResponse> {
    return apiClient.post<LogoutResponse>('/api/auth/logout');
  }
}

// src/services/dashboard.service.ts
export class DashboardService {
  // Upload first (POST /api/datasets), run (POST /api/pipeline), then read. Views are read-only.
  static async getDashboard(datasetVersionId: string): Promise<DashboardResponse> {
    return apiClient.get<DashboardResponse>(
      `/api/powerbi/dashboard?dataset_version_id=${encodeURIComponent(datasetVersionId)}`
    );
  }
}

// src/services/report.service.ts
export class ReportService {
  static async getLatestReports(): Promise<ReportsListResponse> {
    return apiClient.get<ReportsListResponse>('/api/reports');
  }
  static getExportTextUrl(reportId?: number): string {
    return reportId ? `/api/reports/${reportId}/export/text` : '/api/reports/export/text';
  }
  static getExportPdfUrl(reportId?: number): string {
    return reportId ? `/api/reports/${reportId}/export/pdf` : '/api/reports/export/pdf';
  }
}

// src/services/ai.service.ts
export class AIService {
  static async getJobStatus(jobId: string): Promise<AIJobResponse> {
    return apiClient.get<AIJobResponse>(`/api/ai/jobs/${jobId}`);
  }
  static async getLatestJob(): Promise<AIJobResponse> {
    return apiClient.get<AIJobResponse>('/api/ai/jobs/latest/status');
  }
  static async retryJob(jobId: string): Promise<AIJobRetryResponse> {
    return apiClient.post<AIJobRetryResponse>(`/api/ai/jobs/${jobId}/retry`);  // FAILED or CANCELLED
  }
  static async cancelJob(jobId: string): Promise<AIJobRetryResponse> {
    return apiClient.post<AIJobRetryResponse>(`/api/ai/jobs/${jobId}/cancel`);  // PENDING or GENERATING
  }
}

// src/services/upload.service.ts
export class UploadService {
  static async uploadDataset(file: File): Promise<DatasetUploadResponse> {
    const form = new FormData();
    form.append('file', file);                      // bytes only; no server paths
    return apiClient.postForm<DatasetUploadResponse>('/api/datasets', form);  // -> dataset_version_id
  }
  static async getAnalysis(datasetVersionId: string): Promise<DatasetAnalysisResponse> {
    return apiClient.get<DatasetAnalysisResponse>(`/api/datasets/${datasetVersionId}/analysis`);
  }
  static async deleteDataset(datasetVersionId: string): Promise<DatasetDeleteResponse> {
    return apiClient.delete<DatasetDeleteResponse>(`/api/datasets/${datasetVersionId}`);
  }
  static async previewCleaning(req: CleaningPreviewRequest): Promise<CleaningPreviewResponse> {
    return apiClient.post<CleaningPreviewResponse>('/api/governance/preview', req);
  }
  static async proposePolicy(req: PolicyProposalRequest): Promise<PolicyProposalResponse> {
    return apiClient.post<PolicyProposalResponse>('/api/governance/policies', req);
  }
  static async reviewPolicy(proposalId: string, approve: boolean): Promise<PolicyProposalResponse> {
    return apiClient.post<PolicyProposalResponse>(
      `/api/governance/policies/${proposalId}/${approve ? 'approve' : 'reject'}`, {}
    );
  }
  static async executePipeline(req: PipelineRequest): Promise<PipelineResponse> {
    // req: { dataset_version_id, cleaning_policy_proposal_id? (must be APPROVED) }
    return apiClient.post<PipelineResponse>('/api/pipeline', req);
  }
}

// src/services/admin.service.ts
export class AdminService {
  static async listUsers(limit = 100, offset = 0): Promise<PaginatedUserResponse> {
    return apiClient.get<PaginatedUserResponse>(`/api/admin/users?limit=${limit}&offset=${offset}`);
  }
  static async updateUser(userId: number, update: AdminUserUpdate): Promise<UserResponse> {
    return apiClient.patch<UserResponse>(`/api/admin/users/${userId}`, update);
  }
  static async deleteUser(userId: number): Promise<void> {
    return apiClient.delete(`/api/admin/users/${userId}`);
  }
  static async unlockUser(userId: number): Promise<UserResponse> {
    return apiClient.post<UserResponse>(`/api/admin/users/${userId}/unlock`);
  }
  static async auditEvents(limit = 100): Promise<Record<string, unknown>[]> {  // untyped in the contract
    return apiClient.get<Record<string, unknown>[]>(`/api/admin/audit-events?limit=${limit}`);
  }
  static async verifyAuditChain(): Promise<Record<string, unknown>> {  // untyped in the contract
    return apiClient.get<Record<string, unknown>>('/api/admin/audit-events/verify');
  }
}
```

---

## 6. State Management & Authentication Lifecycle

1. **Authentication Token Lifecycle:**
   - On successful login, the JWT access token and expiration are stored in `sessionStorage` (or secure HTTP-only cookies).
   - An Axios/Fetch interceptor attaches `Authorization: Bearer <token>` to all outgoing requests.
   - On HTTP 401 response, the client clears local session state and redirects to `/login`.
2. **Global React Contexts:**
   - `AuthContext`: Tracks `user: UserResponse | null`, `isAuthenticated: boolean`, `role: UserRole`, `login()`, `logout()`.
   - `DatasetContext`: Tracks `activeDatasetVersionId: string | null` (server-issued by `POST /api/datasets`; clients never hold server paths), `datasetMetadata: DatasetVersionResponse | null`, `datasetSummary: DashboardSummary | null`.
   - `JobPollingContext`: Manages background polling intervals for pending AI jobs without blocking navigation.

---

## 7. OpenAPI Code Generation

React developers can automatically generate TypeScript interfaces and Axios clients from the frozen OpenAPI contract:

```bash
# Generate TypeScript interfaces from authoritative backend schema
npx openapi-typescript docs/api/openapi.json --output src/types/api.ts

# Or generate full typed client
npx openapi-generator-cli generate -i docs/api/openapi.json -g typescript-axios -o src/api-client
```

---

## 8. Summary Checklist for Frontend Engineers

- [x] OpenAPI 3.1 contract frozen and exported at `docs/api/openapi.json`.
- [x] All **46** paths (49 operations) expose explicit request/response schemas in
      `components.schemas` (51 schemas), as of 2026-10-14. v14.0.0 had 33 paths / 42 schemas;
      the blueprint originally said 40 paths, a count that included the duplicate
      registrations of `reports_router`, removed later in Sprint 14.
- [x] Every functional route is mounted under `/api`. The unprefixed `/reports/*` and
      `/powerbi/*` aliases were removed in v14.0.0 — prepend `/api`.
- [x] Streamlit views talk to the backend only over HTTP. *Fixed in the pre-Sprint-15
      hardening (P2-05):* `views/upload_page.py` used to run `DataProfiler`,
      `CleaningGovernanceService.recommend_dataset_policy` and `CleaningPreviewService.preview`
      in the frontend process; it now calls `GET /api/datasets/{id}/analysis`,
      `POST /api/governance/preview` and the `/api/governance/policies` routes.
      `src/frontend` imports nothing from `src/application`, `src/persistence`, `src/profiling`
      or the other backend packages (`tests/frontend/test_frontend_boundaries.py`, an AST test).
- [ ] Sprint 15 remediation complete (end-to-end governance workflow verification, Dashboard
      information architecture) — the React migration must not reproduce known Sprint 15
      defects. Sprint 15 has not started (2026-10-14).
- [ ] Sprint 16 final React-readiness audit passed and React architecture ADR accepted.
- [x] Per-user isolation enforced server-side (Bearer token identity) and tested on every resource route.
- [x] Export streams available via direct HTTP endpoints.
