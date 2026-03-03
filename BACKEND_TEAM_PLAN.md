# 🖥️ BACKEND — Разделение задач на 3 разработчика

> Стек: Python 3.13 + FastAPI + SQLAlchemy 2.0 async + PostgreSQL 17 + Alembic + uv  
> Архитектура: Clean Architecture (`src/interfaces` → `src/application` → `src/infrastructure`)  
> Каждый пункт = готовый промт для GitHub Copilot Chat  
> Каждый разработчик работает в своей ветке и делает PR в `develop`

---

## 🗂️ Структура проекта (уже создана)

```
src/
├── interfaces/api/
│   ├── app.py              ← FastAPI app (SessionMiddleware, /health уже есть)
│   ├── routers/            ← auth.py, vms.py, networks.py, quotas.py, admin.py (заглушки)
│   └── dependencies/
│       └── session.py      ← get_db() уже реализован
├── application/
│   └── services/           ← vm_service.py, network_service.py (реализовать)
├── infrastructure/
│   ├── models/
│   │   └── base.py         ← Base, engine, async_session_maker (уже есть)
│   ├── repositories/
│   │   └── base.py         ← BaseRepository с CRUD (уже есть)
│   └── shemas/             ← auth.py, vm.py, network.py, quota.py, tenant.py, admin.py
└── settings/
    └── __init__.py         ← Pydantic Settings (расширить)
alembic/                    ← уже инициализирован
pyproject.toml              ← зависимости через uv
Dockerfile                  ← multi-stage python:3.13 + uv (уже есть)
docker-compose.yaml         ← db (postgres:17) + backend (уже есть)
```

---

## 🌿 Git-стратегия

```
main
└── develop
    ├── feature/be1-foundation        ← Dev 1
    ├── feature/be2-vm-hypervisor     ← Dev 2
    └── feature/be3-admin-audit       ← Dev 3
```

**Порядок мержей:**
1. Dev 1 мержит первым (foundation) — остальные делают `git rebase develop` после этого
2. Dev 2 и Dev 3 могут работать параллельно с Dev 1 на заглушках, мержат после Dev 1
3. Итоговый мерж `develop → main` делает тимлид после прохождения всех тестов

---

## ⚡ ОБЩИЙ СТАРТ

```bash
# Клонировать репо и переключиться на develop
git clone <repo> && cd hakaton && git checkout develop

# Установить зависимости через uv
pip install uv
uv pip install -e .

# Dev 1 создаёт ветку и пушит
git checkout -b feature/be1-foundation
# Dev 2, Dev 3 аналогично
git checkout -b feature/be2-vm-hypervisor
git checkout -b feature/be3-admin-audit
```

---

---

# 👤 DEV 1 — Foundation: Settings + Models + Auth

> **Ветка:** `feature/be1-foundation`  
> **Зона ответственности:** всё, от чего зависят Dev 2 и Dev 3  
> **Приоритет:** сделать первым и смержить как можно раньше

---

### ✅ День 1 — Утро

#### 1.1 Зависимости (pyproject.toml + uv)
```
Update pyproject.toml dependencies section to add:
"asyncpg>=0.30.0",
"pydantic-settings>=2.0.0",
"passlib[bcrypt]>=1.7.4",
"python-jose[cryptography]>=3.3.0",
"uvicorn[standard]>=0.29.0",
"uvloop>=0.19.0",
"httpx>=0.27.0",
"pytest-asyncio>=0.23.0",
"pytest>=8.0.0"

Then run: uv pip install -e .
File: pyproject.toml
```

#### 1.2 Settings (src/settings/__init__.py)
```
Expand src/settings/__init__.py using pydantic-settings BaseSettings.
Add nested DbSettings class with fields:
  host (str), port (int=5432), name (str), user (str), password (str)
  property url → f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"

Add to main Settings class:
  db: DbSettings
  secret_key: str
  access_token_expire_minutes: int = 15
  refresh_token_expire_days: int = 7
  allowed_origins: list[str] = ["*"]
  first_admin_email: str = "admin@cloud.local"
  first_admin_password: str = "changeme"

Load from .env using model_config = SettingsConfigDict(env_nested_delimiter="__")
So env vars look like: POSTGRES_HOST, POSTGRES_PORT, etc. (map via env prefix aliases)
Export singleton: settings = Settings()
File: src/settings/__init__.py
```

