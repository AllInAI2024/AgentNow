import os
import re
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class ConversationStage(str, Enum):
    WELCOME = "welcome"
    CLARIFYING = "clarifying"
    OUTLINE_DRAFT = "outline_draft"
    OUTLINE_CONFIRMED = "outline_confirmed"
    TEMPLATE_SELECT = "template_select"
    FINAL_GENERATING = "final_generating"
    CONTENT_READY = "content_ready"
    COMPLETED = "completed"


@dataclass
class PPTContent:
    title: str
    subtitle: Optional[str] = None
    scene: Optional[str] = None
    audience: Optional[str] = None
    style: Optional[str] = None
    slides: List[Dict[str, Any]] = None


class HermesChatService:
    """
    Hermes 对话服务 - 通过 HTTP API 调用 Hermes 进行对话
    """

    PPT_ASSISTANT_PROMPT = """你是企业 PPT 助手，帮助用户快速生成 PPT。

## 工作流程
1. 需求收集：询问主题、受众、场景、页数、风格
2. 大纲生成：生成大纲并询问用户确认
3. 模板选择：让用户选择风格（公司标准模板、正式汇报、客户介绍、销售展示）
4. 最终确认：询问是否开始生成
5. 输出结构化 JSON

## 输出格式
最终输出必须包含完整的 JSON：
```json
{"type":"ppt_content","title":"标题","subtitle":"副标题","scene":"场景","audience":"受众","style":"风格","slides":[{"index":1,"title":"页面标题","subtitle":"副标题","bullets":["要点1"],"speaker_notes":"备注","layout":"title_slide"}]}
```

## 确认关键词
确认：可以、没问题、确认、好的、继续、往下做、对的、是的、行、ok、OK
修改：改、修改、调整、换、增加、删除、不要、不对、不太对、重新

## 知识使用
涉及公司介绍、产品能力、品牌表述、案例数据时，优先查询企业知识库。

开始对话时，先友好问候，然后了解需求。"""

    def __init__(self):
        self._base_url = settings.HERMES_BASE_URL or "http://127.0.0.1:8642"
        self._api_key = os.environ.get("HERMES_API_KEY")
        self._timeout = 120.0

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }
        if self._api_key and self._api_key.strip():
            headers["Authorization"] = f"Bearer {self._api_key.strip()}"
        return headers

    def chat_completions(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        stream: bool = False,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        调用 Hermes 的 chat/completions API
        """
        url = f"{self._base_url}/v1/chat/completions"

        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)

        payload = {
            "model": "hermes-agent",
            "messages": all_messages,
            "stream": stream,
        }

        headers = self._get_headers()
        if session_id:
            headers["X-Hermes-Session-Id"] = session_id

        logger.info(f"Calling Hermes API: {url}")
        logger.info(f"Messages count: {len(all_messages)}")
        logger.info(f"System prompt length: {len(system_prompt) if system_prompt else 0}")
        logger.debug(f"Full messages: {json.dumps(all_messages, ensure_ascii=False)}")

        with httpx.Client(timeout=self._timeout) as client:
            try:
                response = client.post(
                    url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()
                logger.debug(f"Hermes API response received")
                return result
            except httpx.HTTPStatusError as e:
                logger.error(f"Hermes API HTTP error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Hermes API error: {e}")
                raise

    def _extract_json_from_content(self, content: str) -> Optional[Dict[str, Any]]:
        """
        从内容中提取 JSON
        """
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        json_match = re.search(r'\{[\s\S]*"type"\s*:\s*"ppt_content"[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _detect_stage_from_content(self, content: str) -> ConversationStage:
        """
        根据对话内容推断当前阶段
        """
        content_lower = content.lower()

        if '"type": "ppt_content"' in content or 'ppt_content' in content_lower:
            return ConversationStage.CONTENT_READY

        if '大纲' in content and '确认' in content:
            if '页面设计' in content or '第1页' in content:
                return ConversationStage.OUTLINE_DRAFT

        if '风格' in content and ('选择' in content or '模板' in content):
            return ConversationStage.TEMPLATE_SELECT

        if '最终确认' in content or ('确认' in content and '页数' in content and '结构' in content):
            return ConversationStage.FINAL_GENERATING

        if '主题' in content_lower and '受众' in content_lower and '场景' in content_lower:
            return ConversationStage.CLARIFYING

        return ConversationStage.CLARIFYING

    def parse_ppt_content(self, content: str) -> Optional[PPTContent]:
        """
        解析 PPT 内容
        """
        json_data = self._extract_json_from_content(content)
        if not json_data or json_data.get("type") != "ppt_content":
            return None

        try:
            return PPTContent(
                title=json_data.get("title", "未命名 PPT"),
                subtitle=json_data.get("subtitle"),
                scene=json_data.get("scene"),
                audience=json_data.get("audience"),
                style=json_data.get("style"),
                slides=json_data.get("slides", []),
            )
        except Exception as e:
            logger.error(f"Failed to parse PPT content: {e}")
            return None

    def chat_with_ppt_assistant(
        self,
        messages: List[Dict[str, Any]],
        session_id: Optional[str] = None,
    ) -> tuple[str, ConversationStage, Optional[PPTContent]]:
        """
        使用 PPT 助手进行对话

        Returns:
            (assistant_content, current_stage, ppt_content)
            
        Raises:
            Exception: 如果 Hermes API 调用失败
        """
        logger.info(f"Calling Hermes chat/completions with {len(messages)} messages, session_id: {session_id}")
        logger.debug(f"Messages: {json.dumps(messages, ensure_ascii=False)}")

        response = self.chat_completions(
            messages=messages,
            system_prompt=self.PPT_ASSISTANT_PROMPT,
            session_id=session_id,
        )

        assistant_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        logger.info(f"Hermes response received, content length: {len(assistant_content)}")
        logger.debug(f"Response content: {assistant_content[:500]}...")

        stage = self._detect_stage_from_content(assistant_content)
        ppt_content = self.parse_ppt_content(assistant_content)

        return assistant_content, stage, ppt_content

    def generate_welcome_message(self) -> str:
        """
        生成欢迎语
        """
        return """你好，我是企业 PPT 助手。

你可以直接告诉我：
1. 这份 PPT 是做什么用的
2. 是给谁看的
3. 想做多少页
4. 有没有必须引用的公司资料

如果你暂时说不全，我也会一步一步带你把这件事理顺。"""

    def is_confirmation(self, message: str) -> bool:
        """
        判断用户消息是否为确认
        """
        confirm_keywords = [
            "可以", "没问题", "确认", "好的",
            "继续", "往下做", "对的", "是的",
            "行", "ok", "OK", "确认大纲", "确认模板"
        ]
        return any(keyword in message for keyword in confirm_keywords)

    def is_revision(self, message: str) -> bool:
        """
        判断用户消息是否为修改
        """
        revision_keywords = [
            "改", "修改", "调整", "换",
            "增加", "删除", "不要",
            "不对", "不太对", "重新"
        ]
        return any(keyword in message for keyword in revision_keywords)
