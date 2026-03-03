# ПРОМТ ДЛЯ ГЕНЕРАЦИИ ДОКУМЕНТАЦИИ ПРОЕКТА

---

## 📋 ПРОМТ (вставить в нейронку / Copilot Chat целиком)

---

# 📁 ДОКУМЕНТАЦИЯ ПРОЕКТА: CloudIaaS Platform

## 1. System Overview

### Architecture (C4 Context)

```
[Customer Browser] ──► [React SPA: Customer Portal :3000]
[Admin Browser]    ──► [React SPA: Admin Panel :3001]
                              │
                        [FastAPI Backend :8000]
                         /    │     \
               [PostgreSQL] [Redis] [Docker Engine]
                  :5432      :6379   (Mock Hypervisor)
```

**Key Decisions:**
- FastAPI (async) — native async, auto OpenAPI, Pydantic v2 validation
- Single PostgreSQL DB with `tenant_id` column + Row-Level Security
- Docker SDK replaces real hypervisor — containers act as VMs
- JWT stateless auth: access tokens (15 min) + refresh tokens (7 days)
- Monorepo for 2-3 day sprint velocity

---

## 2. Project Structure

```
cloudiaas/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── middleware/
│   │   ├── hypervisor/
│   │   └── utils/
│   ├── migrations/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── customer-portal/
│   └── admin-panel/
├── infra/
│   ├── docker-compose.yml
│   └── nginx/nginx.conf
├── docs/
│   └── architecture.md
└── .env.example
```

---

## 3. Data Models

| Model | Key Fields |
|-------|-----------|
| Tenant | id, name, slug, status, max_vms |
| User | id, tenant_id, email, hashed_password, role |
| VirtualMachine | id, tenant_id, name, status, cpu_cores, ram_mb, disk_gb, docker_container_id |
| Network | id, tenant_id, name, cidr, is_active |
| ResourceQuota | id, tenant_id, max_cpu_cores, max_ram_mb, used_cpu_cores, used_ram_mb |
| AuditLog | id, tenant_id, user_id, action, resource_type, detail (JSONB) |

---

## 4. API Design

### Auth `/api/v1/auth`
- POST `/register` — создать тенанта + owner user, вернуть токены
- POST `/login` — вернуть access + refresh JWT
- POST `/refresh` — обменять refresh token
- POST `/logout` — инвалидировать токен

### VMs `/api/v1/vms`
- GET `/` — список VM тенанта
- POST `/` — создать VM (запускает Docker контейнер)
- GET `/{vm_id}` — детали VM
- POST `/{vm_id}/start` — запустить контейнер
- POST `/{vm_id}/stop` — остановить контейнер
- DELETE `/{vm_id}` — удалить VM + контейнер

### Networks `/api/v1/networks`
- GET `/`, POST `/`, DELETE `/{id}`

### Quotas `/api/v1/quotas`
- GET `/me` — текущее использование квоты

### Admin `/api/v1/admin`
- GET/POST `/tenants`
- PUT `/tenants/{id}/quota`
- PUT `/tenants/{id}/status`
- GET `/audit-logs`
- GET `/stats`

### Auth Middleware
```python
get_current_user → verify_jwt → load_user_from_db
get_tenant_context → tenant_id из токена → request.state
require_admin → проверка role == "admin"
```

---

## 5. Frontend Architecture

### Customer Portal Routes
```
/login, /register
/dashboard       — квота overview
/vms             — список VM
/vms/create      — создать VM
/vms/:id         — детали + start/stop/delete
/networks        — список сетей
/networks/create — создать сеть
```

### Admin Panel Routes
```
/admin/login
/admin           — stats + charts
/admin/tenants   — список тенантов
/admin/tenants/:id — редактор квот
/admin/audit     — audit log
```

### Стек
- React Query — серверный стейт, refetch каждые 10с для статусов VM
- Zustand — auth стейт (токен, роль, пользователь)
- Axios — базовый URL из env, auto Bearer token, 401 → редирект

---

## 6. Mock Hypervisor