#### 1.3 Все ORM модели
```
Create SQLAlchemy 2.0 ORM model files in src/infrastructure/models/.
All use mapped_column syntax, UUID primary keys with server_default=text("gen_random_uuid()").
All import Base from src.infrastructure.models.base.

File src/infrastructure/models/tenant.py:
class Tenant: id (UUID PK), name (str unique), slug (str unique),
status (str default="active"), created_at (datetime server_default=now()),
max_vms (int=10), max_networks (int=5)

File src/infrastructure/models/user.py:
class User: id (UUID PK), tenant_id (ForeignKey Tenant nullable),
email (str unique), hashed_password (str), role (str: admin/tenant_owner/tenant_user),
is_active (bool=True), created_at

File src/infrastructure/models/virtual_machine.py:
class VirtualMachine: id (UUID PK), tenant_id (FK Tenant NOT NULL), name (str),
status (str default="creating"), cpu_cores (int), ram_mb (int), disk_gb (int),
docker_container_id (str nullable), ip_address (str nullable),
created_at, updated_at (onupdate=datetime.utcnow)

File src/infrastructure/models/network.py:
class Network: id (UUID PK), tenant_id (FK Tenant NOT NULL), name (str),
cidr (str), is_active (bool=True), created_at

File src/infrastructure/models/resource_quota.py:
class ResourceQuota: id (UUID PK), tenant_id (FK Tenant UNIQUE NOT NULL),
max_cpu_cores (int=8), max_ram_mb (int=8192), max_disk_gb (int=100),
max_vms (int=5), max_networks (int=5),
used_cpu_cores (int=0), used_ram_mb (int=0), used_disk_gb (int=0), used_vms (int=0)

File src/infrastructure/models/audit_log.py:
class AuditLog: id (UUID PK), tenant_id (FK nullable), user_id (FK nullable),
action (str), resource_type (str), resource_id (str nullable),
detail (JSON nullable), created_at

File src/infrastructure/models/__init__.py:
Export all: from .tenant import Tenant, from .user import User, etc.
```

#### 1.4 Alembic — настройка и первая миграция
```
Alembic already initialized in alembic/ directory.
Update alembic/env.py:
- from src.settings import settings
- Set sqlalchemy.url = settings.db.url.replace("+asyncpg", "")
- Import Base from src.infrastructure.models.base
- Import all models from src.infrastructure.models (so autogenerate detects them)
- Use run_migrations_online() with sync engine pattern

Generate migration:
  alembic revision --autogenerate -m "initial_schema"

Verify migration creates 6 tables:
  tenants, users, virtual_machines, networks, resource_quotas, audit_logs

Apply:
  alembic upgrade head

File: alembic/env.py
```

---

### ✅ День 1 — Вторая половина

#### 1.5 JWT утилиты
```
Create src/infrastructure/utils/jwt.py with functions:
- create_access_token(data: dict) → str
  python-jose jwt.encode, HS256, exp = now + settings.access_token_expire_minutes
- create_refresh_token(data: dict) → str
  exp = now + settings.refresh_token_expire_days * 24 * 60 minutes
- decode_token(token: str) → dict
  jwt.decode, raise HTTPException(401) on JWTError or ExpiredSignatureError

JWT payload: sub (user_id str), tenant_id (str|None), role (str), exp
File: src/infrastructure/utils/jwt.py
```

