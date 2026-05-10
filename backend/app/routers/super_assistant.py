from __future__ import annotations

import os
import asyncio
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Request, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

import yaml

from app.models import User
from app.schemas.user import APIResponse
from app.services.auth_service import decode_access_token, SessionLocal
from app.schemas.super_assistant import (
    SuperAssistantSession,
    SuperAssistantSessionListResponse,
    SuperAssistantChatStartRequest,
    SuperAssistantChatStartResponse,
    SuperAssistantDeleteSessionRequest,
    SuperAssistantModelListResponse,
    SuperAssistantModelListItem,
    SuperAssistantUploadResponse,
    SuperAssistantWorkspaceListResponse,
    SuperAssistantWorkspaceItem,
    SuperAssistantWorkspaceSelectRequest,
)
from app.services.auth_service import get_db, permission_required
from app.services.super_assistant_service import (
    SuperAssistantService,
    start_hermes_chat_stream,
    get_stream,
    stream_sse_generator,
    cancel_stream,
)
from app.services.hermes_profile_service import HermesProfileService

router = APIRouter(prefix="/assistant", tags=["超级助理"])
webui_compat_router = APIRouter(tags=["Hermes WebUI 兼容"])


def _extract_bearer_token(value: str | None) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.lower().startswith("bearer "):
        raw = raw[7:].strip()
    return raw or None


def _resolve_user_id_for_stream(request: Request, token: str | None) -> int | None:
    t = _extract_bearer_token(token) or _extract_bearer_token(request.headers.get("Authorization"))
    if not t:
        return None
    return decode_access_token(t)


@router.get(
    "/sessions",
    response_model=APIResponse[SuperAssistantSessionListResponse],
    summary="获取会话列表",
)
def list_sessions(
    current_user: User = Depends(permission_required("dashboard")),
    db: Session = Depends(get_db),
):
    service = SuperAssistantService(db)
    items = service.list_sessions(user=current_user)
    return APIResponse(code=200, message="获取成功", data=SuperAssistantSessionListResponse(items=items))


@router.get(
    "/workspaces",
    response_model=APIResponse[SuperAssistantWorkspaceListResponse],
    summary="获取工作区列表",
)
def list_workspaces(
    current_user: User = Depends(permission_required("dashboard")),
    db: Session = Depends(get_db),
):
    service = SuperAssistantService(db)
    res = service.list_workspaces(user=current_user)
    items = [SuperAssistantWorkspaceItem(**i) for i in (res.get("items") or [])]
    current = str(res.get("current") or "")
    default_ws = str(res.get("default") or "")
    return APIResponse(code=200, message="获取成功", data=SuperAssistantWorkspaceListResponse(items=items, current=current, default=default_ws))


@router.post(
    "/workspaces/select",
    response_model=APIResponse[SuperAssistantWorkspaceListResponse],
    summary="选择工作区",
)
def select_workspace(
    body: SuperAssistantWorkspaceSelectRequest,
    current_user: User = Depends(permission_required("dashboard")),
    db: Session = Depends(get_db),
):
    service = SuperAssistantService(db)
    try:
        res = service.select_workspace(user=current_user, path=body.path)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    items = [SuperAssistantWorkspaceItem(**i) for i in (res.get("items") or [])]
    current = str(res.get("current") or "")
    default_ws = str(res.get("default") or "")
    return APIResponse(code=200, message="设置成功", data=SuperAssistantWorkspaceListResponse(items=items, current=current, default=default_ws))