```python
class MockHypervisor:
    async def create_vm(vm_id, cpu_cores, ram_mb) -> str  # container_id
    async def start_vm(container_id) -> None
    async def stop_vm(container_id) -> None
    async def delete_vm(container_id) -> None
    async def get_status(container_id) -> str  # running/stopped/error
```
Docker SDK: запускает `alpine:latest` с cpu/memory limits. Блокирующие вызовы — через `run_in_executor`.

---

## 7. Security & Isolation

```json
JWT payload: { "sub": "user_uuid", "tenant_id": "...", "role": "tenant_owner|admin", "exp": ... }
```

- Все запросы к БД фильтруются по `tenant_id` из токена
- `tenant_id` никогда не берётся из тела запроса
- Admin endpoints — только `role == admin`
- Пароли: bcrypt через passlib

---

## 8. Deployment

```yaml
services:
  postgres:           # postgres:15-alpine, port 5432
  redis:              # redis:7-alpine, port 6379
  backend:            # build ./backend, port 8000, mount docker.sock
  frontend-customer:  # build ./frontend/customer-portal, port 3000
  frontend-admin:     # build ./frontend/admin-panel, port 3001
  nginx:              # reverse proxy, port 80
```

```env
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/cloudiaas
SECRET_KEY=<random 32 bytes>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
DOCKER_HOST=unix:///var/run/docker.sock
FIRST_ADMIN_EMAIL=admin@cloud.local
FIRST_ADMIN_PASSWORD=changeme
```

---

# 🗓️ ПЛАН РЕАЛИЗАЦИИ (GitHub Copilot–ready)

> Каждый пункт — готовый промт для GitHub Copilot Chat.
> Открой нужный файл/папку, вставь пункт в Copilot Chat.

---

## DAY 1 — Backend: Scaffold + Auth + Models

### 1.1 [DevOps] Scaffold проекта
```
Create the full monorepo folder structure for the CloudIaaS project as described
in the documentation Project Structure section. Initialize backend/ with FastAPI,
SQLAlchemy 2.0 async, Alembic, Pydantic v2. Create requirements.txt with:
fastapi, uvicorn[standard], sqlalchemy[asyncio], asyncpg, alembic,
pydantic-settings, passlib[bcrypt], python-jose[cryptography], docker, httpx.
```

### 1.2 [BE] Database configuration
```
Create backend/app/database.py with async SQLAlchemy engine using DATABASE_URL
from environment, AsyncSession factory, Base declarative class, and get_db()
async dependency that yields AsyncSession.
Reference: Documentation Section 8 (DATABASE_URL env var).
```

### 1.3 [BE] Config
```
Create backend/app/config.py using pydantic-settings BaseSettings.
Include all environment variables from Documentation Section 8.
Export a singleton `settings` instance.
```

### 1.4 [BE] ORM Models
```
Create backend/app/models/ with one file per entity.
Implement all 6 models from Documentation Section 3:
Tenant, User, VirtualMachine, Network, ResourceQuota, AuditLog.
Use SQLAlchemy 2.0 mapped_column syntax with UUID primary keys.
Add indexes on tenant_id and status columns.
```

### 1.5 [BE] Alembic + Initial Migration
```
Initialize Alembic in backend/migrations/.
Configure env.py to use async engine and import all models from app.models.
Generate initial migration: alembic revision --autogenerate -m "initial_schema"
```

### 1.6 [BE] Pydantic Schemas
```
Create backend/app/schemas/ with files: auth.py, tenant.py, vm.py, network.py,
quota.py, admin.py. For each entity create: Create schema (input), Response schema
(output), Update schema where needed. Use Pydantic v2 ConfigDict(from_attributes=True).
```

### 1.7 [BE] JWT Utilities
```
Create backend/app/utils/jwt.py with:
- create_access_token(data: dict) → str  (expires in ACCESS_TOKEN_EXPIRE_MINUTES)
- create_refresh_token(data: dict) → str  (expires in REFRESH_TOKEN_EXPIRE_DAYS)
- decode_token(token: str) → dict
Use python-jose HS256. JWT payload: sub, tenant_id, role, exp.
Reference: Documentation Section 7 (JWT Structure).
```

