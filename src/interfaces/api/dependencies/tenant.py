from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from src.infrastructure.models.tenant import Tenant
from src.interfaces.api.dependencies.session import get_db


async def get_tenant_id(request: Request) -> UUID:
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context missing",
        )
    return tenant_id


async def get_current_tenant(
    tenant_id: UUID = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_db),
) -> Tenant:
    tenant = await session.get(Tenant, tenant_id)
    if not tenant or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant not found or inactive",
        )
    return tenant
