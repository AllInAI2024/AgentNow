from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, BigInteger, String, Index
from sqlalchemy.orm import validates

from app.models import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    phone = Column(String(20), nullable=False, unique=True, comment="手机号（登录账号）")
    password_hash = Column(String(255), nullable=False, comment="密码哈希值")
    username = Column(String(50), nullable=False, comment="用户名")
    role = Column(String(20), default="user", comment="角色：admin-管理员，user-普通用户")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_default_password = Column(Boolean, default=True, comment="是否为默认密码（首次登录需修改）")
    hermes_profile = Column(String(100), nullable=True, comment="对应的 Hermes Profile 名称")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_phone", "phone"),
        Index("idx_role", "role"),
        Index("idx_hermes_profile", "hermes_profile"),
    )

    @validates("role")
    def validate_role(self, key, role):
        if role not in ["admin", "user"]:
            raise ValueError("角色必须是 admin 或 user")
        return role

    def __repr__(self):
        return f"<User(id={self.id}, phone={self.phone}, role={self.role})>"

    def to_dict(self):
        return {
            "id": self.id,
            "phone": self.phone,
            "username": self.username,
            "role": self.role,
            "is_active": self.is_active,
            "is_default_password": self.is_default_password,
            "hermes_profile": self.hermes_profile,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
