from datetime import datetime
from sqlalchemy import Column, BigInteger, DateTime, Index, ForeignKey, UniqueConstraint

from app.models import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="关联ID")
    role_id = Column(BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, comment="角色ID")
    permission_id = Column(BigInteger, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, comment="权限ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uk_role_permission"),
        Index("idx_role_id", "role_id"),
        Index("idx_permission_id", "permission_id"),
    )

    def __repr__(self):
        return f"<RolePermission(id={self.id}, role_id={self.role_id}, permission_id={self.permission_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "role_id": self.role_id,
            "permission_id": self.permission_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }