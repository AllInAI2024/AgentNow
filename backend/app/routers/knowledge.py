from typing import List, Optional
from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status, 
    Query, 
    UploadFile, 
    File, 
    Form,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import json

from app.models import User, KnowledgeConfig
from app.schemas import (
    KnowledgeDocCreate,
    KnowledgeDocUpdate,
    KnowledgeDocResponse,
    KnowledgeDocListResponse,
    KnowledgeConfigResponse,
    KnowledgeConfigUpdate,
    SyncStatusResponse,
    DeleteResult,
    APIResponse,
)
from app.services.auth_service import (
    get_db,
    get_current_user,
    permission_required,
)
from app.services.knowledge_service import KnowledgeService
from app.services.hermes_sync_service import HermesSyncService

router = APIRouter(prefix="/knowledge", tags=["知识库管理"])


@router.get(
    "/docs",
    response_model=APIResponse[KnowledgeDocListResponse],
    summary="获取文档列表",
    description="获取所有文档列表，支持分页、搜索和筛选"
)
def get_documents(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词（标题、文件名、描述）"),
    category: Optional[str] = Query(None, description="文档分类"),
    status: Optional[int] = Query(None, description="状态：1-已上传，2-已同步到Hermes，3-处理中，4-失败"),
    sync_status: Optional[int] = Query(None, description="同步状态：0-未同步，1-已同步，2-同步失败"),
    current_user: User = Depends(permission_required("knowledge:doc:query")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    result = service.get_document_list(
        page=page,
        page_size=page_size,
        keyword=keyword,
        category=category,
        status=status,
        sync_status=sync_status,
    )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=result
    )


@router.get(
    "/docs/{doc_id}",
    response_model=APIResponse[KnowledgeDocResponse],
    summary="获取文档详情",
    description="根据ID获取文档的详细信息"
)
def get_document(
    doc_id: int,
    current_user: User = Depends(permission_required("knowledge:doc:detail")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    doc = service.get_document_by_id(doc_id)
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=KnowledgeDocResponse.model_validate(doc)
    )


@router.post(
    "/docs",
    response_model=APIResponse[KnowledgeDocResponse],
    summary="上传文档",
    description="上传新的文档，自动同步到Hermes（如果启用自动同步）"
)
async def upload_document(
    title: str = Form(..., description="文档标题"),
    description: Optional[str] = Form(None, description="文档描述"),
    tags: Optional[str] = Form(None, description="标签列表（JSON数组格式）"),
    category: Optional[str] = Form(None, description="文档分类"),
    is_public: bool = Form(True, description="是否公开"),
    file: UploadFile = File(..., description="上传的文件"),
    current_user: User = Depends(permission_required("knowledge:doc:create")),
    db: Session = Depends(get_db)
):
    file_content = await file.read()
    original_filename = file.filename or "unknown"
    
    tags_list = []
    if tags:
        try:
            tags_list = json.loads(tags)
            if not isinstance(tags_list, list):
                tags_list = []
        except json.JSONDecodeError:
            tags_list = []
    
    doc_data = KnowledgeDocCreate(
        title=title,
        description=description,
        tags=tags_list,
        category=category,
        is_public=is_public,
    )
    
    service = KnowledgeService(db)
    doc, message = service.create_document(
        file_content=file_content,
        original_filename=original_filename,
        doc_data=doc_data,
        created_by=current_user.id,
    )
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return APIResponse(
        code=200,
        message=message,
        data=KnowledgeDocResponse.model_validate(doc)
    )


@router.put(
    "/docs/{doc_id}",
    response_model=APIResponse[KnowledgeDocResponse],
    summary="更新文档信息",
    description="更新文档的元数据信息（不更新文件本身）"
)
def update_document(
    doc_id: int,
    update_data: KnowledgeDocUpdate,
    current_user: User = Depends(permission_required("knowledge:doc:update")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    doc, message = service.update_document(
        doc_id=doc_id,
        update_data=update_data,
        user_id=current_user.id,
        is_admin=current_user.is_super_admin,
    )
    
    if not doc:
        if "not found" in message.lower():
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
        data=KnowledgeDocResponse.model_validate(doc)
    )


@router.delete(
    "/docs/{doc_id}",
    response_model=APIResponse[DeleteResult],
    summary="删除文档",
    description="软删除文档，同时从Hermes同步目录移除"
)
def delete_document(
    doc_id: int,
    current_user: User = Depends(permission_required("knowledge:doc:delete")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    success, message = service.delete_document(
        doc_id=doc_id,
        user_id=current_user.id,
        is_admin=current_user.is_super_admin,
    )
    
    if not success:
        if "not found" in message.lower():
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
        data=DeleteResult(success=True, message=message)
    )


@router.get(
    "/docs/{doc_id}/download",
    summary="下载文档",
    description="下载文档文件"
)
def download_document(
    doc_id: int,
    current_user: User = Depends(permission_required("knowledge:doc:download")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    file_content, mime_type, filename = service.download_document(doc_id)
    
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=filename
        )
    
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
        }
    )


@router.post(
    "/docs/{doc_id}/sync",
    response_model=APIResponse[SyncStatusResponse],
    summary="手动同步文档到Hermes",
    description="手动将文档同步到Hermes workspace目录"
)
def sync_document(
    doc_id: int,
    current_user: User = Depends(permission_required("knowledge:doc:sync")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    success, message = service.sync_document(doc_id)
    
    doc = service.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    return APIResponse(
        code=200 if success else 500,
        message=message,
        data=SyncStatusResponse(
            doc_id=doc.id,
            sync_status=doc.sync_status,
            synced_at=doc.synced_at,
            message=message,
        )
    )


@router.get(
    "/categories",
    response_model=APIResponse[List[str]],
    summary="获取文档分类列表",
    description="获取所有已使用的文档分类"
)
def get_categories(
    current_user: User = Depends(permission_required("knowledge:doc:query")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    categories = service.get_categories()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=categories
    )


@router.get(
    "/configs",
    response_model=APIResponse[List[KnowledgeConfigResponse]],
    summary="获取知识库配置",
    description="获取所有知识库配置项"
)
def get_configs(
    current_user: User = Depends(permission_required("knowledge:config:view")),
    db: Session = Depends(get_db)
):
    configs = db.query(KnowledgeConfig).order_by(KnowledgeConfig.id).all()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=[KnowledgeConfigResponse.model_validate(c) for c in configs]
    )


@router.put(
    "/configs/{config_id}",
    response_model=APIResponse[KnowledgeConfigResponse],
    summary="更新知识库配置",
    description="更新指定的知识库配置项"
)
def update_config(
    config_id: int,
    update_data: KnowledgeConfigUpdate,
    current_user: User = Depends(permission_required("knowledge:config:edit")),
    db: Session = Depends(get_db)
):
    config = db.query(KnowledgeConfig).filter(KnowledgeConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    config.config_value = update_data.config_value
    db.commit()
    db.refresh(config)
    
    return APIResponse(
        code=200,
        message="更新成功",
        data=KnowledgeConfigResponse.model_validate(config)
    )


@router.get(
    "/hermes-files",
    response_model=APIResponse[List[dict]],
    summary="获取Hermes workspace文件列表",
    description="获取Hermes workspace目录中的所有文件"
)
def get_hermes_files(
    current_user: User = Depends(permission_required("knowledge:config:view")),
    db: Session = Depends(get_db)
):
    sync_service = HermesSyncService(db)
    files = sync_service.list_hermes_files()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=[{
            "filename": f["filename"],
            "size": f["size"],
            "modified": f["modified"].isoformat() if f["modified"] else None
        } for f in files]
    )
