from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Integer, SmallInteger, Boolean, DateTime, Text, Index, ForeignKey

from app.models import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="部门ID")
    parent_id = Column(BigInteger, default=0, comment="父部门ID（0表示顶级）")
    name = Column(String(100), nullable=False, comment="部门名称")
    code = Column(String(50), comment="部门编码")
    manager_id = Column(BigInteger, comment="部门负责人ID")
    phone = Column(String(20), comment="部门电话")
    email = Column(String(100), comment="部门邮箱")
    sort = Column(Integer, default=0, comment="排序号")
    status = Column(SmallInteger, default=1, comment="状态：0-禁用，1-启用")
    description = Column(Text, comment="部门描述")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_parent_id", "parent_id"),
        Index("idx_code", "code"),
        Index("idx_status", "status"),
    )

    def __repr__(self):
        return f"<Department(id={self.id}, name={self.name})>"

    def to_dict(self):
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "name": self.name,
            "code": self.code,
            "manager_id": self.manager_id,
            "phone": self.phone,
            "email": self.email,
            "sort": self.sort,
            "status": self.status,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
