from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.models import Permission
from app.schemas.permission import (
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
    PermissionTreeResponse,
)
from app.schemas.user import APIResponse
from app.services.auth_service import (
    get_db,
    get_current_user,
)

router = APIRouter(prefix="/permissions", tags=["权限管理"])


def build_permission_tree(permissions: List[Permission], parent_id: int = 0) -> List[PermissionTreeResponse]:
    tree = []
    for permission in permissions:
        if permission.parent_id == parent_id:
            tree_node = PermissionTreeResponse.model_validate(permission)
            tree_node.children = build_permission_tree(permissions, permission.id)
            tree.append(tree_node)
    return tree


@router.get(
    "",
    response_model=APIResponse[List[PermissionResponse]],
    summary="获取权限列表",
    description="获取所有功能点/权限列表，支持按类型和状态筛选"
)
def get_permissions(
    type: Optional[int] = Query(None, description="权限类型：1-菜单，2-按钮，3-API接口"),
    status: Optional[int] = Query(None, description="状态：0-禁用，1-启用"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Permission)
    
    if type is not None:
        query = query.filter(Permission.type == type)
    if status is not None:
        query = query.filter(Permission.status == status)
    
    permissions = query.order_by(Permission.sort, Permission.id).all()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=[PermissionResponse.model_validate(p) for p in permissions]
    )


@router.get(
    "/tree",
    response_model=APIResponse[List[PermissionTreeResponse]],
    summary="获取权限树形结构",
    description="获取树形结构的权限列表，用于菜单展示"
)
def get_permission_tree(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    permissions = db.query(Permission).filter(
        Permission.status == 1
    ).order_by(Permission.parent_id, Permission.sort, Permission.id).all()
    
    tree = build_permission_tree(permissions, 0)
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=tree
    )


@router.get(
    "/{permission_id}",
    response_model=APIResponse[PermissionResponse],
    summary="获取权限详情",
    description="根据ID获取权限的详细信息"
)
def get_permission(
    permission_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=PermissionResponse.model_validate(permission)
    )


@router.post(
    "",
    response_model=APIResponse[PermissionResponse],
    summary="创建权限",
    description="创建新的功能点/权限"
)
def create_permission(
    permission_data: PermissionCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Permission).filter(Permission.code == permission_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"权限编码 '{permission_data.code}' 已存在"
        )
    
    if permission_data.parent_id > 0:
        parent = db.query(Permission).filter(Permission.id == permission_data.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"父权限 ID '{permission_data.parent_id}' 不存在"
            )
    
    permission = Permission(
        parent_id=permission_data.parent_id,
        enterprise_id=permission_data.enterprise_id,
        name=permission_data.name,
        code=permission_data.code,
        type=permission_data.type,
        path=permission_data.path,
        component=permission_data.component,
        icon=permission_data.icon,
        sort=permission_data.sort,
        visible=permission_data.visible,
        keep_alive=permission_data.keep_alive,
        redirect=permission_data.redirect,
        permission_level=permission_data.permission_level,
        description=permission_data.description,
    )
    
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
    return APIResponse(
        code=200,
        message="创建成功",
        data=PermissionResponse.model_validate(permission)
    )


@router.put(
    "/{permission_id}",
    response_model=APIResponse[PermissionResponse],
    summary="更新权限",
    description="更新权限的信息"
)
def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    if permission_data.code and permission_data.code != permission.code:
        existing = db.query(Permission).filter(
            Permission.code == permission_data.code,
            Permission.id != permission_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"权限编码 '{permission_data.code}' 已存在"
            )
    
    if permission_data.parent_id is not None and permission_data.parent_id > 0:
        if permission_data.parent_id == permission_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="父权限不能是自身"
            )
        parent = db.query(Permission).filter(Permission.id == permission_data.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"父权限 ID '{permission_data.parent_id}' 不存在"
            )
    
    update_data = permission_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(permission, key, value)
    
    db.commit()
    db.refresh(permission)
    
    return APIResponse(
        code=200,
        message="更新成功",
        data=PermissionResponse.model_validate(permission)
    )


@router.delete(
    "/{permission_id}",
    response_model=APIResponse[None],
    summary="删除权限",
    description="删除权限，注意：有子权限的权限不能直接删除"
)
def delete_permission(
    permission_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    children = db.query(Permission).filter(Permission.parent_id == permission_id).first()
    if children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该权限存在子权限，请先删除子权限"
        )
    
    db.delete(permission)
    db.commit()
    
    return APIResponse(
        code=200,
        message="删除成功",
        data=None
    )