### 1.8 [BE] Auth Middleware Dependencies
```
Create backend/app/middleware/auth.py with FastAPI dependency functions:
- get_current_user(token, db) → User
- get_tenant_context(current_user) → UUID
- require_admin(current_user) → User (raises 403 if not admin)
Reference: Documentation Section 4 (Auth Middleware Pattern).
```

### 1.9 [BE] Auth Router
```
Create backend/app/routers/auth.py with 4 endpoints from Documentation Section 4:
POST /register — create Tenant + User(role=tenant_owner), return tokens
POST /login — verify email+password with passlib, return tokens
POST /refresh — validate refresh token, return new access token
POST /logout — return 200
```

### 1.10 [BE] Main App Factory
```
Create backend/app/main.py:
FastAPI app, include auth router with prefix="/api/v1/auth",
add CORS middleware, startup event runs alembic upgrade head + seed.
```

### 1.11 [BE] Seed Script
```
Create backend/app/seed.py (idempotent):
- Create admin user: email=FIRST_ADMIN_EMAIL, role=admin, tenant_id=None
- Create demo tenant "Demo Corp" + owner user demo@cloud.local / demo1234
- Create ResourceQuota for demo: max_vms=5, max_cpu_cores=8, max_ram_mb=8192
```

---

## DAY 1 (вторая половина) — VM + Network + Quota APIs + Mock Hypervisor

### 1.12 [BE] Mock Hypervisor Client
```
Create backend/app/hypervisor/docker_client.py with class MockHypervisor.
Async methods using Docker SDK:
- create_vm(vm_id, cpu_cores, ram_mb) → container_id: run alpine:latest detached,
  name f"cloudiaas-vm-{vm_id}", with cpu and memory limits
- start_vm(container_id), stop_vm(container_id), delete_vm(container_id)
- get_status(container_id) → map docker status to running/stopped/error
Use run_in_executor to wrap blocking docker calls.
```

### 1.13 [BE] VM Service
```
Create backend/app/services/vm_service.py with VMService class.
Methods (all accept db: AsyncSession, tenant_id: UUID):
- list_vms, get_vm (404 if wrong tenant), create_vm (check quota, call MockHypervisor,
  write AuditLog), start_vm, stop_vm, delete_vm (update quota after delete)
Reference: Documentation Section 7 (Tenant Isolation).
```

### 1.14 [BE] VM Router
```
Create backend/app/routers/vms.py with all 6 VM endpoints from Documentation Section 4.
All routes require get_current_user. Use VMService. Return 201 for create, 204 for delete.
Include in main.py with prefix="/api/v1/vms".
```

### 1.15 [BE] Network Service + Router
```
Create backend/app/services/network_service.py and backend/app/routers/networks.py.
Implement 3 endpoints from Documentation Section 4 (Network Routes).
Validate CIDR format on create. Check quota. Write AuditLog. Include with prefix="/api/v1/networks".
```

### 1.16 [BE] Quota Router
```
Create backend/app/routers/quotas.py with GET /me endpoint.
Query ResourceQuota by tenant_id from current_user. Return quota with usage percentages.
Include with prefix="/api/v1/quotas".
```

### 1.17 [BE] Admin Router
```
Create backend/app/routers/admin.py with all admin endpoints from Documentation Section 4.
All routes require require_admin. No tenant filtering.
GET /tenants (paginated), POST /tenants, PUT /tenants/{id}/quota,
PUT /tenants/{id}/status, GET /audit-logs (filterable), GET /stats.
Include with prefix="/api/v1/admin".
```

---

## DAY 2 — Frontend Customer Portal

### 2.1 [FE] Customer Portal Scaffold
```
Create frontend/customer-portal/ using: npm create vite@latest -- --template react-ts
Install: tailwindcss, @tanstack/react-query, axios, zustand, react-router-dom, lucide-react
Configure tailwind. Create src/api/client.ts: Axios instance with VITE_API_URL base,
Bearer token from Zustand auth store, 401 interceptor → redirect to /login.
```

