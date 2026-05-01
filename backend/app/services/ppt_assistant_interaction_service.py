import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


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
    PPT 助手交互服务。
    第一版不做通用流程引擎，但要把前 5 步做扎实：
    动态补问 -> 输出大纲 -> 确认大纲 -> 选择风格 -> 最终生成前确认。
    """

    WELCOME_MESSAGE = """你好，我是企业 PPT 助手。

你可以直接告诉我：
1. 这份 PPT 是做什么用的
2. 是给谁看的
3. 想做多少页
4. 有没有必须引用的公司资料

如果你暂时说不全，我也会一步一步带你把这件事理顺。"""

    def __init__(self):
        self._requirements = PPTRequirements()
        self._current_stage = ConversationStage.WELCOME
        self._outline_draft: Optional[List[Dict[str, Any]]] = None
        self._structured_result: Optional[Dict[str, Any]] = None
        self._messages_history: List[Dict[str, Any]] = []

    def load_state(
        self,
        *,
        current_stage: Optional[str] = None,
        requirements: Optional[Dict[str, Any]] = None,
        outline_draft: Optional[List[Dict[str, Any]]] = None,
        structured_result: Optional[Dict[str, Any]] = None,
        messages_history: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        if current_stage:
            try:
                self._current_stage = ConversationStage(current_stage)
            except ValueError:
                self._current_stage = ConversationStage.WELCOME

        if requirements:
            self._requirements = PPTRequirements(
                topic=requirements.get("topic"),
                audience=requirements.get("audience"),
                scene=requirements.get("scene"),
                page_count=requirements.get("page_count"),
                style=requirements.get("style"),
                must_reference_materials=requirements.get("must_reference_materials"),
                use_standard_template=requirements.get("use_standard_template"),
            )

        if outline_draft:
            self._outline_draft = outline_draft

        if structured_result:
            self._structured_result = structured_result

        if messages_history:
            self._messages_history = messages_history

    def export_state(self) -> Dict[str, Any]:
        return {
            "current_stage": self._current_stage.value,
            "requirements": asdict(self._requirements),
            "outline_draft": self._outline_draft,
            "structured_result": self._structured_result,
            "messages_history": self._messages_history,
        }

    def _add_message(self, role: str, content: str) -> None:
        if not content:
            return
        self._messages_history.append({
            "role": role,
            "content": content,
        })

    def _normalize_page_count(self, page_count: Optional[int]) -> int:
        if not page_count:
            return 8
        return max(6, min(page_count, 16))

    def _parse_user_input(self, message: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "topic": None,
            "audience": None,
            "scene": None,
            "page_count": None,
            "style": None,
            "must_reference_materials": None,
            "use_standard_template": None,
        }

        cleaned = message.strip()
        if not cleaned:
            return result

        page_match = re.search(r"(\d{1,2})\s*(页|p|P|slide|slides)", cleaned)
        if page_match:
            result["page_count"] = int(page_match.group(1))

        audience_patterns = [
            (r"(给|面向|向)(客户|客户方)", "客户"),
            (r"(给|面向|向)(老板|领导|管理层)", "管理层"),
            (r"(给|面向|向)(内部团队|内部同事|同事)", "内部团队"),
            (r"(给|面向|向)(投资人|投资者)", "投资者"),
            (r"(给|面向|向)(合作伙伴)", "合作伙伴"),
        ]
        for pattern, value in audience_patterns:
            if re.search(pattern, cleaned):
                result["audience"] = value
                break

        if not result["audience"]:
            audience_keywords = [
                ("客户", "客户"),
                ("老板", "管理层"),
                ("领导", "管理层"),
                ("管理层", "管理层"),
                ("内部", "内部团队"),
                ("同事", "内部团队"),
                ("投资者", "投资者"),
            ]
            for keyword, value in audience_keywords:
                if keyword in cleaned:
                    result["audience"] = value
                    break

        scene_keywords = [
            ("公司介绍", "公司介绍"),
            ("产品介绍", "产品介绍"),
            ("产品宣讲", "产品宣讲"),
            ("售前", "售前宣讲"),
            ("客户拜访", "客户拜访"),
            ("汇报", "内部汇报"),
            ("方案", "方案说明"),
            ("路演", "路演"),
            ("评审", "方案评审"),
        ]
        for keyword, value in scene_keywords:
            if keyword in cleaned:
                result["scene"] = value
                break

        style_keywords = [
            ("正式", "正式汇报风格"),
            ("管理层", "正式汇报风格"),
            ("客户介绍", "客户介绍风格"),
            ("销售", "销售展示风格"),
            ("简洁", "简洁商务风格"),
            ("商务", "简洁商务风格"),
        ]
        for keyword, value in style_keywords:
            if keyword in cleaned:
                result["style"] = value
                break

        if "标准模板" in cleaned or "公司模板" in cleaned:
            result["style"] = "公司标准模板"
            result["use_standard_template"] = True

        materials_match = re.search(r"(必须引用|需要引用|参考|基于)(.+?)(资料|材料|文档|案例)", cleaned)
        if materials_match:
            result["must_reference_materials"] = materials_match.group(2).strip()

        topic_patterns = [
            r"帮我做一份(.+?)(?:PPT|ppt)",
            r"做一份(.+?)(?:PPT|ppt)",
            r"写一份(.+?)(?:PPT|ppt)",
            r"关于(.+?)(?:的PPT|PPT|ppt)",
        ]
        for pattern in topic_patterns:
            match = re.search(pattern, cleaned)
            if match:
                topic = match.group(1).strip("：:，,。. ")
                if len(topic) >= 2:
                    result["topic"] = topic[:80]
                    break

        if not result["topic"]:
            explicit_topics = ["公司介绍", "产品介绍", "客户拜访汇报", "售前宣讲", "内部季度汇报", "解决方案汇报"]
            for topic in explicit_topics:
                if topic in cleaned:
                    result["topic"] = topic
                    break

        if not result["topic"] and len(cleaned) > 6:
            candidate = re.sub(r"(帮我|做一份|写一份|我需要|我想做|请|给我)", "", cleaned).strip()
            if candidate:
                result["topic"] = candidate[:80]

        return result

    def _update_requirements(self, parsed: Dict[str, Any]) -> List[str]:
        updated_fields: List[str] = []
        for field in [
            "topic",
            "audience",
            "scene",
            "page_count",
            "style",
            "must_reference_materials",
            "use_standard_template",
        ]:
            value = parsed.get(field)
            if value is not None and value != "":
                if getattr(self._requirements, field) != value:
                    setattr(self._requirements, field, value)
                    updated_fields.append(field)
        return updated_fields

    def _get_required_missing_keys(self) -> List[str]:
        missing = []
        if not self._requirements.topic:
            missing.append("topic")
        if not self._requirements.audience:
            missing.append("audience")
        if not self._requirements.scene:
            missing.append("scene")
        if not self._requirements.page_count:
            missing.append("page_count")
        return missing

    def _format_requirements_summary(self) -> str:
        lines = []
        if self._requirements.topic:
            lines.append(f"- 主题：{self._requirements.topic}")
        if self._requirements.audience:
            lines.append(f"- 受众：{self._requirements.audience}")
        if self._requirements.scene:
            lines.append(f"- 场景：{self._requirements.scene}")
        if self._requirements.page_count:
            lines.append(f"- 页数：{self._requirements.page_count} 页")
        if self._requirements.style:
            lines.append(f"- 风格：{self._requirements.style}")
        if self._requirements.must_reference_materials:
            lines.append(f"- 必须参考资料：{self._requirements.must_reference_materials}")
        return "\n".join(lines)

    def _generate_dynamic_clarify_response(self, missing_keys: List[str], updated_fields: Optional[List[str]] = None) -> str:
        intro = "为了把这份 PPT 做得更贴合你的实际场景，我先补齐几个关键信息："
        if updated_fields:
            collected = []
            field_labels = {
                "topic": "主题",
                "audience": "受众",
                "scene": "场景",
                "page_count": "页数",
                "style": "风格",
            }
            for field in updated_fields:
                if field in field_labels:
                    collected.append(field_labels[field])
            if collected:
                intro = f"收到，你已经补充了{ '、'.join(collected) }。为了继续往下做，我还想确认："

        question_map = {
            "topic": "这份 PPT 的主题/核心用途是什么？",
            "audience": "这份 PPT 主要是给谁看的？",
            "scene": "它主要用在什么场景？比如客户介绍、内部汇报、售前宣讲。",
            "page_count": "你希望大概控制在多少页左右？",
            "style": "你希望风格更偏正式汇报、客户介绍，还是销售展示？",
        }

        lines = [intro, ""]
        for index, key in enumerate(missing_keys, start=1):
            lines.append(f"{index}. {question_map[key]}")

        if self._requirements.must_reference_materials:
            lines.extend(["", f"我已记住需要参考的资料方向：{self._requirements.must_reference_materials}。"])

        lines.extend(["", "你先按知道的部分回复就行，不用一次性说全。"])
        return "\n".join(lines)

    def _infer_outline_sections(self) -> List[Tuple[str, str, List[str], str]]:
        topic = self._requirements.topic or "本次汇报"
        scene = self._requirements.scene or "汇报场景"
        audience = self._requirements.audience or "目标受众"

        if "公司介绍" in topic or scene == "公司介绍":
            return [
                ("封面", f"{topic} - 面向{audience}", [f"主题：{topic}", f"适用场景：{scene}"], "开场页建议突出公司定位与沟通场景。"),
                ("目录", "本次介绍结构", ["公司概况", "核心能力", "产品与方案", "合作价值"], "让听众先建立整体预期。"),
                ("公司概况", "快速建立基础认知", ["公司定位", "发展阶段", "核心业务"], "适合用 3 个关键事实建立信任。"),
                ("核心能力", "我们能解决什么问题", ["能力一", "能力二", "能力三"], "避免写成流水账，突出差异化。"),
                ("产品与方案", "核心产品或解决方案概览", ["产品矩阵", "典型应用", "关键优势"], "聚焦与受众最相关的能力。"),
                ("典型案例", "增强可信度", ["行业案例", "客户收益", "落地成果"], "优先引用企业知识库里的真实案例。"),
                ("合作方式", "下一步如何推进", ["合作流程", "支持方式", "里程碑"], "帮助听众自然进入下一步。"),
                ("总结与Q&A", "重点回顾", ["核心价值回顾", "建议行动", "答疑环节"], "收尾页保持简洁。"),
            ]

        if "产品" in topic or scene in {"产品介绍", "产品宣讲"}:
            return [
                ("封面", f"{topic} - 面向{audience}", [f"主题：{topic}", f"适用场景：{scene}"], "封面可突出产品名称与定位。"),
                ("目录", "本次宣讲结构", ["市场背景", "产品定位", "核心功能", "价值收益"], "帮助听众把握讲解节奏。"),
                ("业务痛点", "为什么需要这款产品", ["当前问题", "影响范围", "改进机会"], "先讲痛点再讲产品更容易建立认同。"),
                ("产品定位", "产品解决什么问题", ["目标用户", "核心定位", "应用场景"], "说明产品在整体方案中的位置。"),
                ("核心功能", "最值得记住的能力", ["功能一", "功能二", "功能三"], "每页只保留最关键的信息。"),
                ("方案优势", "为什么值得选择", ["效率提升", "成本优势", "交付保障"], "可结合案例或数据强化。"),
                ("落地案例", "已有实践与效果", ["案例背景", "实施过程", "结果收益"], "尽量引用真实资料。"),
                ("总结与Q&A", "重点回顾", ["核心价值", "推荐动作", "答疑环节"], "结尾回到业务价值。"),
            ]

        if "汇报" in topic or scene == "内部汇报":
            return [
                ("封面", f"{topic} - 面向{audience}", [f"主题：{topic}", f"适用场景：{scene}"], "封面标题建议直接体现汇报事项。"),
                ("目录", "本次汇报结构", ["背景目标", "工作进展", "问题挑战", "下一步计划"], "先给出结构，方便领导跟进。"),
                ("背景与目标", "为什么做这件事", ["背景说明", "本期目标", "衡量指标"], "交代背景时尽量简洁。"),
                ("阶段进展", "已经完成了什么", ["关键动作", "里程碑结果", "阶段成果"], "建议用结果导向表述。"),
                ("问题与挑战", "当前卡点", ["核心问题", "影响范围", "原因分析"], "体现判断力，不只是罗列问题。"),
                ("解决方案", "如何推进", ["应对方案", "资源需求", "风险控制"], "方案要可执行。"),
                ("下一步计划", "接下来怎么做", ["时间安排", "重点任务", "预期产出"], "让管理层明确下一步。"),
                ("总结与决策建议", "需要达成什么共识", ["关键结论", "决策建议", "待确认事项"], "收尾页突出需要拍板的内容。"),
            ]

        return [
            ("封面", f"{topic} - 面向{audience}", [f"主题：{topic}", f"适用场景：{scene}"], "封面建议直接体现主题与对象。"),
            ("目录", "本次内容结构", ["背景与目标", "核心方案", "实施路径", "总结建议"], "目录页用于帮助受众建立整体认知。"),
            ("背景与目标", "先把问题讲清楚", ["当前背景", "目标是什么", "为什么现在做"], "第一部分聚焦共识建立。"),
            ("核心方案", "方案的主要内容", ["核心做法", "关键优势", "与其他方案区别"], "这是整份 PPT 的重点页。"),
            ("实施路径", "如何落地", ["阶段步骤", "资源安排", "时间规划"], "让方案更可执行。"),
            ("预期效果", "能带来什么价值", ["直接收益", "间接收益", "衡量指标"], "最好结合数据或案例。"),
            ("风险与应对", "提前说明挑战", ["潜在风险", "应对措施", "备选方案"], "体现方案完整性。"),
            ("总结与Q&A", "重点回顾", ["结论回顾", "建议动作", "答疑环节"], "最后一页突出重点。"),
        ]

    def _generate_outline(self, *, revision_note: Optional[str] = None) -> Tuple[List[Dict[str, Any]], str]:
        page_count = self._normalize_page_count(self._requirements.page_count)
        sections = self._infer_outline_sections()

        if len(sections) > page_count:
            sections = sections[:page_count]
        elif len(sections) < page_count:
            while len(sections) < page_count - 1:
                extra_index = len(sections)
                sections.insert(
                    -1,
                    (
                        f"补充页 {extra_index - 1}",
                        "根据具体主题补充",
                        ["关键事实", "支持论据", "行动建议"],
                        "这页用于承接主题细节，后续可继续细化。",
                    ),
                )

        outline: List[Dict[str, Any]] = []
        for index, (title, subtitle, bullets, notes) in enumerate(sections, start=1):
            outline.append({
                "index": index,
                "title": title,
                "subtitle": subtitle,
                "bullets": bullets,
                "speaker_notes": notes,
            })

        outline_text = [
            f"# {self._requirements.topic or 'PPT 方案'}",
            "",
            f"适用场景：{self._requirements.scene or '待补充'}",
            f"目标受众：{self._requirements.audience or '待补充'}",
            f"建议页数：{len(outline)} 页",
        ]
        if self._requirements.style:
            outline_text.append(f"建议风格：{self._requirements.style}")

        outline_text.extend(["", "## 页面设计："])
        for slide in outline:
            outline_text.append(f"{slide['index']}. 第{slide['index']}页：{slide['title']}")

        outline_text.extend(["", "## 每页文案："])
        for slide in outline:
            outline_text.append(f"第{slide['index']}页：{slide['title']}")
            outline_text.append(f"- 标题：{slide['title']}")
            outline_text.append(f"- 副标题：{slide['subtitle']}")
            outline_text.append("- 要点：")
            for bullet in slide["bullets"]:
                outline_text.append(f"  - {bullet}")
            outline_text.append(f"- 演讲备注：{slide['speaker_notes']}")

        if revision_note:
            outline_text.extend(["", f"本轮调整说明：{revision_note}"])

        return outline, "\n".join(outline_text)

    def _build_structured_result(self) -> Optional[Dict[str, Any]]:
        if not self._outline_draft:
            return None
        self._structured_result = {
            "type": "ppt_outline",
            "title": self._requirements.topic or "PPT 大纲",
            "slides": self._outline_draft,
            "requirements": asdict(self._requirements),
        }
        return self._structured_result

    def _generate_outline_confirmation_message(self, outline_text: str, *, updated: bool = False) -> str:
        intro = "这是我根据你提供的信息整理的第一版大纲。"
        if updated:
            intro = "我已经根据你刚才补充的信息更新了一版大纲。"
        return (
            f"{intro}\n\n{outline_text}\n\n---\n\n"
            "你先看整体结构对不对。\n\n"
            "如果这版结构没问题，我就继续进入风格确认；如果哪里不合适，你直接告诉我删哪一页、补哪一页，或者整体风格往哪个方向调。"
        )

    def _generate_template_selection_message(self) -> str:
        return (
            "好的，大纲已确认。接下来我们把展示风格定下来。\n\n"
            "你可以选择：\n"
            "1. 公司标准模板\n"
            "2. 正式汇报风格\n"
            "3. 客户介绍风格\n"
            "4. 销售展示风格\n\n"
            "确认后我再进入正式生成。"
        )

    def _generate_final_confirmation_message(self) -> str:
        return (
            "内容结构已经基本确定，我准备进入正式生成前的最后确认。\n\n"
            "我先确认三件事：\n"
            "1. 页数已经确认\n"
            "2. 大纲结构没有问题\n"
            "3. 展示风格或模板已经定下来\n\n"
            "如果你确认，就点击“生成 PPT”继续。"
        )

    def _is_confirmation_message(self, message: str) -> bool:
        confirm_keywords = [
            "可以", "没问题", "确认", "好的", "就这样",
            "继续", "往下做", "对的", "是的", "行", "ok", "OK",
        ]
        return any(keyword in message for keyword in confirm_keywords)

    def _is_revision_message(self, message: str) -> bool:
        revision_keywords = [
            "改", "修改", "调整", "换", "增加", "删除",
            "不要", "需要加", "删一页", "不对", "不太对", "重新",
        ]
        return any(keyword in message for keyword in revision_keywords)

    def _is_redo_request(self, message: str) -> bool:
        redo_keywords = [
            "重做", "重新做", "再做一遍", "重来", "从头来",
            "改一改", "调整一下", "再改一版",
        ]
        return any(keyword in message for keyword in redo_keywords)

    def _is_regenerate_request(self, message: str) -> bool:
        regenerate_keywords = [
            "再生成", "重新生成", "再导一份", "再出一版",
            "重试", "再试一次", "重新来",
        ]
        return any(keyword in message for keyword in regenerate_keywords)

    def _is_local_modification(self, message: str) -> Tuple[bool, str]:
        local_keywords = [
            ("第", "页"), ("第", "章"), ("第", "节"),
            ("封面",), ("目录",), ("总结",), ("结尾",),
            ("第\\d+",), ("第一",), ("第二",), ("第三",),
            ("首页",), ("最后一页",), ("最后一",),
        ]
        
        for pattern in local_keywords:
            if len(pattern) == 1:
                if pattern[0] in message:
                    return True, pattern[0]
            else:
                if pattern[0] in message and pattern[1] in message:
                    return True, f"{pattern[0]}{pattern[1]}"
        
        return False, ""

    def _parse_modification_type(self, message: str) -> str:
        if self._is_regenerate_request(message):
            return "regenerate"
        elif self._is_redo_request(message):
            return "redo"
        else:
            is_local, target = self._is_local_modification(message)
            if is_local:
                return "local"
            elif self._is_revision_message(message):
                return "revision"
            elif self._is_confirmation_message(message):
                return "confirm"
            else:
                return "unknown"

    def _parse_numeric_selection(self, message: str) -> Optional[int]:
        stripped_message = message.strip()
        match = re.match(r"^(\d+)[、.．，,：:\s]*$", stripped_message)
        if match:
            return int(match.group(1))
        match = re.match(r"^选[择]?[：:：]?\s*(\d+)", stripped_message)
        if match:
            return int(match.group(1))
        return None

    def process_message(
        self,
        message: str,
        action_type: str = "message",
        is_new_conversation: bool = False,
    ) -> Tuple[str, Optional[Dict[str, Any]], ConversationStage]:
        if action_type == "message" and message:
            self._add_message("user", message)

        if is_new_conversation and self._current_stage == ConversationStage.WELCOME and not message.strip():
            self._add_message("assistant", self.WELCOME_MESSAGE)
            return self.WELCOME_MESSAGE, self._structured_result, self._current_stage

        parsed = self._parse_user_input(message)
        updated_fields = self._update_requirements(parsed) if message else []

        if action_type == "confirm_outline":
            self._current_stage = ConversationStage.TEMPLATE_SELECT
            response = self._generate_template_selection_message()
            self._add_message("assistant", response)
            return response, self._structured_result, self._current_stage

        if action_type == "confirm_template":
            if not self._requirements.style:
                self._requirements.style = "公司标准模板"
                self._requirements.use_standard_template = True
            self._current_stage = ConversationStage.FINAL_GENERATING
            response = self._generate_final_confirmation_message()
            self._add_message("assistant", response)
            return response, self._structured_result, self._current_stage

        if self._current_stage in {ConversationStage.WELCOME, ConversationStage.CLARIFYING}:
            missing_keys = self._get_required_missing_keys()
            if missing_keys:
                self._current_stage = ConversationStage.CLARIFYING
                response = self._generate_dynamic_clarify_response(missing_keys, updated_fields)
                self._add_message("assistant", response)
                return response, self._structured_result, self._current_stage

            self._current_stage = ConversationStage.OUTLINE_DRAFT
            self._outline_draft, outline_text = self._generate_outline()
            structured_result = self._build_structured_result()
            response = self._generate_outline_confirmation_message(outline_text, updated=bool(updated_fields))
            self._add_message("assistant", response)
            return response, structured_result, self._current_stage

        if self._current_stage == ConversationStage.OUTLINE_DRAFT:
            if action_type == "revise_outline" or self._is_revision_message(message):
                self._outline_draft, outline_text = self._generate_outline(revision_note=message or "根据用户意见进行了调整")
                structured_result = self._build_structured_result()
                response = self._generate_outline_confirmation_message(outline_text, updated=True)
                self._add_message("assistant", response)
                return response, structured_result, self._current_stage

            if updated_fields:
                self._outline_draft, outline_text = self._generate_outline(revision_note="已吸收你刚补充的信息")
                structured_result = self._build_structured_result()
                response = self._generate_outline_confirmation_message(outline_text, updated=True)
                self._add_message("assistant", response)
                return response, structured_result, self._current_stage

            if self._is_confirmation_message(message):
                self._current_stage = ConversationStage.TEMPLATE_SELECT
                response = self._generate_template_selection_message()
                self._add_message("assistant", response)
                return response, self._structured_result, self._current_stage

            response = (
                "如果你认可这版大纲，可以直接点“确认大纲”；如果还想调整，也可以直接告诉我想改哪几页、补什么内容、风格往哪个方向调。"
            )
            self._add_message("assistant", response)
            return response, self._structured_result, self._current_stage

        if self._current_stage == ConversationStage.OUTLINE_CONFIRMED:
            self._current_stage = ConversationStage.TEMPLATE_SELECT
            response = self._generate_template_selection_message()
            self._add_message("assistant", response)
            return response, self._structured_result, self._current_stage

        if self._current_stage == ConversationStage.TEMPLATE_SELECT:
            selection = self._parse_numeric_selection(message)
            style_map = {
                1: "公司标准模板",
                2: "正式汇报风格",
                3: "客户介绍风格",
                4: "销售展示风格",
            }
            if selection in style_map:
                self._requirements.style = style_map[selection]
                self._requirements.use_standard_template = selection == 1

            if not self._requirements.style:
                if "标准" in message:
                    self._requirements.style = "公司标准模板"
                    self._requirements.use_standard_template = True
                elif "正式" in message:
                    self._requirements.style = "正式汇报风格"
                elif "客户" in message:
                    self._requirements.style = "客户介绍风格"
                elif "销售" in message:
                    self._requirements.style = "销售展示风格"

            if self._requirements.style:
                self._current_stage = ConversationStage.FINAL_GENERATING
                response = f"好的，已选择「{self._requirements.style}」。\n\n{self._generate_final_confirmation_message()}"
                self._add_message("assistant", response)
                return response, self._structured_result, self._current_stage

            response = (
                "你可以直接回复想要的风格，或者输入数字：\n"
                "1. 公司标准模板\n"
                "2. 正式汇报风格\n"
                "3. 客户介绍风格\n"
                "4. 销售展示风格"
            )
            self._add_message("assistant", response)
            return response, self._structured_result, self._current_stage

        if self._current_stage == ConversationStage.FINAL_GENERATING:
            response = (
                "已准备好进入正式生成。\n\n"
                f"{self._format_requirements_summary()}\n\n"
                "如果这些信息都没问题，直接点击“生成 PPT”即可。"
            )
            self._add_message("assistant", response)
            return response, self._structured_result, self._current_stage

        if self._current_stage == ConversationStage.COMPLETED:
            modification_type = self._parse_modification_type(message)
            
            if modification_type == "regenerate":
                self._current_stage = ConversationStage.FINAL_GENERATING
                response = (
                    "好的，我准备再次生成 PPT 文件。\n\n"
                    f"{self._format_requirements_summary()}\n\n"
                    "如果你确认这些信息没有变化，直接点击“生成 PPT”即可生成新版本。"
                )
                self._add_message("assistant", response)
                return response, self._structured_result, self._current_stage
            
            elif modification_type == "redo":
                self._current_stage = ConversationStage.OUTLINE_DRAFT
                self._outline_draft, outline_text = self._generate_outline(revision_note=message or "根据用户意见重新调整")
                structured_result = self._build_structured_result()
                response = (
                    "好的，我基于当前信息重新调整一下大纲。\n\n"
                    f"{outline_text}\n\n---\n\n"
                    "你先看这版结构是否更合适。如果想调整风格、页数或其他信息，也可以直接告诉我。"
                )
                self._add_message("assistant", response)
                return response, structured_result, self._current_stage
            
            elif modification_type == "local":
                is_local, target = self._is_local_modification(message)
                response = (
                    f"我理解你想调整「{target}」相关内容。\n\n"
                    "由于这是第一版，我建议我们分两步来：\n"
                    "1. 先把整体结构和关键信息确认清楚\n"
                    "2. 再进行局部调整\n\n"
                    "如果你想调整局部内容，可以告诉我：\n"
                    "- 具体想改哪一页的什么内容\n"
                    "- 或者想调整整体风格/页数\n\n"
                    "我会先按你的意见更新大纲，然后你可以确认后再生成新版本。"
                )
                
                if self._is_revision_message(message):
                    self._current_stage = ConversationStage.OUTLINE_DRAFT
                    self._outline_draft, outline_text = self._generate_outline(revision_note=message)
                    structured_result = self._build_structured_result()
                    response = (
                        f"好的，我根据你的意见调整一下相关内容。\n\n"
                        f"{outline_text}\n\n---\n\n"
                        "你先看这版是否更合适。如果还需要调整，可以继续告诉我。"
                    )
                    self._add_message("assistant", response)
                    return response, structured_result, self._current_stage
                
                self._add_message("assistant", response)
                return response, self._structured_result, self._current_stage
            
            elif modification_type == "revision":
                parsed = self._parse_user_input(message)
                updated_fields = self._update_requirements(parsed) if message else []
                
                if updated_fields:
                    self._current_stage = ConversationStage.OUTLINE_DRAFT
                    self._outline_draft, outline_text = self._generate_outline(revision_note="已吸收你刚补充的信息")
                    structured_result = self._build_structured_result()
                    
                    field_labels = {
                        "topic": "主题",
                        "audience": "受众",
                        "scene": "场景",
                        "page_count": "页数",
                        "style": "风格",
                    }
                    collected = []
                    for field in updated_fields:
                        if field in field_labels:
                            collected.append(field_labels[field])
                    
                    update_note = f"收到，你补充了{ '、'.join(collected) }。" if collected else "收到，我根据你的意见调整一下。"
                    
                    response = (
                        f"{update_note}\n\n"
                        f"{outline_text}\n\n---\n\n"
                        "这是更新后的大纲。你先确认整体结构没问题，我再进入下一步。"
                    )
                    self._add_message("assistant", response)
                    return response, structured_result, self._current_stage
                
                else:
                    response = (
                        "这份 PPT 已经完成了。\n\n"
                        "如果你想继续调整，可以：\n"
                        "1. 告诉我想改哪部分（如「第3页调整一下」）\n"
                        "2. 或者告诉我想修改的信息（如「改成20页」「风格改成销售展示」）\n"
                        "3. 或者直接说「再生成一版」来创建新版本\n\n"
                        f"当前已确认的信息：\n{self._format_requirements_summary()}"
                    )
                    self._add_message("assistant", response)
                    return response, self._structured_result, self._current_stage
            
            elif modification_type == "confirm":
                response = (
                    "这份 PPT 已经完成了。\n\n"
                    "如果你想：\n"
                    "- 生成新版本：说「再生成一版」或点击「生成 PPT」\n"
                    "- 调整内容：告诉我具体想改什么\n\n"
                    f"当前已确认的信息：\n{self._format_requirements_summary()}"
                )
                self._add_message("assistant", response)
                return response, self._structured_result, self._current_stage
            
            else:
                parsed = self._parse_user_input(message)
                updated_fields = self._update_requirements(parsed) if message else []
                
                if updated_fields:
                    self._current_stage = ConversationStage.OUTLINE_DRAFT
                    self._outline_draft, outline_text = self._generate_outline(revision_note="已吸收你刚补充的信息")
                    structured_result = self._build_structured_result()
                    
                    response = (
                        "收到，我根据你补充的信息更新一下大纲。\n\n"
                        f"{outline_text}\n\n---\n\n"
                        "你先确认整体结构没问题，我再进入下一步。"
                    )
                    self._add_message("assistant", response)
                    return response, structured_result, self._current_stage
                
                else:
                    response = (
                        "这份 PPT 已经完成了。\n\n"
                        "如果你想继续调整，可以告诉我：\n"
                        "1. 想修改的具体内容（如「改成15页」「风格改成正式汇报」）\n"
                        "2. 或者直接说「再生成一版」\n\n"
                        f"当前已确认的信息：\n{self._format_requirements_summary()}"
                    )
                    self._add_message("assistant", response)
                    return response, self._structured_result, self._current_stage

        response = "这轮会话已经完成。如果你还想继续修改，我可以基于当前内容帮你继续调整。"
        self._add_message("assistant", response)
        return response, self._structured_result, self._current_stage

    def get_current_stage(self) -> ConversationStage:
        return self._current_stage

    def get_requirements(self) -> PPTRequirements:
        return self._requirements

    def get_outline_draft(self) -> Optional[List[Dict[str, Any]]]:
        return self._outline_draft
