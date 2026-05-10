from __future__ import annotations

import json
import os
import queue
import re
import sqlite3
import threading
import time
import uuid
import base64
import mimetypes
import sys
import hashlib
import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any
from sqlalchemy.orm import Session
import httpx

import yaml

from app.models import User
from app.schemas.super_assistant import (
    SuperAssistantMessage,
    SuperAssistantSession,
    SuperAssistantSessionListItem,
)
from app.services.hermes_profile_service import HermesProfileService
from app.services.hermes_service import hermes_service


_SESSION_ID_RE = re.compile(r"session_id:\s*([0-9A-Za-z_-]+)")
_SESSION_LINE_RE = re.compile(r"\bSession:\s*([0-9A-Za-z_-]+)\b")
_RESUMED_LINE_RE = re.compile(r"(?m)^\s*↻\s*Resumed session.*$")
_ANSI_CSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
_ANSI_OSC_RE = re.compile(r"\x1b\][^\x07]*(?:\x07|\x1b\\)")


def _now_s() -> float:
    return time.time()


def _is_blank_text(value: str) -> bool:
    s = str(value or "")
    s = s.replace("\u200b", "")
    return not s.strip()


def _path_is_relative_to(p: Path, base: Path) -> bool:
    try:
        p.relative_to(base)
        return True
    except Exception:
        return False


def _is_blocked_workspace_path(candidate: Path) -> bool:
    p = candidate
    allowed_prefixes = (Path.home(), Path("/Users"), Path("/Volumes"), Path("/var/folders"), Path("/private/var/folders"))
    for a in allowed_prefixes:
        if _path_is_relative_to(p, a):
            return False
    blocked_prefixes = (
        Path("/System"),
        Path("/Library"),
        Path("/etc"),
        Path("/usr"),
        Path("/bin"),
        Path("/sbin"),
        Path("/private/etc"),
        Path("/private/var/db"),
        Path("/private/var/root"),
    )
    for b in blocked_prefixes:
        if p == b or _path_is_relative_to(p, b):
            return True
    if str(p) == "/":
        return True
    return False


def _agentnow_workspace_root() -> Path:
    return Path.home() / ".agentnow" / "workspace"


def _is_allowed_agentnow_workspace_path(candidate: Path, *, profile_name: str) -> bool:
    root = _agentnow_workspace_root().expanduser()
    try:
        root = root.resolve()
    except Exception:
        pass
    try:
        p = candidate.resolve()
    except Exception:
        p = candidate
    if not profile_name:
        return False
    allowed = root / profile_name
    try:
        allowed = allowed.resolve()
    except Exception:
        pass
    return p == allowed or _path_is_relative_to(p, allowed)


def _safe_json_load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _safe_json_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _sha1_text(value: str) -> str:
    return hashlib.sha1((value or "").strip().encode("utf-8", errors="ignore")).hexdigest()

def _derive_session_title_from_user_text(text: str) -> str:
    raw = str(text or "").strip()
    if not raw:
        return "Untitled"
    first_line = raw.splitlines()[0].strip()
    s = re.sub(r"\s+", " ", first_line).strip()
    if not s:
        return "Untitled"
    if len(s) > 64:
        s = s[:64].rstrip()
    return s or "Untitled"

def _is_default_session_title(title: str) -> bool:
    t = str(title or "").strip()
    if not t:
        return True
    return t.lower() in ("untitled", "new chat")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _sse_bytes(event: str, data: dict) -> bytes:
    return _sse(event, data).encode("utf-8")


def _load_dotenv(env_path: Path) -> Dict[str, str]:
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
    except Exception:
        return {}
    return env


def _get_hermes_base_home() -> Path:
    base_override = os.environ.get("HERMES_BASE_HOME")
    if base_override and base_override.strip():
        return Path(base_override.strip()).expanduser()

    hermes_home = os.environ.get("HERMES_HOME")
    if hermes_home and hermes_home.strip():
        p = Path(hermes_home.strip()).expanduser()
        if p.parent.name == "profiles":
            return p.parent.parent
        return p

    return Path.home() / ".hermes"


def _build_hermes_cli_env(profile_service: HermesProfileService, profile_name: Optional[str]) -> Dict[str, str]:
    env: Dict[str, str] = {}
    pn = (profile_name or "").strip()
    if pn:
        _, profile_env_path = profile_service.get_profile_config_path(pn)
        env.update(_load_dotenv(profile_env_path))

    base_home = _get_hermes_base_home()
    env.update(_load_dotenv(base_home / ".env"))

    return env


def _read_global_hermes_config() -> dict:
    base_home = _get_hermes_base_home()
    config_path = base_home / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _normalize_custom_provider_name(name: str) -> str:
    return (name or "").strip().lower().replace(" ", "-")


def _resolve_provider_for_model(model_id: str, global_cfg: dict) -> tuple[Optional[str], Optional[str]]:
    mid = str(model_id or "").strip()
    if not mid:
        return None, None

    custom = global_cfg.get("custom_providers", [])
    if isinstance(custom, list):
        for entry in custom:
            if not isinstance(entry, dict):
                continue
            entry_model = str(entry.get("model") or "").strip()
            if entry_model and entry_model == mid:
                name = str(entry.get("name") or "").strip()
                base_url = str(entry.get("base_url") or "").strip() or None
                if name:
                    return f"custom:{_normalize_custom_provider_name(name)}", base_url
                return "custom", base_url

    model_cfg = global_cfg.get("model", {})
    if isinstance(model_cfg, dict):
        provider = str(model_cfg.get("provider") or "").strip() or None
        base_url = str(model_cfg.get("base_url") or "").strip() or None
        return provider, base_url

    if isinstance(model_cfg, str):
        return None, None

    return None, None


def _extract_delta_from_openai_chunk(payload: dict) -> str:
    if not isinstance(payload, dict):
        return ""
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        parts: List[str] = []
        for c in choices:
            if not isinstance(c, dict):
                continue
            delta = c.get("delta")
            if isinstance(delta, dict):
                content = delta.get("content")
                if isinstance(content, str) and content:
                    parts.append(content)
        return "".join(parts)
    return ""


def _strip_ansi(s: str) -> str:
    t = s or ""
    t = _ANSI_OSC_RE.sub("", t)
    t = _ANSI_CSI_RE.sub("", t)
    return t


_HERMES_AGENT_ENV_LOCK = threading.Lock()
_HERMES_AGENT_PREWARM_DONE = threading.Event()
_HERMES_AGENT_PREWARM_OK = {"yes": False}
_HERMES_AGENT_IMPORT_LAST_ERROR = {"text": ""}


@contextmanager
def _temporary_environ(updates: Dict[str, Optional[str]]):
    with _HERMES_AGENT_ENV_LOCK:
        keys = list((updates or {}).keys())
        prev: Dict[str, Optional[str]] = {k: os.environ.get(k) for k in keys}
        try:
            for k, v in (updates or {}).items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = str(v)
            yield
        finally:
            for k in keys:
                old = prev.get(k)
                if old is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = old


def _import_hermes_ai_agent() -> Optional[type]:
    try:
        from run_agent import AIAgent  # type: ignore
        return AIAgent
    except Exception:
        try:
            _HERMES_AGENT_IMPORT_LAST_ERROR["text"] = traceback.format_exc(limit=40)[-12000:]
        except Exception:
            _HERMES_AGENT_IMPORT_LAST_ERROR["text"] = "import failed"
        return None


