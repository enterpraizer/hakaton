# 📋 BACKEND PLAN (FastAPI) — README_BACKEND.md

## Project Overview
CloudIaaS backend — REST API for managing virtual machines, networks, quotas and tenants.
Built with Clean Architecture: `interfaces` → `application` → `infrastructure`.

## Tech Stack
- Python 3.13
- FastAPI 0.121 + Uvicorn + uvloop
- SQLAlchemy 2.0 async + asyncpg
- PostgreSQL 17
- Alembic 1.17 (migrations)
- Redis + Celery (async tasks / email)
- JWT Auth (python-jose + passlib/bcrypt) — **already implemented**
- Docker + docker-compose
- Pytest + pytest-asyncio

## Current State (already done ✅)
- `User` model + `UserRepository`
- `AuthService` (register, login, refresh, change_password, email confirmation via Celery)
- `UserService` (get, get_all, create, update, delete)
- Routers: `POST /auth/register`, `GET /auth/register_confirm`, `POST /auth/token`, `POST /auth/refresh`, `PATCH /auth/change_password`, `GET /auth/me`, `GET /users`, `GET /users/{id}`, `PATCH /users/{id}`, `DELETE /users/delete`
- `BaseRepository` with create/get/get_all/update/delete

## Team
- **Dev-1**: Project Lead / Architecture & Routing
- **Dev-2**: Models & Database & Migrations
- **Dev-3**: VM Service & Endpoints
- **Dev-4**: Networks, Quotas, Tenants Services & Endpoints
- **Dev-5**: Testing, DevOps & Final Hardening

---

## DAY 1 — Foundation & Core Domain Models

### 1.1 [Dev-1] Fix docker-compose + project wiring
- [ ] Fix docker-compose and app bootstrap

<details>
<summary>📎 Copilot Prompt</summary>

```
In /Users/.../Backend/docker-compose.yaml the `backend` service depends_on `accounts-db`
but the service is actually named `db`. Fix that reference.
Also add `redis` as a dependency for the `backend` service with condition: service_healthy.
Add missing volume `auth_redis_data` to the top-level volumes section.
In src/interfaces/api/app.py add: CORSMiddleware allowing all origins (configurable via settings),
a global exception handler for the custom exceptions in src/application/services/exceptions.py
that returns JSON {"detail": str(e)} with correct HTTP status codes:
UserNotFound → 404, UserPermissionDenied → 403, UserAlreadyExistsError → 409, UserValidationError → 422.
```
</details>

---

### 1.2 [Dev-2] VM Model + Migration
- [ ] Create VM SQLAlchemy model and Alembic migration

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/infrastructure/models/users.py and src/infrastructure/models/base.py.
Create src/infrastructure/models/vm.py with a SQLAlchemy 2.0 async ORM model class `VirtualMachine`:
- id: UUID primary key, server_default gen_random_uuid()
- owner_id: UUID ForeignKey → users.id, nullable=False, index=True
- name: String(100), nullable=False
- status: ENUM('pending','running','stopped','error'), nullable=False, default='pending'
- cpu_cores: Integer, nullable=False
- ram_mb: Integer, nullable=False
- disk_gb: Integer, nullable=False
- ip_address: String(45), nullable=True
- created_at: DateTime, server_default=func.now()
- updated_at: DateTime, server_default=func.now(), onupdate=func.now()
Add the model to src/infrastructure/models/__init__.py.
Then add it to alembic/env.py imports (target_metadata already uses Base.metadata).
Run: alembic revision --autogenerate -m "add_virtual_machines_table"
```
</details>

---

### 1.3 [Dev-3] Network Model + Migration
- [ ] Create Network SQLAlchemy model

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/infrastructure/models/base.py and src/infrastructure/models/vm.py (once created).
Create src/infrastructure/models/network.py with SQLAlchemy 2.0 model `Network`:
- id: UUID primary key, server_default gen_random_uuid()
- owner_id: UUID ForeignKey → users.id, nullable=False, index=True
- name: String(100), nullable=False, unique=True
- cidr: String(18), nullable=False  (e.g. "10.0.0.0/24")
- is_public: Boolean, default=False
- status: ENUM('active','inactive'), default='active'
- created_at: DateTime, server_default=func.now()
Add `NetworkVMAssociation` many-to-many table linking networks ↔ virtual_machines (network_id UUID FK, vm_id UUID FK).
Add model to src/infrastructure/models/__init__.py.
Run: alembic revision --autogenerate -m "add_networks_table"
```
</details>

