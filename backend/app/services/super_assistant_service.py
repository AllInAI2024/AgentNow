from __future__ import annotations

import json
import os
import queue
import re
import shutil
import sqlite3
import subprocess
import threading
import time
import uuid
import base64
import mimetypes
import select
import pty
import sys
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
    base_home = _get_hermes_base_home()
    agent_root = base_home / "hermes-agent"
    if agent_root.exists() and str(agent_root) not in sys.path:
        sys.path.insert(0, str(agent_root))
    try:
        from run_agent import AIAgent  # type: ignore
        return AIAgent
    except Exception:
        return None


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
            if nl == -1:
                break
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
                if not self._opened_think:
                    out.append("<think>\n")
                    self._opened_think = True
                if t:
                    out.append(t + ("\n" if not allow_partial else ""))
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

    def _get_webui_state_dir(self, profile_name: str) -> Path:
        d = self._get_hermes_home_for_profile(profile_name) / "webui_state"
        d.mkdir(parents=True, exist_ok=True)
        return d

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
                    out.append(
                        SuperAssistantMessage(
                            role=role,  # type: ignore[arg-type]
                            content=content,
                            ts=float(row["timestamp"] or 0),
                        )
                    )
                return out
        except Exception:
            return []

    def list_sessions(self, *, user: User) -> List[SuperAssistantSessionListItem]:
        profile = self._ensure_profile_for_user(user)
        items: List[SuperAssistantSessionListItem] = []
        for row in self._read_session_rows(profile, limit=200):
            try:
                sid = str(row.get("id") or "").strip()
                if not sid:
                    continue
                source = str(row.get("source") or "").strip().lower()
                if source == "cron":
                    continue
                message_count = int(row.get("actual_message_count") or row.get("message_count") or 0)
                if message_count <= 0:
                    continue
                started_at = float(row.get("started_at") or 0)
                last_activity = float(row.get("last_activity") or started_at or 0)
                title = str(row.get("title") or "").strip() or "Untitled"
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

        meta = self._read_session_meta(profile, sid)
        messages = self._read_session_messages(profile, sid)
        if not meta and not messages:
            raise FileNotFoundError("Session not found")

        created_at = float(meta.get("started_at") or (messages[0].ts if messages else _now_s()))
        updated_at = float(meta.get("last_activity") or (messages[-1].ts if messages else created_at))
        title = str(meta.get("title") or "").strip() or "Untitled"
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
    )
    with _STREAMS_LOCK:
        _STREAMS[stream_id] = st

    def _run():
        assistant_chunks: List[str] = []
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

            think_opened = {"yes": False}
            think_closed = {"yes": False}

            def _send(text: str) -> None:
                if not text:
                    return
                assistant_chunks.append(text)
                st.q.put(("delta", {"text": text}))

            def _send_chunked(text: str) -> None:
                s = str(text or "")
                if not s:
                    return
                step = 24
                for i in range(0, len(s), step):
                    if st.cancelled:
                        break
                    _send(s[i : i + step])
                    time.sleep(0.01)

            def _open_think() -> None:
                if think_opened["yes"]:
                    return
                think_opened["yes"] = True
                _send("<think>\n")

            def _close_think() -> None:
                if not think_opened["yes"] or think_closed["yes"]:
                    return
                think_closed["yes"] = True
                _send("\n</think>\n\n")

            def _on_reasoning_delta(t: str) -> None:
                _open_think()
                _send(str(t or ""))

            def _on_status(t: str) -> None:
                _open_think()
                _send(str(t or "") + "\n")

            def _on_tool_start(tool_name: str, args_preview: str = "") -> None:
                _open_think()
                preview = (args_preview or "").strip()
                if preview:
                    _send(f"\n[tool] {tool_name}: {preview}\n")
                else:
                    _send(f"\n[tool] {tool_name}\n")

            def _on_tool_complete(tool_name: str, ok: bool = True) -> None:
                _open_think()
                _send(f"[tool] {tool_name} {'ok' if ok else 'failed'}\n")

            first_assistant_delta = {"yes": False}

            def _on_assistant_delta(t: str) -> None:
                if not first_assistant_delta["yes"]:
                    first_assistant_delta["yes"] = True
                    _close_think()
                _send(str(t or ""))

            mode_used = {"v": "agent"}
            with _temporary_environ(env_updates):
                AIAgent = _import_hermes_ai_agent()
                if AIAgent is not None:
                    mode_used["v"] = "agent"
                    _open_think()
                    _send("正在初始化智能体…\n")
                    agent = AIAgent(
                        model=selected_model or "",
                        session_id=hermes_session_id or None,
                        stream_delta_callback=_on_assistant_delta,
                        reasoning_callback=_on_reasoning_delta if (show_reasoning is not False) else None,
                        tool_progress_callback=_on_tool_start,
                        tool_complete_callback=_on_tool_complete,
                        status_callback=_on_status,
                    )
                    captured_session_id = getattr(agent, "session_id", None) or hermes_session_id
                    result = agent.run_conversation(msg_text, stream_callback=None)
                    out_text = ""
                    if isinstance(result, dict):
                        out_text = str(result.get("final_response") or result.get("response") or "")
                    if out_text and not first_assistant_delta["yes"]:
                        _close_think()
                        _send_chunked(out_text)
                    if not think_closed["yes"]:
                        _close_think()
                else:
                    hermes_bin_path = shutil.which("hermes")
                    if not hermes_bin_path:
                        raise RuntimeError("hermes not found and hermes-agent not importable")

                    mode_used["v"] = "cli-pty"
                    _open_think()
                    _send("正在初始化智能体…\n")

                    cmd: List[str] = [hermes_bin_path]
                    if profile and profile != "default":
                        cmd.extend(["-p", profile])
                    cmd.extend(["chat", "-q", msg_text, "--source", "webui"])
                    if hermes_session_id:
                        cmd.extend(["--resume", hermes_session_id])

                    env = os.environ.copy()
                    env.update(_build_hermes_cli_env(profile_service, profile))
                    env["PYTHONUNBUFFERED"] = "1"
                    if resolved_ws:
                        env["TERMINAL_CWD"] = str(resolved_ws)
                        env["HERMES_WRITE_SAFE_ROOT"] = str(resolved_ws)

                    parser = HermesCliStreamParser(opened_think=True)
                    master_fd: Optional[int] = None
                    slave_fd: Optional[int] = None

                    try:
                        master_fd, slave_fd = pty.openpty()
                        proc = subprocess.Popen(
                            cmd,
                            stdin=slave_fd,
                            stdout=slave_fd,
                            stderr=slave_fd,
                            env=env,
                            cwd=resolved_ws or None,
                            close_fds=True,
                        )
                        st.proc = proc
                        try:
                            os.close(slave_fd)
                        except Exception:
                            pass
                        slave_fd = None

                        try:
                            os.set_blocking(master_fd, False)
                        except Exception:
                            pass

                        while True:
                            if st.cancelled:
                                try:
                                    proc.terminate()
                                except Exception:
                                    pass
                                break

                            if proc.poll() is not None:
                                break

                            r, _, _ = select.select([master_fd], [], [], 0.25)
                            if not r:
                                continue

                            try:
                                data = os.read(master_fd, 4096)
                            except Exception:
                                data = b""

                            if not data:
                                continue

                            text = data.decode("utf-8", errors="ignore")
                            st.q.put(("term", {"data": text}))
                            emitted, sid = parser.feed(text)
                            if sid:
                                captured_session_id = sid
                            if emitted:
                                for part in emitted:
                                    if part:
                                        _send(part)

                        try:
                            proc.wait(timeout=2)
                        except Exception:
                            try:
                                proc.kill()
                            except Exception:
                                pass
                            try:
                                proc.wait(timeout=2)
                            except Exception:
                                pass

                        emitted, sid = parser.feed("", flush_partial=True)
                        if sid:
                            captured_session_id = sid
                        if emitted:
                            for part in emitted:
                                if part:
                                    _send(part)
                    except Exception:
                        mode_used["v"] = "cli"
                        try:
                            if slave_fd is not None:
                                os.close(slave_fd)
                        except Exception:
                            pass
                        try:
                            if master_fd is not None:
                                os.close(master_fd)
                        except Exception:
                            pass

                        cmd_q: List[str] = [hermes_bin_path]
                        if profile and profile != "default":
                            cmd_q.extend(["-p", profile])
                        cmd_q.extend(["chat", "-q", msg_text, "-Q", "--source", "webui"])
                        if hermes_session_id:
                            cmd_q.extend(["--resume", hermes_session_id])
                        proc_q = subprocess.Popen(
                            cmd_q,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1,
                            env=env,
                            cwd=resolved_ws or None,
                        )
                        st.proc = proc_q
                        out = ""
                        if proc_q.stdout is not None:
                            out = proc_q.stdout.read() or ""
                        proc_q.wait()
                        _close_think()
                        if out:
                            _send_chunked(out.strip())
                    finally:
                        try:
                            if slave_fd is not None:
                                os.close(slave_fd)
                        except Exception:
                            pass
                        try:
                            if master_fd is not None:
                                os.close(master_fd)
                        except Exception:
                            pass

            if st.cancelled:
                try:
                    if st.proc is not None:
                        st.proc.terminate()
                except Exception:
                    pass

            full = "".join(assistant_chunks).strip()

            sid_out = captured_session_id or hermes_session_id
            if st.cancelled:
                st.q.put(("cancel", {"ok": True, "session_id": sid_out, "mode": mode_used["v"]}))
            else:
                st.q.put(("done", {"ok": True, "session_id": sid_out, "mode": mode_used["v"]}))
        except Exception as e:
            st.error = str(e)
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
        except queue.Empty:
            if st.done.is_set():
                break
            now = _now_s()
            if now - last_ping >= 15:
                last_ping = now
                yield b": ping\n\n"
            continue

    remove_stream(stream_id)
