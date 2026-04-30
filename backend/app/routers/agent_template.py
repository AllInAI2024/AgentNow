from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
)
from sqlalchemy.orm import Session

from app.models import User, AgentTemplate, AgentTemplateVersion
from app.schemas import (
    AgentTemplateCreate,
    AgentTemplateUpdate,
    AgentTemplateResponse,
    AgentTemplateListResponse,
    AgentTemplateVersionResponse,
    PublishTemplateRequest,
    SyncTemplateRequest,
    APIResponse,
)
from app.services.auth_service import (
    get_db,
    get_current_user,
    permission_required,
)
from app.services.agent_template_service import AgentTemplateService

router = APIRouter(prefix="/agent-templates", tags=["智能体模板管理"])


@router.get(
    "",
    response_model=APIResponse[AgentTemplateListResponse],
    summary="获取模板列表",
    description="获取所有智能体模板列表，支持分页、搜索和筛选"
)
def get_templates(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词（名称、编码、描述）"),
    status: Optional[int] = Query(None, description="模板状态：0-草稿，1-启用，2-停用"),
    is_default: Optional[bool] = Query(None, description="是否默认模板"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方式：asc 或 desc"),
    current_user: User = Depends(permission_required("agent:template:query")),
    db: Session = Depends(get_db)
):
    service = AgentTemplateService(db)
    result = service.get_template_list(
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
        is_default=is_default,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=result
    )


@router.get(
    "/{template_id}",
    response_model=APIResponse[AgentTemplateResponse],
    summary="获取模板详情",
    description="根据ID获取模板的详细信息"
)
def get_template(
    template_id: int,
    current_user: User = Depends(permission_required("agent:template:query")),
    db: Session = Depends(get_db)
):
    service = AgentTemplateService(db)
    template = service.get_template_by_id(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=AgentTemplateResponse.model_validate(template)
    )


@router.post(
    "",
    response_model=APIResponse[AgentTemplateResponse],
    summary="创建模板",
    description="创建新的智能体模板"
)
def create_template(
    template_data: AgentTemplateCreate,
    current_user: User = Depends(permission_required("agent:template:create")),
    db: Session = Depends(get_db)
):
    service = AgentTemplateService(db)
    template, message = service.create_template(
        template_data=template_data,
        created_by=current_user.id,
    )
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return APIResponse(
        code=200,
        message=message,
        data=AgentTemplateResponse.model_validate(template)
    )


@router.put(
    "/{template_id}",
    response_model=APIResponse[AgentTemplateResponse],
    summary="更新模板",
    description="更新模板的元数据信息"
)
def update_template(
    template_id: int,
    update_data: AgentTemplateUpdate,
    current_user: User = Depends(permission_required("agent:template:update")),
    db: Session = Depends(get_db)
):
    service = AgentTemplateService(db)
    template, message = service.update_template(
        template_id=template_id,
        update_data=update_data,
        user_id=current_user.id,
        is_admin=current_user.is_super_admin,
    )
    
    if not template:
        if "不存在" in message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=message
            )
    
    return APIResponse(
        code=200,
        message=message,
        data=AgentTemplateResponse.model_validate(template)
    )


@router.post(
    "/{template_id}/publish",
    response_model=APIResponse[AgentTemplateVersionResponse],
    summary="发布模板",
    description="发布模板版本，生成版本快照"
)
def publish_template(
    template_id: int,
    publish_data: PublishTemplateRequest,
    current_user: User = Depends(permission_required("agent:template:update")),
    db: Session = Depends(get_db)
):
    service = AgentTemplateService(db)
    version, message = service.publish_template(
        template_id=template_id,
        version_label=publish_data.version_label,
        change_summary=publish_data.change_summary,
        published_by=current_user.id,
    )
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return APIResponse(
        code=200,
        message=message,
        data=AgentTemplateVersionResponse.model_validate(version)
    )


@router.post(
    "/{template_id}/enable",
    response_model=APIResponse[AgentTemplateResponse],
    summary="启用模板",
    description="启用指定的模板"
)
def enable_template(
    template_id: int,
    current_user: User = Depends(permission_required("agent:template:enable")),
    db: Session = Depends(get_db)
):
    service = AgentTemplateService(db)
    template, message = service.enable_template(
        template_id=template_id,
        user_id=current_user.id,
    )
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )
    
    return APIResponse(
        code=200,
        message=message,
        data=AgentTemplateResponse.model_validate(template)
    )


@router.post(
    "/{template_id}/disable",
    response_model=APIResponse[AgentTemplateResponse],
    summary="停用模板",
    description="停用指定的模板"
)
def disable_template(
    template_id: int,
    current_user: User = Depends(permission_required("agent:template:enable")),
    db: Session = Depends(get_db)
):
    service = AgentTemplateService(db)
    template, message = service.disable_template(
        template_id=template_id,
        user_id=current_user.id,
    )
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )
    
    return APIResponse(
        code=200,
        message=message,
        data=AgentTemplateResponse.model_validate(template)
    )


@router.post(
    "/{template_id}/sync",
    response_model=APIResponse[dict],
    summary="同步模板到已开通员工",
    description="将模板最新配置同步到已开通该模板的员工智能体"
)
def sync_template(
    template_id: int,
    sync_data: SyncTemplateRequest,
    current_user: User = Depends(permission_required("agent:template:update")),
    db: Session = Depends(get_db)
):
    service = AgentTemplateService(db)
    result, message = service.sync_template(
        template_id=template_id,
        sync_mode=sync_data.sync_mode,
        user_ids=sync_data.user_ids,
        operator_id=current_user.id,
    )
    
    return APIResponse(
        code=200,
        message=message,
        data=result
    )


@router.get(
    "/{template_id}/versions",
    response_model=APIResponse[List[AgentTemplateVersionResponse]],
    summary="获取模板版本历史",
    description="获取指定模板的所有发布版本历史"
)
def get_template_versions(
    template_id: int,
    current_user: User = Depends(permission_required("agent:template:query")),
    db: Session = Depends(get_db)
):
    service = AgentTemplateService(db)
    versions = service.get_template_versions(template_id)
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=[AgentTemplateVersionResponse.model_validate(v) for v in versions]
    )
