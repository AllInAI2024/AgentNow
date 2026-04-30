from app.routers.auth import router as auth_router
from app.routers.permission import router as permission_router
from app.routers.department import router as department_router
from app.routers.employee import router as employee_router
from app.routers.role import router as role_router
from app.routers.knowledge import router as knowledge_router
from app.routers.hermes import router as hermes_router
from app.routers.agent_template import router as agent_template_router
from app.routers.agent import router as agent_router

__all__ = [
    "auth_router",
    "permission_router",
    "department_router",
    "employee_router",
    "role_router",
    "knowledge_router",
    "hermes_router",
    "agent_template_router",
    "agent_router",
]
