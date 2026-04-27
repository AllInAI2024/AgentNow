from datetime import datetime
from sqlalchemy import Column, BigInteger, String, DateTime, Text, Integer, SmallInteger, Index

from app.models import Base


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="权限ID")
    parent_id = Column(BigInteger, default=0, comment="父权限ID（0表示顶级）")
    name = Column(String(50), nullable=False, comment="权限名称")
    code = Column(String(100), nullable=False, comment="权限编码（英文标识，如user:list, user:create）")
    type = Column(SmallInteger, default=1, comment="类型：1-菜单，2-按钮，3-API接口")
    path = Column(String(255), comment="路由路径/接口路径")
    icon = Column(String(100), comment="菜单图标")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_parent_id", "parent_id"),
        Index("idx_code", "code"),
        Index("idx_type", "type"),
    )

    def __repr__(self):
        return f"<Permission(id={self.id}, name={self.name}, code={self.code})>"

    def to_dict(self):
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "name": self.name,
            "code": self.code,
            "type": self.type,
            "path": self.path,
            "icon": self.icon,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }