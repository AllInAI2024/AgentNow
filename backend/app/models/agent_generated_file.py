from datetime import datetime
from typing import Optional
from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, Index, Text, SmallInteger

from app.models import Base


class AgentGeneratedFile(Base):
    __tablename__ = "agent_generated_files"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="生成文件ID")
    user_id = Column(BigInteger, nullable=False, comment="员工用户ID")
    user_agent_id = Column(BigInteger, nullable=False, comment="员工智能体ID")
    conversation_id = Column(BigInteger, comment="来源会话ID")
    
    file_type = Column(String(50), nullable=False, comment="文件类型，如 pptx、pdf、md")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_path = Column(String(1000), nullable=False, comment="文件存储路径")
    file_size = Column(BigInteger, default=0, comment="文件大小（字节）")
    mime_type = Column(String(100), comment="MIME类型")
    
    template_name = Column(String(100), comment="生成时使用的模板名称或母版名称")
    source_type = Column(String(50), default="generated", comment="来源类型：generated-自动生成，regenerated-重新生成，manual_upload-人工上传")
    version_no = Column(BigInteger, default=1, comment="文件版本号，同一会话多次生成时递增")
    
    generation_status = Column(SmallInteger, default=1, comment="生成状态：0-生成中，1-成功，2-失败")
    error_message = Column(Text, comment="失败原因")
    
    deleted_at = Column(DateTime, comment="删除时间（软删除）")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_user_agent_id", "user_agent_id"),
        Index("idx_conversation_id", "conversation_id"),
        Index("idx_file_type", "file_type"),
        Index("idx_generation_status", "generation_status"),
        Index("idx_deleted_at", "deleted_at"),
    )

    def __repr__(self):
        return f"<AgentGeneratedFile(id={self.id}, file_name={self.file_name}, file_type={self.file_type})>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_agent_id": self.user_agent_id,
            "conversation_id": self.conversation_id,
            "file_type": self.file_type,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "template_name": self.template_name,
            "source_type": self.source_type,
            "version_no": self.version_no,
            "generation_status": self.generation_status,
            "error_message": self.error_message,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
