from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, BigInteger, String, DateTime, Text, Boolean, Index, JSON, SmallInteger

from app.models import Base


class UserAgent(Base):
    __tablename__ = "user_agents"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="员工智能体ID")
    user_id = Column(BigInteger, nullable=False, comment="员工用户ID")
    template_id = Column(BigInteger, nullable=False, comment="绑定的模板ID")
    display_name = Column(String(100), nullable=False, comment="员工看到的智能体显示名称")
    hermes_profile = Column(String(100), nullable=False, comment="绑定的 Hermes Profile 名称")
    template_version = Column(BigInteger, nullable=False, default=1, comment="开通时使用的模板版本号")
    config_snapshot = Column(JSON, nullable=False, comment="模板配置快照（JSON），避免后续模板修改直接影响历史实例")
    
    agent_status = Column(SmallInteger, default=1, comment="智能体状态：0-待开通，1-可用，2-已停用，3-开通失败")
    activation_mode = Column(String(20), default="auto", comment="开通方式：auto-自动开通，manual-手动开通")
    
    enabled_at = Column(DateTime, comment="开通时间")
    last_used_at = Column(DateTime, comment="最近使用时间")
    disabled_at = Column(DateTime, comment="停用时间")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_user_template", "user_id", "template_id", unique=True),
        Index("idx_user_id", "user_id"),
        Index("idx_template_id", "template_id"),
        Index("idx_hermes_profile", "hermes_profile"),
        Index("idx_agent_status", "agent_status"),
        Index("idx_last_used_at", "last_used_at"),
    )

    def __repr__(self):
        return f"<UserAgent(id={self.id}, user_id={self.user_id}, hermes_profile={self.hermes_profile})>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "template_id": self.template_id,
            "display_name": self.display_name,
            "hermes_profile": self.hermes_profile,
            "template_version": self.template_version,
            "config_snapshot": self.config_snapshot,
            "agent_status": self.agent_status,
            "activation_mode": self.activation_mode,
            "enabled_at": self.enabled_at.isoformat() if self.enabled_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "disabled_at": self.disabled_at.isoformat() if self.disabled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