#### 1.6 Pydantic Schemas — Auth + User + Tenant
```
Create Pydantic v2 schemas with model_config = ConfigDict(from_attributes=True):

File src/infrastructure/shemas/auth.py:
- RegisterRequest: name(str), email(EmailStr), password(str min_length=8), company_name(str)
- LoginRequest: email(EmailStr), password(str)
- TokenResponse: access_token(str), refresh_token(str), token_type(str="bearer")
- RefreshRequest: refresh_token(str)

File src/infrastructure/shemas/tenant.py:
- TenantResponse: id(UUID), name, slug, status, created_at, max_vms, max_networks
- TenantCreate: name(str), email(EmailStr), password(str), max_vms(int=5)

File src/infrastructure/shemas/user.py (create if not exists):
- UserResponse: id(UUID), email, role, tenant_id(UUID|None), is_active, created_at
```

#### 1.7 Auth Dependencies
```
Create src/interfaces/api/dependencies/auth.py with FastAPI dependency functions:

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = decode_token(token)
    user = await db.get(User, UUID(payload["sub"]))
    if not user or not user.is_active: raise HTTPException(401)
    return user

async def get_tenant_context(current_user: User = Depends(get_current_user)) -> UUID:
    if not current_user.tenant_id: raise HTTPException(403, "No tenant")
    return current_user.tenant_id

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin": raise HTTPException(403, "Admin only")
    return current_user

File: src/interfaces/api/dependencies/auth.py
```

#### 1.8 Auth Router
```
Implement src/interfaces/api/routers/auth.py (file exists, replace stub):
APIRouter(prefix="/auth", tags=["auth"])

POST /register:
- Validate RegisterRequest
- Check email not taken (raise 409 if exists)
- Create Tenant(name=company_name, slug=slugify(company_name))
- Create User(email, hashed_password=bcrypt(password), role="tenant_owner", tenant_id=tenant.id)
- Create ResourceQuota(tenant_id=tenant.id) with defaults
- Commit via db session, return TokenResponse

POST /login:
- Find User by email, verify bcrypt, check is_active
- Return TokenResponse with create_access_token + create_refresh_token

POST /refresh:
- Decode refresh token, get user, return new access_token

POST /logout:
- Return {"message": "logged out"} (stateless JWT)

File: src/interfaces/api/routers/auth.py
```

#### 1.9 Обновить app.py — подключить роутеры
```
Update src/interfaces/api/app.py:
- Add CORSMiddleware with settings.allowed_origins
- Include all routers with prefixes:
  from src.interfaces.api.routers import auth, vms, networks, quotas, admin
  app.include_router(auth.router, prefix="/api/v1/auth")
  app.include_router(vms.router, prefix="/api/v1/vms")
  app.include_router(networks.router, prefix="/api/v1/networks")
  app.include_router(quotas.router, prefix="/api/v1/quotas")
  app.include_router(admin.router, prefix="/api/v1/admin")
- Add startup event: run alembic upgrade head, then await seed()
- Keep existing /health endpoint (already works)
- Add docs_url="/api/docs"

File: src/interfaces/api/app.py
```

#### 1.10 Seed script
```
Create src/infrastructure/seed.py as async main():
1. Check if User with settings.first_admin_email exists → skip if yes (idempotent)
2. Create User: email=settings.first_admin_email, role="admin", tenant_id=None,
   hashed_password=bcrypt(settings.first_admin_password), is_active=True
3. Create Tenant: name="Demo Corp", slug="demo", status="active"
4. Create User: email="demo@cloud.local", password="demo1234", role="tenant_owner"
5. Create ResourceQuota for demo: max_vms=5, max_cpu_cores=8, max_ram_mb=8192
6. Print "Seed completed" / "Seed skipped"

Use async_session_maker from src.infrastructure.models.base
Run with: python -m src.infrastructure.seed
File: src/infrastructure/seed.py
```

#### 1.11 Auth тесты
```
Create tests/conftest.py with pytest-asyncio fixtures:
- event_loop fixture
- async_client using httpx.AsyncClient(app=app, base_url="http://test")

Create tests/test_auth.py:
- test_register_success(): POST /api/v1/auth/register → 201, access_token in response
- test_register_duplicate_email(): register twice same email → 409
- test_login_success(): register then login → 200, tokens returned
- test_login_wrong_password(): → 401
- test_refresh_token(): login → use refresh_token → new access_token → 200

File: tests/conftest.py, tests/test_auth.py
```