---

### 1.4 [Dev-4] Tenant + Quota Models + Migrations
- [ ] Create Tenant and Quota SQLAlchemy models

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/infrastructure/models/base.py and existing models.
Create src/infrastructure/models/tenant.py with model `Tenant`:
- id: UUID PK, server_default gen_random_uuid()
- name: String(100), unique=True, nullable=False
- owner_id: UUID FK → users.id, nullable=False
- created_at: DateTime, server_default=func.now()

Create src/infrastructure/models/quota.py with model `Quota`:
- id: UUID PK
- tenant_id: UUID FK → tenants.id, nullable=False, unique=True
- max_vcpu: Integer, default=10
- max_ram_mb: Integer, default=20480
- max_disk_gb: Integer, default=500
- max_vms: Integer, default=5
- used_vcpu: Integer, default=0
- used_ram_mb: Integer, default=0
- used_disk_gb: Integer, default=0
- used_vms: Integer, default=0

Add both models to src/infrastructure/models/__init__.py.
Run: alembic revision --autogenerate -m "add_tenants_quotas_tables"
```
</details>

---

### 1.5 [Dev-5] .env.example + Makefile + CI scaffold
- [ ] Complete environment setup

<details>
<summary>📎 Copilot Prompt</summary>

```
Read the existing .env.example, pyproject.toml, docker-compose.yaml and src/settings/.
Generate a complete .env.example with ALL variables required by the settings classes:
POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
REDIS_HOST, REDIS_PORT, REDIS_DB,
EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD,
SECRET_KEY, FRONTEND_URL,
APP_SECRET_KEY, APP_REFRESH_SECRET_KEY, APP_ALGORITHM, APP_ACCESS_TOKEN_EXPIRE_MINUTES, APP_REFRESH_TOKEN_EXPIRE_DAYS,
DEBUG.

Generate Makefile in project root with targets:
- make dev        → docker compose up --build
- make down       → docker compose down -v
- make migrate    → docker compose exec backend alembic upgrade head
- make makemigrations msg="..." → docker compose exec backend alembic revision --autogenerate -m "$(msg)"
- make test       → docker compose exec backend pytest -v
- make shell      → docker compose exec backend python

Generate .github/workflows/ci.yml: on push/PR to main and dev, run: install uv deps, run pytest with SQLite in-memory.
```
</details>

---

## DAY 2 — Business Logic & API Endpoints

### 2.1 [Dev-2] VM Repository + Schemas
- [ ] Implement VM repository and Pydantic schemas

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/infrastructure/repositories/base.py and src/infrastructure/models/vm.py.
Create src/infrastructure/repositories/vm.py with class `VMRepository(BaseRepository)`:
- table = VirtualMachine
- async get_by_owner(owner_id: UUID, limit: int, offset: int) → list of VMs filtered by owner_id
- async get_by_status(status: str, limit: int, offset: int) → filter by status
- async count_by_owner(owner_id: UUID) → int (for quota checks)

Read src/infrastructure/schemas/users.py for style reference.
Create src/infrastructure/schemas/vm.py with Pydantic v2 models:
- VMCreate: name, cpu_cores, ram_mb, disk_gb (all required, with validators: cpu_cores 1-64, ram_mb 512-131072, disk_gb 10-2000)
- VMUpdate: name optional, status optional (only 'stopped'/'running' allowed from user)
- VMResponse: id, owner_id, name, status, cpu_cores, ram_mb, disk_gb, ip_address, created_at
- VMList: items: List[VMResponse], total: int
Use model_config = ConfigDict(from_attributes=True) on response schemas.
```
</details>

