from datetime import datetime
from sqlalchemy import Column, BigInteger, String, DateTime, Text, Index

from app.models import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="角色ID")
    name = Column(String(50), nullable=False, comment="角色名称")
    code = Column(String(50), nullable=False, unique=True, comment="角色编码（英文标识）")
    description = Column(Text, comment="角色描述")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_code", "code"),
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name}, code={self.code})>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }