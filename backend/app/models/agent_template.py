from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, BigInteger, String, DateTime, Text, Boolean, Index, JSON, SmallInteger

from app.models import Base


class AgentTemplate(Base):
    __tablename__ = "agent_templates"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="模板ID")
    code = Column(String(100), nullable=False, unique=True, comment="模板编码（英文唯一标识，如 ppt_assistant）")
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(String(1000), comment="模板描述")
    template_type = Column(String(50), default="business", comment="模板类型：business-业务模板，system-系统模板")
    
    role_prompt = Column(Text, comment="角色说明提示词")
    system_prompt = Column(Text, comment="系统提示词")
    welcome_message = Column(Text, comment="欢迎语")
    
    knowledge_scope = Column(String(50), default="category", comment="知识范围类型：none/global/category/custom")
    knowledge_categories = Column(JSON, comment="允许使用的知识分类列表（JSON数组）")
    
    tool_policy = Column(JSON, comment="工具白名单与工具策略（JSON）")
    output_rules = Column(JSON, comment="输出格式和输出约束（JSON）")
    confirmation_rules = Column(JSON, comment="用户确认规则（JSON）")
    interaction_rules = Column(JSON, comment="关键交互规则（JSON）")
    workflow_hints = Column(JSON, comment="轻量流程提示（JSON，为后续流程编排预留）")
    model_settings = Column("model_config", JSON, comment="模型相关配置（JSON，可选）")
    
    status = Column(SmallInteger, default=0, comment="模板状态：0-草稿，1-启用，2-停用")
    is_default = Column(Boolean, default=False, comment="是否为默认模板")
    version = Column(BigInteger, default=1, comment="当前版本号")
    
    created_by = Column(BigInteger, comment="创建人用户ID")
    updated_by = Column(BigInteger, comment="最后更新人用户ID")
    published_at = Column(DateTime, comment="最近发布时间")
    
    deleted_at = Column(DateTime, comment="删除时间（软删除）")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_agent_template_code", "code", unique=True),
        Index("idx_template_type", "template_type"),
        Index("idx_status", "status"),
        Index("idx_is_default", "is_default"),
        Index("idx_created_by", "created_by"),
        Index("idx_deleted_at", "deleted_at"),
    )

    def __repr__(self):
        return f"<AgentTemplate(id={self.id}, code={self.code}, name={self.name})>"

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type,
            "role_prompt": self.role_prompt,
            "system_prompt": self.system_prompt,
            "welcome_message": self.welcome_message,
            "knowledge_scope": self.knowledge_scope,
            "knowledge_categories": self.knowledge_categories,
            "tool_policy": self.tool_policy,
            "output_rules": self.output_rules,
            "confirmation_rules": self.confirmation_rules,
            "interaction_rules": self.interaction_rules,
            "workflow_hints": self.workflow_hints,
            "model_settings": self.model_settings,
            "status": self.status,
            "is_default": self.is_default,
            "version": self.version,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_snapshot(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type,
            "role_prompt": self.role_prompt,
            "system_prompt": self.system_prompt,
            "welcome_message": self.welcome_message,
            "knowledge_scope": self.knowledge_scope,
            "knowledge_categories": self.knowledge_categories,
            "tool_policy": self.tool_policy,
            "output_rules": self.output_rules,
            "confirmation_rules": self.confirmation_rules,
            "interaction_rules": self.interaction_rules,
            "workflow_hints": self.workflow_hints,
            "model_settings": self.model_settings,
            "version": self.version,
        }
