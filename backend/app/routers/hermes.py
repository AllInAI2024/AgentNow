import tempfile
import zipfile
import tarfile
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from pathlib import Path

from app.models import User
from app.schemas.hermes import (
    HermesOverviewResponse,
    VersionCheckResponse,
    UpdateProgress,
    SkillListResponse,
    SkillDetailResponse,
    SkillInstallParams,
    SkillCreateParams,
    MCPServiceListResponse,
    MCPServiceDetailResponse,
    MCPServiceTestResult,
    BuiltinToolListResponse,
    MemoryResponse,
    ProfileMemoryListResponse,
    ConfigResponse,
    ConfigProfileListResponse,
    HermesKnowledgeStatus,
    HermesKnowledgeListResponse,
    HermesKnowledgeDocDetail,
    HermesAuditLogListResponse,
)
from app.schemas.user import APIResponse
from app.services.auth_service import get_db, get_current_user
from app.services.hermes_service import hermes_service

router = APIRouter(prefix="/hermes", tags=["Hermes 系统管理"])


@router.get(
    "/overview",
    response_model=APIResponse[HermesOverviewResponse],
    summary="获取系统概览",
    description="获取 Hermes 系统的整体运行状态、统计信息和健康状态"
)
async def get_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    overview = await hermes_service.get_overview(db)
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=overview
    )


@router.get(
    "/health",
    response_model=APIResponse[dict],
    summary="获取健康状态",
    description="获取 Hermes 系统的健康状态详情"
)
async def get_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    health_status = hermes_service.get_health_status(db)
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=health_status.model_dump()
    )


@router.get(
    "/version/check",
    response_model=APIResponse[VersionCheckResponse],
    summary="检查版本更新",
    description="检查 Hermes 是否有新版本可用"
)
async def check_version(
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    version_info = await hermes_service.check_version()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=version_info
    )


@router.post(
    "/version/update",
    response_model=APIResponse[UpdateProgress],
    summary="开始版本升级",
    description="启动 Hermes 版本升级流程"
)
async def start_update(
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    version_info = await hermes_service.check_version()
    
    if not version_info.has_update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前已是最新版本，无需升级"
        )
    
    progress = await hermes_service.start_update()
    
    return APIResponse(
        code=200,
        message="升级已启动",
        data=progress
    )


@router.get(
    "/version/update/progress",
    response_model=APIResponse[UpdateProgress],
    summary="获取升级进度",
    description="获取当前版本升级的进度状态"
)
async def get_update_progress(
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    progress = hermes_service.get_update_progress()
    
    if progress is None:
        return APIResponse(
            code=200,
            message="没有进行中的升级",
            data=None
        )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=progress
    )


@router.get(
    "/skills",
    response_model=APIResponse[SkillListResponse],
    summary="获取技能列表",
    description="获取 Hermes 已安装的技能列表，支持分类和搜索筛选"
)
async def get_skills(
    category: Optional[str] = Query(None, description="按分类筛选"),
    search: Optional[str] = Query(None, description="搜索关键词（名称、描述、标签）"),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    skill_list = hermes_service.list_skills(category=category, search=search)
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=skill_list
    )


@router.get(
    "/skills/{skill_name}",
    response_model=APIResponse[SkillDetailResponse],
    summary="获取技能详情",
    description="获取指定技能的详细信息"
)
async def get_skill_detail(
    skill_name: str,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    skill_detail = hermes_service.get_skill_detail(skill_name)
    
    if skill_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"技能 '{skill_name}' 不存在"
        )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=skill_detail
    )


@router.post(
    "/skills/install",
    response_model=APIResponse[dict],
    summary="安装技能",
    description="从技能仓库安装新技能"
)
async def install_skill(
    params: SkillInstallParams,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    result = hermes_service.install_skill(params)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "安装失败")
        )
    
    return APIResponse(
        code=200,
        message="安装成功",
        data=result
    )


@router.post(
    "/skills/{skill_name}/uninstall",
    response_model=APIResponse[dict],
    summary="卸载技能",
    description="卸载已安装的技能"
)
async def uninstall_skill(
    skill_name: str,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    result = hermes_service.uninstall_skill(skill_name)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "卸载失败")
        )
    
    return APIResponse(
        code=200,
        message="卸载成功",
        data=result
    )


@router.post(
    "/skills/create",
    response_model=APIResponse[dict],
    summary="创建新技能",
    description="创建自定义技能"
)
async def create_skill(
    params: SkillCreateParams,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    result = hermes_service.create_skill(params)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "创建失败")
        )
    
    return APIResponse(
        code=200,
        message="创建成功",
        data=result
    )