### 2.2 [FE] Auth Store + Auth Pages
```
Create src/store/authStore.ts with Zustand: state (user, accessToken, isAuthenticated),
actions (login, logout, setToken).
Create LoginPage.tsx: POST /api/v1/auth/login, store token, redirect to /dashboard.
Create RegisterPage.tsx: POST /api/v1/auth/register.
Create ProtectedRoute.tsx: redirect to /login if not authenticated.
```

### 2.3 [FE] API Hooks (React Query)
```
Create src/api/hooks/: useVMs.ts, useNetworks.ts, useQuota.ts.
useVMs: useVMList() with refetchInterval:10000, useCreateVM() mutation with cache invalidation,
useVMAction(vmId) for start/stop/delete mutations.
useNetworks: list, create, delete hooks.
useQuota: useMyQuota() → GET /api/v1/quotas/me.
```

### 2.4 [FE] Dashboard Page
```
Create src/pages/DashboardPage.tsx.
Show 4 ResourceCard components for VMs, CPU, RAM, Networks (used/max with progress bar).
ResourceCard: icon, label, value, progress bar (green<70%, yellow<90%, red>=90%).
Use useMyQuota(). Show loading skeleton while fetching.
```

### 2.5 [FE] VM Pages
```
Create VMListPage.tsx: table (Name, VMStatusBadge, CPU, RAM, IP, Actions).
VMStatusBadge: green=running, gray=stopped, yellow=creating, red=error.
Actions: Start/Stop (context-aware disabled state), Delete with ConfirmModal.

Create VMCreatePage.tsx: form (Name, CPU slider 1-8, RAM select, Disk GB),
quota warning if limits exceeded, submit → useCreateVM() → redirect /vms.

Create VMDetailPage.tsx: all fields, action buttons with loading states,
auto-refresh every 10s.
```

### 2.6 [FE] Networks Page
```
Create NetworkListPage.tsx: table (Name, CIDR, Status, Actions).
Inline create form with CIDR validation. Delete with ConfirmModal.
Show quota bar for networks used/max. Use useNetworks hooks.
```

### 2.7 [FE] App Router + Layout
```
Create src/App.tsx with React Router v6 routes for all paths in Documentation Section 5.
Create Layout.tsx: sidebar (Dashboard, VMs, Networks, Settings links),
top bar (user email + logout). Wrap authenticated routes with ProtectedRoute + Layout.
```

---

## DAY 2 (вторая половина) — Admin Panel

### 2.8 [FE] Admin Panel Scaffold
```
Create frontend/admin-panel/ with same Vite+React+TS+Tailwind setup.
Admin auth store with role check: redirect if role !== "admin".
AdminLoginPage.tsx using POST /api/v1/auth/login.
```

### 2.9 [FE] Admin Dashboard
```
Create AdminDashboardPage.tsx.
Fetch GET /api/v1/admin/stats. Display stat cards:
Total Tenants, Total VMs, Running VMs, Suspended Tenants.
Add recharts BarChart for VMs per tenant (top 10).
Recent audit log table (last 10 rows).
```

### 2.10 [FE] Tenant Management Pages
```
Create TenantListPage.tsx: DataTable (Name, Status badge, VM count, Actions).
Actions: View Details, Suspend/Activate toggle. "Create Tenant" modal.

Create TenantDetailPage.tsx (/admin/tenants/:id):
Tenant info + quota editor form (editable max_vms, max_cpu_cores, max_ram_mb, max_disk_gb)
→ PUT /api/v1/admin/tenants/:id/quota.
VM list table (read-only). Suspend/Activate button.
```

### 2.11 [FE] Audit Log Page
```
Create AuditLogPage.tsx: filterable paginated table (20/page).
Columns: Timestamp, Tenant, User, Action, Resource Type, Resource ID, Details.
Filters: date range, tenant dropdown, action search.
Expandable JSON viewer for detail field.
```

---

## DAY 3 — Docker + Тесты + Финал

