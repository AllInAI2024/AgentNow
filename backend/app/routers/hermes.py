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