> **После:** `git add . && git commit -m "feat: foundation - settings, models, auth" && git push`  
> **Затем:** создать PR `feature/be1-foundation → develop` и смержить  
> **Dev 2 и Dev 3:** `git rebase develop` на своих ветках

---

---

# 👤 DEV 2 — VM Service + Mock Hypervisor + Quota Logic

> **Ветка:** `feature/be2-vm-hypervisor`  
> **Зона ответственности:** жизненный цикл виртуальных машин, гипервизор-мок, квоты  
> **Зависимость:** нужны модели от Dev 1. Пока Dev 1 не смержил — работай на заглушках моделей

---

### ✅ День 1 — Параллельно с Dev 1 (заглушки)

#### 2.1 Stub-модели для локальной работы
```
Until Dev 1 merges, create temporary stub files in src/infrastructure/models/_stubs.py:
@dataclass class VirtualMachine: id, tenant_id, name, status, cpu_cores, ram_mb, disk_gb, docker_container_id
@dataclass class ResourceQuota: max_vms, max_cpu_cores, max_ram_mb, used_vms, used_cpu_cores, used_ram_mb

Delete this file after rebasing on develop with Dev 1's ORM models.
File: src/infrastructure/models/_stubs.py (временный)
```

#### 2.2 VM Pydantic Schemas
```
Implement src/infrastructure/shemas/vm.py (file exists, replace stub):
Pydantic v2 schemas with ConfigDict(from_attributes=True):

- VMCreate: name(str min=1 max=64), cpu_cores(int ge=1 le=16),
  ram_mb(int ge=512 le=32768), disk_gb(int ge=10 le=1000)
- VMResponse: id(UUID), tenant_id(UUID), name, status, cpu_cores, ram_mb, disk_gb,
  docker_container_id(str|None), ip_address(str|None), created_at, updated_at
- VMListResponse: items(list[VMResponse]), total(int)

File: src/infrastructure/shemas/vm.py
```

#### 2.3 Mock Hypervisor Client
```
Create src/infrastructure/hypervisor/docker_client.py with class MockHypervisor.
Use Docker SDK: import docker. Wrap blocking calls with asyncio.get_event_loop().run_in_executor(None, ...).

async def create_vm(self, vm_id: str, cpu_cores: int, ram_mb: int) -> str:
  container = client.containers.run(
    "alpine:latest", command="sleep infinity", detach=True,
    name=f"cloudiaas-vm-{vm_id}",
    cpu_period=100000, cpu_quota=cpu_cores * 100000,
    mem_limit=f"{ram_mb}m", labels={"cloudiaas": "true", "vm_id": vm_id}
  )
  return container.id

async def start_vm(self, container_id: str) -> None
async def stop_vm(self, container_id: str) -> None
async def delete_vm(self, container_id: str) -> None
async def get_status(self, container_id: str) -> str:
  map: running→running, exited→stopped, created→creating, NotFound→deleted

Singleton: hypervisor = MockHypervisor()
File: src/infrastructure/hypervisor/docker_client.py
```

---

### ✅ День 1 — После мержа Dev 1

#### 2.4 Quota Service
```
Create src/application/services/quota_service.py with QuotaService class.
Use SQLAlchemy select() directly (or BaseRepository pattern).

async def get_quota(db: AsyncSession, tenant_id: UUID) -> ResourceQuota
async def check_vm_quota(db, tenant_id, vm: VMCreate) -> None
  raises HTTPException(422) if used_vms >= max_vms, cpu or ram exceeded
async def consume_vm_quota(db, tenant_id, vm: VirtualMachine) -> None
  increments used_vms, used_cpu_cores, used_ram_mb, flush + commit
async def release_vm_quota(db, tenant_id, vm: VirtualMachine) -> None
  decrements (min 0), commit

File: src/application/services/quota_service.py
```