@router.post(
    "/skills/{skill_name}/update",
    response_model=APIResponse[dict],
    summary="更新技能",
    description="更新已安装的技能到最新版本"
)
async def update_skill(
    skill_name: str,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    result = hermes_service.update_skill(skill_name)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "更新失败")
        )
    
    return APIResponse(
        code=200,
        message="更新成功",
        data=result
    )


@router.get(
    "/skills/available/browse",
    response_model=APIResponse[list],
    summary="浏览可用技能",
    description="浏览技能仓库中可用的技能"
)
async def browse_available_skills(
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    skills = hermes_service.search_available_skills()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=skills
    )


def _extract_skill_from_archive(archive_path: Path, extract_dir: Path) -> Optional[Path]:
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extract_dir)
    elif archive_path.suffix in [".tar", ".gz", ".tgz"]:
        mode = "r:gz" if archive_path.suffix in [".gz", ".tgz"] else "r"
        with tarfile.open(archive_path, mode) as tf:
            tf.extractall(extract_dir)
    else:
        return None
    
    skill_dir: Optional[Path] = None
    for item in extract_dir.iterdir():
        if item.is_dir():
            skill_md = item / "SKILL.md"
            if skill_md.exists():
                skill_dir = item
                break
    
    if skill_dir is None:
        skill_md = extract_dir / "SKILL.md"
        if skill_md.exists():
            skill_dir = extract_dir
    
    return skill_dir


@router.post(
    "/skills/upload",
    response_model=APIResponse[dict],
    summary="上传技能",
    description="上传技能压缩包（.zip 或 .tar.gz）并安装"
)
async def upload_skill(
    file: UploadFile = File(..., description="技能压缩包文件"),
    category: Optional[str] = Form(None, description="安装到的分类目录"),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    allowed_types = [
        "application/zip",
        "application/x-zip-compressed",
        "application/gzip",
        "application/x-gzip",
        "application/x-tar",
    ]
    
    file_ext = Path(file.filename or "").suffix.lower()
    allowed_extensions = [".zip", ".tar", ".gz", ".tgz"]
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式。支持的格式：{', '.join(allowed_extensions)}"
        )
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        archive_path = temp_path / f"skill{file_ext}"
        
        content = await file.read()
        with open(archive_path, "wb") as f:
            f.write(content)
        
        extract_dir = temp_path / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        skill_dir = _extract_skill_from_archive(archive_path, extract_dir)
        
        if skill_dir is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="压缩包中未找到有效的技能目录（需要包含 SKILL.md 文件）"
            )
        
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="技能目录中缺少 SKILL.md 文件"
            )
        
        result = hermes_service.install_skill_from_directory(
            skill_dir, 
            category or "custom"
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "安装失败")
            )
        
        return APIResponse(
            code=200,
            message="技能上传成功",
            data=result
        )


@router.get(
    "/mcp",
    response_model=APIResponse[MCPServiceListResponse],
    summary="获取 MCP 服务列表",
    description="获取 Hermes 配置的所有 MCP 服务列表，包括状态、类型、工具数等信息"
)
async def get_mcp_services(
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    mcp_list = hermes_service.list_mcp_services()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=mcp_list
    )


@router.get(
    "/mcp/{service_name}",
    response_model=APIResponse[MCPServiceDetailResponse],
    summary="获取 MCP 服务详情",
    description="获取指定 MCP 服务的详细信息，包括配置和工具列表"
)
async def get_mcp_service_detail(
    service_name: str,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    service_detail = hermes_service.get_mcp_service_detail(service_name)
    
    if service_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP 服务 '{service_name}' 不存在"
        )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=service_detail
    )


@router.post(
    "/mcp/{service_name}/test",
    response_model=APIResponse[MCPServiceTestResult],
    summary="测试 MCP 服务连接",
    description="测试指定 MCP 服务的连接状态，检查是否能正常获取工具列表"
)
async def test_mcp_service(
    service_name: str,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    test_result = hermes_service.test_mcp_service(service_name)
    
    return APIResponse(
        code=200,
        message="测试完成" if test_result.success else "测试失败",
        data=test_result
    )


@router.get(
    "/tools",
    response_model=APIResponse[BuiltinToolListResponse],
    summary="获取内置工具列表",
    description="获取 Hermes 所有内置工具列表，支持按分类和关键词筛选"
)
async def get_builtin_tools(
    category: Optional[str] = Query(None, description="按工具分类筛选"),
    search: Optional[str] = Query(None, description="搜索关键词（工具名称、显示名称、描述）"),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    tool_list = hermes_service.list_builtin_tools(category=category, search=search)
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=tool_list
    )


@router.get(
    "/memory/list",
    response_model=APIResponse[ProfileMemoryListResponse],
    summary="获取所有 Profile 的记忆列表",
    description="获取所有 Profile 的记忆文件状态概览，包括 MEMORY.md 和 USER.md 的使用情况"
)
async def get_memory_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    memory_list = hermes_service.list_profile_memories(db)
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=memory_list
    )


