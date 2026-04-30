from typing import List, Optional
from urllib.parse import quote
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.models import User
from app.schemas import (
    EnableAgentRequest,
    EnableAgentResponse,
    UserAgentResponse,
    UserAgentWithTemplateResponse,
    UserAgentListResponse,
    AgentConversationResponse,
    AgentConversationListResponse,
    ChatRequest,
    ChatResponse,
    ConversationDetailResponse,
    AgentGeneratedFileResponse,
    GeneratePPTRequest,
    APIResponse,
)
from app.services.auth_service import (
    get_db,
    get_current_user,
    permission_required,
)
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["智能体管理（员工侧）"])


@router.get(
    "/me",
    response_model=APIResponse[UserAgentListResponse],
    summary="获取我的智能体列表",
    description="获取当前登录员工已开通的智能体列表"
)
def get_my_agents(
    current_user: User = Depends(permission_required("agent:use")),
    db: Session = Depends(get_db)
):
    service = AgentService(db)
    result = service.get_user_agents(user_id=current_user.id)
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=result
    )


@router.post(
    "/me/enable",
    response_model=APIResponse[EnableAgentResponse],
    summary="首次开通默认智能体",
    description="员工第一次进入智能体模块时调用，自动创建或绑定 Hermes Profile，并开通默认模板"
)
def enable_my_agent(
    enable_data: EnableAgentRequest,
    current_user: User = Depends(permission_required("agent:use")),
    db: Session = Depends(get_db)
):
    service = AgentService(db)
    result, message = service.enable_agent_for_user(
        user_id=current_user.id,
        template_id=enable_data.template_id,
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return APIResponse(
        code=200,
        message=message,
        data=result
    )


@router.get(
    "/me/{agent_id}",
    response_model=APIResponse[UserAgentWithTemplateResponse],
    summary="获取我的智能体详情",
    description="获取当前员工某个智能体实例的详细信息"
)
def get_my_agent_detail(
    agent_id: int,
    current_user: User = Depends(permission_required("agent:use")),
    db: Session = Depends(get_db)
):
    service = AgentService(db)
    user_agent, message = service.get_user_agent_detail(
        agent_id=agent_id,
        user_id=current_user.id,
    )
    
    if not user_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )
    
    return APIResponse(
        code=200,
        message=message,
        data=user_agent
    )


@router.post(
    "/me/{agent_id}/chat",
    response_model=APIResponse[ChatResponse],
    summary="发送消息",
    description="向当前员工的智能体发送消息并获取回复"
)
def send_chat_message(
    agent_id: int,
    chat_data: ChatRequest,
    current_user: User = Depends(permission_required("agent:use")),
    db: Session = Depends(get_db)
):
    service = AgentService(db)
    result, message = service.send_chat_message(
        agent_id=agent_id,
        user_id=current_user.id,
        conversation_id=chat_data.conversation_id,
        message=chat_data.message,
        action_type=chat_data.action_type,
        metadata=chat_data.metadata,
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return APIResponse(
        code=200,
        message=message,
        data=result
    )


@router.get(
    "/me/{agent_id}/conversations",
    response_model=APIResponse[AgentConversationListResponse],
    summary="获取会话列表",
    description="获取当前员工某个智能体的会话列表"
)
def get_conversations(
    agent_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[int] = Query(None, description="会话状态：0-草稿，1-进行中，2-已完成，3-已归档，4-失败"),
    current_user: User = Depends(permission_required("agent:history:view")),
    db: Session = Depends(get_db)
):
    service = AgentService(db)
    result = service.get_conversations(
        agent_id=agent_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
    )
    
    return APIResponse(
        code=200,
        message="获取成功",
        data=result
    )


@router.get(
    "/me/{agent_id}/conversations/{conversation_id}",
    response_model=APIResponse[ConversationDetailResponse],
    summary="获取会话详情",
    description="获取某个会话的完整详情"
)
def get_conversation_detail(
    agent_id: int,
    conversation_id: int,
    current_user: User = Depends(permission_required("agent:history:view")),
    db: Session = Depends(get_db)
):
    service = AgentService(db)
    result, message = service.get_conversation_detail(
        conversation_id=conversation_id,
        agent_id=agent_id,
        user_id=current_user.id,
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
    "/me/{agent_id}/generate-ppt",
    response_model=APIResponse[AgentGeneratedFileResponse],
    summary="生成正式 PPT",
    description="当大纲、风格和正式生成都确认后，触发最终 .pptx 生成"
)
def generate_ppt(
    agent_id: int,
    generate_data: GeneratePPTRequest,
    current_user: User = Depends(permission_required("agent:use")),
    db: Session = Depends(get_db)
):
    service = AgentService(db)
    result, message = service.generate_ppt(
        agent_id=agent_id,
        conversation_id=generate_data.conversation_id,
        user_id=current_user.id,
        template_name=generate_data.template_name,
        regenerate=generate_data.regenerate,
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return APIResponse(
        code=200,
        message=message,
        data=result
    )


@router.get(
    "/me/{agent_id}/files/{file_id}",
    summary="下载生成文件",
    description="下载当前员工自己的生成文件"
)
def download_generated_file(
    agent_id: int,
    file_id: int,
    current_user: User = Depends(permission_required("agent:use")),
    db: Session = Depends(get_db)
):
    service = AgentService(db)
    file_content, mime_type, filename, message = service.download_generated_file(
        file_id=file_id,
        agent_id=agent_id,
        user_id=current_user.id,
    )
    
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )
    
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename, safe='')}"
        }
    )
