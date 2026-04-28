from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.models import Role, Permission, RolePermission, User, UserRole
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleWithPermissionsResponse,
    AssignPermissionsRequest,
)
from app.schemas.user import (
    AssignRolesRequest,
    APIResponse,
)
from app.services.auth_service import (
    get_db,
    get_current_user,
    get_super_admin_role,
)
from app.config import settings

router = APIRouter(prefix="/roles", tags=["角色管理"])


def is_super_admin_role(role: Role) -> bool:
    return role.code == "super_admin"


def is_super_admin_user(user: User) -> bool:
    return user.is_super_admin


@router.get(
    "",
    response_model=APIResponse[List[RoleResponse]],
    summary="获取角色列表",
    description="获取所有角色列表"
)
def get_roles(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    roles = db.query(Role).order_by(Role.id).all()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=[RoleResponse.model_validate(r) for r in roles]
    )


@router.get(
    "/{role_id}",
    response_model=APIResponse[RoleWithPermissionsResponse],
    summary="获取角色详情",
    description="根据ID获取角色的详细信息，包含已分配的权限"
)
def get_role(
    role_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    role_permissions = db.query(RolePermission).filter(
        RolePermission.role_id == role_id
    ).all()
    permission_ids = [rp.permission_id for rp in role_permissions]
    
    response = RoleWithPermissionsResponse.model_validate(role)
    response.permissions = permission_ids
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=response
    )


@router.post(
    "",
    response_model=APIResponse[RoleResponse],
    summary="创建角色",
    description="创建新的角色"
)
def create_role(
    role_data: RoleCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Role).filter(Role.code == role_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"角色编码 '{role_data.code}' 已存在"
        )
    
    role = Role(
        name=role_data.name,
        code=role_data.code,
        description=role_data.description,
    )
    
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return APIResponse(
        code=200,
        message="创建成功",
        data=RoleResponse.model_validate(role)
    )


@router.put(
    "/{role_id}",
    response_model=APIResponse[RoleResponse],
    summary="更新角色",
    description="更新角色的信息，编码不可修改"
)
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    update_data = role_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(role, key, value)
    
    db.commit()
    db.refresh(role)
    
    return APIResponse(
        code=200,
        message="更新成功",
        data=RoleResponse.model_validate(role)
    )


@router.delete(
    "/{role_id}",
    response_model=APIResponse[None],
    summary="删除角色",
    description="删除角色，注意：超级管理员角色不能删除，已分配给用户的角色不能删除"
)
def delete_role(
    role_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    if is_super_admin_role(role):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="超级管理员角色不能删除"
        )
    
    user_roles = db.query(UserRole).filter(UserRole.role_id == role_id).first()
    if user_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该角色已分配给用户，请先解除分配"
        )
    
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    
    db.delete(role)
    db.commit()
    
    return APIResponse(
        code=200,
        message="删除成功",
        data=None
    )


@router.get(
    "/{role_id}/permissions",
    response_model=APIResponse[List[int]],
    summary="获取角色权限",
    description="获取角色已分配的权限ID列表"
)
def get_role_permissions(
    role_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    role_permissions = db.query(RolePermission).filter(
        RolePermission.role_id == role_id
    ).all()
    permission_ids = [rp.permission_id for rp in role_permissions]
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=permission_ids
    )


@router.put(
    "/{role_id}/permissions",
    response_model=APIResponse[List[int]],
    summary="分配角色权限",
    description="为角色分配权限，全量覆盖"
)
def assign_role_permissions(
    role_id: int,
    request: AssignPermissionsRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    for pid in request.permission_ids:
        permission = db.query(Permission).filter(Permission.id == pid).first()
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"权限 ID '{pid}' 不存在"
            )
    
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    
    for pid in request.permission_ids:
        role_permission = RolePermission(role_id=role_id, permission_id=pid)
        db.add(role_permission)
    
    db.commit()
    
    return APIResponse(
        code=200,
        message="权限分配成功",
        data=request.permission_ids
    )


@router.get(
    "/users/{user_id}",
    response_model=APIResponse[List[int]],
    summary="获取用户角色",
    description="获取用户已分配的角色ID列表"
)
def get_user_roles(
    user_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    role_ids = [ur.role_id for ur in user_roles]
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=role_ids
    )


@router.put(
    "/users/{user_id}",
    response_model=APIResponse[List[int]],
    summary="分配用户角色",
    description="为用户分配角色，全量覆盖。超级管理员用户的超级管理员角色不可移除。"
)
def assign_user_roles(
    user_id: int,
    request: AssignRolesRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    for rid in request.role_ids:
        role = db.query(Role).filter(Role.id == rid).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"角色 ID '{rid}' 不存在"
            )
    
    role_ids = request.role_ids.copy()
    
    if is_super_admin_user(user):
        super_admin_role = get_super_admin_role(db)
        if super_admin_role and super_admin_role.id not in role_ids:
            role_ids.append(super_admin_role.id)
    
    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    
    for rid in role_ids:
        user_role = UserRole(user_id=user_id, role_id=rid)
        db.add(user_role)
    
    db.commit()
    
    return APIResponse(
        code=200,
        message="角色分配成功",
        data=role_ids
    )
