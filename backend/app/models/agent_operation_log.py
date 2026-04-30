from datetime import datetime
from typing import Optional
from sqlalchemy import Column, BigInteger, String, DateTime, Index, JSON, Text, SmallInteger

from app.models import Base


class AgentOperationLog(Base):
    __tablename__ = "agent_operation_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日志ID")
    operator_user_id = Column(BigInteger, nullable=False, comment="操作人用户ID")
    target_type = Column(String(50), nullable=False, comment="目标类型：template/user_agent/conversation/file")
    target_id = Column(BigInteger, comment="目标ID")
    
    action = Column(String(100), nullable=False, comment="操作编码，如 template:create、agent:enable、ppt:generate")
    action_name = Column(String(100), comment="操作名称")
    
    result_status = Column(SmallInteger, default=1, comment="执行结果：1-成功，0-失败")
    details = Column(JSON, comment="操作详情（JSON）")
    error_message = Column(Text, comment="失败原因")
    
    ip_address = Column(String(50), comment="操作者IP")
    user_agent = Column(String(500), comment="请求来源 User-Agent")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    __table_args__ = (
        Index("idx_operator_user_id", "operator_user_id"),
        Index("idx_target_type_target_id", "target_type", "target_id"),
        Index("idx_action", "action"),
        Index("idx_result_status", "result_status"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<AgentOperationLog(id={self.id}, action={self.action}, result_status={self.result_status})>"

    def to_dict(self):
        return {
            "id": self.id,
            "operator_user_id": self.operator_user_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "action": self.action,
            "action_name": self.action_name,
            "result_status": self.result_status,
            "details": self.details,
            "error_message": self.error_message,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
