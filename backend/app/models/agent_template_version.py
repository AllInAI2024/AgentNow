from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, BigInteger, String, DateTime, Text, Boolean, Index, JSON

from app.models import Base


class AgentTemplateVersion(Base):
    __tablename__ = "agent_template_versions"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="版本ID")
    template_id = Column(BigInteger, nullable=False, comment="模板ID")
    version_no = Column(BigInteger, nullable=False, comment="版本号")
    version_label = Column(String(100), comment="版本标签，如 v1.0、初版、销售优化版")
    change_summary = Column(String(1000), comment="版本变更说明")
    template_snapshot = Column(JSON, nullable=False, comment="模板完整快照（JSON）")
    published_by = Column(BigInteger, comment="发布人用户ID")
    published_at = Column(DateTime, comment="发布时间")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    __table_args__ = (
        Index("idx_template_version", "template_id", "version_no", unique=True),
        Index("idx_template_id", "template_id"),
        Index("idx_published_by", "published_by"),
    )

    def __repr__(self):
        return f"<AgentTemplateVersion(id={self.id}, template_id={self.template_id}, version_no={self.version_no})>"

    def to_dict(self):
        return {
            "id": self.id,
            "template_id": self.template_id,
            "version_no": self.version_no,
            "version_label": self.version_label,
            "change_summary": self.change_summary,
            "template_snapshot": self.template_snapshot,
            "published_by": self.published_by,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
