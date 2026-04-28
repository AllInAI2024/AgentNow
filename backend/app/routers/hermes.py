from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.schemas.hermes import (
    HermesOverviewResponse,
    VersionCheckResponse,
    UpdateProgress,
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
