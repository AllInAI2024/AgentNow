import re
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class ConversationStage(Enum):
    WELCOME = "welcome"
    CLARIFYING = "clarifying"
    OUTLINE_DRAFT = "outline_draft"
    OUTLINE_CONFIRMED = "outline_confirmed"
    TEMPLATE_SELECT = "template_select"
    FINAL_GENERATING = "final_generating"
    COMPLETED = "completed"


@dataclass
class PPTRequirements:
    topic: Optional[str] = None
    audience: Optional[str] = None
    scene: Optional[str] = None
    page_count: Optional[int] = None
    style: Optional[str] = None
    must_reference_materials: Optional[str] = None
    use_standard_template: Optional[bool] = None


class PPTAssistantInteractionService:
    """
    PPT 助手交互服务
    负责处理对话流程：欢迎语 -> 补问 -> 大纲 -> 确认 -> 生成
    """
    
    WELCOME_MESSAGE = """你好，我是企业 PPT 助手。

你可以直接告诉我：
1. 这份 PPT 是做什么用的
2. 是给谁看的
3. 想做多少页
4. 有没有必须引用的公司资料

如果你暂时说不全，我也会一步一步带你把这件事理顺。"""

    CLARIFY_QUESTIONS_TEMPLATE = """为了把这份 PPT 做得更贴合你的实际场景，我先确认几个关键信息：

1. 这份 PPT 是给谁看的？
2. 主要用在什么场景？
3. 你希望控制在多少页左右？
4. 风格更偏正式汇报、客户介绍，还是销售展示？
5. 有没有必须引用的公司资料、产品资料或案例？

你先按你知道的部分告诉我，不完整也没关系，我会继续帮你补齐。"""

    def __init__(self):
        self._requirements = PPTRequirements()
        self._current_stage = ConversationStage.WELCOME
        self._outline_draft: Optional[List[Dict[str, Any]]] = None
        self._messages_history: List[Dict[str, Any]] = []
    
    def _add_message(self, role: str, content: str):
        self._messages_history.append({
            "role": role,
            "content": content,
        })
    
    def _parse_user_input(self, message: str) -> Dict[str, Any]:
        """
        解析用户输入，提取关键信息
        """
        result = {
            "topic": None,
            "audience": None,
            "scene": None,
            "page_count": None,
            "style": None,
        }
        
        message_lower = message.lower()
        
        page_match = re.search(r'(\d+)\s*[页p]', message)
        if page_match:
            result["page_count"] = int(page_match.group(1))
        
        audience_keywords = [
            ("客户", "客户"),
            ("老板", "老板"),
            ("领导", "领导"),
            ("内部", "内部"),
            ("同事", "同事"),
            ("投资者", "投资者"),
            ("管理层", "管理层"),
        ]
        for keyword, value in audience_keywords:
            if keyword in message:
                result["audience"] = value
                break
        
        scene_keywords = [
            ("汇报", "内部汇报"),
            ("介绍", "介绍"),
            ("宣讲", "宣讲"),
            ("拜访", "客户拜访"),
            ("投标", "投标"),
            ("评审", "评审"),
        ]
        for keyword, value in scene_keywords:
            if keyword in message:
                result["scene"] = value
                break
        
        style_keywords = [
            ("正式", "正式汇报"),
            ("销售", "销售展示"),
            ("简洁", "简洁风格"),
            ("创意", "创意风格"),
        ]
        for keyword, value in style_keywords:
            if keyword in message:
                result["style"] = value
                break
        
        topic_indicators = ["关于", "做一份", "帮我", "我需要", "想做", "主题是", "关于"]
        for indicator in topic_indicators:
            if indicator in message:
                parts = message.split(indicator)
                if len(parts) > 1:
                    potential_topic = parts[1].strip()
                    if len(potential_topic) > 2:
                        result["topic"] = potential_topic[:50]
                        break
        
        if not result["topic"] and len(message) > 5:
            result["topic"] = message[:50]
        
        return result
    
    def _update_requirements(self, parsed: Dict[str, Any]):
        """
        更新需求信息
        """
        if parsed.get("topic"):
            self._requirements.topic = parsed["topic"]
        if parsed.get("audience"):
            self._requirements.audience = parsed["audience"]
        if parsed.get("scene"):
            self._requirements.scene = parsed["scene"]
        if parsed.get("page_count"):
            self._requirements.page_count = parsed["page_count"]
        if parsed.get("style"):
            self._requirements.style = parsed["style"]
    
    def _get_missing_info(self) -> List[str]:
        """
        获取缺失的关键信息
        """
        missing = []
        
        if not self._requirements.topic:
            missing.append("PPT 的主题/用途")
        if not self._requirements.audience:
            missing.append("目标受众")
        if not self._requirements.scene:
            missing.append("使用场景")
        if not self._requirements.page_count:
            missing.append("预计页数")
        
        return missing
    
    def _generate_clarify_response(self, missing: List[str]) -> str:
        """
        生成补问响应
        """
        if not missing:
            return ""
        
        response = "我还需要了解几个关键信息，才能帮你做出更贴合实际的 PPT：\n\n"
        
        for i, item in enumerate(missing, 1):
            response += f"{i}. {item}\n"
        
        response += "\n你可以一次性告诉我这些信息，也可以先回答你知道的部分。"
        
        return response
    
    def _generate_outline(self) -> Tuple[List[Dict[str, Any]], str]:
        """
        生成 PPT 大纲
        """
        topic = self._requirements.topic or "演示文稿"
        page_count = self._requirements.page_count or 10
        audience = self._requirements.audience or "受众"
        scene = self._requirements.scene or "场景"
        
        outline = []
        
        outline.append({
            "index": 1,
            "title": "封面",
            "subtitle": f"{topic} - {scene}",
            "bullets": [
                f"主题：{topic}",
                f"场景：{scene}"
            ],
            "speaker_notes": "这是第一页，建议保持简洁大方。"
        })
        
        outline.append({
            "index": 2,
            "title": "目录/议程",
            "subtitle": "本次演示内容概览",
            "bullets": [
                "背景与目标",
                "核心内容",
                "行动建议",
                "总结与展望"
            ],
            "speaker_notes": "用目录让听众快速了解整体结构。"
        })
        
        content_pages = min(page_count - 5, 6)
        for i in range(content_pages):
            page_index = i + 3
            if i == 0:
                outline.append({
                    "index": page_index,
                    "title": "背景与目标",
                    "subtitle": "我们为什么要做这件事",
                    "bullets": [
                        "当前背景介绍",
                        "核心目标是什么",
                        "预期达成什么效果"
                    ],
                    "speaker_notes": "先讲清楚背景，让听众进入状态。"
                })
            elif i == 1:
                outline.append({
                    "index": page_index,
                    "title": "核心方案",
                    "subtitle": "我们的解决方案",
                    "bullets": [
                        "方案核心要点",
                        "关键优势",
                        "与其他方案的区别"
                    ],
                    "speaker_notes": "这是核心内容页，建议突出重点。"
                })
            elif i == 2:
                outline.append({
                    "index": page_index,
                    "title": "实施路径",
                    "subtitle": "如何落地执行",
                    "bullets": [
                        "关键步骤",
                        "时间规划",
                        "资源需求"
                    ],
                    "speaker_notes": "讲清楚怎么做，让方案更可信。"
                })
            elif i == 3:
                outline.append({
                    "index": page_index,
                    "title": "预期效果",
                    "subtitle": "能带来什么价值",
                    "bullets": [
                        "直接收益",
                        "间接价值",
                        "成功案例参考"
                    ],
                    "speaker_notes": "用数据或案例支撑预期效果。"
                })
            elif i == 4:
                outline.append({
                    "index": page_index,
                    "title": "风险与应对",
                    "subtitle": "可能遇到的问题及解决方案",
                    "bullets": [
                        "潜在风险点",
                        "应对措施",
                        "应急预案"
                    ],
                    "speaker_notes": "展示思考的全面性。"
                })
            else:
                outline.append({
                    "index": page_index,
                    "title": f"补充内容 {i-4}",
                    "subtitle": "根据实际需要调整",
                    "bullets": [
                        "要点一",
                        "要点二",
                        "要点三"
                    ],
                    "speaker_notes": "这部分内容可以根据具体主题调整。"
                })
        
        outline.append({
            "index": len(outline) + 1,
            "title": "总结",
            "subtitle": "核心要点回顾",
            "bullets": [
                "我们要做什么",
                "为什么要做",
                "预期达成什么效果"
            ],
            "speaker_notes": "简洁总结，强化记忆点。"
        })
        
        outline.append({
            "index": len(outline) + 1,
            "title": "Q&A",
            "subtitle": "感谢聆听，欢迎提问",
            "bullets": [],
            "speaker_notes": "留出时间回答问题。"
        })
        
        outline_text = f"""# {topic}

适用场景：{scene}
目标受众：{audience}
建议页数：{len(outline)} 页

## 页面设计：
"""
        for slide in outline:
            outline_text += f"\n{slide['index']}. 第{slide['index']}页：{slide['title']}"
        
        outline_text += f"""

## 每页文案：
"""
        for slide in outline:
            outline_text += f"""
第{slide['index']}页：{slide['title']}
- 标题：{slide['title']}
- 副标题：{slide['subtitle']}
- 要点：
"""
            for bullet in slide['bullets']:
                outline_text += f"  - {bullet}\n"
            outline_text += f"- 演讲备注：{slide['speaker_notes']}\n"
        
        return outline, outline_text
    
    def _generate_outline_confirmation_message(self, outline_text: str) -> str:
        """
        生成大纲确认消息
        """
        return f"""这是我根据你提供的信息整理的第一版大纲。

{outline_text}

---

你先看整体结构对不对。

如果这版结构没问题，我就继续补全逐页内容；如果哪里不合适，你直接告诉我删哪一页、补哪一页，或者整体风格往哪个方向调。"""
    
    def _is_confirmation_message(self, message: str) -> bool:
        """
        判断用户消息是否是确认
        """
        confirm_keywords = [
            "可以", "没问题", "确认", "好的", "就这样",
            "继续", "往下做", "没问题的", "对的", "是的",
            "ok", "OK", "行", "可以的"
        ]
        
        for keyword in confirm_keywords:
            if keyword in message:
                return True
        
        return False
    
    def _is_revision_message(self, message: str) -> bool:
        """
        判断用户消息是否是修改意见
        """
        revision_keywords = [
            "改", "修改", "调整", "换", "增加", "删除",
            "不要", "需要加", "加一页", "删一页", "不对",
            "不太对", "再想想", "重新", "换个"
        ]
        
        for keyword in revision_keywords:
            if keyword in message:
                return True
        
        return False
    
    def _parse_numeric_selection(self, message: str) -> Optional[int]:
        """
        解析用户输入的数字选择（如"1"、"2"等）
        返回选择的数字，如果没有数字选择则返回 None
        """
        import re
        
        stripped_message = message.strip()
        
        match = re.match(r'^(\d+)[、.．，,：:\s]*$', stripped_message)
        if match:
            return int(match.group(1))
        
        match = re.match(r'^选[择]?[：:：]?\s*(\d+)', stripped_message)
        if match:
            return int(match.group(1))
        
        match = re.match(r'^第(\d+)[个项]?$', stripped_message)
        if match:
            return int(match.group(1))
        
        if stripped_message in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            return int(stripped_message)
        
        return None
    
    def process_message(
        self, 
        message: str, 
        action_type: str = "message",
        is_new_conversation: bool = False
    ) -> Tuple[str, Optional[Dict[str, Any]], ConversationStage]:
        """
        处理用户消息，生成响应
        
        Returns:
            - assistant_message: 助手回复文本
            - structured_result: 结构化结果（如大纲）
            - current_stage: 当前会话阶段
        """
        self._add_message("user", message)
        
        if is_new_conversation and self._current_stage == ConversationStage.WELCOME:
            welcome = self.WELCOME_MESSAGE
            self._add_message("assistant", welcome)
            return welcome, None, ConversationStage.WELCOME
        
        parsed = self._parse_user_input(message)
        self._update_requirements(parsed)
        
        if action_type == "confirm_outline":
            self._current_stage = ConversationStage.OUTLINE_CONFIRMED
            response = "好的，大纲已确认。接下来我建议把展示风格也定下来。\n\n你可以告诉我：\n1. 想用公司标准模板\n2. 还是更偏正式汇报、客户介绍、销售展示的风格\n\n这个定下来以后，后面的正式文件会更稳。"
            self._add_message("assistant", response)
            return response, None, ConversationStage.TEMPLATE_SELECT
        
        if action_type == "confirm_template":
            self._current_stage = ConversationStage.FINAL_GENERATING
            response = "我准备开始生成正式 PPT 文件了。\n\n我先最后确认三件事：\n1. 页数你这边确认了\n2. 大纲结构没有问题\n3. 展示风格或模板已经定下来\n\n如果你确认，我就按这个版本出正式文件。"
            self._add_message("assistant", response)
            return response, None, ConversationStage.FINAL_GENERATING
        
        if self._current_stage == ConversationStage.WELCOME:
            if not message or message.strip() == "":
                self._current_stage = ConversationStage.CLARIFYING
                response = self.CLARIFY_QUESTIONS_TEMPLATE
                self._add_message("assistant", response)
                return response, None, ConversationStage.CLARIFYING
            
            missing = self._get_missing_info()
            
            if len(missing) >= 2:
                self._current_stage = ConversationStage.CLARIFYING
                response = self._generate_clarify_response(missing)
                self._add_message("assistant", response)
                return response, None, ConversationStage.CLARIFYING
            else:
                self._current_stage = ConversationStage.OUTLINE_DRAFT
                self._outline_draft, outline_text = self._generate_outline()
                response = self._generate_outline_confirmation_message(outline_text)
                
                structured_result = {
                    "type": "ppt_outline",
                    "title": self._requirements.topic or "PPT 大纲",
                    "slides": self._outline_draft,
                    "requirements": {
                        "topic": self._requirements.topic,
                        "audience": self._requirements.audience,
                        "scene": self._requirements.scene,
                        "page_count": self._requirements.page_count,
                        "style": self._requirements.style,
                    }
                }
                
                self._add_message("assistant", response)
                return response, structured_result, ConversationStage.OUTLINE_DRAFT
        
        elif self._current_stage == ConversationStage.CLARIFYING:
            missing = self._get_missing_info()
            
            if len(missing) >= 1:
                response = self._generate_clarify_response(missing)
                self._add_message("assistant", response)
                return response, None, ConversationStage.CLARIFYING
            else:
                self._current_stage = ConversationStage.OUTLINE_DRAFT
                self._outline_draft, outline_text = self._generate_outline()
                response = self._generate_outline_confirmation_message(outline_text)
                
                structured_result = {
                    "type": "ppt_outline",
                    "title": self._requirements.topic or "PPT 大纲",
                    "slides": self._outline_draft,
                    "requirements": {
                        "topic": self._requirements.topic,
                        "audience": self._requirements.audience,
                        "scene": self._requirements.scene,
                        "page_count": self._requirements.page_count,
                        "style": self._requirements.style,
                    }
                }
                
                self._add_message("assistant", response)
                return response, structured_result, ConversationStage.OUTLINE_DRAFT
        
        elif self._current_stage == ConversationStage.OUTLINE_DRAFT:
            if self._is_confirmation_message(message):
                self._current_stage = ConversationStage.OUTLINE_CONFIRMED
                response = "好的，大纲已确认。接下来我建议把展示风格也定下来。\n\n你可以告诉我：\n1. 想用公司标准模板\n2. 还是更偏正式汇报、客户介绍、销售展示的风格\n\n这个定下来以后，后面的正式文件会更稳。"
                self._add_message("assistant", response)
                return response, None, ConversationStage.TEMPLATE_SELECT
            
            elif self._is_revision_message(message):
                response = f"收到，我来调整大纲。你说的是：{message}\n\n我理解你希望调整的方向，我来重新整理一版大纲。\n\n（注：第一版先用规则引擎，后续可以接入 LLM 来理解更复杂的修改意见）\n\n目前版本的大纲信息：\n- 主题：{self._requirements.topic}\n- 受众：{self._requirements.audience}\n- 场景：{self._requirements.scene}\n- 页数：{self._requirements.page_count}\n\n你可以更具体地告诉我：\n1. 哪几页需要增加\n2. 哪几页需要删除\n3. 哪些部分需要更正式、更多销售感，或更偏管理层汇报"
                self._add_message("assistant", response)
                return response, None, ConversationStage.OUTLINE_DRAFT
            
            else:
                missing = self._get_missing_info()
                if missing:
                    self._current_stage = ConversationStage.CLARIFYING
                    response = self._generate_clarify_response(missing)
                    self._add_message("assistant", response)
                    return response, None, ConversationStage.CLARIFYING
                
                response = "我理解你可能在补充信息。让我再确认一下当前状态：\n\n已收集的信息：\n"
                if self._requirements.topic:
                    response += f"- 主题：{self._requirements.topic}\n"
                if self._requirements.audience:
                    response += f"- 受众：{self._requirements.audience}\n"
                if self._requirements.scene:
                    response += f"- 场景：{self._requirements.scene}\n"
                if self._requirements.page_count:
                    response += f"- 页数：{self._requirements.page_count}\n"
                
                response += "\n如果信息已经完整，你可以说「确认」或「继续」，我来生成大纲；如果还需要补充，继续告诉我就好。"
                self._add_message("assistant", response)
                return response, None, ConversationStage.OUTLINE_DRAFT
        
        elif self._current_stage == ConversationStage.OUTLINE_CONFIRMED:
            self._current_stage = ConversationStage.TEMPLATE_SELECT
            response = "好的，接下来我们定一下展示风格。\n\n你可以选择：\n1. 使用公司标准模板\n2. 使用更正式的汇报模板\n3. 使用更偏客户介绍的展示模板\n\n确认后我再生成正式 PPT 文件。"
            self._add_message("assistant", response)
            return response, None, ConversationStage.TEMPLATE_SELECT
        
        elif self._current_stage == ConversationStage.TEMPLATE_SELECT:
            numeric_selection = self._parse_numeric_selection(message)
            
            if numeric_selection is not None:
                self._requirements.style = {
                    1: "公司标准模板",
                    2: "正式汇报风格",
                    3: "客户介绍风格",
                    4: "销售展示风格"
                }.get(numeric_selection, "标准风格")
                self._requirements.use_standard_template = (numeric_selection == 1)
                
                self._current_stage = ConversationStage.FINAL_GENERATING
                response = f"好的，已选择「{self._requirements.style}」。\n\n我准备开始生成正式 PPT 文件了。\n\n我先最后确认三件事：\n1. 页数你这边确认了\n2. 大纲结构没有问题\n3. 展示风格或模板已经定下来\n\n如果你确认，我就按这个版本出正式文件。"
                self._add_message("assistant", response)
                return response, None, ConversationStage.FINAL_GENERATING
            
            if self._is_confirmation_message(message) or "标准" in message or "正式" in message or "销售" in message or "客户" in message:
                if "标准" in message:
                    self._requirements.style = "公司标准模板"
                    self._requirements.use_standard_template = True
                elif "正式" in message:
                    self._requirements.style = "正式汇报风格"
                elif "销售" in message:
                    self._requirements.style = "销售展示风格"
                elif "客户" in message:
                    self._requirements.style = "客户介绍风格"
                
                self._current_stage = ConversationStage.FINAL_GENERATING
                response = "我准备开始生成正式 PPT 文件了。\n\n我先最后确认三件事：\n1. 页数你这边确认了\n2. 大纲结构没有问题\n3. 展示风格或模板已经定下来\n\n如果你确认，我就按这个版本出正式文件。"
                self._add_message("assistant", response)
                return response, None, ConversationStage.FINAL_GENERATING
            else:
                response = "你可以告诉我想用哪种风格，直接回复数字即可：\n1. 公司标准模板\n2. 正式汇报风格\n3. 客户介绍风格\n4. 销售展示风格"
                self._add_message("assistant", response)
                return response, None, ConversationStage.TEMPLATE_SELECT
        
        elif self._current_stage == ConversationStage.FINAL_GENERATING:
            numeric_selection = self._parse_numeric_selection(message)
            
            if numeric_selection is not None or self._is_confirmation_message(message):
                self._current_stage = ConversationStage.COMPLETED
                response = "好的，我开始生成正式 PPT 文件。\n\n（注：第一版先生成结构化内容，后续接入 PPT 生成服务后可导出 .pptx 文件）\n\n当前已确认的信息：\n"
                if self._requirements.topic:
                    response += f"- 主题：{self._requirements.topic}\n"
                if self._requirements.audience:
                    response += f"- 受众：{self._requirements.audience}\n"
                if self._requirements.scene:
                    response += f"- 场景：{self._requirements.scene}\n"
                if self._requirements.page_count:
                    response += f"- 页数：{self._requirements.page_count}\n"
                if self._requirements.style:
                    response += f"- 风格：{self._requirements.style}\n"
                
                response += "\nPPT 已准备就绪！"
                self._add_message("assistant", response)
                return response, None, ConversationStage.COMPLETED
            else:
                response = "我已经准备好了。如果你确认要生成正式 PPT，直接回复「确认」或「1」即可。"
                self._add_message("assistant", response)
                return response, None, ConversationStage.FINAL_GENERATING
        
        response = "收到你的消息了。让我先确认一下当前的状态。\n\n你可以告诉我：\n1. 想调整大纲\n2. 想确认继续\n3. 或者有其他需求"
        self._add_message("assistant", response)
        return response, None, self._current_stage
    
    def get_current_stage(self) -> ConversationStage:
        return self._current_stage
    
    def get_requirements(self) -> PPTRequirements:
        return self._requirements
    
    def get_outline_draft(self) -> Optional[List[Dict[str, Any]]]:
        return self._outline_draft
