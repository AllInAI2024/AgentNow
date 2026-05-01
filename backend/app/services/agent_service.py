import math
import json
import os
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.config import settings
from app.models import (
    User,
    UserAgent,
    AgentTemplate,
    AgentConversation,
    AgentGeneratedFile,
    AgentOperationLog,
)
from app.schemas import (
    UserAgentListResponse,
    UserAgentWithTemplateResponse,
    EnableAgentResponse,
    AgentConversationListResponse,
    ChatResponse,
    ConversationDetailResponse,
)
from app.services.hermes_profile_service import HermesProfileService
from app.services.ppt_assistant_interaction_service import (
    PPTAssistantInteractionService,
    ConversationStage,
)
from app.services.knowledge_retrieval_service import KnowledgeRetrievalService


class AgentService:
    def __init__(self, db: Session):
        self.db = db
        self._profile_service: Optional[HermesProfileService] = None
    
    def _get_profile_service(self) -> HermesProfileService:
        if self._profile_service is None:
            self._profile_service = HermesProfileService()
        return self._profile_service
    
    def get_user_agent_by_id(self, agent_id: int, user_id: int) -> Optional[UserAgent]:
        return self.db.query(UserAgent).filter(
            UserAgent.id == agent_id,
            UserAgent.user_id == user_id
        ).first()
    
    def get_user_agents(self, user_id: int) -> UserAgentListResponse:
        user_agents = self.db.query(UserAgent).filter(
            UserAgent.user_id == user_id
        ).order_by(UserAgent.last_used_at.desc()).all()
        
        items = []
        for ua in user_agents:
            template = self.db.query(AgentTemplate).filter(
                AgentTemplate.id == ua.template_id
            ).first()
            
            template_dict = None
            if template:
                template_dict = {
                    "id": template.id,
                    "code": template.code,
                    "name": template.name,
                    "description": template.description,
                    "status": template.status,
                    "is_default": template.is_default,
                    "version": template.version,
                }
            
            items.append(UserAgentWithTemplateResponse(
                id=ua.id,
                user_id=ua.user_id,
                template_id=ua.template_id,
                display_name=ua.display_name,
                hermes_profile=ua.hermes_profile,
                template_version=ua.template_version,
                config_snapshot=ua.config_snapshot,
                agent_status=ua.agent_status,
                activation_mode=ua.activation_mode,
                enabled_at=ua.enabled_at,
                last_used_at=ua.last_used_at,
                disabled_at=ua.disabled_at,
                created_at=ua.created_at,
                updated_at=ua.updated_at,
                template=template_dict,
            ))
        
        return UserAgentListResponse(
            items=items,
            total=len(items),
        )
    
    def get_user_agent_detail(
        self,
        agent_id: int,
        user_id: int,
    ) -> Tuple[Optional[UserAgentWithTemplateResponse], str]:
        user_agent = self.get_user_agent_by_id(agent_id, user_id)
        if not user_agent:
            return None, "智能体不存在或无权限访问"
        
        template = self.db.query(AgentTemplate).filter(
            AgentTemplate.id == user_agent.template_id
        ).first()
        
        template_dict = None
        if template:
            template_dict = {
                "id": template.id,
                "code": template.code,
                "name": template.name,
                "description": template.description,
                "status": template.status,
                "is_default": template.is_default,
                "version": template.version,
            }
        
        result = UserAgentWithTemplateResponse(
            id=user_agent.id,
            user_id=user_agent.user_id,
            template_id=user_agent.template_id,
            display_name=user_agent.display_name,
            hermes_profile=user_agent.hermes_profile,
            template_version=user_agent.template_version,
            config_snapshot=user_agent.config_snapshot,
            agent_status=user_agent.agent_status,
            activation_mode=user_agent.activation_mode,
            enabled_at=user_agent.enabled_at,
            last_used_at=user_agent.last_used_at,
            disabled_at=user_agent.disabled_at,
            created_at=user_agent.created_at,
            updated_at=user_agent.updated_at,
            template=template_dict,
        )
        
        return result, "获取成功"
    
    def _log_operation(
        self,
        operator_user_id: int,
        target_type: str,
        target_id: Optional[int],
        action: str,
        action_name: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> None:
        log = AgentOperationLog(
            operator_user_id=operator_user_id,
            target_type=target_type,
            target_id=target_id,
            action=action,
            action_name=action_name,
            result_status=1 if success else 0,
            details=details,
            error_message=error_message,
            created_at=datetime.utcnow(),
        )
        self.db.add(log)
        self.db.commit()
    
    def _get_default_template(self) -> Optional[AgentTemplate]:
        return self.db.query(AgentTemplate).filter(
            AgentTemplate.is_default == True,
            AgentTemplate.status == 1,
            AgentTemplate.deleted_at.is_(None)
        ).first()
    
    def _get_template_by_id(self, template_id: int) -> Optional[AgentTemplate]:
        return self.db.query(AgentTemplate).filter(
            AgentTemplate.id == template_id,
            AgentTemplate.status == 1,
            AgentTemplate.deleted_at.is_(None)
        ).first()
    
    def _get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()
    
    def _ensure_hermes_profile_for_user(
        self,
        user_id: int,
        tenant_id: int = 1,
    ) -> Tuple[str, bool, str]:
        profile_service = self._get_profile_service()
        
        profile_name, created, message = profile_service.ensure_profile(
            user_id=user_id,
            tenant_id=tenant_id,
        )
        
        return profile_name, created, message
    
    def enable_agent_for_user(
        self,
        user_id: int,
        template_id: Optional[int] = None,
        tenant_id: int = 1,
    ) -> Tuple[Optional[EnableAgentResponse], str]:
        user = self._get_user_by_id(user_id)
        if not user:
            return None, "用户不存在或已被停用"
        
        if template_id:
            template = self._get_template_by_id(template_id)
            if not template:
                return None, f"模板 ID={template_id} 不存在或已停用"
        else:
            template = self._get_default_template()
            if not template:
                return None, "没有可用的模板，请先配置默认模板"
        
        existing_agent = self.db.query(UserAgent).filter(
            UserAgent.user_id == user_id,
            UserAgent.template_id == template.id
        ).first()
        
        if existing_agent:
            return None, "该智能体已开通"
        
        profile_name, created_profile, profile_message = self._ensure_hermes_profile_for_user(
            user_id=user_id,
            tenant_id=tenant_id,
        )
        
        if not profile_name:
            self._log_operation(
                operator_user_id=user_id,
                target_type="user_agent",
                target_id=None,
                action="agent:enable",
                action_name="开通智能体",
                success=False,
                details={
                    "template_id": template.id,
                    "template_code": template.code,
                },
                error_message=profile_message,
            )
            return None, f"创建 Hermes Profile 失败: {profile_message}"
        
        if user.hermes_profile != profile_name:
            user.hermes_profile = profile_name
            user.updated_at = datetime.utcnow()
        
        config_snapshot = template.to_snapshot()
        
        user_agent = UserAgent(
            user_id=user_id,
            template_id=template.id,
            display_name=template.name,
            hermes_profile=profile_name,
            template_version=template.version,
            config_snapshot=config_snapshot,
            agent_status=1,
            activation_mode="auto",
            enabled_at=datetime.utcnow(),
        )
        
        self.db.add(user_agent)
        self.db.commit()
        self.db.refresh(user_agent)
        
        self._log_operation(
            operator_user_id=user_id,
            target_type="user_agent",
            target_id=user_agent.id,
            action="agent:enable",
            action_name="开通智能体",
            success=True,
            details={
                "template_id": template.id,
                "template_code": template.code,
                "hermes_profile": profile_name,
                "created_profile": created_profile,
            },
        )
        
        return EnableAgentResponse(
            user_agent=user_agent,
            created_profile=created_profile,
        ), "开通成功"
    
    def get_or_create_agent_for_user(
        self,
        user_id: int,
        tenant_id: int = 1,
    ) -> Tuple[Optional[UserAgent], str]:
        existing_agents = self.db.query(UserAgent).filter(
            UserAgent.user_id == user_id,
            UserAgent.agent_status == 1
        ).all()
        
        if existing_agents:
            if len(existing_agents) == 1:
                return existing_agents[0], "获取已开通智能体"
            else:
                default_template = self._get_default_template()
                if default_template:
                    for agent in existing_agents:
                        if agent.template_id == default_template.id:
                            return agent, "获取默认模板智能体"
                return existing_agents[0], "获取首个已开通智能体"
        
        result, message = self.enable_agent_for_user(
            user_id=user_id,
            template_id=None,
            tenant_id=tenant_id,
        )
        
        if result:
            return result.user_agent, "自动开通智能体成功"
        else:
            return None, message
    
    def _get_interaction_service_from_conversation(
        self, 
        conversation: AgentConversation
    ) -> PPTAssistantInteractionService:
        """
        从会话中恢复交互服务状态
        """
        service = PPTAssistantInteractionService()
        
        if conversation.current_stage:
            try:
                stage_map = {
                    "welcome": ConversationStage.WELCOME,
                    "clarifying": ConversationStage.CLARIFYING,
                    "outline_draft": ConversationStage.OUTLINE_DRAFT,
                    "outline_confirmed": ConversationStage.OUTLINE_CONFIRMED,
                    "template_select": ConversationStage.TEMPLATE_SELECT,
                    "final_generating": ConversationStage.FINAL_GENERATING,
                    "completed": ConversationStage.COMPLETED,
                }
                service._current_stage = stage_map.get(conversation.current_stage, ConversationStage.WELCOME)
            except Exception:
                pass
        
        return service
    
    def _update_conversation_from_service(
        self, 
        conversation: AgentConversation, 
        service: PPTAssistantInteractionService,
        structured_result: Optional[Dict[str, Any]]
    ) -> None:
        """
        根据交互服务更新会话状态
        """
        stage_map = {
            ConversationStage.WELCOME: "welcome",
            ConversationStage.CLARIFYING: "clarifying",
            ConversationStage.OUTLINE_DRAFT: "outline_draft",
            ConversationStage.OUTLINE_CONFIRMED: "outline_confirmed",
            ConversationStage.TEMPLATE_SELECT: "template_select",
            ConversationStage.FINAL_GENERATING: "final_generating",
            ConversationStage.COMPLETED: "completed",
        }
        
        conversation.current_stage = stage_map.get(service.get_current_stage(), "chatting")
        
        current_stage = service.get_current_stage()
        conversation.outline_confirmed = current_stage in [
            ConversationStage.OUTLINE_CONFIRMED,
            ConversationStage.TEMPLATE_SELECT,
            ConversationStage.FINAL_GENERATING,
            ConversationStage.COMPLETED,
        ]
        
        conversation.template_confirmed = current_stage in [
            ConversationStage.FINAL_GENERATING,
            ConversationStage.COMPLETED,
        ]
        
        conversation.final_generation_confirmed = current_stage == ConversationStage.COMPLETED
        
        if current_stage == ConversationStage.COMPLETED:
            conversation.status = 2
            conversation.completed_at = datetime.utcnow()
    
    def _get_welcome_message_from_template(self, user_agent: UserAgent) -> str:
        """
        从模板快照中获取欢迎语
        """
        default_welcome = """你好，我是企业 PPT 助手。

你可以直接告诉我：
1. 这份 PPT 是做什么用的
2. 是给谁看的
3. 想做多少页
4. 有没有必须引用的公司资料

如果你暂时说不全，我也会一步一步带你把这件事理顺。"""
        
        try:
            config_snapshot = user_agent.config_snapshot
            if config_snapshot and isinstance(config_snapshot, dict):
                welcome = config_snapshot.get("welcome_message")
                if welcome and isinstance(welcome, str) and len(welcome) > 0:
                    return welcome
        except Exception:
            pass
        
        return default_welcome
    
    def _is_ppt_assistant(self, user_agent: UserAgent) -> bool:
        """
        判断是否是 PPT 助手模板
        """
        try:
            config_snapshot = user_agent.config_snapshot
            if config_snapshot and isinstance(config_snapshot, dict):
                code = config_snapshot.get("code", "")
                if "ppt" in code.lower():
                    return True
        except Exception:
            pass
        
        return True
    
    def _get_knowledge_categories_from_template(self, user_agent: UserAgent) -> Optional[List[str]]:
        """
        从模板快照中获取知识分类配置
        """
        try:
            config_snapshot = user_agent.config_snapshot
            if config_snapshot and isinstance(config_snapshot, dict):
                knowledge_scope = config_snapshot.get("knowledge_scope", "none")
                knowledge_categories = config_snapshot.get("knowledge_categories")
                
                if knowledge_scope == "none":
                    return None
                elif knowledge_scope == "global":
                    return []
                elif knowledge_scope == "category" and knowledge_categories:
                    if isinstance(knowledge_categories, list):
                        return [str(c) for c in knowledge_categories if c]
        except Exception as e:
            print(f"获取知识分类配置失败: {e}")
        
        return None
    
    def _build_knowledge_query(self, requirements, message: str) -> str:
        """
        根据需求和消息构建知识检索查询
        """
        query_parts = []
        
        if requirements.topic:
            query_parts.append(requirements.topic)
        if requirements.audience:
            query_parts.append(requirements.audience)
        if requirements.scene:
            query_parts.append(requirements.scene)
        
        if message and len(message) > 3:
            query_parts.append(message)
        
        return " ".join(query_parts) if query_parts else ""
    
    def send_chat_message(
        self,
        agent_id: int,
        user_id: int,
        conversation_id: Optional[int],
        message: Optional[str],
        action_type: str = "message",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[ChatResponse], str]:
        user_agent = self.get_user_agent_by_id(agent_id, user_id)
        if not user_agent:
            return None, "智能体不存在或无权限访问"
        
        is_new_conversation = False
        
        if conversation_id:
            conversation = self.db.query(AgentConversation).filter(
                AgentConversation.id == conversation_id,
                AgentConversation.user_agent_id == agent_id,
                AgentConversation.user_id == user_id
            ).first()
            if not conversation:
                return None, "会话不存在或无权限访问"
        else:
            is_new_conversation = True
            conversation = AgentConversation(
                user_id=user_id,
                user_agent_id=agent_id,
                hermes_profile=user_agent.hermes_profile,
                title=message[:50] if message else "新对话",
                current_stage="welcome",
                status=1,
                message_count=0,
                latest_user_input=message[:1000] if message else None,
            )
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
        
        user_agent.last_used_at = datetime.utcnow()
        conversation.message_count += 1
        conversation.last_message_at = datetime.utcnow()
        if message:
            conversation.latest_user_input = message[:1000]
        
        assistant_content = ""
        structured_result = None
        
        if self._is_ppt_assistant(user_agent):
            interaction_service = self._get_interaction_service_from_conversation(conversation)
            
            knowledge_categories = self._get_knowledge_categories_from_template(user_agent)
            knowledge_context = None
            knowledge_retrieval_service = None
            
            if knowledge_categories is not None:
                knowledge_retrieval_service = KnowledgeRetrievalService(self.db)
                current_reqs = interaction_service.get_requirements()
                knowledge_query = self._build_knowledge_query(current_reqs, message or "")
                
                if knowledge_query:
                    knowledge_context = knowledge_retrieval_service.get_knowledge_context(
                        query=knowledge_query,
                        categories=knowledge_categories if knowledge_categories else None,
                        max_docs=3
                    )
            
            if is_new_conversation and not message:
                welcome_msg = self._get_welcome_message_from_template(user_agent)
                assistant_content = welcome_msg
                structured_result = None
            else:
                actual_message = message if message else ""
                assistant_content, structured_result, new_stage = interaction_service.process_message(
                    message=actual_message,
                    action_type=action_type,
                    is_new_conversation=is_new_conversation
                )
                
                if knowledge_retrieval_service and knowledge_context:
                    current_reqs = interaction_service.get_requirements()
                    topic_for_output = current_reqs.topic if current_reqs else None
                    
                    if new_stage == ConversationStage.OUTLINE_DRAFT:
                        if knowledge_context.get("has_knowledge"):
                            sources = knowledge_context.get("sources", [])
                            if sources:
                                assistant_content += "\n\n📚 以上大纲参考了以下企业资料："
                                for i, source in enumerate(sources, 1):
                                    ref = f"\n{i}. 《{source['title']}》"
                                    if source.get("category"):
                                        ref += f"（{source['category']}）"
                                    assistant_content += ref
                        else:
                            assistant_content += "\n\n⚠️ 说明："
                            if topic_for_output:
                                assistant_content += f"关于「{topic_for_output}」"
                            else:
                                assistant_content += "这份大纲"
                            assistant_content += "未找到企业知识库中的相关资料，以上为通用结构建议。"
                            assistant_content += "\n如需更贴合企业实际的内容，请上传相关资料到知识库。"
                    elif new_stage == ConversationStage.CLARIFYING:
                        if message and len(message) > 3:
                            if not knowledge_context.get("has_knowledge"):
                                pass
                
                self._update_conversation_from_service(
                    conversation, 
                    interaction_service, 
                    structured_result
                )
                
                if new_stage == ConversationStage.COMPLETED and not conversation.final_file_id:
                    try:
                        reqs = interaction_service.get_requirements()
                        template_name = None
                        if reqs and hasattr(reqs, 'style'):
                            template_name = reqs.style
                        
                        generated_file, gen_msg = self.generate_ppt(
                            agent_id=agent_id,
                            conversation_id=conversation.id,
                            user_id=user_id,
                            template_name=template_name,
                            regenerate=False
                        )
                        
                        if generated_file:
                            assistant_content += f"\n\n📎 已生成文件：{generated_file.file_name}"
                            assistant_content += "\n您可以点击下方的下载按钮获取文件。"
                    except Exception as e:
                        print(f"生成PPT失败: {e}")
        else:
            assistant_content = "智能体对话功能开发中..."
            structured_result = None
        
        self.db.commit()
        
        assistant_message = {
            "role": "assistant",
            "content": assistant_content,
        }
        
        return ChatResponse(
            conversation=conversation,
            assistant_message=assistant_message,
            structured_result=structured_result,
        ), "发送成功"
    
    def get_conversations(
        self,
        agent_id: int,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[int] = None,
    ) -> AgentConversationListResponse:
        query = self.db.query(AgentConversation).filter(
            AgentConversation.user_agent_id == agent_id,
            AgentConversation.user_id == user_id
        )
        
        if status is not None:
            query = query.filter(AgentConversation.status == status)
        
        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        
        offset = (page - 1) * page_size
        conversations = query.order_by(
            AgentConversation.last_message_at.desc()
        ).offset(offset).limit(page_size).all()
        
        from app.schemas import AgentConversationResponse
        
        return AgentConversationListResponse(
            items=[AgentConversationResponse.model_validate(c) for c in conversations],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    def get_conversation_detail(
        self,
        conversation_id: int,
        agent_id: int,
        user_id: int,
    ) -> Tuple[Optional[ConversationDetailResponse], str]:
        conversation = self.db.query(AgentConversation).filter(
            AgentConversation.id == conversation_id,
            AgentConversation.user_agent_id == agent_id,
            AgentConversation.user_id == user_id
        ).first()
        
        if not conversation:
            return None, "会话不存在或无权限访问"
        
        files = self.db.query(AgentGeneratedFile).filter(
            AgentGeneratedFile.conversation_id == conversation_id,
            AgentGeneratedFile.user_id == user_id,
            AgentGeneratedFile.deleted_at.is_(None)
        ).all()
        
        file_dicts = []
        for f in files:
            file_dicts.append({
                "id": f.id,
                "file_type": f.file_type,
                "file_name": f.file_name,
                "file_size": f.file_size,
                "template_name": f.template_name,
                "version_no": f.version_no,
                "generation_status": f.generation_status,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            })
        
        from app.schemas import AgentConversationResponse
        
        return ConversationDetailResponse(
            conversation=AgentConversationResponse.model_validate(conversation),
            messages=[],
            structured_result=None,
            files=file_dicts,
        ), "获取成功"
    
    def generate_ppt(
        self,
        agent_id: int,
        conversation_id: int,
        user_id: int,
        template_name: Optional[str],
        regenerate: bool = False,
    ) -> Tuple[Optional[AgentGeneratedFile], str]:
        user_agent = self.get_user_agent_by_id(agent_id, user_id)
        if not user_agent:
            return None, "智能体不存在或无权限访问"
        
        conversation = self.db.query(AgentConversation).filter(
            AgentConversation.id == conversation_id,
            AgentConversation.user_agent_id == agent_id,
            AgentConversation.user_id == user_id
        ).first()
        
        if not conversation:
            return None, "会话不存在或无权限访问"
        
        if not conversation.outline_confirmed:
            return None, "大纲未确认，无法生成"
        
        if not conversation.template_confirmed:
            return None, "模板风格未确认，无法生成"
        
        existing_files = self.db.query(AgentGeneratedFile).filter(
            AgentGeneratedFile.conversation_id == conversation_id,
            AgentGeneratedFile.user_id == user_id,
            AgentGeneratedFile.deleted_at.is_(None)
        ).all()
        
        next_version = len(existing_files) + 1
        
        output_dir = os.path.join(
            settings.GENERATED_FILES_PATH,
            str(user_id),
            str(conversation_id)
        )
        os.makedirs(output_dir, exist_ok=True)
        
        file_name = f"PPT_{conversation_id}_v{next_version}.pptx"
        file_path = os.path.join(output_dir, file_name)
        
        knowledge_categories = self._get_knowledge_categories_from_template(user_agent)
        knowledge_context = None
        
        if knowledge_categories is not None:
            knowledge_retrieval_service = KnowledgeRetrievalService(self.db)
            topic = "未设置主题"
            if conversation.requirements_json:
                try:
                    reqs = json.loads(conversation.requirements_json)
                    topic = reqs.get("topic", "未设置主题")
                except:
                    pass
            
            knowledge_context = knowledge_retrieval_service.get_knowledge_context(
                query=topic,
                categories=knowledge_categories if knowledge_categories else None,
                max_docs=3
            )
        
        try:
            ppt_content = self._create_demo_ppt(
                conversation=conversation,
                version=next_version,
                template_name=template_name,
                knowledge_context=knowledge_context
            )
            with open(file_path, "wb") as f:
                f.write(ppt_content)
            
            file_size = os.path.getsize(file_path)
        except Exception as e:
            return None, f"生成PPT失败: {str(e)}"
        
        generated_file = AgentGeneratedFile(
            user_id=user_id,
            user_agent_id=agent_id,
            conversation_id=conversation_id,
            file_type="pptx",
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            template_name=template_name or "默认模板",
            source_type="regenerated" if regenerate else "generated",
            version_no=next_version,
            generation_status=1,
        )
        
        self.db.add(generated_file)
        self.db.commit()
        self.db.refresh(generated_file)
        
        conversation.final_file_id = generated_file.id
        conversation.current_stage = "completed"
        conversation.status = 2
        conversation.completed_at = datetime.utcnow()
        conversation.final_generation_confirmed = True
        
        self.db.commit()
        
        self._log_operation(
            operator_user_id=user_id,
            target_type="file",
            target_id=generated_file.id,
            action="ppt:generate",
            action_name="生成PPT",
            success=True,
            details={
                "conversation_id": conversation_id,
                "template_name": template_name,
                "version_no": next_version,
            },
        )
        
        return generated_file, "PPT生成成功"
    
    def _create_demo_ppt(
        self, 
        conversation: AgentConversation, 
        version: int,
        template_name: Optional[str],
        knowledge_context: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        创建一个演示用的 PPT 文件
        如果有 python-pptx 库，使用它创建真实的 PPT
        否则，创建一个简单的占位文件
        """
        try:
            from pptx import Presentation
            from pptx.util import Inches, Pt
            from pptx.dml.color import RGBColor
            
            prs = Presentation()
            
            topic = "未设置主题"
            audience = None
            scene = None
            page_count = None
            style = None
            
            if conversation.requirements_json:
                try:
                    reqs = json.loads(conversation.requirements_json)
                    topic = reqs.get("topic", "未设置主题")
                    audience = reqs.get("audience")
                    scene = reqs.get("scene")
                    page_count = reqs.get("page_count")
                    style = reqs.get("style")
                except:
                    pass
            
            title_slide_layout = prs.slide_layouts[0]
            slide = prs.slides.add_slide(title_slide_layout)
            title = slide.shapes.title
            subtitle = slide.placeholders[1]
            
            title.text = topic
            subtitle_text = f"版本 v{version}\n模板: {template_name or '默认'}"
            if style:
                subtitle_text += f"\n风格: {style}"
            subtitle.text = subtitle_text
            
            outline_slide_layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(outline_slide_layout)
            title = slide.shapes.title
            body = slide.placeholders[1]
            
            title.text = "目录"
            tf = body.text_frame
            tf.text = ""
            
            if audience or scene or page_count:
                p = tf.add_paragraph()
                p.text = "【基本信息】"
                p.bold = True
                p.level = 0
                
                if audience:
                    p = tf.add_paragraph()
                    p.text = f"• 目标受众：{audience}"
                    p.level = 1
                if scene:
                    p = tf.add_paragraph()
                    p.text = f"• 使用场景：{scene}"
                    p.level = 1
                if page_count:
                    p = tf.add_paragraph()
                    p.text = f"• 预计页数：{page_count}页"
                    p.level = 1
            
            p = tf.add_paragraph()
            p.text = ""
            p = tf.add_paragraph()
            p.text = "【内容结构】"
            p.bold = True
            p.level = 0
            
            p = tf.add_paragraph()
            p.text = "• 第1页：封面（本页）"
            p.level = 1
            p = tf.add_paragraph()
            p.text = "• 第2页：目录（本页）"
            p.level = 1
            p = tf.add_paragraph()
            p.text = "• 第3页：正文内容"
            p.level = 1
            
            if knowledge_context and knowledge_context.get("has_knowledge"):
                p = tf.add_paragraph()
                p.text = "• 第4页：参考资料（来自知识库）"
                p.level = 1
                p = tf.add_paragraph()
                p.text = "• 第5页：总结与说明"
                p.level = 1
            else:
                p = tf.add_paragraph()
                p.text = "• 第4页：总结与说明"
                p.level = 1
            
            content_slide_layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(content_slide_layout)
            title = slide.shapes.title
            body = slide.placeholders[1]
            
            title.text = "正文内容"
            tf = body.text_frame
            tf.text = "这是一个由 AgentNow 智能体平台生成的 PPT。"
            
            p = tf.add_paragraph()
            p.text = ""
            p = tf.add_paragraph()
            p.text = "【需求信息】"
            p.bold = True
            
            if audience:
                p = tf.add_paragraph()
                p.text = f"• 目标受众：{audience}"
            if scene:
                p = tf.add_paragraph()
                p.text = f"• 使用场景：{scene}"
            if page_count:
                p = tf.add_paragraph()
                p.text = f"• 预计页数：{page_count}"
            if style:
                p = tf.add_paragraph()
                p.text = f"• 展示风格：{style}"
            
            if knowledge_context and knowledge_context.get("has_knowledge"):
                sources = knowledge_context.get("sources", [])
                if sources:
                    reference_slide_layout = prs.slide_layouts[1]
                    slide = prs.slides.add_slide(reference_slide_layout)
                    title = slide.shapes.title
                    body = slide.placeholders[1]
                    
                    title.text = "参考资料（企业知识库）"
                    tf = body.text_frame
                    tf.text = "以下内容来自企业知识库："
                    
                    for i, source in enumerate(sources, 1):
                        p = tf.add_paragraph()
                        p.text = ""
                        p = tf.add_paragraph()
                        p.text = f"{i}. 《{source['title']}》"
                        p.bold = True
                        if source.get("category"):
                            p = tf.add_paragraph()
                            p.text = f"   分类：{source['category']}"
                    
                    knowledge_text = knowledge_context.get("knowledge_text", "")
                    if knowledge_text and len(knowledge_text) > 0:
                        p = tf.add_paragraph()
                        p.text = ""
                        p = tf.add_paragraph()
                        p.text = "【资料摘要】"
                        p.bold = True
                        
                        content_lines = knowledge_text[:800].split('\n')
                        for line in content_lines[:15]:
                            if line.strip():
                                p = tf.add_paragraph()
                                p.text = line[:80]
                                p.level = 1
            
            summary_slide_layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(summary_slide_layout)
            title = slide.shapes.title
            body = slide.placeholders[1]
            
            title.text = "总结与说明"
            tf = body.text_frame
            tf.text = "PPT 生成完成！"
            
            p = tf.add_paragraph()
            p.text = ""
            p = tf.add_paragraph()
            p.text = "【生成信息】"
            p.bold = True
            
            p = tf.add_paragraph()
            p.text = f"• 会话ID: {conversation.id}"
            p = tf.add_paragraph()
            p.text = f"• 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            p = tf.add_paragraph()
            p.text = f"• 版本: v{version}"
            
            p = tf.add_paragraph()
            p.text = ""
            p = tf.add_paragraph()
            p.text = "【说明】"
            p.bold = True
            
            if knowledge_context and knowledge_context.get("has_knowledge"):
                p = tf.add_paragraph()
                p.text = "✓ 本 PPT 内容参考了企业知识库中的相关资料"
                p.level = 1
            else:
                p = tf.add_paragraph()
                p.text = "⚠ 本 PPT 为通用结构建议，未找到企业知识库中的相关资料"
                p.level = 1
                p = tf.add_paragraph()
                p.text = "  如需更贴合企业实际的内容，请上传相关资料到知识库"
                p.level = 1
            
            import io
            output = io.BytesIO()
            prs.save(output)
            output.seek(0)
            return output.read()
            
        except ImportError:
            placeholder_content = f"""PPT 演示文件
================
会话ID: {conversation.id}
版本: v{version}
模板: {template_name or '默认'}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

说明：
- 此为演示版本
- 正式版本将生成真实的 .pptx 文件
- 请安装 python-pptx 库以启用完整功能

需求信息：
{conversation.requirements_json or '未记录详细需求'}

知识检索状态：
"""
            
            if knowledge_context and knowledge_context.get("has_knowledge"):
                placeholder_content += "✓ 已检索到企业知识库资料\n"
                sources = knowledge_context.get("sources", [])
                for i, source in enumerate(sources, 1):
                    placeholder_content += f"  {i}. {source['title']}"
                    if source.get("category"):
                        placeholder_content += f"（{source['category']}）"
                    placeholder_content += "\n"
            else:
                placeholder_content += "⚠ 未检索到企业知识库中的相关资料\n"
                placeholder_content += "  本内容为通用建议\n"
            
            return placeholder_content.encode('utf-8')
    
    def download_generated_file(
        self,
        file_id: int,
        agent_id: int,
        user_id: int,
    ) -> Tuple[Optional[bytes], Optional[str], str, str]:
        generated_file = self.db.query(AgentGeneratedFile).filter(
            AgentGeneratedFile.id == file_id,
            AgentGeneratedFile.user_agent_id == agent_id,
            AgentGeneratedFile.user_id == user_id,
            AgentGeneratedFile.deleted_at.is_(None)
        ).first()
        
        if not generated_file:
            return None, None, "", "文件不存在或无权限访问"
        
        if generated_file.generation_status != 1:
            return None, None, "", "文件生成未完成或已失败"
        
        file_path = generated_file.file_path
        if not file_path or not os.path.exists(file_path):
            return None, None, "", "文件已删除或不可访问"
        
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
            return file_content, generated_file.mime_type, generated_file.file_name, "获取成功"
        except Exception as e:
            return None, None, "", f"读取文件失败: {str(e)}"
