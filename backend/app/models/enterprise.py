from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text, Index

from app.models import Base


class Enterprise(Base):
    __tablename__ = "enterprises"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="企业ID")
    name = Column(String(100), nullable=False, comment="企业名称")
    short_name = Column(String(50), comment="企业简称")
    code = Column(String(50), comment="企业代码/统一社会信用代码")
    contact_person = Column(String(50), comment="联系人")
    contact_phone = Column(String(20), comment="联系电话")
    contact_email = Column(String(100), comment="联系邮箱")
    address = Column(String(255), comment="企业地址")
    logo_url = Column(String(500), comment="企业Logo URL")
    description = Column(Text, comment="企业描述")
    industry = Column(String(100), comment="所属行业")
    scale = Column(String(50), comment="企业规模")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_verified = Column(Boolean, default=False, comment="是否认证")
    verified_at = Column(DateTime, comment="认证时间")
    verified_by = Column(BigInteger, comment="认证人ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_name", "name"),
        Index("idx_code", "code"),
        Index("idx_is_active", "is_active"),
    )

    def __repr__(self):
        return f"<Enterprise(id={self.id}, name={self.name})>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "short_name": self.short_name,
            "code": self.code,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "address": self.address,
            "logo_url": self.logo_url,
            "description": self.description,
            "industry": self.industry,
            "scale": self.scale,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "verified_by": self.verified_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