---

### 2.2 [Dev-3] VM Service + Router
- [ ] Implement VM business logic and FastAPI router

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/application/services/users_service.py and src/infrastructure/repositories/vm.py (once created).
Create src/application/services/vm_service.py with class `VMService`:
- __init__(self, repository: VMRepository = Depends(), user_service: UserService = Depends())
- async create(vm_data: VMCreate, request_user: UserRequest) → VMResponse
  (check quota: count_by_owner must be < quota.max_vms; raise HTTPException 429 if exceeded)
- async get(vm_id: UUID, request_user: UserRequest) → VMResponse (owner or admin only)
- async get_all(limit: int, offset: int, request_user: UserRequest) → VMList
- async update(vm_id: UUID, request_user: UserRequest, data: VMUpdate) → VMResponse
- async delete(vm_id: UUID, request_user: UserRequest) → None

Create src/interfaces/api/routers/vms.py replacing the TODO stub:
- GET    /vms              → list VMs (paginated, requires auth)
- POST   /vms              → create VM (requires auth)
- GET    /vms/{vm_id}      → VM detail (requires auth)
- PATCH  /vms/{vm_id}      → update VM (owner or admin)
- DELETE /vms/{vm_id}      → delete VM (owner or admin)
Include router in src/interfaces/api/app.py.
```
</details>

---

### 2.3 [Dev-4] Network + Quota Service + Routers
- [ ] Implement Network and Quota endpoints

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/application/services/vm_service.py and models for Network and Quota.
Create src/infrastructure/repositories/network.py with `NetworkRepository(BaseRepository)`:
- table = Network
- async get_by_owner(owner_id, limit, offset) → list
- async attach_vm(network_id: UUID, vm_id: UUID) → inserts into NetworkVMAssociation
- async detach_vm(network_id: UUID, vm_id: UUID) → deletes from NetworkVMAssociation

Create src/application/services/network_service.py replacing the stub:
VMService-like CRUD with ownership checks + POST /networks/{id}/attach-vm, POST /networks/{id}/detach-vm.

Create src/infrastructure/repositories/quota.py with `QuotaRepository(BaseRepository)`:
- table = Quota
- async get_by_tenant(tenant_id: UUID) → Quota
- async increment(tenant_id: UUID, vcpu: int, ram_mb: int, disk_gb: int) → updates used_* fields
- async decrement(...) → same but subtracts

Create src/interfaces/api/routers/networks.py and src/interfaces/api/routers/quotas.py,
each with full CRUD. Include both routers in src/interfaces/api/app.py.
```
</details>

---

### 2.4 [Dev-1] Admin Router + Role-Based Access
- [ ] Implement admin endpoints with RBAC

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/interfaces/api/routers/auth.py and src/infrastructure/schemas/users.py.
Create src/interfaces/api/dependencies/permissions.py with:
- require_admin: a FastAPI Depends callable that reads current user via AuthService.get_current_user
  and raises HTTPException 403 if user.role != 'admin'
- require_active: raises 403 if not is_active

Create src/interfaces/api/routers/admin.py replacing the stub:
- GET  /admin/users                    → list all users (admin only, paginated)
- PATCH /admin/users/{user_id}/role    → change user role (admin only), body: {"role": "admin"|"user"}
- PATCH /admin/users/{user_id}/activate → set is_active=True (admin only)
- DELETE /admin/users/{user_id}        → hard delete user (admin only)
- GET  /admin/stats                    → return counts: total_users, active_users, total_vms, total_networks

