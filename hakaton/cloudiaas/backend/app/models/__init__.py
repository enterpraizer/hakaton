import uuid
from sqlalchemy import String, Integer, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class TenantStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"


class UserRole(str, enum.Enum):
    tenant_owner = "tenant_owner"
    admin = "admin"


class VMStatus(str, enum.Enum):
    creating = "creating"
    running = "running"
    stopped = "stopped"
    error = "error"


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[TenantStatus] = mapped_column(SAEnum(TenantStatus), default=TenantStatus.active)
    max_vms: Mapped[int] = mapped_column(Integer, default=5)

    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")
    vms: Mapped[list["VirtualMachine"]] = relationship("VirtualMachine", back_populates="tenant")
    networks: Mapped[list["Network"]] = relationship("Network", back_populates="tenant")
    quota: Mapped["ResourceQuota"] = relationship("ResourceQuota", back_populates="tenant", uselist=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.tenant_owner)

    tenant: Mapped["Tenant | None"] = relationship("Tenant", back_populates="users")


class VirtualMachine(Base):
    __tablename__ = "virtual_machines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[VMStatus] = mapped_column(SAEnum(VMStatus), default=VMStatus.creating, index=True)
    cpu_cores: Mapped[int] = mapped_column(Integer, nullable=False)
    ram_mb: Mapped[int] = mapped_column(Integer, nullable=False)
    disk_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    docker_container_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="vms")


class Network(Base):
    __tablename__ = "networks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cidr: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="networks")


class ResourceQuota(Base):
    __tablename__ = "resource_quotas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), unique=True, nullable=False, index=True)
    max_cpu_cores: Mapped[int] = mapped_column(Integer, default=8)
    max_ram_mb: Mapped[int] = mapped_column(Integer, default=8192)
    max_disk_gb: Mapped[int] = mapped_column(Integer, default=500)
    used_cpu_cores: Mapped[int] = mapped_column(Integer, default=0)
    used_ram_mb: Mapped[int] = mapped_column(Integer, default=0)
    used_disk_gb: Mapped[int] = mapped_column(Integer, default=0)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="quota")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