#### 2.5 VM Service
```
Implement src/application/services/vm_service.py (file exists, replace stub).
All methods accept (db: AsyncSession, tenant_id: UUID).
Always filter by tenant_id.

async def list_vms(db, tenant_id) -> list[VirtualMachine]
async def get_vm(db, tenant_id, vm_id: UUID) -> VirtualMachine  # 404 if wrong tenant
async def create_vm(db, tenant_id, data: VMCreate, user_id: UUID) -> VirtualMachine:
  check_vm_quota → create VM row (status=creating) → hypervisor.create_vm →
  update status=running + docker_container_id → write AuditLog → consume_vm_quota
async def start_vm(db, tenant_id, vm_id, user_id) -> VirtualMachine
async def stop_vm(db, tenant_id, vm_id, user_id) -> VirtualMachine
async def delete_vm(db, tenant_id, vm_id, user_id) -> None:
  hypervisor.delete_vm → release_vm_quota → db.delete(vm)

File: src/application/services/vm_service.py
```

#### 2.6 VM Router
```
Implement src/interfaces/api/routers/vms.py (file exists, replace stub):
APIRouter(prefix="", tags=["vms"])
All routes: current_user=Depends(get_current_user), db=Depends(get_db)
Extract tenant_id = current_user.tenant_id (raise 403 if None)

GET /                → VMListResponse
POST /               → VMResponse, status_code=201
GET /{vm_id}         → VMResponse
POST /{vm_id}/start  → VMResponse
POST /{vm_id}/stop   → VMResponse
DELETE /{vm_id}      → Response(status_code=204)

File: src/interfaces/api/routers/vms.py
```

#### 2.7 Quota Router
```
Implement src/interfaces/api/routers/quotas.py (file exists, replace stub):
APIRouter(prefix="", tags=["quotas"])

GET /me:
  quota = await QuotaService.get_quota(db, current_user.tenant_id)
  Return QuotaResponse with usage percentages:
  vm_percent = round(quota.used_vms / quota.max_vms * 100, 1)

Schema QuotaResponse in src/infrastructure/shemas/quota.py:
  all ResourceQuota fields + vm_percent, cpu_percent, ram_percent

File: src/interfaces/api/routers/quotas.py, src/infrastructure/shemas/quota.py
```

#### 2.8 VM тесты
```
Create tests/test_vms.py using pytest-asyncio + httpx AsyncClient:

test_create_vm_success(): register → login → POST /api/v1/vms → 201, status="running"
test_create_vm_updates_quota(): create VM → GET /api/v1/quotas/me → used_vms == 1
test_get_vm_not_found(): GET /api/v1/vms/<random_uuid> → 404
test_cannot_access_other_tenant_vm():
  register tenant A, create VM
  register tenant B, GET /api/v1/vms/{vm_id} → 404 (isolation)
test_vm_quota_exceeded(): max_vms=1 in quota → create 2nd VM → 422
test_stop_running_vm(): create → stop → status=="stopped"
test_delete_vm_removes_from_list(): create → delete → GET / → empty

Use unittest.mock to patch hypervisor methods (no real Docker needed)
File: tests/test_vms.py
```

> **После:** `git add . && git commit -m "feat: vm service, hypervisor mock, quota logic" && git push`

---

---

# 👤 DEV 3 — Networks + Admin Panel + AuditLog + DevOps

> **Ветка:** `feature/be3-admin-audit`  
> **Зона ответственности:** сетевой слой, весь admin API, audit log, Docker Compose  
> **Зависимость:** нужны модели от Dev 1. Работай на заглушках до мержа

---

### ✅ День 1 — Параллельно с Dev 1