def prewarm_hermes_agent() -> None:
    try:
        _ = _import_hermes_ai_agent()
        _HERMES_AGENT_PREWARM_OK["yes"] = _ is not None
    except Exception:
        _HERMES_AGENT_PREWARM_OK["yes"] = False
    finally:
        _HERMES_AGENT_PREWARM_DONE.set()


def _safe_yaml_load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _deep_merge_fill(dst: dict, src: dict) -> dict:
    out = dict(dst or {})
    for k, v in (src or {}).items():
        if k not in out:
            out[k] = v
            continue
        if isinstance(out.get(k), dict) and isinstance(v, dict):
            out[k] = _deep_merge_fill(out[k], v)
    return out


def _ensure_profile_config_has_base(profile_config_path: Path) -> None:
    base_home = _get_hermes_base_home()
    base_cfg_path = base_home / "config.yaml"
    base_cfg = _safe_yaml_load(base_cfg_path)
    profile_cfg = _safe_yaml_load(profile_config_path)
    merged = _deep_merge_fill(profile_cfg, base_cfg)
    try:
        profile_config_path.write_text(
            yaml.safe_dump(merged, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    except Exception:
        pass


class HermesCliStreamParser:
    def __init__(self, *, opened_think: bool = False):
        self._buf = ""
        self._in_reasoning = False
        self._in_answer = False
        self._opened_think = bool(opened_think)
        self._in_tools_panel = False
        self._in_trailer = False
        self._done = False

    def feed(self, chunk: str, *, flush_partial: bool = False) -> tuple[list[str], Optional[str]]:
        if self._done:
            return [], None
        out: list[str] = []
        captured_session_id: Optional[str] = None
        self._buf += chunk or ""

        while True:
            nl = self._buf.find("\n")
            cr = self._buf.find("\r")
            if nl == -1 and cr == -1:
                break
            if cr != -1 and (nl == -1 or cr < nl):
                cut = cr + 1
                if cut < len(self._buf) and self._buf[cut] == "\n":
                    cut += 1
                line = self._buf[:cut]
                self._buf = self._buf[cut:]
            else:
                line = self._buf[: nl + 1]
                self._buf = self._buf[nl + 1 :]
            emitted, sid = self._handle_line(line)
            if sid:
                captured_session_id = sid
            if emitted:
                out.extend(emitted)

        if flush_partial and self._buf:
            emitted, sid = self._handle_line(self._buf, allow_partial=True)
            self._buf = ""
            if sid:
                captured_session_id = sid
            if emitted:
                out.extend(emitted)

        return out, captured_session_id

    def _is_border_line(self, s: str) -> bool:
        t = s.strip().replace(" ", "")
        if not t:
            return True
        border_chars = set("─┌┐└┘│╭╮╰╯═┃┏┓┗┛┠┨┯┷┳┻╱╲")
        return all((c in border_chars) for c in t)

    def _clean_box_content(self, s: str) -> str:
        t = s.rstrip("\n")
        t = t.strip("\r")
        if t.startswith("│") and t.endswith("│") and len(t) >= 2:
            t = t[1:-1]
        return t.strip()

    def _handle_line(self, line: str, *, allow_partial: bool = False) -> tuple[list[str], Optional[str]]:
        out: list[str] = []
        sid: Optional[str] = None
        raw = line or ""
        raw = raw.replace("\r", "")
        raw = _strip_ansi(raw)

        m = _SESSION_ID_RE.search(raw)
        if m:
            sid = m.group(1)
            raw = _SESSION_ID_RE.sub("", raw)
        m2 = _SESSION_LINE_RE.search(raw)
        if m2 and not sid:
            sid = m2.group(1)

        s = raw.rstrip("\n")
        t = s.strip()

        if self._in_trailer:
            m3 = re.search(r"\b--resume\s+([0-9A-Za-z_-]+)\b", s)
            if m3 and not sid:
                sid = m3.group(1)
            if sid:
                self._done = True
            return out, sid

        if "Resume this session with:" in raw or raw.lstrip().startswith("Resume this session"):
            self._in_answer = False
            self._in_trailer = True
            if self._opened_think:
                out.append("\n</think>\n\n")
                self._opened_think = False
            return out, sid

        if self._in_tools_panel:
            if t.startswith("╰") or "╰" in t:
                self._in_tools_panel = False
            return out, sid

        if "Available Tools" in s or "MCP Servers" in s or "Available Skills" in s:
            self._in_tools_panel = True
            return out, sid

        if self._is_border_line(s):
            return out, sid

        if not self._in_reasoning and not self._in_answer:
            if "┌─ Reasoning" in s or "┌─ 思考" in s or "┌─ 推理" in s:
                self._in_reasoning = True
                if not self._opened_think:
                    out.append("<think>\n")
                    self._opened_think = True
                return out, sid
            if (("⚕" in s and "Hermes" in s) or re.search(r"^\s*─\s*Hermes\b", s)):
                self._in_answer = True
                if self._opened_think:
                    out.append("\n</think>\n\n")
                    self._opened_think = False
                return out, sid
            if t.startswith("Query:") or "Initializing agent" in s:
                return out, sid
            return out, sid

        if self._in_reasoning:
            if s.startswith("└") and "─" in s:
                self._in_reasoning = False
                return out, sid
            content = self._clean_box_content(s)
            if content:
                out.append(content + ("\n" if not allow_partial else ""))
            return out, sid

        if self._in_answer:
            if t.startswith("Session:") or t.startswith("Duration:") or t.startswith("Messages:") or t.startswith("Resume this session with:"):
                self._in_answer = False
                return out, sid
            rule = t.replace(" ", "")
            if rule and all((c == "─") for c in rule):
                return out, sid
            if t:
                out.append(t + ("\n" if not allow_partial else ""))
            return out, sid

        return out, sid


def _is_image_mime(mime: str) -> bool:
    return bool(mime) and mime.startswith("image/")


def _read_file_as_data_url(path: Path, mime: str) -> Optional[str]:
    try:
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{data}"
    except Exception:
        return None


def _api_server_config_for_profile(profile_service: HermesProfileService, profile_name: str) -> tuple[bool, str, Optional[str]]:
    config_path, env_path = profile_service.get_profile_config_path(profile_name)
    env_vars = _load_dotenv(env_path)
    enabled = str(env_vars.get("API_SERVER_ENABLED", "false")).lower() in ("true", "1", "yes")
    host = env_vars.get("API_SERVER_HOST", "127.0.0.1")
    port_raw = env_vars.get("API_SERVER_PORT", "8642")
    try:
        port = int(port_raw)
    except Exception:
        port = 8642
    key = env_vars.get("API_SERVER_KEY")
    base_url = f"http://{host}:{port}"
    _ = config_path
    return enabled, base_url, key


def _api_headers(api_key: Optional[str]) -> dict:
    if api_key and str(api_key).strip():
        key = str(api_key).strip()
        try:
            key.encode("ascii")
        except Exception:
            return {}
        return {"Authorization": f"Bearer {key}"}
    return {}


def _is_ascii(value: Optional[str]) -> bool:
    if value is None:
        return True
    s = str(value)
    try:
        s.encode("ascii")
        return True
    except Exception:
        return False


def _update_dotenv_file(env_path: Path, updates: Dict[str, str]) -> None:
    env_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        lines = []

    remaining = dict(updates or {})
    out: List[str] = []
    for line in lines:
        replaced = False
        for k, v in list(remaining.items()):
            if re.match(rf"^\s*{re.escape(k)}\s*=", line):
                out.append(f"{k}={v}")
                remaining.pop(k, None)
                replaced = True
                break
        if not replaced:
            out.append(line)

    if remaining:
        if out and out[-1].strip() != "":
            out.append("")
        for k, v in remaining.items():
            out.append(f"{k}={v}")

    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def ensure_profile_api_server_key_ascii(profile_service: HermesProfileService, profile_name: str) -> tuple[bool, str, Optional[str]]:
    enabled, base_url, api_key = _api_server_config_for_profile(profile_service, profile_name)
    if not enabled:
        return enabled, base_url, api_key

    if _is_ascii(api_key) and api_key:
        return enabled, base_url, api_key

    config_path, env_path = profile_service.get_profile_config_path(profile_name)
    _ = config_path
    new_key = uuid.uuid4().hex
    _update_dotenv_file(
        env_path,
        {
            "API_SERVER_ENABLED": "true",
            "API_SERVER_KEY": new_key,
        },
    )
    try:
        hermes_service.restart_profile(profile_name)
        time.sleep(1.2)
    except Exception:
        try:
            hermes_service.start_profile(profile_name)
            time.sleep(1.2)
        except Exception:
            pass

    enabled2, base_url2, api_key2 = _api_server_config_for_profile(profile_service, profile_name)
    return enabled2, base_url2, api_key2 or new_key


@dataclass
class StreamState:
    user_id: int
    session_id: str
    created_at: float
    q: "queue.Queue[Tuple[str, dict]]"
    done: threading.Event
    error: Optional[str] = None
    cancelled: bool = False
    proc: Optional[subprocess.Popen] = None
    thread_id: Optional[int] = None
    legacy_delta_enabled: bool = True
    api_base_url: Optional[str] = None
    api_key: Optional[str] = None
    run_id: Optional[str] = None


class SuperAssistantService:
    def __init__(self, db: Session):
        self.db = db
        self._profile_service: Optional[HermesProfileService] = None

    def _get_profile_service(self) -> HermesProfileService:
        if self._profile_service is None:
            self._profile_service = HermesProfileService()
        return self._profile_service

    def _ensure_profile_for_user(self, user: User) -> str:
        profile = (user.hermes_profile or "").strip()
        if profile:
            return profile
        profile_service = self._get_profile_service()
        profile_name, _created, _message = profile_service.ensure_profile(user_id=user.id, tenant_id=1)
        if profile_name and user.hermes_profile != profile_name:
            user.hermes_profile = profile_name
            user.updated_at = datetime.utcnow()
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return profile_name

    def _get_hermes_home_for_profile(self, profile_name: str) -> Path:
        profile = (profile_name or "").strip() or "default"
        profile_service = self._get_profile_service()
        if profile == "default":
            hermes_home = os.environ.get("HERMES_HOME")
            if hermes_home and hermes_home.strip():
                p = Path(hermes_home.strip()).expanduser()
                if p.parent.name == "profiles":
                    return p.parent.parent
                return p
            base_override = os.environ.get("HERMES_BASE_HOME")
            if base_override and base_override.strip():
                return Path(base_override.strip()).expanduser()
            return Path.home() / ".hermes"

        p = profile_service.get_profile_path(profile)
        if p is not None:
            return p
        return Path.home() / ".hermes" / "profiles" / profile

    def _get_state_db_path(self, profile_name: str) -> Path:
        return self._get_hermes_home_for_profile(profile_name) / "state.db"

    def _get_webui_sessions_dir(self, hermes_home: Path) -> Path:
        return Path(hermes_home) / "webui" / "sessions"

    def _candidate_hermes_homes(self, profile_name: str) -> List[Path]:
        homes: List[Path] = []
        try:
            homes.append(_get_hermes_base_home())
        except Exception:
            pass
        try:
            homes.append(self._get_hermes_home_for_profile(profile_name))
        except Exception:
            pass
        uniq: List[Path] = []
        seen: set[str] = set()
        for h in homes:
            try:
                p = Path(h).expanduser().resolve()
            except Exception:
                p = Path(h).expanduser()
            key = str(p)
            if key in seen:
                continue
            seen.add(key)
            uniq.append(p)
        return uniq

    def _load_webui_session_index(self, hermes_home: Path) -> List[dict]:
        sessions_dir = self._get_webui_sessions_dir(hermes_home)
        idx = sessions_dir / "_index.json"
        if not idx.exists():
            return []
        try:
            raw = json.loads(idx.read_text(encoding="utf-8"))
        except Exception:
            return []
        if not isinstance(raw, list):
            return []
        out: List[dict] = []
        for it in raw:
            if isinstance(it, dict):
                out.append(it)
        return out

    def _read_webui_session_file(self, hermes_home: Path, session_id: str) -> dict:
        sid = (session_id or "").strip()
        if not sid:
            return {}
        sessions_dir = self._get_webui_sessions_dir(hermes_home)
        candidates = [
            sessions_dir / f"{sid}.json",
            sessions_dir / f"session_{sid}.json",
        ]
        for p in candidates:
            if not p.exists():
                continue
            try:
                raw = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(raw, dict):
                return raw
        return {}

    def _read_webui_first_user_message_text(self, hermes_home: Path, session_id: str) -> str:
        sess = self._read_webui_session_file(hermes_home, session_id)
        msgs = sess.get("messages")
        if not isinstance(msgs, list):
            return ""
        fallback = ""
        for m in msgs:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role") or "").strip().lower()
            content = str(m.get("content") or "")
            if _is_blank_text(content):
                continue
            if not fallback:
                fallback = content
            if role in ("user", "human"):
                return content
        return fallback

    def _extract_thinking_from_webui_message(self, msg: dict) -> Optional[str]:
        if not isinstance(msg, dict):
            return None
        rc = msg.get("reasoning_content")
        if isinstance(rc, str) and rc.strip():
            return rc
        rd = msg.get("reasoning_details")
        if isinstance(rd, list):
            for it in rd:
                if not isinstance(it, dict):
                    continue
                thinking = it.get("thinking")
                if isinstance(thinking, str) and thinking.strip():
                    return thinking
        r = msg.get("reasoning")
        if isinstance(r, str) and r.strip():
            return r
        return None

    def _get_webui_state_dir(self, profile_name: str) -> Path:
        d = self._get_hermes_home_for_profile(profile_name) / "webui_state"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _get_thinking_store_path(self, profile_name: str, session_id: str) -> Path:
        sid = (session_id or "").strip()
        base = self._get_webui_state_dir(profile_name) / "thinking"
        base.mkdir(parents=True, exist_ok=True)
        name = re.sub(r"[^0-9A-Za-z_-]+", "_", sid) or "unknown"
        return base / f"{name}.json"

    def _load_thinking_map(self, profile_name: str, session_id: str) -> dict[str, list[str]]:
        p = self._get_thinking_store_path(profile_name, session_id)
        if not p.exists():
            return {}
        raw = _safe_json_load(p)
        if not isinstance(raw, dict):
            return {}
        items = raw.get("items")
        if not isinstance(items, list):
            return {}
        out: dict[str, list[str]] = {}
        for it in items:
            if not isinstance(it, dict):
                continue
            h = str(it.get("answer_hash") or "").strip()
            t = str(it.get("thinking") or "")
            if not h or not t.strip():
                continue
            out.setdefault(h, []).append(t)
        return out

    def _persist_thinking_record(self, profile_name: str, *, session_id: str, answer: str, thinking: str) -> None:
        sid = (session_id or "").strip()
        if not sid:
            return
        a = str(answer or "").strip()
        th = str(thinking or "").strip()
        if not a or not th:
            return
        p = self._get_thinking_store_path(profile_name, sid)
        raw = _safe_json_load(p) if p.exists() else {}
        if not isinstance(raw, dict):
            raw = {}
        items = raw.get("items")
        if not isinstance(items, list):
            items = []
        rec = {
            "ts": _now_s(),
            "answer_hash": _sha1_text(a),
            "thinking": th,
        }
        items.append(rec)
        raw["items"] = items[-200:]
        try:
            _safe_json_write(p, raw)  # type: ignore[arg-type]
        except Exception:
            return

    def _get_workspaces_file(self, profile_name: str) -> Path:
        return self._get_webui_state_dir(profile_name) / "workspaces.json"

    def _get_last_workspace_file(self, profile_name: str) -> Path:
        return self._get_webui_state_dir(profile_name) / "last_workspace.txt"

    def _default_workspace_for_profile(self, profile_name: str) -> str:
        pn = (profile_name or "").strip() or "default"
        root = _agentnow_workspace_root()
        p = (root / pn).expanduser()
        p.mkdir(parents=True, exist_ok=True)
        try:
            return str(p.resolve())
        except Exception:
            return str(p)

    def _load_workspaces(self, profile_name: str) -> List[dict]:
        ws_file = self._get_workspaces_file(profile_name)
        raw = _safe_json_load(ws_file) if ws_file.exists() else []
        workspaces: List[dict] = []
        if isinstance(raw, list):
            for item in raw:
                if not isinstance(item, dict):
                    continue
                path = str(item.get("path") or "").strip()
                name = str(item.get("name") or "").strip()
                if not path:
                    continue
                p = Path(path).expanduser()
                try:
                    p = p.resolve()
                except Exception:
                    pass
                if not p.is_dir():
                    continue
                if _is_blocked_workspace_path(p):
                    continue
                if not _is_allowed_agentnow_workspace_path(p, profile_name=profile_name):
                    continue
                if not name:
                    name = p.name or "Workspace"
                if name.lower() == "default":
                    name = "Home"
                workspaces.append({"name": name, "path": str(p)})

        default_ws = self._default_workspace_for_profile(profile_name)
        if not workspaces:
            workspaces = [{"name": "Home", "path": default_ws}]
        else:
            has_default = any(str(w.get("path")) == default_ws for w in workspaces)
            if not has_default:
                workspaces.insert(0, {"name": "Home", "path": default_ws})
        seen: set[str] = set()
        deduped: List[dict] = []
        for w in workspaces:
            p = str(w.get("path") or "")
            if not p or p in seen:
                continue
            seen.add(p)
            deduped.append(w)
        try:
            _safe_json_write(ws_file, deduped)  # type: ignore[arg-type]
        except Exception:
            pass
        return deduped

    def _get_last_workspace(self, profile_name: str) -> str:
        last_file = self._get_last_workspace_file(profile_name)
        if last_file.exists():
            try:
                p = last_file.read_text(encoding="utf-8").strip()
                if p and Path(p).is_dir():
                    resolved = Path(p).expanduser()
                    try:
                        resolved = resolved.resolve()
                    except Exception:
                        pass
                    if _is_allowed_agentnow_workspace_path(resolved, profile_name=profile_name):
                        return str(resolved)
            except Exception:
                pass
        items = self._load_workspaces(profile_name)
        if items:
            return str(items[0].get("path") or "")
        return self._default_workspace_for_profile(profile_name)

    def _set_last_workspace(self, profile_name: str, path: str) -> str:
        raw = str(path or "").strip()
        p = Path(raw).expanduser()
        try:
            p = p.resolve()
        except Exception:
            pass
        if _is_blocked_workspace_path(p):
            raise ValueError("不允许的工作区路径")
        if not _is_allowed_agentnow_workspace_path(p, profile_name=profile_name):
            raise ValueError(f"工作区必须位于 {_agentnow_workspace_root() / profile_name}")
        p.mkdir(parents=True, exist_ok=True)
        if not p.is_dir():
            raise ValueError("工作区路径不可用")

        ws_file = self._get_workspaces_file(profile_name)
        items = self._load_workspaces(profile_name)
        name = p.name or "Workspace"
        if str(p) == self._default_workspace_for_profile(profile_name):
            name = "Home"
        items = [w for w in items if str(w.get("path") or "") != str(p)]
        items.append({"name": name, "path": str(p)})
        _safe_json_write(ws_file, items)  # type: ignore[arg-type]
        last_file = self._get_last_workspace_file(profile_name)
        last_file.write_text(str(p), encoding="utf-8")
        return str(p)

    def list_workspaces(self, *, user: User) -> Dict[str, Any]:
        profile = self._ensure_profile_for_user(user)
        items = self._load_workspaces(profile)
        current = self._get_last_workspace(profile)
        default_ws = self._default_workspace_for_profile(profile)
        return {"items": items, "current": current, "default": default_ws}

    def select_workspace(self, *, user: User, path: str) -> Dict[str, Any]:
        profile = self._ensure_profile_for_user(user)
        current = self._set_last_workspace(profile, path)
        items = self._load_workspaces(profile)
        default_ws = self._default_workspace_for_profile(profile)
        return {"items": items, "current": current, "default": default_ws}

    def _read_session_rows(self, profile_name: str, *, limit: int = 200) -> List[dict]:
        db_path = self._get_state_db_path(profile_name)
        if not db_path.exists():
            return []
        try:
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("PRAGMA table_info(sessions)")
                cols = {row[1] for row in cur.fetchall()}
                if not cols:
                    return []

                last_activity_expr = "s.last_activity" if "last_activity" in cols else "s.started_at"
                actual_count_expr = "s.actual_message_count" if "actual_message_count" in cols else "s.message_count"
                source_expr = "s.source" if "source" in cols else "NULL AS source"
                model_expr = "s.model" if "model" in cols else "NULL AS model"
                title_expr = "s.title" if "title" in cols else "NULL AS title"
                started_expr = "s.started_at" if "started_at" in cols else "0 AS started_at"
                message_count_expr = "s.message_count" if "message_count" in cols else "0 AS message_count"

                cur.execute(
                    f"""
                    SELECT s.id,
                           {title_expr},
                           {model_expr},
                           {message_count_expr} AS message_count,
                           {started_expr} AS started_at,
                           {last_activity_expr} AS last_activity,
                           {actual_count_expr} AS actual_message_count,
                           {source_expr}
                    FROM sessions s
                    WHERE s.id IS NOT NULL
                    ORDER BY COALESCE({last_activity_expr}, {started_expr}) DESC
                    LIMIT ?
                    """,
                    (int(limit),),
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception:
            return []

    def _read_session_meta(self, profile_name: str, session_id: str) -> dict:
        sid = (session_id or "").strip()
        if not sid:
            return {}
        db_path = self._get_state_db_path(profile_name)
        if not db_path.exists():
            return {}
        try:
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("PRAGMA table_info(sessions)")
                cols = {row[1] for row in cur.fetchall()}
                if not cols:
                    return {}

                last_activity_expr = "last_activity" if "last_activity" in cols else "started_at"
                actual_count_expr = "actual_message_count" if "actual_message_count" in cols else "message_count"
                source_expr = "source" if "source" in cols else "NULL AS source"
                model_expr = "model" if "model" in cols else "NULL AS model"
                title_expr = "title" if "title" in cols else "NULL AS title"
                started_expr = "started_at" if "started_at" in cols else "0 AS started_at"
                message_count_expr = "message_count" if "message_count" in cols else "0 AS message_count"

                cur.execute(
                    f"""
                    SELECT id,
                           {title_expr},
                           {model_expr},
                           {message_count_expr} AS message_count,
                           {started_expr} AS started_at,
                           {last_activity_expr} AS last_activity,
                           {actual_count_expr} AS actual_message_count,
                           {source_expr}
                    FROM sessions
                    WHERE id = ?
                    LIMIT 1
                    """,
                    (sid,),
                )
                row = cur.fetchone()
                return dict(row) if row else {}
        except Exception:
            return {}

    def _read_session_messages(self, profile_name: str, session_id: str) -> List[SuperAssistantMessage]:
        sid = (session_id or "").strip()
        if not sid:
            return []
        thinking_map = self._load_thinking_map(profile_name, sid)
        thinking_cursor: dict[str, int] = {}
        db_path = self._get_state_db_path(profile_name)
        if not db_path.exists():
            return []
        try:
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT role, content, timestamp
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY timestamp ASC
                    """,
                    (sid,),
                )
                out: List[SuperAssistantMessage] = []
                for row in cur.fetchall():
                    role = str(row["role"] or "").strip().lower()
                    if role not in ("user", "assistant"):
                        continue
                    content = str(row["content"] or "")
                    if _is_blank_text(content):
                        continue
                    thinking: Optional[str] = None
                    if role == "assistant" and thinking_map:
                        h = _sha1_text(content)
                        lst = thinking_map.get(h) or []
                        idx = thinking_cursor.get(h, 0)
                        if idx < len(lst):
                            thinking = lst[idx]
                            thinking_cursor[h] = idx + 1
                    out.append(
                        SuperAssistantMessage(
                            role=role,  # type: ignore[arg-type]
                            content=content,
                            thinking=thinking,
                            ts=float(row["timestamp"] or 0),
                        )
                    )
                return out
        except Exception:
            return []

    def _read_first_user_message_text(self, profile_name: str, session_id: str) -> str:
        sid = (session_id or "").strip()
        if not sid:
            return ""
        db_path = self._get_state_db_path(profile_name)
        if not db_path.exists():
            return ""
        try:
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT role, content
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY timestamp ASC
                    LIMIT 50
                    """,
                    (sid,),
                )
                fallback: str = ""
                for row in cur.fetchall():
                    role = str(row["role"] or "").strip().lower()
                    content = str(row["content"] or "")
                    if _is_blank_text(content):
                        continue
                    if not fallback:
                        fallback = content
                    if role in ("user", "human"):
                        return content
                return fallback
        except Exception:
            return ""

    def _ensure_session_title(self, profile_name: str, session_id: str, user_text: str) -> str:
        sid = (session_id or "").strip()
        if not sid:
            return "Untitled"
        desired = _derive_session_title_from_user_text(user_text)
        db_path = self._get_state_db_path(profile_name)
        if not db_path.exists():
            return desired
        try:
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("PRAGMA table_info(sessions)")
                cols = {row[1] for row in cur.fetchall()}
                if "title" not in cols:
                    return desired
                cur.execute("SELECT title FROM sessions WHERE id = ? LIMIT 1", (sid,))
                row = cur.fetchone()
                existing = str(row["title"] if row and "title" in row.keys() else "").strip()
                if existing and not _is_default_session_title(existing):
                    return existing
                cur.execute("UPDATE sessions SET title = ? WHERE id = ?", (desired, sid))
                conn.commit()
                return desired
        except Exception:
            return desired

    def list_sessions(self, *, user: User) -> List[SuperAssistantSessionListItem]:
        profile = self._ensure_profile_for_user(user)
        homes = self._candidate_hermes_homes(profile)
        by_id: dict[str, dict] = {}
        for h in homes:
            for it in self._load_webui_session_index(h):
                sid = str(it.get("session_id") or it.get("id") or "").strip()
                if not sid:
                    continue
                prev = by_id.get(sid)
                if prev is None:
                    by_id[sid] = dict(it)
                    by_id[sid]["__home"] = str(h)
                    continue
                try:
                    prev_ts = float(prev.get("updated_at") or prev.get("last_message_at") or prev.get("created_at") or 0)
                except Exception:
                    prev_ts = 0.0
                try:
                    cur_ts = float(it.get("updated_at") or it.get("last_message_at") or it.get("created_at") or 0)
                except Exception:
                    cur_ts = 0.0
                if cur_ts >= prev_ts:
                    by_id[sid] = dict(it)
                    by_id[sid]["__home"] = str(h)

        def _build_items(*, require_profile_match: bool) -> List[SuperAssistantSessionListItem]:
            out: List[SuperAssistantSessionListItem] = []
            for sid, it in by_id.items():
                try:
                    source = str(it.get("source_tag") or it.get("source") or "").strip().lower()
                    if source == "cron" or sid.startswith("cron_"):
                        continue
                    sess_profile = str(it.get("profile") or "default").strip() or "default"
                    if require_profile_match and sess_profile != (profile or "default"):
                        continue
                    title = str(it.get("title") or "").strip()
                    created_at = float(it.get("created_at") or 0)
                    updated_at = float(it.get("updated_at") or it.get("last_message_at") or created_at or 0)
                    last_message_at = it.get("last_message_at")
                    try:
                        last_message_at_f = float(last_message_at) if last_message_at is not None else None
                    except Exception:
                        last_message_at_f = None
                    message_count = int(it.get("message_count") or 0)

                    home_str = str(it.get("__home") or "").strip()
                    home = Path(home_str) if home_str else None
                    if (message_count <= 0 or _is_default_session_title(title)) and home is not None:
                        seed = self._read_webui_first_user_message_text(home, sid)
                        if _is_default_session_title(title) and seed:
                            title = _derive_session_title_from_user_text(seed)
                        if message_count <= 0 and seed:
                            message_count = 1

                    title = str(title or "").strip() or "Untitled"
                    if message_count <= 0 and _is_default_session_title(title):
                        continue

                    out.append(
                        SuperAssistantSessionListItem(
                            session_id=sid,
                            title=title,
                            profile=profile or "default",
                            created_at=created_at or updated_at or _now_s(),
                            updated_at=updated_at or created_at or _now_s(),
                            message_count=message_count,
                            last_message_at=last_message_at_f or updated_at or None,
                        )
                    )
                except Exception:
                    continue
            out.sort(key=lambda s: (s.updated_at or s.created_at), reverse=True)
            if len(out) > 200:
                out = out[:200]
            return out

        items = _build_items(require_profile_match=True)
        if items:
            return items
        items = _build_items(require_profile_match=False)
        if items:
            return items

        items = []
        for row in self._read_session_rows(profile, limit=200):
            try:
                sid = str(row.get("id") or "").strip()
                if not sid:
                    continue
                source = str(row.get("source") or "").strip().lower()
                if source == "cron":
                    continue
                message_count = int(row.get("actual_message_count") or row.get("message_count") or 0)
                started_at = float(row.get("started_at") or 0)
                last_activity = float(row.get("last_activity") or started_at or 0)
                title = str(row.get("title") or "").strip()
                if _is_default_session_title(title):
                    first_user = self._read_first_user_message_text(profile, sid)
                    title = self._ensure_session_title(profile, sid, first_user)
                title = str(title or "").strip() or "Untitled"
                if message_count <= 0 and _is_default_session_title(title):
                    continue
                items.append(
                    SuperAssistantSessionListItem(
                        session_id=sid,
                        title=title,
                        profile=profile or "default",
                        created_at=started_at or last_activity or _now_s(),
                        updated_at=last_activity or started_at or _now_s(),
                        message_count=message_count,
                        last_message_at=last_activity or None,
                    )
                )
            except Exception:
                continue
        return items

    def get_session(self, *, user: User, session_id: str) -> SuperAssistantSession:
        profile = self._ensure_profile_for_user(user)
        sid = (session_id or "").strip()
        if not sid:
            raise FileNotFoundError("Session not found")

        homes = self._candidate_hermes_homes(profile)
        def _try_read_webui(*, require_profile_match: bool) -> Optional[SuperAssistantSession]:
            for h in homes:
                sess = self._read_webui_session_file(h, sid)
                if not sess:
                    continue
                sess_profile = str(sess.get("profile") or "default").strip() or "default"
                if require_profile_match and sess_profile != (profile or "default"):
                    continue
                title = str(sess.get("title") or "").strip() or "Untitled"
                created_at = float(sess.get("created_at") or _now_s())
                updated_at = float(sess.get("updated_at") or created_at)
                model = str(sess.get("model") or "").strip() or None
                raw_msgs = sess.get("messages")
                out_msgs: List[SuperAssistantMessage] = []
                if isinstance(raw_msgs, list):
                    for m in raw_msgs:
                        if not isinstance(m, dict):
                            continue
                        role = str(m.get("role") or "").strip().lower()
                        if role not in ("user", "assistant"):
                            continue
                        content = str(m.get("content") or "")
                        if _is_blank_text(content):
                            continue
                        thinking = None
                        if role == "assistant":
                            thinking = self._extract_thinking_from_webui_message(m)
                        ts = m.get("timestamp")
                        try:
                            ts_f = float(ts) if ts is not None else 0.0
                        except Exception:
                            ts_f = 0.0
                        out_msgs.append(
                            SuperAssistantMessage(
                                role=role,  # type: ignore[arg-type]
                                content=content,
                                thinking=thinking,
                                ts=ts_f or 0.0,
                            )
                        )
                if _is_default_session_title(title):
                    seed = ""
                    for m in out_msgs:
                        if m.role == "user" and not _is_blank_text(m.content):
                            seed = m.content
                            break
                    if seed:
                        title = _derive_session_title_from_user_text(seed)
                return SuperAssistantSession(
                    session_id=sid,
                    title=title,
                    profile=profile or "default",
                    hermes_session_id=sid,
                    hermes_response_id=None,
                    model=model,
                    reasoning_effort=None,
                    show_reasoning=None,
                    created_at=created_at,
                    updated_at=updated_at,
                    message_count=len(out_msgs),
                    messages=out_msgs,
                )
            return None

        session = _try_read_webui(require_profile_match=True)
        if session is None:
            session = _try_read_webui(require_profile_match=False)
        if session is not None:
            return session

        meta = self._read_session_meta(profile, sid)
        messages = self._read_session_messages(profile, sid)
        if not meta and not messages:
            raise FileNotFoundError("Session not found")

        created_at = float(meta.get("started_at") or (messages[0].ts if messages else _now_s()))
        updated_at = float(meta.get("last_activity") or (messages[-1].ts if messages else created_at))
        title = str(meta.get("title") or "").strip()
        if _is_default_session_title(title):
            seed = ""
            for m in messages:
                if m.role == "user" and not _is_blank_text(m.content):
                    seed = m.content
                    break
            if not seed:
                seed = self._read_first_user_message_text(profile, sid)
            title = self._ensure_session_title(profile, sid, seed)
        title = str(title or "").strip() or "Untitled"
        model = str(meta.get("model") or "").strip() or None

        return SuperAssistantSession(
            session_id=sid,
            title=title,
            profile=profile or "default",
            hermes_session_id=sid,
            hermes_response_id=None,
            model=model,
            reasoning_effort=None,
            show_reasoning=None,
            created_at=created_at,
            updated_at=updated_at,
            message_count=len(messages),
            messages=messages,
        )

    def update_session_settings(
        self,
        *,
        user: User,
        session_id: str,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        show_reasoning: Optional[bool] = None,
    ) -> SuperAssistantSession:
        session = self.get_session(user=user, session_id=session_id)
        if model is not None:
            session.model = model.strip() or None
        if reasoning_effort is not None:
            session.reasoning_effort = reasoning_effort.strip() or None
        if show_reasoning is not None:
            session.show_reasoning = bool(show_reasoning)
        return session

    def delete_session(self, *, user: User, session_id: str) -> None:
        profile = self._ensure_profile_for_user(user)
        sid = (session_id or "").strip()
        if not sid:
            return
        db_path = self._get_state_db_path(profile)
        if not db_path.exists():
            return
        try:
            with sqlite3.connect(str(db_path)) as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM messages WHERE session_id = ?", (sid,))
                cur.execute("DELETE FROM sessions WHERE id = ?", (sid,))
                conn.commit()
        except Exception:
            return

    def append_user_message(self, *, user: User, session_id: str, content: str) -> SuperAssistantSession:
        return self.get_session(user=user, session_id=session_id)

    def finalize_assistant_message(
        self,
        *,
        user: User,
        session_id: str,
        assistant_content: str,
        hermes_session_id: Optional[str] = None,
        hermes_response_id: Optional[str] = None,
    ) -> SuperAssistantSession:
        return self.get_session(user=user, session_id=session_id)


_STREAMS_LOCK = threading.Lock()
_STREAMS: Dict[str, StreamState] = {}


def start_hermes_chat_stream(
    *,
    db: Session,
    user: User,
    session_id: Optional[str],
    message: str,
    workspace: Optional[str] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    show_reasoning: Optional[bool] = None,
    attachments: Optional[list[dict]] = None,
    legacy_delta_enabled: bool = True,
) -> Tuple[str, StreamState]:
    service = SuperAssistantService(db)
    profile = (service._ensure_profile_for_user(user) or "").strip() or "default"
    resolved_ws: Optional[str] = None
    try:
        if workspace and str(workspace).strip():
            resolved_ws = service._set_last_workspace(profile, str(workspace))
        else:
            resolved_ws = service._get_last_workspace(profile)
    except Exception:
        resolved_ws = service._default_workspace_for_profile(profile)

    att_list = attachments or []
    att_paths: List[str] = []
    image_atts: List[Tuple[Path, str]] = []
    for att in att_list:
        if not isinstance(att, dict):
            continue
        raw_path = str(att.get("path") or "").strip()
        if not raw_path:
            continue
        p = Path(raw_path).expanduser()
        if not p.exists() or not p.is_file():
            continue
        mime = str(att.get("mime") or "").strip() or (mimetypes.guess_type(p.name)[0] or "")
        is_image = bool(att.get("is_image")) or _is_image_mime(mime)
        att_paths.append(str(p))
        if is_image and mime:
            image_atts.append((p, mime))

    msg_text = (message or "").strip()
    title_seed_text = msg_text
    if att_paths and not msg_text:
        msg_text = f"I've uploaded {len(att_paths)} file(s): {', '.join(att_paths)}"
    elif att_paths:
        msg_text = f"{msg_text}\n\n[Attached files: {', '.join(att_paths)}]"
    hermes_session_id = (session_id or "").strip() or None

    stream_id = uuid.uuid4().hex
    st = StreamState(
        user_id=user.id,
        session_id=hermes_session_id or "",
        created_at=_now_s(),
        q=queue.Queue(),
        done=threading.Event(),
        legacy_delta_enabled=bool(legacy_delta_enabled),
    )
    with _STREAMS_LOCK:
        _STREAMS[stream_id] = st

    def _run():
        assistant_chunks: List[str] = []
        reasoning_chunks: List[str] = []
        captured_session_id: Optional[str] = None
        try:
            st.thread_id = threading.current_thread().ident
            profile_service = service._get_profile_service()
            global_cfg = _read_global_hermes_config()
            if reasoning_effort:
                profile_service.update_profile_config(profile, {"agent": {"reasoning_effort": reasoning_effort}})
            if show_reasoning is not None:
                profile_service.update_profile_config(profile, {"display": {"show_reasoning": bool(show_reasoning)}})
            selected_model = (model or "").strip()
            provider_cfg = profile_service.get_profile_config(profile) or {}
            existing_model_cfg = provider_cfg.get("model", {})
            existing_provider = None
            if isinstance(existing_model_cfg, dict):
                existing_provider = str(existing_model_cfg.get("provider") or "").strip() or None

            if selected_model:
                provider, base_url = _resolve_provider_for_model(selected_model, global_cfg)
                model_patch: dict = {"default": selected_model}
                if provider:
                    model_patch["provider"] = provider
                if base_url:
                    model_patch["base_url"] = base_url
                profile_service.update_profile_config(profile, {"model": model_patch})
            elif not existing_provider:
                provider, base_url = _resolve_provider_for_model(str(existing_model_cfg.get("default") or "").strip(), global_cfg) if isinstance(existing_model_cfg, dict) else _resolve_provider_for_model("", global_cfg)
                model_patch: dict = {}
                if provider:
                    model_patch["provider"] = provider
                if base_url:
                    model_patch["base_url"] = base_url
                if model_patch:
                    profile_service.update_profile_config(profile, {"model": model_patch})

            profile_dir = profile_service.get_profile_path(profile)
            if profile_dir is None:
                profile_dir = Path.home() / ".hermes" / "profiles" / profile
            profile_config_path, _profile_env_path = profile_service.get_profile_config_path(profile)
            _ensure_profile_config_has_base(profile_config_path)

            env_updates: Dict[str, Optional[str]] = {}
            env_updates.update({k: v for k, v in _build_hermes_cli_env(profile_service, profile).items()})
            env_updates["HERMES_HOME"] = str(profile_dir)
            env_updates["PYTHONUNBUFFERED"] = "1"
            if resolved_ws:
                env_updates["TERMINAL_CWD"] = str(resolved_ws)
                env_updates["HERMES_WRITE_SAFE_ROOT"] = str(resolved_ws)

            def _put(event: str, payload: dict) -> None:
                try:
                    st.q.put((event, payload))
                except Exception:
                    return

            trace_enabled = True
            model_reasoning_enabled = show_reasoning is True
            legacy_think_opened = {"yes": False}
            legacy_think_closed = {"yes": False}

            def _legacy_delta(text: str) -> None:
                if not st.legacy_delta_enabled:
                    return
                if not text:
                    return
                try:
                    st.q.put(("delta", {"text": text}))
                except Exception:
                    return

            def _legacy_open_think() -> None:
                if legacy_think_opened["yes"] or not trace_enabled:
                    return
                legacy_think_opened["yes"] = True
                _legacy_delta("<think>\n")

            def _legacy_close_think() -> None:
                if not legacy_think_opened["yes"] or legacy_think_closed["yes"]:
                    return
                legacy_think_closed["yes"] = True
                _legacy_delta("\n</think>\n\n")

            def _emit_token(text: str) -> None:
                if not text:
                    return
                _legacy_close_think()
                assistant_chunks.append(text)
                _put("token", {"text": text})
                _legacy_delta(text)

            def _emit_reasoning(text: str) -> None:
                if not trace_enabled:
                    return
                if not text:
                    return
                _legacy_open_think()
                _legacy_delta(text)
                reasoning_chunks.append(text)
                _put("reasoning", {"text": text})

            def _on_reasoning_delta(t: str) -> None:
                _emit_reasoning(str(t or ""))

            def _on_tool_start(tool_name: str, args_preview: str = "") -> None:
                preview = (args_preview or "").strip()
                _put(
                    "tool",
                    {
                        "event_type": "tool.started",
                        "name": str(tool_name or ""),
                        "preview": preview or None,
                        "args": {},
                    },
                )

            def _on_tool_complete(tool_name: str, ok: bool = True) -> None:
                _put(
                    "tool_complete",
                    {
                        "event_type": "tool.completed",
                        "name": str(tool_name or ""),
                        "is_error": not bool(ok),
                    },
                )

            def _on_assistant_delta(t: str) -> None:
                _emit_token(str(t or ""))

            class _ThinkTagDemuxer:
                def __init__(self) -> None:
                    self._buf = ""
                    self._in_think = False

                def feed(self, chunk: str) -> None:
                    if not chunk:
                        return
                    self._buf += chunk
                    self._drain()

                def flush(self) -> None:
                    self._drain(flush=True)

                def _drain(self, *, flush: bool = False) -> None:
                    while True:
                        lo = self._buf.lower()
                        open_i = lo.find("<think>")
                        close_i = lo.find("</think>")
                        if open_i == -1 and close_i == -1:
                            if flush and self._buf:
                                self._emit(self._buf)
                                self._buf = ""
                            return
                        if open_i != -1 and (close_i == -1 or open_i < close_i):
                            before = self._buf[:open_i]
                            if before:
                                self._emit(before)
                            self._buf = self._buf[open_i + 7 :]
                            self._in_think = True
                            continue
                        if close_i != -1:
                            before = self._buf[:close_i]
                            if before:
                                self._emit(before)
                            self._buf = self._buf[close_i + 8 :]
                            self._in_think = False
                            continue

                def _emit(self, text: str) -> None:
                    if not text:
                        return
                    if self._in_think:
                        _emit_reasoning(text)
                    else:
                        _emit_token(text)

            demux = _ThinkTagDemuxer()

            mode_used = {"v": "agent"}
            with _temporary_environ(env_updates):
                AIAgent = _import_hermes_ai_agent()
                if AIAgent is None and not _HERMES_AGENT_PREWARM_DONE.is_set():
                    for _ in range(900):
                        if st.cancelled:
                            break
                        if _HERMES_AGENT_PREWARM_DONE.wait(timeout=0.2):
                            break
                    AIAgent = _import_hermes_ai_agent()
                if AIAgent is not None:
                    mode_used["v"] = "agent"
                    resolved_provider: Optional[str] = None
                    resolved_base_url: Optional[str] = None
                    resolved_api_key: Optional[str] = None
                    resolved_api_mode: Optional[str] = None
                    try:
                        provider_hint, base_url_hint = _resolve_provider_for_model(selected_model, global_cfg) if selected_model else (None, None)
                        from hermes_cli.runtime_provider import resolve_runtime_provider  # type: ignore
                        rt = resolve_runtime_provider(
                            requested=provider_hint,
                            explicit_base_url=base_url_hint,
                            target_model=selected_model or None,
                        )
                        resolved_provider = str(rt.get("provider") or provider_hint or "").strip() or None
                        resolved_base_url = str(rt.get("base_url") or base_url_hint or "").strip() or None
                        resolved_api_key = str(rt.get("api_key") or "").strip() or None
                        resolved_api_mode = str(rt.get("api_mode") or "").strip() or None
                    except Exception:
                        resolved_provider = None
                        resolved_base_url = None
                        resolved_api_key = None
                        resolved_api_mode = None

                    reasoning_cfg: Optional[dict] = None
                    if str(reasoning_effort or "").strip() and str(reasoning_effort or "").strip().lower() != "none":
                        eff = str(reasoning_effort or "").strip() or "medium"
                        reasoning_cfg = {"enabled": True, "effort": eff}
                    else:
                        reasoning_cfg = {"enabled": False, "effort": "none"}

                    agent = AIAgent(
                        base_url=resolved_base_url,
                        api_key=resolved_api_key,
                        provider=resolved_provider,
                        api_mode=resolved_api_mode,
                        model=selected_model or "",
                        platform="webui",
                        quiet_mode=True,
                        session_id=hermes_session_id or None,
                        stream_delta_callback=_on_assistant_delta,
                        reasoning_callback=_on_reasoning_delta if model_reasoning_enabled else None,
                        tool_progress_callback=_on_tool_start,
                        tool_complete_callback=_on_tool_complete,
                        reasoning_config=reasoning_cfg,
                    )
                    captured_session_id = getattr(agent, "session_id", None) or hermes_session_id
                    def _stream_enable_noop(_: str) -> None:
                        return
                    result = agent.run_conversation(msg_text, stream_callback=_stream_enable_noop)
                    out_text = ""
                    if isinstance(result, dict):
                        out_text = str(result.get("final_response") or result.get("response") or "")
                    if out_text and not assistant_chunks:
                        _emit_token(out_text)
                else:
                    detail = str(_HERMES_AGENT_IMPORT_LAST_ERROR.get("text") or "").strip()
                    hint = "请在 AgentNow 后端环境执行 uv sync（确保已包含 hermes-agent 依赖），然后重启后端。"
                    raise RuntimeError(
                        "当前后端环境未能加载 hermes-agent（WebUI 的真实流式依赖它）。\n"
                        + hint
                        + ("\n\nimport traceback (tail):\n" + detail if detail else "")
                    )

            if st.cancelled:
                try:
                    if st.proc is not None:
                        st.proc.terminate()
                except Exception:
                    pass

            full = "".join(assistant_chunks).strip()
            thinking_full = "".join(reasoning_chunks).strip()
            if not full and thinking_full and "⚕ Hermes" in thinking_full:
                p = thinking_full.find("⚕ Hermes")
                ls = thinking_full.rfind("\n", 0, p)
                if ls == -1:
                    ls = 0
                le = thinking_full.find("\n", p)
                if le == -1:
                    le = p
                derived = thinking_full[le:].strip()
                prefix = thinking_full[:ls].strip()
                if derived:
                    full = derived
                    thinking_full = prefix

            sid_out = captured_session_id or hermes_session_id
            if st.cancelled:
                _legacy_close_think()
                st.q.put(("cancel", {"ok": True, "session_id": sid_out, "mode": mode_used["v"]}))
            else:
                _legacy_close_think()
                try:
                    if sid_out:
                        service._ensure_session_title(profile, str(sid_out), title_seed_text)
                        service._persist_thinking_record(profile, session_id=str(sid_out), answer=full, thinking=thinking_full)
                except Exception:
                    pass
                st.q.put(("done", {"ok": True, "session_id": sid_out, "mode": mode_used["v"]}))
        except Exception as e:
            st.error = str(e)
            _legacy_close_think()
            st.q.put(("error", {"ok": False, "message": str(e)}))
        finally:
            st.done.set()

    threading.Thread(target=_run, daemon=True).start()
    return stream_id, st


def get_stream(stream_id: str) -> Optional[StreamState]:
    with _STREAMS_LOCK:
        return _STREAMS.get(stream_id)


def remove_stream(stream_id: str) -> None:
    with _STREAMS_LOCK:
        _STREAMS.pop(stream_id, None)


def cancel_stream(stream_id: str, *, user_id: int) -> bool:
    st = get_stream(stream_id)
    if st is None:
        return False
    if st.user_id != user_id:
        return False
    st.cancelled = True
    try:
        base_home = _get_hermes_base_home()
        agent_root = base_home / "hermes-agent"
        if agent_root.exists() and str(agent_root) not in sys.path:
            sys.path.insert(0, str(agent_root))
        from tools.interrupt import set_interrupt  # type: ignore
        if st.thread_id is not None:
            set_interrupt(True, thread_id=st.thread_id)
    except Exception:
        pass
    if st.proc is not None:
        try:
            st.proc.terminate()
        except Exception:
            pass
    try:
        st.q.put(("cancel", {"ok": True, "stream_id": stream_id}))
    except Exception:
        pass
    st.done.set()
    return True


def stream_sse_generator(stream_id: str):
    st = get_stream(stream_id)
    if st is None:
        yield _sse_bytes("error", {"ok": False, "message": "stream not found"})
        return

    yield (": init " + (" " * 2048) + "\n\n").encode("utf-8")
    yield _sse_bytes("open", {"ok": True, "stream_id": stream_id})
    last_ping = _now_s()
    while True:
        try:
            evt, payload = st.q.get(timeout=0.75)
            yield _sse_bytes(evt, payload)
            if evt in {"done", "error", "cancel"}:
                yield _sse_bytes("stream_end", {"stream_id": stream_id})
                break
        except queue.Empty:
            if st.done.is_set():
                break
            now = _now_s()
            if now - last_ping >= 15:
                last_ping = now
                yield b": ping\n\n"
            continue

    remove_stream(stream_id)
