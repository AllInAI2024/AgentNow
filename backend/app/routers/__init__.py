from app.routers.auth import router as auth_router
from app.routers.permission import router as permission_router
from app.routers.department import router as department_router
from app.routers.employee import router as employee_router

__all__ = ["auth_router", "permission_router", "department_router", "employee_router"]
