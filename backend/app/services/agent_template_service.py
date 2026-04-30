import math
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import AgentTemplate, AgentTemplateVersion, UserAgent
from app.schemas import (
    AgentTemplateCreate,
    AgentTemplateUpdate,
    AgentTemplateListResponse,
    AgentTemplateResponse,
)


class AgentTemplateService:
    def __init__(self, db: Session):
        self.db = db

    def get_template_by_id(self, template_id: int) -> Optional[AgentTemplate]:
        return self.db.query(AgentTemplate).filter(
            AgentTemplate.id == template_id,
            AgentTemplate.deleted_at.is_(None)
        ).first()

    def get_template_by_code(self, code: str) -> Optional[AgentTemplate]:
        return self.db.query(AgentTemplate).filter(
            AgentTemplate.code == code,
            AgentTemplate.deleted_at.is_(None)
        ).first()

    def get_default_template(self) -> Optional[AgentTemplate]:
        return self.db.query(AgentTemplate).filter(
            AgentTemplate.is_default == True,
            AgentTemplate.status == 1,
            AgentTemplate.deleted_at.is_(None)
        ).first()

    def get_template_list(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[int] = None,
        is_default: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> AgentTemplateListResponse:
        query = self.db.query(AgentTemplate).filter(AgentTemplate.deleted_at.is_(None))
        
        if keyword:
            query = query.filter(
                or_(
                    AgentTemplate.name.contains(keyword),
                    AgentTemplate.code.contains(keyword),
                    AgentTemplate.description.contains(keyword),
                )
            )
        
        if status is not None:
            query = query.filter(AgentTemplate.status == status)
        
        if is_default is not None:
            query = query.filter(AgentTemplate.is_default == is_default)
        
        sort_column = getattr(AgentTemplate, sort_by, AgentTemplate.created_at)
        if sort_order.lower() == "desc":
            sort_column = sort_column.desc()
        
        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        
        offset = (page - 1) * page_size
        templates = query.order_by(sort_column).offset(offset).limit(page_size).all()
        
        return AgentTemplateListResponse(
            items=[AgentTemplateResponse.model_validate(t) for t in templates],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def create_template(
        self,
        template_data: AgentTemplateCreate,
        created_by: int,
    ) -> Tuple[Optional[AgentTemplate], str]:
        existing = self.get_template_by_code(template_data.code)
        if existing:
            return None, f"模板编码 '{template_data.code}' 已存在"
        
        if template_data.is_default:
            existing_default = self.get_default_template()
            if existing_default:
                existing_default.is_default = False
                self.db.commit()
        
        template = AgentTemplate(
            code=template_data.code,
            name=template_data.name,
            description=template_data.description,
            template_type=template_data.template_type,
            role_prompt=template_data.role_prompt,
            system_prompt=template_data.system_prompt,
            welcome_message=template_data.welcome_message,
            knowledge_scope=template_data.knowledge_scope,
            knowledge_categories=template_data.knowledge_categories if template_data.knowledge_categories else [],
            tool_policy=template_data.tool_policy if template_data.tool_policy else {},
            output_rules=template_data.output_rules if template_data.output_rules else {},
            confirmation_rules=template_data.confirmation_rules if template_data.confirmation_rules else {},
            interaction_rules=template_data.interaction_rules if template_data.interaction_rules else {},
            workflow_hints=template_data.workflow_hints if template_data.workflow_hints else {},
            model_config=template_data.model_config if template_data.model_config else {},
            status=0,
            is_default=template_data.is_default,
            version=1,
            created_by=created_by,
            updated_by=created_by,
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        return template, "创建成功"

    def update_template(
        self,
        template_id: int,
        update_data: AgentTemplateUpdate,
        user_id: int,
        is_admin: bool = False,
    ) -> Tuple[Optional[AgentTemplate], str]:
        template = self.get_template_by_id(template_id)
        if not template:
            return None, "模板不存在"
        
        if update_data.is_default:
            existing_default = self.get_default_template()
            if existing_default and existing_default.id != template_id:
                existing_default.is_default = False
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(template, key, value)
        
        template.updated_by = user_id
        
        self.db.commit()
        self.db.refresh(template)
        
        return template, "更新成功"

    def publish_template(
        self,
        template_id: int,
        version_label: Optional[str],
        change_summary: Optional[str],
        published_by: int,
    ) -> Tuple[Optional[AgentTemplateVersion], str]:
        template = self.get_template_by_id(template_id)
        if not template:
            return None, "模板不存在"
        
        latest_version = self.db.query(AgentTemplateVersion).filter(
            AgentTemplateVersion.template_id == template_id
        ).order_by(AgentTemplateVersion.version_no.desc()).first()
        
        next_version = latest_version.version_no + 1 if latest_version else 1
        
        version = AgentTemplateVersion(
            template_id=template_id,
            version_no=next_version,
            version_label=version_label,
            change_summary=change_summary,
            template_snapshot=template.to_snapshot(),
            published_by=published_by,
            published_at=datetime.utcnow(),
        )
        
        template.version = next_version
        template.published_at = datetime.utcnow()
        template.updated_by = published_by
        
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        
        return version, "发布成功"

    def enable_template(
        self,
        template_id: int,
        user_id: int,
    ) -> Tuple[Optional[AgentTemplate], str]:
        template = self.get_template_by_id(template_id)
        if not template:
            return None, "模板不存在"
        
        template.status = 1
        template.updated_by = user_id
        
        self.db.commit()
        self.db.refresh(template)
        
        return template, "启用成功"

    def disable_template(
        self,
        template_id: int,
        user_id: int,
    ) -> Tuple[Optional[AgentTemplate], str]:
        template = self.get_template_by_id(template_id)
        if not template:
            return None, "模板不存在"
        
        template.status = 2
        template.updated_by = user_id
        
        self.db.commit()
        self.db.refresh(template)
        
        return template, "停用成功"

    def sync_template(
        self,
        template_id: int,
        sync_mode: str,
        user_ids: Optional[List[int]],
        operator_id: int,
    ) -> Tuple[Dict[str, Any], str]:
        template = self.get_template_by_id(template_id)
        if not template:
            return {"synced_count": 0}, "模板不存在"
        
        query = self.db.query(UserAgent).filter(UserAgent.template_id == template_id)
        
        if sync_mode == "selected_users" and user_ids:
            query = query.filter(UserAgent.user_id.in_(user_ids))
        
        user_agents = query.all()
        synced_count = 0
        latest_snapshot = template.to_snapshot()
        
        for ua in user_agents:
            ua.config_snapshot = latest_snapshot
            ua.template_version = template.version
            synced_count += 1
        
        self.db.commit()
        
        return {
            "synced_count": synced_count,
            "template_id": template_id,
            "new_version": template.version,
        }, "同步成功"

    def get_template_versions(self, template_id: int) -> List[AgentTemplateVersion]:
        return self.db.query(AgentTemplateVersion).filter(
            AgentTemplateVersion.template_id == template_id
        ).order_by(AgentTemplateVersion.version_no.desc()).all()