@router.get(
    "/profiles/{profile_name}/memory",
    response_model=APIResponse[MemoryResponse],
    summary="获取指定 Profile 的记忆详情",
    description="获取指定 Profile 的 MEMORY.md 和 USER.md 的完整内容和解析后的记忆条目"
)
async def get_profile_memory(
    profile_name: str,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    memory = hermes_service.get_memory(profile_name)
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=memory
    )


@router.get(
    "/config/profiles",
    response_model=APIResponse[ConfigProfileListResponse],
    summary="获取配置 Profile 列表",
    description="获取所有可用的配置 Profile 列表，包括全局配置和各 Profile 配置"
)
async def get_config_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    profiles = hermes_service.list_config_profiles(db)
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=profiles
    )


@router.get(
    "/config",
    response_model=APIResponse[ConfigResponse],
    summary="获取全局配置",
    description="获取 Hermes 全局配置信息（config.yaml 和 .env），敏感信息已脱敏"
)
async def get_global_config(
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    config = hermes_service.get_config("global")
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=config
    )


@router.get(
    "/config/{profile_name}",
    response_model=APIResponse[ConfigResponse],
    summary="获取指定 Profile 的配置",
    description="获取指定 Profile 的配置信息，敏感信息已脱敏"
)
async def get_profile_config(
    profile_name: str,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    config = hermes_service.get_config(profile_name)
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=config
    )


@router.get(
    "/knowledge/status",
    response_model=APIResponse[HermesKnowledgeStatus],
    summary="获取知识库状态",
    description="获取 Hermes 知识库的整体状态，包括文档数量、索引状态等"
)
async def get_knowledge_status(
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    knowledge_status = hermes_service.get_knowledge_status()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=knowledge_status
    )


@router.get(
    "/knowledge/documents",
    response_model=APIResponse[HermesKnowledgeListResponse],
    summary="获取知识库文档列表",
    description="获取 Hermes 知识库的文档列表，支持分页、搜索和筛选"
)
async def get_knowledge_documents(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(20, description="每页数量", ge=1, le=100),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    file_type: Optional[str] = Query(None, description="文件类型筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    doc_list = hermes_service.list_knowledge_docs(
        page=page,
        page_size=page_size,
        keyword=keyword,
        file_type=file_type,
        category=category,
    )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=doc_list
    )


@router.get(
    "/knowledge/documents/{doc_id:path}",
    response_model=APIResponse[HermesKnowledgeDocDetail],
    summary="获取文档详情",
    description="获取 Hermes 知识库中指定文档的详细信息，包括内容"
)
async def get_knowledge_document_detail(
    doc_id: str,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    doc_detail = hermes_service.get_knowledge_doc_detail(doc_id)
    
    if doc_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档 '{doc_id}' 不存在"
        )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=doc_detail
    )


@router.get(
    "/knowledge/file-types",
    response_model=APIResponse[list],
    summary="获取文件类型统计",
    description="获取知识库中各文件类型的统计信息"
)
async def get_knowledge_file_types(
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    file_types = hermes_service.get_knowledge_file_types()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=file_types
    )


@router.get(
    "/audit",
    response_model=APIResponse[HermesAuditLogListResponse],
    summary="获取审计日志",
    description="获取 Hermes 操作审计日志，支持分页、筛选"
)
async def get_audit_logs(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(20, description="每页数量", ge=1, le=100),
    action: Optional[str] = Query(None, description="操作类型筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    user_name: Optional[str] = Query(None, description="用户名筛选"),
    target_type: Optional[str] = Query(None, description="目标类型筛选"),
    start_time: Optional[str] = Query(None, description="开始时间（ISO格式）"),
    end_time: Optional[str] = Query(None, description="结束时间（ISO格式）"),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问 Hermes 系统管理"
        )
    
    audit_logs = hermes_service.get_audit_logs(
        page=page,
        page_size=page_size,
        action=action,
        user_id=user_id,
        user_name=user_name,
        target_type=target_type,
        start_time=start_time,
        end_time=end_time,
    )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=audit_logs
    )
