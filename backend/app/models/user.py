from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, BigInteger, String, Text, Index

from app.models import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    department_id = Column(BigInteger, comment="所属部门ID")
    login_name = Column(String(50), nullable=False, unique=True, comment="登录账号（唯一，用于登录）")
    phone = Column(String(20), unique=True, comment="手机号（可选，可用于登录）")
    email = Column(String(100), unique=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希值")
    username = Column(String(50), nullable=False, comment="用户姓名/昵称")
    avatar_url = Column(String(500), comment="头像URL")
    hermes_profile = Column(String(100), nullable=True, comment="对应的 Hermes Profile 名称")
    hermes_profile_config = Column(Text, comment="Hermes Profile 配置(JSON)")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_default_password = Column(Boolean, default=True, comment="是否为默认密码（首次登录需修改）")
    is_super_admin = Column(Boolean, default=False, comment="是否为超级管理员（全局权限）")
    last_login_at = Column(DateTime, comment="最后登录时间")
    last_login_ip = Column(String(50), comment="最后登录IP")
    password_changed_at = Column(DateTime, comment="密码修改时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_department_id", "department_id"),
        Index("idx_login_name", "login_name"),
        Index("idx_phone", "phone"),
        Index("idx_hermes_profile", "hermes_profile"),
        Index("idx_is_active", "is_active"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, login_name={self.login_name}, username={self.username})>"

    def to_dict(self):
        return {
            "id": self.id,
            "department_id": self.department_id,
            "login_name": self.login_name,
            "phone": self.phone,
            "email": self.email,
            "username": self.username,
            "avatar_url": self.avatar_url,
            "hermes_profile": self.hermes_profile,
            "hermes_profile_config": self.hermes_profile_config,
            "is_active": self.is_active,
            "is_default_password": self.is_default_password,
            "is_super_admin": self.is_super_admin,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "last_login_ip": self.last_login_ip,
            "password_changed_at": self.password_changed_at.isoformat() if self.password_changed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }