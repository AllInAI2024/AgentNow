from typing import List, Optional
from urllib.parse import quote
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
    KnowledgeDocDetailResponse,
    KnowledgeDocListResponse,
    KnowledgeDocContentUpdate,
    KnowledgeConfigResponse,
    KnowledgeConfigUpdate,
    DeleteResult,
    UploadResult,
    ContentUpdateResult,
    AllTagsResponse,
    AllCategoriesResponse,
    FileSystemInfo,
    StatisticsResponse,
    APIResponse,
)
from app.services.auth_service import (
    get_db,
    get_current_user,
    permission_required,
)
from app.services.knowledge_service import KnowledgeService

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
    tag: Optional[str] = Query(None, description="标签"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    created_by: Optional[int] = Query(None, description="创建者ID"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方式：asc 或 desc"),
    current_user: User = Depends(permission_required("knowledge:doc:query")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    result = service.get_document_list(
        page=page,
        page_size=page_size,
        keyword=keyword,
        category=category,
        tag=tag,
        is_public=is_public,
        created_by=created_by,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=result
    )


@router.get(
    "/docs/{doc_id}",
    response_model=APIResponse[KnowledgeDocDetailResponse],
    summary="获取文档详情",
    description="根据ID获取文档的详细信息，可选择包含文档内容"
)
def get_document(
    doc_id: int,
    include_content: bool = Query(False, description="是否包含文档内容（仅文本文件）"),
    current_user: User = Depends(permission_required("knowledge:doc:detail")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    result, message = service.get_document_detail(
        doc_id=doc_id,
        include_content=include_content
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )
    
    return APIResponse(
        code=200,
        message=message,
        data=result
    )


@router.post(
    "/docs",
    response_model=APIResponse[KnowledgeDocResponse],
    summary="上传文档",
    description="上传新的文档文件"
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


@router.post(
    "/docs/markdown",
    response_model=APIResponse[KnowledgeDocResponse],
    summary="创建Markdown文档",
    description="直接创建新的Markdown文档（不通过文件上传）"
)
def create_markdown_document(
    title: str = Form(..., description="文档标题"),
    description: Optional[str] = Form(None, description="文档描述"),
    tags: Optional[str] = Form(None, description="标签列表（JSON数组格式）"),
    category: Optional[str] = Form(None, description="文档分类"),
    is_public: bool = Form(True, description="是否公开"),
    content: str = Form("", description="Markdown内容"),
    filename: Optional[str] = Form(None, description="文件名（不包含.md扩展名）"),
    current_user: User = Depends(permission_required("knowledge:doc:create")),
    db: Session = Depends(get_db)
):
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
    
    use_filename = filename or title
    
    service = KnowledgeService(db)
    doc, message = service.create_markdown_document(
        content=content,
        filename=use_filename,
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
    description="更新文档的元数据信息（标题、描述、标签、分类、公开状态）"
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
        data=KnowledgeDocResponse.model_validate(doc)
    )


@router.put(
    "/docs/{doc_id}/content",
    response_model=APIResponse[KnowledgeDocResponse],
    summary="更新文档内容",
    description="更新文本类型文档的内容（Markdown、txt等）"
)
def update_document_content(
    doc_id: int,
    update_data: KnowledgeDocContentUpdate,
    current_user: User = Depends(permission_required("knowledge:doc:update")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    doc, message = service.update_document_content(
        doc_id=doc_id,
        content=update_data.content,
        user_id=current_user.id,
        is_admin=current_user.is_super_admin,
    )
    
    if not doc:
        if "不存在" in message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message
            )
        elif "无权限" in message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
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
    description="软删除文档（可选择硬删除）"
)
def delete_document(
    doc_id: int,
    hard_delete: bool = Query(False, description="是否硬删除（永久删除，不可恢复）"),
    current_user: User = Depends(permission_required("knowledge:doc:delete")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    success, message = service.delete_document(
        doc_id=doc_id,
        user_id=current_user.id,
        is_admin=current_user.is_super_admin,
        hard_delete=hard_delete,
    )
    
    if not success:
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
        data=DeleteResult(success=success, message=message)
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
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename, safe='')}"
        }
    )


@router.get(
    "/categories",
    response_model=APIResponse[AllCategoriesResponse],
    summary="获取所有分类",
    description="获取所有已使用的文档分类"
)
def get_categories(
    current_user: User = Depends(permission_required("knowledge:doc:query")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    categories = service.get_all_categories()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=AllCategoriesResponse(
            categories=categories,
            total=len(categories)
        )
    )


@router.get(
    "/tags",
    response_model=APIResponse[AllTagsResponse],
    summary="获取所有标签",
    description="获取所有已使用的文档标签"
)
def get_tags(
    current_user: User = Depends(permission_required("knowledge:doc:query")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    tags = service.get_all_tags()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=AllTagsResponse(
            tags=tags,
            total=len(tags)
        )
    )


@router.get(
    "/statistics",
    response_model=APIResponse[StatisticsResponse],
    summary="获取知识库统计信息",
    description="获取知识库的统计信息（文档数量、大小、分类、标签等）"
)
def get_statistics(
    current_user: User = Depends(permission_required("knowledge:config:view")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    stats = service.get_statistics()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=StatisticsResponse(**stats)
    )


@router.get(
    "/storage",
    response_model=APIResponse[FileSystemInfo],
    summary="获取存储信息",
    description="获取文件系统存储信息（总文件数、总大小、可用空间等"
)
def get_storage_info(
    current_user: User = Depends(permission_required("knowledge:config:view")),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    info = service.get_storage_info()
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="无法获取存储信息"
        )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=FileSystemInfo(
            base_path=info.get("base_path", ""),
            total_files=info.get("total_files", 0),
            total_size=info.get("total_size", 0),
            free_space=info.get("free_space", 0)
        )
    )


@router.post(
    "/sync",
    response_model=APIResponse[dict],
    summary="从存储目录同步/重建知识库索引",
    description="扫描知识库存储目录，将磁盘文件同步到知识库数据库记录中；可选清理数据库中已不存在的文件记录"
)
def sync_knowledge_index(
    dry_run: bool = Query(False, description="仅模拟，不写入数据库"),
    purge_missing: bool = Query(False, description="将数据库中缺失文件的记录标记为删除"),
    mark_public: bool = Query(True, description="同步时将文档设置为公开（仅对已存在记录生效）"),
    current_user: User = Depends(permission_required("knowledge:doc:update")),
    db: Session = Depends(get_db),
):
    service = KnowledgeService(db)
    result = service.sync_from_storage(
        user_id=current_user.id,
        dry_run=dry_run,
        purge_missing=purge_missing,
        mark_public=mark_public,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message") or "同步失败")
    return APIResponse(code=200, message="同步完成", data=result)


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
