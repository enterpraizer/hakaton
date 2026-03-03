# CloudIaaS Platform — Backend

REST API для управления виртуальными машинами и сетями в облачной IaaS-платформе.

## Архитектура

```
[Client] ──► [FastAPI Backend :8000]
                      │
               [PostgreSQL :5432]
```

Проект построен по принципам **Clean Architecture** с разделением на слои:

```
src/
├── interfaces/          # Точки входа (HTTP API)
│   └── api/
│       ├── app.py       # FastAPI приложение
│       ├── routers/     # Маршруты: auth, vms, networks, quotas, admin
│       └── dependencies/
│           └── session.py  # AsyncSession dependency (get_db)
│
├── application/         # Бизнес-логика (use cases)
│   └── services/
│       ├── vm_service.py
│       └── network_service.py
│
├── infrastructure/      # Инфраструктурный слой
│   ├── models/
│   │   └── base.py      # SQLAlchemy Base, async engine, session maker
│   ├── repositories/
│   │   └── base.py      # BaseRepository (CRUD)
│   └── shemas/          # Pydantic schemas: auth, vm, network, quota, tenant, admin
│
└── settings/
    └── __init__.py      # Pydantic Settings (конфигурация из .env)
```

## Технологический стек

| Компонент | Технология |
|-----------|-----------|
| Runtime | Python 3.13 |
| Web Framework | FastAPI + uvicorn + uvloop |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Database | PostgreSQL 17 |
| Package Manager | uv |
| Validation | Pydantic v2 + pydantic-settings |
| Session | Starlette SessionMiddleware |

## Структура файлов

```
hakaton/
├── src/
│   ├── interfaces/api/
│   │   ├── app.py
│   │   ├── routers/        # auth.py, vms.py, networks.py, quotas.py, admin.py
│   │   └── dependencies/
│   │       └── session.py
│   ├── application/
│   │   └── services/       # vm_service.py, network_service.py
│   ├── infrastructure/
│   │   ├── models/base.py
│   │   ├── repositories/base.py
│   │   └── shemas/         # auth.py, vm.py, network.py, quota.py, tenant.py, admin.py
│   └── settings/__init__.py
├── alembic/                 # Миграции БД
├── Dockerfile
├── docker-compose.yaml
├── pyproject.toml
└── .env.example
```

## API

Базовый URL: `http://localhost:8000`

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/health` | Проверка состояния сервиса и подключения к БД |
| — | `/api/v1/auth` | Аутентификация (регистрация, логин, refresh, logout) |
| — | `/api/v1/vms` | Управление виртуальными машинами |
| — | `/api/v1/networks` | Управление сетями |
| — | `/api/v1/quotas` | Квоты ресурсов |
| — | `/api/v1/admin` | Административные операции |

Документация OpenAPI доступна по адресу: `http://localhost:8000/docs`

## Быстрый старт

### С Docker Compose

```bash
cp .env.example .env
# Заполни переменные в .env

docker compose up --build
```

Сервисы:
- **backend**: `http://localhost:8000`
- **postgres**: `localhost:5432`

### Локально (без Docker)

```bash
# Установить зависимости через uv
pip install uv
uv pip install -e .

# Применить миграции
alembic upgrade head

# Запустить сервер
uvicorn src.interfaces.api.app:app --reload --host 0.0.0.0 --port 8000
```

## Переменные окружения

Создай `.env` на основе `.env.example`:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cloudiaas
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

## Паттерн репозитория

`BaseRepository` в `src/infrastructure/repositories/base.py` предоставляет универсальные CRUD-методы через SQLAlchemy Core:

```python
await repo.create(**kwargs)          # INSERT ... RETURNING
await repo.get(*where_clauses)       # SELECT ... WHERE
await repo.get_all(limit, offset)    # SELECT с пагинацией
await repo.update(*where, **values)  # UPDATE ... RETURNING
await repo.delete(*where_clauses)    # DELETE ... RETURNING
```

Все методы автоматически получают `AsyncSession` через FastAPI Dependency Injection.

## Миграции

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "описание"

# Применить все миграции
alembic upgrade head

# Откатить последнюю
alembic downgrade -1
```

## Healthcheck

```bash
curl http://localhost:8000/health
# {"status": "healthy", "database": "connected"}
```
