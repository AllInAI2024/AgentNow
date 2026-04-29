from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text, Integer, SmallInteger, Index

from app.models import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="角色ID")
    name = Column(String(50), nullable=False, comment="角色名称")
    code = Column(String(50), nullable=False, comment="角色编码（英文标识）")
    description = Column(Text, comment="角色描述")
    sort = Column(Integer, default=0, comment="排序号")
    status = Column(SmallInteger, default=1, comment="状态：0-禁用，1-启用")
    is_system = Column(Boolean, default=False, comment="是否为系统内置角色（不可删除）")
    data_scope = Column(SmallInteger, default=1, comment="数据权限范围：1-全部数据，2-本部门数据，3-本部门及以下数据，4-仅本人数据，5-自定义数据")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_code", "code"),
        Index("idx_status", "status"),
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name}, code={self.code})>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "sort": self.sort,
            "status": self.status,
            "is_system": self.is_system,
            "data_scope": self.data_scope,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