#### 3.1 Network + Admin Pydantic Schemas
```
Implement src/infrastructure/shemas/network.py (file exists, replace stub):
- NetworkCreate: name(str), cidr(str — validate with regex r'^\d+\.\d+\.\d+\.\d+/\d+$')
- NetworkResponse: id(UUID), tenant_id(UUID), name, cidr, is_active, created_at
  ConfigDict(from_attributes=True)

Implement src/infrastructure/shemas/admin.py (file exists, replace stub):
- TenantAdminResponse: id, name, slug, status, created_at, vm_count(int), quota(QuotaResponse|None)
- QuotaUpdateRequest: max_vms(int|None), max_cpu_cores(int|None), max_ram_mb(int|None), max_disk_gb(int|None)
- TenantStatusUpdate: status(Literal["active","suspended"])
- PlatformStats: total_tenants(int), total_vms(int), running_vms(int), suspended_tenants(int)
- AuditLogResponse: id, tenant_id, user_id, action, resource_type, resource_id, detail, created_at
- PaginatedAuditLog: items(list[AuditLogResponse]), total(int), page(int), size(int)

File: src/infrastructure/shemas/network.py, src/infrastructure/shemas/admin.py
```

#### 3.2 Обновить docker-compose.yaml и .env.example
```
Update docker-compose.yaml (file exists, fix issues):
- Rename service "accounts-db" → "db" (already named "db" in healthcheck but depends_on references "accounts-db")
- Fix depends_on in backend service: db (not accounts-db)
- Add to backend service: volumes: [/var/run/docker.sock:/var/run/docker.sock]
- Verify postgres service image is postgres:17.0 (already set)
- Add SECRET_KEY to env_file variables

Update .env.example with full variable set:
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=cloudiaas
POSTGRES_USER=cloudiaas
POSTGRES_PASSWORD=cloudiaas
SECRET_KEY=change_me_use_openssl_rand_hex_32
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
FIRST_ADMIN_EMAIL=admin@cloud.local
FIRST_ADMIN_PASSWORD=Admin1234!

File: docker-compose.yaml, .env.example
```

---

### ✅ День 1 — После мержа Dev 1

#### 3.3 Network Service
```
Implement src/application/services/network_service.py (file exists, replace stub):

async def list_networks(db, tenant_id) -> list[Network]

async def create_network(db, tenant_id, data: NetworkCreate, user_id: UUID) -> Network:
  - Count existing networks, compare with quota max_networks (raise 422 if exceeded)
  - Check CIDR uniqueness within tenant (raise 409 if duplicate)
  - Insert Network row + AuditLog("network.create")
  - Commit, return network

async def delete_network(db, tenant_id, network_id: UUID, user_id: UUID) -> None:
  - 404 if not found or wrong tenant
  - Write AuditLog("network.delete")
  - db.delete(network), commit

File: src/application/services/network_service.py
```

#### 3.4 Network Router
```
Implement src/interfaces/api/routers/networks.py (file exists, replace stub):
APIRouter(prefix="", tags=["networks"])
All routes: current_user=Depends(get_current_user), db=Depends(get_db)

GET /                  → list[NetworkResponse]
POST /                 → NetworkResponse, status_code=201
DELETE /{network_id}   → Response(status_code=204)

File: src/interfaces/api/routers/networks.py
```

#### 3.5 Admin Service
```
Create src/application/services/admin_service.py:

async def list_tenants(db, page=1, size=20) -> tuple[list[Tenant], int]
async def get_tenant(db, tenant_id: UUID) -> Tenant  # with vm_count subquery
async def update_tenant_quota(db, tenant_id, data: QuotaUpdateRequest) -> ResourceQuota
async def update_tenant_status(db, tenant_id, data: TenantStatusUpdate) -> Tenant:
  - If suspended: set all tenant users is_active=False
  - If active: restore is_active=True
async def get_platform_stats(db) -> PlatformStats:
  - total_tenants, total_vms, running_vms, suspended_tenants via COUNT queries
async def list_audit_logs(db, tenant_id=None, action=None, page=1, size=20) -> tuple[list, int]:
  - Filterable, ordered by created_at desc, paginated

File: src/application/services/admin_service.py
```

