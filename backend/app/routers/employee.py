from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.models import User, Department
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    APIResponse,
)
from app.services.auth_service import (
    get_db,
    get_current_user,
    get_password_hash,
    permission_required,
)

router = APIRouter(prefix="/employees", tags=["员工管理"])

DEFAULT_PASSWORD = "123456"


@router.get(
    "",
    response_model=APIResponse[List[UserResponse]],
    summary="获取员工列表",
    description="获取所有员工列表，支持按部门、状态筛选"
)
def get_employees(
    department_id: Optional[int] = Query(None, description="部门ID"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_user: User = Depends(permission_required("employee:query")),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    
    if department_id is not None:
        query = query.filter(User.department_id == department_id)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    employees = query.order_by(User.id).all()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=[UserResponse.model_validate(e) for e in employees]
    )


@router.get(
    "/{employee_id}",
    response_model=APIResponse[UserResponse],
    summary="获取员工详情",
    description="根据ID获取员工的详细信息"
)
def get_employee(
    employee_id: int,
    current_user: User = Depends(permission_required("employee:query")),
    db: Session = Depends(get_db)
):
    employee = db.query(User).filter(User.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="员工不存在"
        )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=UserResponse.model_validate(employee)
    )


@router.post(
    "",
    response_model=APIResponse[UserResponse],
    summary="创建员工",
    description="创建新的员工，默认密码为123456，首次登录需修改密码"
)
def create_employee(
    employee_data: UserCreate,
    current_user: User = Depends(permission_required("employee:create")),
    db: Session = Depends(get_db)
):
    if not employee_data.department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="员工必须属于一个部门"
        )
    
    department = db.query(Department).filter(Department.id == employee_data.department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"部门 ID '{employee_data.department_id}' 不存在"
        )
    
    existing = db.query(User).filter(User.login_name == employee_data.login_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"登录名 '{employee_data.login_name}' 已存在"
        )
    
    if employee_data.phone:
        existing_phone = db.query(User).filter(User.phone == employee_data.phone).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"手机号 '{employee_data.phone}' 已存在"
            )
    
    if employee_data.email:
        existing_email = db.query(User).filter(User.email == employee_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"邮箱 '{employee_data.email}' 已存在"
            )
    
    password_to_use = employee_data.password if employee_data.password else DEFAULT_PASSWORD
    
    employee = User(
        department_id=employee_data.department_id,
        login_name=employee_data.login_name,
        phone=employee_data.phone,
        email=employee_data.email,
        password_hash=get_password_hash(password_to_use),
        username=employee_data.username,
        avatar_url=employee_data.avatar_url,
        hermes_profile=employee_data.hermes_profile,
        hermes_profile_config=employee_data.hermes_profile_config,
        is_active=True,
        is_default_password=True,
        is_super_admin=False,
    )
    
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    return APIResponse(
        code=200,
        message="创建成功",
        data=UserResponse.model_validate(employee)
    )


@router.put(
    "/{employee_id}",
    response_model=APIResponse[UserResponse],
    summary="更新员工",
    description="更新员工的信息"
)
def update_employee(
    employee_id: int,
    employee_data: UserUpdate,
    current_user: User = Depends(permission_required("employee:update")),
    db: Session = Depends(get_db)
):
    employee = db.query(User).filter(User.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="员工不存在"
        )
    
    update_data = employee_data.model_dump(exclude_unset=True)
    
    if "department_id" in update_data and update_data["department_id"]:
        department = db.query(Department).filter(Department.id == update_data["department_id"]).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"部门 ID '{update_data['department_id']}' 不存在"
            )
    
    if "phone" in update_data and update_data["phone"]:
        existing = db.query(User).filter(
            User.phone == update_data["phone"],
            User.id != employee_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"手机号 '{update_data['phone']}' 已存在"
            )
    
    if "email" in update_data and update_data["email"]:
        existing = db.query(User).filter(
            User.email == update_data["email"],
            User.id != employee_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"邮箱 '{update_data['email']}' 已存在"
            )
    
    for key, value in update_data.items():
        setattr(employee, key, value)
    
    db.commit()
    db.refresh(employee)
    
    return APIResponse(
        code=200,
        message="更新成功",
        data=UserResponse.model_validate(employee)
    )


@router.delete(
    "/{employee_id}",
    response_model=APIResponse[None],
    summary="删除员工",
    description="删除员工"
)
def delete_employee(
    employee_id: int,
    current_user: User = Depends(permission_required("employee:delete")),
    db: Session = Depends(get_db)
):
    employee = db.query(User).filter(User.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="员工不存在"
        )
    
    if employee.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除超级管理员"
        )
    
    db.delete(employee)
    db.commit()
    
    return APIResponse(
        code=200,
        message="删除成功",
        data=None
    )


@router.post(
    "/{employee_id}/reset-password",
    response_model=APIResponse[None],
    summary="重置员工密码",
    description="重置员工密码为默认密码123456，员工需首次登录修改密码"
)
def reset_employee_password(
    employee_id: int,
    current_user: User = Depends(permission_required("employee:reset_password")),
    db: Session = Depends(get_db)
):
    employee = db.query(User).filter(User.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="员工不存在"
        )
    
    employee.password_hash = get_password_hash(DEFAULT_PASSWORD)
    employee.is_default_password = True
    employee.password_changed_at = None
    
    db.commit()
    
    return APIResponse(
        code=200,
        message="密码重置成功，默认密码为123456",
        data=None
    )


@router.put(
    "/{employee_id}/status",
    response_model=APIResponse[UserResponse],
    summary="启用/禁用员工",
    description="启用或禁用员工账号"
)
def toggle_employee_status(
    employee_id: int,
    current_user: User = Depends(permission_required("employee:toggle_status")),
    db: Session = Depends(get_db)
):
    employee = db.query(User).filter(User.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="员工不存在"
        )
    
    if employee.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用超级管理员"
        )
    
    employee.is_active = not employee.is_active
    db.commit()
    db.refresh(employee)
    
    return APIResponse(
        code=200,
        message="状态更新成功",
        data=UserResponse.model_validate(employee)
    )
