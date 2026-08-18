# React Migration Mapping & Frontend Architecture Blueprint

**Sprint:** Sprint 14 Phase 6 — OpenAPI / React Migration Readiness
**Target Release:** Sprint 15 (React Presentation Layer)
**Status:** Approved Architectural Blueprint

---

## 1. Executive Summary & Migration Strategy

AnalystGPT Enterprise was engineered with a strict layered architecture to ensure that presentation concerns remain isolated from application core workflows. In Sprint 15, the platform will migrate from the Streamlit presentation layer to a modern, production-ready React frontend (Vite + TypeScript + TailwindCSS).

This document establishes the authoritative contract mapping and component decomposition required for React frontend engineers, guaranteeing that:
1. **Zero Backend Changes Required:** The FastAPI REST API is frozen and fully typed (OpenAPI 3.1).
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
| `upload_page.py` | `/upload` | Upload Dataset | Authenticated (`ANALYST`, `ADMIN`) | Ingest raw datasets, non-destructive cleaning preview, pipeline execution dispatch. |
| `report_page.py` | `/reports` | Reports | Authenticated (`ANALYST`, `ADMIN`, `VIEWER`) | Interactive structured analytics, KPI cards, download triggers (Plain Text, Vector PDF). |
| `ai_insights_page.py` | `/ai-insights` | AI Insights | Authenticated (`ANALYST`, `ADMIN`, `VIEWER`) | Asynchronous AI job lifecycle monitoring, retry button, executive synthesis, recommendations. |
| `admin_page.py` | `/admin/users` | Administration | Restricted (`ADMIN` only) | User directory, role assignment, status toggling, account deletion, audit trail. |
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
        │     ├── <AIJobStatusBanner (PENDING | GENERATING | READY | FAILED) />
        │     ├── <AIExecutiveSynthesis />
        │     ├── <AIRecommendationsList />
        │     ├── <AIDiagnosticExplanations />
        │     └── <RetryJobButton />
        │
        └── [Route: /admin/users]
              ├── <UserDirectoryTable />
              ├── <UserEditModal />
              └── <UserDeleteConfirmDialog />
```

---

## 5. Frontend Service Layer Mapping

The Python frontend service layer in `src/frontend/services/` maps 1:1 to TypeScript API client modules in React:

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
  static async getDashboard(datasetPath: string): Promise<DashboardResponse> {
    return apiClient.get<DashboardResponse>(`/powerbi/dashboard?dataset=${encodeURIComponent(datasetPath)}`);
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
    return apiClient.post<AIJobRetryResponse>(`/api/ai/jobs/${jobId}/retry`);
  }
}

// src/services/upload.service.ts
export class UploadService {
  static async previewCleaning(req: CleaningPreviewRequest): Promise<CleaningPreviewResponse> {
    return apiClient.post<CleaningPreviewResponse>('/api/governance/preview', req);
  }
  static async executePipeline(req: PipelineRequest): Promise<PipelineResponse> {
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
   - `DatasetContext`: Tracks `activeDatasetPath: string | null`, `datasetMetadata: DatasetVersionResponse | null`, `datasetSummary: DashboardSummary | null`.
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

## 8. Summary Checklist for Sprint 15 React Engineers

- [x] OpenAPI 3.1 contract frozen and exported at `docs/api/openapi.json`.
- [x] All 40 endpoints expose explicit request/response schemas in `components.schemas`.
- [x] Streamlit views verified to be presentation-only (no backend logic to extract).
- [x] Multi-tenant isolation backend-enforced via JWT headers.
- [x] Export streams available via direct HTTP endpoints.