#### 3.6 Admin Router
```
Implement src/interfaces/api/routers/admin.py (file exists, replace stub):
APIRouter(prefix="", tags=["admin"])
All routes: admin=Depends(require_admin), db=Depends(get_db)

GET /tenants              → paginated TenantAdminResponse
POST /tenants             → create tenant + owner user
GET /tenants/{id}         → TenantAdminResponse with quota and vm_count
PUT /tenants/{id}/quota   → QuotaResponse
PUT /tenants/{id}/status  → TenantResponse
GET /audit-logs           → PaginatedAuditLog (query params: tenant_id?, action?, page, size)
GET /stats                → PlatformStats

File: src/interfaces/api/routers/admin.py
```

#### 3.7 Network + Admin тесты
```
Create tests/test_networks.py:
- test_create_network_success(): register → POST /api/v1/networks → 201
- test_create_duplicate_cidr(): create twice same CIDR → 409
- test_delete_network(): create → delete → GET / returns empty
- test_network_quota_exceeded(): max_networks=1 → create 2nd → 422

Create tests/test_admin.py:
- test_list_tenants_requires_admin(): tenant token → 403
- test_list_tenants_as_admin(): admin login → GET /api/v1/admin/tenants → 200
- test_update_quota(): max_vms=20 → verify in response
- test_suspend_tenant(): status="suspended" → tenant user 403
- test_get_stats(): PlatformStats with correct counts

File: tests/test_networks.py, tests/test_admin.py
```

#### 3.8 E2E Smoke Test
```
Create tests/e2e_smoke.py as standalone script using httpx (sync):
BASE = "http://localhost:8000"

Steps (print PASS/FAIL per step):
1. POST /api/v1/auth/register → expect 201, save token
2. POST /api/v1/networks → create "net-1" 192.168.1.0/24 → expect 201
3. POST /api/v1/vms → create "web-01" 2cpu/1024mb/20gb → expect 201, save vm_id
4. Poll GET /api/v1/vms/{vm_id} every 2s max 30s until status=="running"
5. POST /api/v1/vms/{vm_id}/stop → expect 200, status=="stopped"
6. DELETE /api/v1/vms/{vm_id} → expect 204
7. GET /api/v1/vms/{vm_id} → expect 404
8. Admin login → GET /api/v1/admin/tenants → verify registered tenant in list
9. GET /api/v1/admin/stats → total_vms >= 0

Run: python tests/e2e_smoke.py
File: tests/e2e_smoke.py
```

> **После:** `git add . && git commit -m "feat: networks, admin api, audit, devops" && git push`

---

---

## 🔀 ПОРЯДОК МЕРЖЕЙ В GIT

```
День 1, вечер:
  Dev 1: PR feature/be1-foundation → develop  (ревью от Dev 2 или 3, мерж)

  Dev 2: git fetch origin && git rebase origin/develop
         PR feature/be2-vm-hypervisor → develop

  Dev 3: git fetch origin && git rebase origin/develop
         PR feature/be3-admin-audit → develop

День 2, утро:
  develop → main  (финальный мерж тимлидом после smoke test)
```

---

## 📋 ИТОГОВЫЙ ЧЕКЛИСТ БЭКЕНДА

```
Dev 1:
□ uv pip install -e . — без ошибок
□ alembic upgrade head — создаёт 6 таблиц
□ POST /api/v1/auth/register → 201 + токены
□ POST /api/v1/auth/login → 200 + токены
□ GET /health → {"status": "healthy", "database": "connected"}
□ tests/test_auth.py — все тесты зелёные

Dev 2:
□ POST /api/v1/vms → 201, status="running"
□ GET /api/v1/vms/{id} → возвращает VM
□ Квота уменьшается после создания VM (GET /api/v1/quotas/me)
□ Изоляция: чужой тенант получает 404 на чужую VM
□ tests/test_vms.py — все тесты зелёные (с моком гипервизора)

Dev 3:
□ POST /api/v1/networks → 201
□ GET /api/v1/admin/tenants → требует роль admin (403 для обычного юзера)
□ GET /api/v1/admin/stats → корректные цифры
□ docker compose up --build → оба сервиса healthy
□ tests/test_networks.py + tests/test_admin.py — зелёные
□ tests/e2e_smoke.py — все шаги PASS
```
