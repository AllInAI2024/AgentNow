from datetime import datetime
from typing import Optional
from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, Index, SmallInteger, JSON

from app.models import Base


class AgentConversation(Base):
    __tablename__ = "agent_conversations"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="会话ID")
    user_id = Column(BigInteger, nullable=False, comment="员工用户ID")
    user_agent_id = Column(BigInteger, nullable=False, comment="员工智能体ID")
    hermes_profile = Column(String(100), nullable=False, comment="会话所属 Hermes Profile")
    hermes_conversation_id = Column(String(100), comment="Hermes 侧会话ID（如有）")
    hermes_response_id = Column(String(100), comment="Hermes 最新响应ID（如使用 Responses API）")
    
    title = Column(String(255), comment="会话标题")
    current_stage = Column(String(50), default="chatting", comment="当前阶段：chatting/outline_draft/outline_confirmed/template_select/final_generating/completed")
    status = Column(SmallInteger, default=1, comment="会话状态：0-草稿，1-进行中，2-已完成，3-已归档，4-失败")
    
    outline_confirmed = Column(Boolean, default=False, comment="是否已确认大纲")
    template_confirmed = Column(Boolean, default=False, comment="是否已确认展示模板/风格")
    final_generation_confirmed = Column(Boolean, default=False, comment="是否已确认正式生成文件")
    
    message_count = Column(BigInteger, default=0, comment="消息总数")
    latest_user_input = Column(String(1000), comment="最近一条用户输入摘要")
    requirements_json = Column(JSON, comment="需求收集结果（JSON）")
    structured_result_json = Column(JSON, comment="最近一次结构化结果缓存（JSON）")
    messages_json = Column(JSON, comment="会话消息缓存（JSON数组）")
    final_file_id = Column(BigInteger, comment="最终生成文件ID（关联生成文件表）")
    
    started_at = Column(DateTime, default=datetime.utcnow, comment="会话开始时间")
    last_message_at = Column(DateTime, default=datetime.utcnow, comment="最后消息时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_profile_conversation", "hermes_profile", "hermes_conversation_id", unique=True),
        Index("idx_profile_response", "hermes_profile", "hermes_response_id", unique=True),
        Index("idx_user_id", "user_id"),
        Index("idx_user_agent_id", "user_agent_id"),
        Index("idx_hermes_profile", "hermes_profile"),
        Index("idx_status", "status"),
        Index("idx_current_stage", "current_stage"),
        Index("idx_last_message_at", "last_message_at"),
    )

    def __repr__(self):
        return f"<AgentConversation(id={self.id}, title={self.title}, status={self.status})>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_agent_id": self.user_agent_id,
            "hermes_profile": self.hermes_profile,
            "hermes_conversation_id": self.hermes_conversation_id,
            "hermes_response_id": self.hermes_response_id,
            "title": self.title,
            "current_stage": self.current_stage,
            "status": self.status,
            "outline_confirmed": self.outline_confirmed,
            "template_confirmed": self.template_confirmed,
            "final_generation_confirmed": self.final_generation_confirmed,
            "message_count": self.message_count,
            "latest_user_input": self.latest_user_input,
            "requirements_json": self.requirements_json,
            "structured_result_json": self.structured_result_json,
            "messages_json": self.messages_json,
            "final_file_id": self.final_file_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