Apply require_admin dependency to all admin routes.
Include admin_router in src/interfaces/api/app.py.
```
</details>

---

### 2.5 [Dev-5] Pytest setup + auth tests
- [ ] Write unit and integration tests for auth

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/interfaces/api/app.py, src/interfaces/api/routers/auth.py, src/infrastructure/schemas/users.py.
Create tests/ directory with:

tests/conftest.py:
- async pytest fixture `client` using httpx.AsyncClient with ASGITransport(app=app), base_url="http://test"
- async fixture `db_session` using SQLite in-memory with create_all on Base.metadata
- Override get_db dependency to use in-memory session
- Fixture `test_user` that creates a user via POST /auth/register and confirms them directly in DB

tests/test_auth.py with pytest-asyncio tests:
- test_register_success: POST /auth/register returns 201, body has email/username/id
- test_register_duplicate_email: returns 409
- test_login_unconfirmed: POST /auth/token returns 401 (not active)
- test_login_success (after manual confirmation): returns access_token and refresh_token
- test_refresh_token: POST /auth/refresh with valid refresh returns new tokens
- test_me_unauthenticated: GET /auth/me returns 401
- test_me_authenticated: GET /auth/me with Bearer token returns user data
- test_change_password_wrong_old: PATCH /auth/change_password returns 401

Run with: pytest tests/ -v --asyncio-mode=auto
```
</details>

---

## DAY 3 — Quality, Security & Docs

### 3.1 [Dev-1] OpenAPI enhancements + /health /metrics
- [ ] Improve API documentation and observability

<details>
<summary>📎 Copilot Prompt</summary>

```
Read all routers in src/interfaces/api/routers/.
In src/interfaces/api/app.py customize FastAPI() constructor:
  title="CloudIaaS API", version="1.0.0", description="...", contact={...}, license_info={...}

For every endpoint in every router add:
  summary="...", description="...", response_model=..., responses={401: ..., 403: ..., 404: ...}

Add to app.py:
  GET /health → {"status":"healthy","db":"connected","redis":"connected"} (check both)
  GET /metrics → {"total_users": int, "total_vms": int, "total_networks": int} (admin only)

Create src/interfaces/api/routers/system.py with these two endpoints and include in app.
```
</details>

---

### 3.2 [Dev-2] DB indexes + query optimisation
- [ ] Add indexes and optimize slow queries

<details>
<summary>📎 Copilot Prompt</summary>

```
Read all models in src/infrastructure/models/.
Add SQLAlchemy Index definitions (using Index() in __table_args__) for:
- VirtualMachine: composite index on (owner_id, status), index on created_at
- Network: index on owner_id, index on cidr
- Tenant: index on owner_id
- Quota: unique index on tenant_id (already FK, ensure DB-level unique constraint)

In src/infrastructure/repositories/base.py add:
- async count(self, *args) → int  (SELECT COUNT(*) WHERE *args)
- async paginate(self, page: int, page_size: int, *args, ordering=None) → dict with items + total + page + pages

Update all get_all calls in services to use paginate() instead of manual limit/offset.
Generate new Alembic migration: alembic revision --autogenerate -m "add_indexes"
```
</details>

---

### 3.3 [Dev-3] VM tests + Network tests
- [ ] Write tests for VM and Network endpoints

<details>
<summary>📎 Copilot Prompt</summary>

```
Read tests/conftest.py (once created) and src/interfaces/api/routers/vms.py.
Create tests/test_vms.py:
- test_create_vm_success: authenticated POST /vms returns 201 with correct fields
- test_create_vm_unauthenticated: returns 401
- test_list_vms_empty: GET /vms returns {"items":[],"total":0}
- test_get_vm_not_found: GET /vms/{random_uuid} returns 404
- test_update_vm_forbidden: user B cannot update user A's VM → 403
- test_delete_vm_success: owner can delete own VM → 204
- test_delete_vm_admin_can_delete_any: admin JWT can delete any user's VM

Create tests/test_networks.py with equivalent CRUD tests for Network endpoints.

Create tests/test_users.py:
- test_get_all_users_requires_auth
- test_update_user_own_profile
- test_update_user_forbidden (other user's profile)
- test_delete_user_self
```
</details>

