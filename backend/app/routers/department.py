from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.models import Department, User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentTreeResponse,
)
from app.schemas.user import APIResponse
from app.services.auth_service import (
    get_db,
    get_current_user,
)

router = APIRouter(prefix="/departments", tags=["部门管理"])


def build_department_tree(departments: List[Department], parent_id: int = 0) -> List[DepartmentTreeResponse]:
    tree = []
    for dept in departments:
        if dept.parent_id == parent_id:
            tree_node = DepartmentTreeResponse.model_validate(dept)
            tree_node.children = build_department_tree(departments, dept.id)
            tree.append(tree_node)
    return tree


def get_all_child_department_ids(db: Session, parent_id: int) -> List[int]:
    all_ids = []
    children = db.query(Department).filter(Department.parent_id == parent_id).all()
    for child in children:
        all_ids.append(child.id)
        all_ids.extend(get_all_child_department_ids(db, child.id))
    return all_ids


@router.get(
    "",
    response_model=APIResponse[List[DepartmentResponse]],
    summary="获取部门列表",
    description="获取所有部门列表，支持按状态筛选"
)
def get_departments(
    status: Optional[int] = Query(None, description="状态：1-启用，0-禁用"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Department)
    
    if status is not None:
        query = query.filter(Department.status == status)
    
    departments = query.order_by(Department.sort, Department.id).all()
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=[DepartmentResponse.model_validate(d) for d in departments]
    )


@router.get(
    "/tree",
    response_model=APIResponse[List[DepartmentTreeResponse]],
    summary="获取部门树形结构",
    description="获取树形结构的部门列表"
)
def get_department_tree(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    departments = db.query(Department).order_by(Department.sort, Department.id).all()
    
    tree = build_department_tree(departments, 0)
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=tree
    )


@router.get(
    "/{department_id}",
    response_model=APIResponse[DepartmentResponse],
    summary="获取部门详情",
    description="根据ID获取部门的详细信息"
)
def get_department(
    department_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    department = db.query(Department).filter(Department.id == department_id).first()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部门不存在"
        )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=DepartmentResponse.model_validate(department)
    )


@router.post(
    "",
    response_model=APIResponse[DepartmentResponse],
    summary="创建部门",
    description="创建新的部门"
)
def create_department(
    department_data: DepartmentCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if department_data.code:
        existing = db.query(Department).filter(Department.code == department_data.code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"部门编码 '{department_data.code}' 已存在"
            )
    
    if department_data.parent_id > 0:
        parent = db.query(Department).filter(Department.id == department_data.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"父部门 ID '{department_data.parent_id}' 不存在"
            )
    
    department = Department(
        parent_id=department_data.parent_id,
        name=department_data.name,
        code=department_data.code,
        description=department_data.description,
        sort=department_data.sort,
        status=department_data.status,
        leader_id=department_data.leader_id,
    )
    
    db.add(department)
    db.commit()
    db.refresh(department)
    
    return APIResponse(
        code=200,
        message="创建成功",
        data=DepartmentResponse.model_validate(department)
    )


@router.put(
    "/{department_id}",
    response_model=APIResponse[DepartmentResponse],
    summary="更新部门",
    description="更新部门的信息"
)
def update_department(
    department_id: int,
    department_data: DepartmentUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    department = db.query(Department).filter(Department.id == department_id).first()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部门不存在"
        )
    
    if department_data.code and department_data.code != department.code:
        existing = db.query(Department).filter(
            Department.code == department_data.code,
            Department.id != department_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"部门编码 '{department_data.code}' 已存在"
            )
    
    if department_data.parent_id is not None:
        if department_data.parent_id == department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="父部门不能是自身"
            )
        
        if department_data.parent_id > 0:
            parent = db.query(Department).filter(Department.id == department_data.parent_id).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"父部门 ID '{department_data.parent_id}' 不存在"
                )
        
        child_ids = get_all_child_department_ids(db, department_id)
        if department_data.parent_id in child_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能将部门移动到其子部门下"
            )
    
    update_data = department_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(department, key, value)
    
    db.commit()
    db.refresh(department)
    
    return APIResponse(
        code=200,
        message="更新成功",
        data=DepartmentResponse.model_validate(department)
    )


@router.delete(
    "/{department_id}",
    response_model=APIResponse[None],
    summary="删除部门",
    description="删除部门，级联删除所有子部门和该部门下的员工"
)
def delete_department(
    department_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    department = db.query(Department).filter(Department.id == department_id).first()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部门不存在"
        )
    
    all_department_ids = [department_id]
    all_department_ids.extend(get_all_child_department_ids(db, department_id))
    
    db.query(User).filter(User.department_id.in_(all_department_ids)).delete(synchronize_session=False)
    
    for dept_id in reversed(all_department_ids):
        db.query(Department).filter(Department.id == dept_id).delete(synchronize_session=False)
    
    db.commit()
    
    return APIResponse(
        code=200,
        message="删除成功",
        data=None
    )