### 3.1 [DevOps] Dockerfiles
```
Create backend/Dockerfile: python:3.11-slim, pip install requirements.txt,
CMD uvicorn app.main:app --host 0.0.0.0 --port 8000, mount /var/run/docker.sock.

Create frontend/customer-portal/Dockerfile (multi-stage):
Stage 1: node:20-alpine, npm ci, npm run build.
Stage 2: nginx:alpine, copy dist/ to /usr/share/nginx/html.

Create frontend/admin-panel/Dockerfile with same multi-stage pattern.
```

### 3.2 [DevOps] Docker Compose
```
Create infra/docker-compose.yml with 6 services from Documentation Section 8:
postgres (healthcheck: pg_isready, named volume),
backend (depends_on postgres healthy, mount docker.sock, env_file),
frontend-customer, frontend-admin,
nginx (proxy /api/ → backend:8000, / → customer:80, /admin/ → admin:80).
Create infra/nginx/nginx.conf accordingly.
```

### 3.3 [DevOps] Environment Setup
```
Create .env.example with all variables from Documentation Section 8.
Create .env: SECRET_KEY=$(openssl rand -hex 32),
DATABASE_URL=postgresql+asyncpg://cloudiaas:cloudiaas@postgres:5432/cloudiaas,
FIRST_ADMIN_EMAIL=admin@cloud.local, FIRST_ADMIN_PASSWORD=Admin1234!,
DOCKER_HOST=unix:///var/run/docker.sock.
Add .env to .gitignore.
```

### 3.4 [BE] Backend Tests
```
Create backend/tests/test_auth.py and test_vms.py using pytest-asyncio + httpx AsyncClient.
test_auth.py: test_register_creates_tenant_and_user(), test_login_returns_tokens(),
test_login_wrong_password_returns_401().
test_vms.py: test_create_vm_updates_quota(), test_cannot_access_other_tenant_vm(),
test_vm_quota_exceeded_returns_422().
```

### 3.5 [Full] E2E Smoke Test
```
Create backend/tests/e2e_smoke.py using httpx:
1. Register tenant "TestCo" → get tokens
2. Create network "net-1" with CIDR 192.168.1.0/24
3. Create VM "web-01" (2 CPU, 1024 MB RAM, 20 GB disk)
4. Poll GET /vms/:id until status == "running" (max 30s, every 2s)
5. Stop VM → verify status == "stopped"
6. Delete VM → verify 404
7. Login as admin → verify "TestCo" in tenant list
Print PASS/FAIL for each step.
```

### 3.6 [Full] README
```
Create README.md with sections:
1. Project Description
2. Architecture Overview (ASCII C4 diagram from Documentation Section 1)
3. Quick Start:
   cp .env.example .env
   docker compose -f infra/docker-compose.yml up --build
   open http://localhost and http://localhost/admin
4. Default Credentials table (admin + demo tenant)
5. API Docs: http://localhost/api/docs
6. Tech Stack table
7. Team & Timeline
```

### 3.7 [FE] UI Polish
```
Add to both frontend apps:
1. Loading spinners on all async operations (Tailwind animate-spin)
2. Toast notifications (Zustand toastStore + Toast component)
3. Empty state components for VM and Network lists
4. 404 page for unknown routes
5. Responsive sidebar: collapses to hamburger on mobile (md: breakpoint)
Show field-level validation errors from API 422 responses.
```

### 3.8 [Full] Architecture Docs
```
Create docs/architecture.md with:
1. C4 Context diagram (ASCII)
2. Sequence diagram for VM creation flow:
   User → Frontend → API → QuotaCheck → MockHypervisor → Docker → DB → Response
3. Data model ERD (text format)
4. Tenant isolation description
5. JWT token flow diagram
```

---

## ✅ ФИНАЛЬНЫЙ ЧЕКЛИСТ

```
□ docker compose up --build запускается без ошибок
□ POST /api/v1/auth/register создаёт тенанта + токен
□ Клиентский портал: http://localhost
□ Админ панель: http://localhost/admin
□ Создать VM → статус меняется creating → running
□ Квота уменьшается после создания VM
□ Admin видит всех тенантов, может изменить квоту
□ Audit log фиксирует действия
□ README содержит инструкцию запуска
□ http://localhost/api/docs — OpenAPI работает
```