@router.get(
    "/session",
    response_model=APIResponse[SuperAssistantSession],
    summary="获取会话详情",
)
def get_session(
    session_id: str = Query(..., description="会话ID"),
    current_user: User = Depends(permission_required("dashboard")),
    db: Session = Depends(get_db),
):
    service = SuperAssistantService(db)
    try:
        session = service.get_session(user=current_user, session_id=session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return APIResponse(code=200, message="获取成功", data=session)


@router.post(
    "/session/delete",
    response_model=APIResponse[dict],
    summary="删除会话",
)
def delete_session(
    body: SuperAssistantDeleteSessionRequest,
    current_user: User = Depends(permission_required("dashboard")),
    db: Session = Depends(get_db),
):
    service = SuperAssistantService(db)
    service.delete_session(user=current_user, session_id=body.session_id)
    return APIResponse(code=200, message="删除成功", data={"ok": True})


@router.post(
    "/chat/start",
    response_model=APIResponse[SuperAssistantChatStartResponse],
    summary="发送消息并启动流式返回",
)
def chat_start(
    body: SuperAssistantChatStartRequest,
    current_user: User = Depends(permission_required("dashboard")),
    db: Session = Depends(get_db),
):
    try:
        stream_id, _ = start_hermes_chat_stream(
            db=db,
            user=current_user,
            session_id=(body.session_id or None),
            message=body.message,
            workspace=(body.workspace or None),
            model=body.model,
            reasoning_effort=body.reasoning_effort,
            show_reasoning=body.show_reasoning,
            attachments=body.attachments,
            legacy_delta_enabled=False,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return APIResponse(code=200, message="已启动", data=SuperAssistantChatStartResponse(stream_id=stream_id))


@router.get(
    "/models",
    response_model=APIResponse[SuperAssistantModelListResponse],
    summary="获取可用模型列表（来自 Hermes API Server）",
)
def list_models(
    current_user: User = Depends(permission_required("dashboard")),
    db: Session = Depends(get_db),
):
    service = SuperAssistantService(db)
    _ = service._ensure_profile_for_user(current_user)

    profile_service = HermesProfileService()
    config_path = profile_service._get_hermes_home() / "config.yaml"
    cfg: dict = {}
    if config_path.exists():
        try:
            cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception:
            cfg = {}

    model_ids: list[str] = []
    seen: set[str] = set()

    def _push(mid: object) -> None:
        s = str(mid or "").strip()
        if not s or s in seen:
            return
        seen.add(s)
        model_ids.append(s)

    model_cfg = cfg.get("model", {})
    if isinstance(model_cfg, dict):
        _push(model_cfg.get("default") or model_cfg.get("model") or model_cfg.get("default_model"))
    elif isinstance(model_cfg, str):
        _push(model_cfg)

    custom = cfg.get("custom_providers", [])
    if isinstance(custom, list):
        for entry in custom:
            if not isinstance(entry, dict):
                continue
            _push(entry.get("model"))

    models: list[SuperAssistantModelListItem] = [SuperAssistantModelListItem(id=mid) for mid in model_ids]
    return APIResponse(code=200, message="获取成功", data=SuperAssistantModelListResponse(models=models))


@router.post(
    "/upload",
    response_model=APIResponse[SuperAssistantUploadResponse],
    summary="上传附件（保存到 Hermes Profile 目录）",
)
async def upload_file(
    session_id: str | None = Form(None, description="可选：会话ID"),
    file: UploadFile = File(...),
    current_user: User = Depends(permission_required("dashboard")),
    db: Session = Depends(get_db),
):
    service = SuperAssistantService(db)
    profile = service._ensure_profile_for_user(current_user)
    profile_service = HermesProfileService()
    profile_home = profile_service.get_profile_path(profile) if profile else None
    if profile_home is None:
        if (profile or "").strip() == "default":
            hermes_home = os.environ.get("HERMES_HOME", "").strip()
            profile_home = Path(hermes_home).expanduser() if hermes_home else (Path.home() / ".hermes")
        else:
            pn = (profile or "").strip()
            profile_home = Path.home() / ".hermes-profiles" / pn if pn else (Path.home() / ".hermes-profiles")

    filename = (file.filename or "upload").strip()
    filename = os.path.basename(filename).replace("\x00", "")
    if not filename:
        filename = "upload"

    key = (session_id or "").strip() or "draft"
    base_dir = profile_home / "uploads" / key
    base_dir.mkdir(parents=True, exist_ok=True)
    target = base_dir / filename

    content = await file.read()
    target.write_bytes(content)

    mime = (file.content_type or "").strip() or None
    is_image = bool(mime and mime.startswith("image/"))
    return APIResponse(
        code=200,
        message="上传成功",
        data=SuperAssistantUploadResponse(
            name=filename,
            path=str(target),
            mime=mime,
            size=len(content),
            is_image=is_image,
        ),
    )


@router.get(
    "/chat/stream",
    summary="SSE 流式输出",
)
def chat_stream(
    stream_id: str = Query(..., description="流ID"),
    current_user: User = Depends(permission_required("dashboard")),
):
    st = get_stream(stream_id)
    if st is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="stream not found")
    if st.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return StreamingResponse(
        stream_sse_generator(stream_id),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.websocket("/chat/ws")
async def chat_ws(
    ws: WebSocket,
    stream_id: str = Query(..., description="流ID"),
    token: str = Query(..., description="Bearer token"),
):
    user_id = decode_access_token(token)
    if user_id is None:
        await ws.close(code=4401)
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or not user.is_active:
            await ws.close(code=4403)
            return

        st = get_stream(stream_id)
        if st is None or st.user_id != user.id:
            await ws.close(code=4404)
            return

        await ws.accept()

        await ws.send_text(json.dumps({"event": "open", "data": {"ok": True, "stream_id": stream_id}}, ensure_ascii=False))

        async def _q_get():
            return await asyncio.to_thread(st.q.get, True, 0.75)

        while True:
            try:
                evt, payload = await _q_get()
                await ws.send_text(json.dumps({"event": evt, "data": payload}, ensure_ascii=False))
                if evt in {"done", "error", "cancel"}:
                    break
            except Exception:
                if st.done.is_set():
                    break
                try:
                    await ws.send_text(json.dumps({"event": "ping", "data": {}}, ensure_ascii=False))
                except Exception:
                    break
    except WebSocketDisconnect:
        try:
            cancel_stream(stream_id, user_id=user_id)
        except Exception:
            pass
    finally:
        try:
            db.close()
        except Exception:
            pass


@router.post(
    "/chat/cancel",
    response_model=APIResponse[dict],
    summary="中断当前对话流",
)
def chat_cancel(
    stream_id: str = Form(..., description="流ID"),
    current_user: User = Depends(permission_required("dashboard")),
):
    ok = cancel_stream(stream_id, user_id=current_user.id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="stream not found")
    return APIResponse(code=200, message="已中断", data={"ok": True})


@webui_compat_router.post("/api/chat/start", summary="WebUI 兼容：启动对话流")
def webui_chat_start(
    request: Request,
    body: dict = Body(...),
):
    token = _extract_bearer_token(request.headers.get("Authorization"))
    user_id = decode_access_token(token or "")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        msg = str((body or {}).get("message") or "").strip()
        if not msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="message is required")
        stream_id, _ = start_hermes_chat_stream(
            db=db,
            user=user,
            session_id=str((body or {}).get("session_id") or "").strip() or None,
            message=msg,
            workspace=str((body or {}).get("workspace") or "").strip() or None,
            model=str((body or {}).get("model") or "").strip() or None,
            reasoning_effort=str((body or {}).get("reasoning_effort") or "").strip() or None,
            show_reasoning=(body or {}).get("show_reasoning"),
            attachments=(body or {}).get("attachments"),
            legacy_delta_enabled=False,
        )
        return {"stream_id": stream_id, "session_id": str((body or {}).get("session_id") or "").strip()}
    finally:
        try:
            db.close()
        except Exception:
            pass


@webui_compat_router.get("/api/chat/stream", summary="WebUI 兼容：SSE 流式输出")
def webui_chat_stream(
    request: Request,
    stream_id: str = Query(..., description="stream_id"),
    token: str | None = Query(None, description="Bearer token（用于 EventSource）"),
):
    user_id = _resolve_user_id_for_stream(request, token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
    st = get_stream(stream_id)
    if st is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="stream not found")
    if st.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return StreamingResponse(
        stream_sse_generator(stream_id),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@webui_compat_router.get("/api/chat/cancel", summary="WebUI 兼容：取消对话流")
def webui_chat_cancel(
    request: Request,
    stream_id: str = Query(..., description="stream_id"),
    token: str | None = Query(None, description="Bearer token（用于 EventSource）"),
):
    user_id = _resolve_user_id_for_stream(request, token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
    ok = cancel_stream(stream_id, user_id=user_id)
    return {"ok": True, "cancelled": ok, "stream_id": stream_id}