---

### 3.4 [Dev-4] Security hardening + rate limiting
- [ ] Add security middleware and rate limiting

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/interfaces/api/app.py and src/settings/redis.py.
Add to app.py using Starlette middleware:

1. Security headers middleware (pure ASGI): add response headers:
   X-Content-Type-Options: nosniff
   X-Frame-Options: DENY
   X-XSS-Protection: 1; mode=block
   Referrer-Policy: strict-origin-when-cross-origin

2. Request logging middleware: log to Python logger:
   "{method} {path} → {status_code} in {duration_ms}ms"

3. Create src/interfaces/api/middleware/rate_limit.py:
   Redis-based sliding window rate limiter Starlette middleware.
   Key = f"rate:{client_ip}", window=60s, max_requests=100.
   Return HTTP 429 {"detail":"Too many requests"} when exceeded.
   Use redis.asyncio client from settings.redis.url.

Add all middleware to app.py. Ensure middleware order: logging → rate_limit → security_headers.
```
</details>

---

### 3.5 [Dev-5] Final README_BACKEND + GitHub Actions
- [ ] Generate production README and CI/CD pipeline

<details>
<summary>📎 Copilot Prompt</summary>

```
Read the entire project: all routers, models, docker-compose.yaml, pyproject.toml, .env.example.
Generate (overwrite) README.md with:

1. Project title + badges (Python 3.13, FastAPI, PostgreSQL, Docker)
2. Architecture diagram in Mermaid showing: Client → FastAPI → Services → Repositories → PostgreSQL/Redis
3. Quick Start:
   git clone / cp .env.example .env / fill .env / make dev / make migrate
4. Full API Endpoints table: Method | Path | Auth | Description
5. Environment Variables table: Variable | Required | Example | Description
6. Project structure tree (src/ layout)
7. Running tests section
8. Docker deployment section

Generate .github/workflows/test.yml:
  trigger: push and pull_request to main and dev
  jobs:
    test:
      runs-on: ubuntu-latest
      services:
        postgres: image postgres:17, env POSTGRES_* from secrets
        redis: image redis:latest
      steps: checkout, setup python 3.13, install uv, uv pip install -e ., run alembic upgrade head, run pytest -v --cov=src
```
</details>

---

## API Endpoints Summary

| Method | Path | Auth | Status |
|--------|------|------|--------|
| POST | `/auth/register` | ❌ | ✅ Done |
| GET | `/auth/register_confirm` | ❌ | ✅ Done |
| POST | `/auth/token` | ❌ | ✅ Done |
| POST | `/auth/refresh` | ❌ | ✅ Done |
| PATCH | `/auth/change_password` | ✅ | ✅ Done |
| GET | `/auth/me` | ✅ | ✅ Done |
| GET | `/users` | ✅ | ✅ Done |
| GET | `/users/{id}` | ✅ | ✅ Done |
| PATCH | `/users/{id}` | ✅ | ✅ Done |
| DELETE | `/users/delete` | ✅ | ✅ Done |
| GET/POST | `/vms` | ✅ | 🔲 Day 2 |
| GET/PATCH/DELETE | `/vms/{id}` | ✅ | 🔲 Day 2 |
| GET/POST | `/networks` | ✅ | 🔲 Day 2 |
| POST | `/networks/{id}/attach-vm` | ✅ | 🔲 Day 2 |
| GET/POST | `/quotas` | ✅ | 🔲 Day 2 |
| GET | `/admin/users` | 🔒 Admin | 🔲 Day 2 |
| GET | `/health` | ❌ | ✅ Done |
| GET | `/metrics` | 🔒 Admin | 🔲 Day 3 |
