import os
import re
import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

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
    Hermes 对话服务 - 通过 Hermes CLI 调用 Hermes 进行对话

    设计目标：
    - AgentNow 只负责“壳/治理/闭环”，不在平台内实现具体智能体推理与工具执行
    - 实际干活由 Hermes（skills/tools/mcp/memory/profile）完成
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

## 重要要求
1. 根据对话历史继续对话，不要重复问已经回答过的问题
2. 如果用户已经回答了某些问题，直接进入下一步
3. 当信息收集完整后，生成大纲并询问用户确认
4. 最终输出必须包含完整的 JSON 结构"""

    def __init__(self):
        self._timeout = 180
        self._hermes_bin = shutil.which("hermes") or "hermes"

    def _load_dotenv(self, env_path: Path) -> Dict[str, str]:
        if not env_path.exists():
            return {}
        env: Dict[str, str] = {}
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k:
                    env[k] = v
        except Exception as e:
            logger.debug(f"Failed to read profile .env: {e}")
        return env

    def _build_profile_env(self, profile_name: Optional[str]) -> Dict[str, str]:
        if not profile_name:
            return {}

        profile_home = Path.home() / ".hermes" / "profiles" / profile_name
        env: Dict[str, str] = {}
        env.update(self._load_dotenv(profile_home / ".env"))
        return env

    def _run_hermes_chat(
        self,
        *,
        query: str,
        system_prompt: Optional[str],
        resume_session_id: Optional[str],
        profile_name: Optional[str],
    ) -> Tuple[str, Optional[str]]:
        cmd: List[str] = [self._hermes_bin]
        if profile_name and profile_name.strip():
            cmd.extend(["-p", profile_name.strip()])
        if system_prompt and system_prompt.strip():
            cmd.extend(["-z", system_prompt.strip()])

        cmd.extend(["chat", "-q", query, "-Q", "--source", "tool"])
        if resume_session_id and resume_session_id.strip():
            cmd.extend(["--resume", resume_session_id.strip()])

        env = os.environ.copy()
        env.update(self._build_profile_env(profile_name))

        logger.info(
            "Calling Hermes CLI chat: resume_session_id=%s, profile=%s",
            resume_session_id,
            profile_name,
        )

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self._timeout,
            env=env,
        )

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if result.returncode != 0:
            msg = stderr or stdout or f"Hermes CLI exited with code {result.returncode}"
            raise RuntimeError(msg)

        session_id = None
        m = re.search(r"session_id:\s*([0-9A-Za-z_-]+)", stdout)
        if m:
            session_id = m.group(1)
            stdout = re.sub(r"(?m)^\s*session_id:\s*[0-9A-Za-z_-]+\s*$", "", stdout).strip()

        stdout = re.sub(r"(?m)^\s*↻\s*Resumed session.*$", "", stdout).strip()

        assistant_content = stdout.strip()
        return assistant_content, session_id

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
        *,
        user_message: str,
        system_prompt: Optional[str],
        profile_name: Optional[str],
        hermes_session_id: Optional[str] = None,
    ) -> tuple[str, ConversationStage, Optional[PPTContent], Optional[str]]:
        """
        使用 PPT 助手进行对话

        Returns:
            (assistant_content, current_stage, ppt_content, new_hermes_session_id)
            
        Raises:
            Exception: 如果 Hermes API 调用失败
        """
        assistant_content, new_session_id = self._run_hermes_chat(
            query=user_message,
            system_prompt=system_prompt or self.PPT_ASSISTANT_PROMPT,
            resume_session_id=hermes_session_id,
            profile_name=profile_name,
        )

        stage = self._detect_stage_from_content(assistant_content)
        ppt_content = self.parse_ppt_content(assistant_content)

        return assistant_content, stage, ppt_content, new_session_id or hermes_session_id

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
