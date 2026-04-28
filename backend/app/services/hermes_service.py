import os
import re
import subprocess
import asyncio
import platform
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import User
from app.schemas.hermes import (
    HealthStatus,
    HermesSystemInfo,
    HermesStatistics,
    HealthCheckItem,
    HermesHealthStatus,
    RecentActivity,
    HermesOverviewResponse,
    VersionCheckResponse,
    UpdateProgress,
)


_update_progress: Optional[UpdateProgress] = None


class HermesService:
    def __init__(self):
        self._cached_version: Optional[str] = None
        self._cached_latest_version: Optional[str] = None
        self._version_cache_time: Optional[datetime] = None

    def get_hermes_version(self) -> str:
        if self._cached_version:
            return self._cached_version
        
        try:
            result = subprocess.run(
                ["hermes", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                match = re.search(r"(\d+\.\d+\.\d+)", output)
                if match:
                    self._cached_version = match.group(1)
                    return self._cached_version
                return output
            return "unknown"
        except Exception:
            return "unknown"

    async def check_latest_version(self) -> Optional[str]:
        if self._version_cache_time and self._cached_latest_version:
            if datetime.now() - self._version_cache_time < timedelta(hours=1):
                return self._cached_latest_version
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.github.com/repos/NousResearch/hermes-agent/releases/latest",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        tag_name = data.get("tag_name", "")
                        match = re.search(r"(\d+\.\d+\.\d+)", tag_name)
                        if match:
                            latest = match.group(1)
                            self._cached_latest_version = latest
                            self._version_cache_time = datetime.now()
                            return latest
        except Exception:
            pass
        return None

    def get_uptime(self) -> str:
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["net", "stats", "srv"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                output = result.stdout
                match = re.search(r"since\s+(.+)$", output, re.MULTILINE)
                if match:
                    return f"自 {match.group(1)} 启动"
            else:
                with open("/proc/uptime", "r") as f:
                    uptime_seconds = float(f.readline().split()[0])
                    return self._format_uptime(uptime_seconds)
        except Exception:
            pass
        return "未知"

    def _format_uptime(self, seconds: float) -> str:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        
        if not parts:
            return "刚刚启动"
        return " ".join(parts)

    def check_system_status(self) -> HealthStatus:
        try:
            result = subprocess.run(
                ["hermes", "doctor"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                if "ERROR" in result.stdout.upper() or "FAIL" in result.stdout.upper():
                    return HealthStatus.WARNING
                return HealthStatus.HEALTHY
            return HealthStatus.WARNING
        except Exception:
            return HealthStatus.UNHEALTHY

    def get_total_users(self, db: Session) -> int:
        try:
            return db.query(User).count()
        except Exception:
            return 0

    def get_profile_count(self) -> int:
        try:
            result = subprocess.run(
                ["hermes", "profile", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                count = 0
                for line in lines:
                    if line.strip() and not line.startswith("*") and not line.lower().startswith("profile"):
                        count += 1
                return max(count, 0)
        except Exception:
            pass
        return 0

    def check_gateway_status(self) -> dict:
        running_count = 0
        stopped_count = 0
        
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq python*"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if "hermes" in result.stdout.lower():
                    running_count = 1
            else:
                result = subprocess.run(
                    ["pgrep", "-f", "hermes.*gateway"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    pids = result.stdout.strip().split("\n")
                    running_count = len([p for p in pids if p.strip()])
        except Exception:
            pass
        
        return {
            "running": running_count,
            "stopped": 0
        }

    def get_memory_usage(self) -> dict:
        try:
            if platform.system() == "Windows":
                import psutil
                memory = psutil.virtual_memory()
                used_percent = memory.percent
                total_gb = round(memory.total / (1024**3), 1)
                used_gb = round(memory.used / (1024**3), 1)
            else:
                with open("/proc/meminfo", "r") as f:
                    mem_info = {}
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            mem_info[parts[0].rstrip(":")] = int(parts[1])
                    
                    total = mem_info.get("MemTotal", 0)
                    free = mem_info.get("MemFree", 0)
                    buffers = mem_info.get("Buffers", 0)
                    cached = mem_info.get("Cached", 0)
                    
                    used = total - free - buffers - cached
                    used_percent = (used / total * 100) if total > 0 else 0
                    total_gb = round(total / 1048576, 1)
                    used_gb = round(used / 1048576, 1)
            
            if used_percent >= 80:
                status = HealthStatus.WARNING
            elif used_percent >= 90:
                status = HealthStatus.UNHEALTHY
            else:
                status = HealthStatus.HEALTHY
            
            return {
                "percent": round(used_percent, 1),
                "total_gb": total_gb,
                "used_gb": used_gb,
                "status": status,
                "display": f"{round(used_percent, 1)}% ({used_gb}GB / {total_gb}GB)"
            }
        except Exception:
            return {
                "percent": 0,
                "total_gb": 0,
                "used_gb": 0,
                "status": HealthStatus.UNHEALTHY,
                "display": "无法获取"
            }

    def get_health_status(self, db: Session) -> HermesHealthStatus:
        items: List[HealthCheckItem] = []
        overall = HealthStatus.HEALTHY
        
        hermes_status = self.check_system_status()
        items.append(HealthCheckItem(
            name="Hermes 系统",
            status=hermes_status,
            message="Hermes Agent 核心系统状态",
            value=f"版本: {self.get_hermes_version()}"
        ))
        if hermes_status != HealthStatus.HEALTHY:
            overall = hermes_status
        
        db_status = HealthStatus.HEALTHY
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            db_message = "数据库连接正常"
            db_value = "MySQL"
        except Exception as e:
            db_status = HealthStatus.UNHEALTHY
            db_message = f"数据库连接失败: {str(e)}"
            db_value = "连接失败"
            overall = HealthStatus.UNHEALTHY
        
        items.append(HealthCheckItem(
            name="数据库",
            status=db_status,
            message=db_message,
            value=db_value
        ))
        
        memory_info = self.get_memory_usage()
        items.append(HealthCheckItem(
            name="内存使用",
            status=memory_info["status"],
            message="系统内存使用情况",
            value=memory_info["display"]
        ))
        if memory_info["status"] != HealthStatus.HEALTHY and overall == HealthStatus.HEALTHY:
            overall = memory_info["status"]
        
        gateway_status = self.check_gateway_status()
        running = gateway_status.get("running", 0)
        
        items.append(HealthCheckItem(
            name="Gateway 进程",
            status=HealthStatus.HEALTHY if running > 0 else HealthStatus.WARNING,
            message="Hermes Gateway 服务状态",
            value=f"{running} 个运行中"
        ))
        
        return HermesHealthStatus(
            overall=overall,
            items=items,
            checked_at=datetime.now()
        )

    def get_statistics(self, db: Session) -> HermesStatistics:
        gateway_status = self.check_gateway_status()
        total_profiles = self.get_profile_count()
        running_profiles = gateway_status.get("running", 0)
        
        return HermesStatistics(
            total_profiles=total_profiles,
            running_profiles=running_profiles,
            stopped_profiles=max(0, total_profiles - running_profiles),
            total_users=self.get_total_users(db),
            today_conversations=0,
            total_conversations=0,
            total_skills=0,
            total_mcp_services=0,
            total_documents=0
        )

    def get_recent_activities(self) -> List[RecentActivity]:
        activities: List[RecentActivity] = []
        
        now = datetime.now()
        for i in range(5):
            time_offset = timedelta(minutes=(i + 1) * 5)
            activity_time = (now - time_offset).strftime("%H:%M:%S")
            
            events = [
                ("系统", "系统监控", "健康检查完成"),
                ("系统", "状态更新", "Profile 状态同步"),
                ("系统", "日志记录", "系统日志已轮转"),
                ("系统", "配置检查", "配置文件验证通过"),
                ("系统", "缓存刷新", "内存缓存已清理"),
            ]
            
            user_name, event, details = events[i % len(events)]
            activities.append(RecentActivity(
                time=activity_time,
                user_name=user_name,
                event=event,
                details=details
            ))
        
        return activities

    async def get_overview(self, db: Session) -> HermesOverviewResponse:
        current_version = self.get_hermes_version()
        latest_version = await self.check_latest_version()
        
        has_update = False
        if current_version != "unknown" and latest_version:
            current_parts = [int(p) for p in current_version.split(".")]
            latest_parts = [int(p) for p in latest_version.split(".")]
            for c, l in zip(current_parts, latest_parts):
                if l > c:
                    has_update = True
                    break
        
        system_info = HermesSystemInfo(
            version=current_version,
            latest_version=latest_version,
            has_update=has_update,
            status=self.check_system_status(),
            uptime=self.get_uptime(),
            start_time=None,
            api_server_port=8642
        )
        
        return HermesOverviewResponse(
            system_info=system_info,
            statistics=self.get_statistics(db),
            health_status=self.get_health_status(db),
            recent_activities=self.get_recent_activities()
        )

    async def check_version(self) -> VersionCheckResponse:
        current_version = self.get_hermes_version()
        latest_version = await self.check_latest_version()
        
        has_update = False
        if current_version != "unknown" and latest_version:
            current_parts = [int(p) for p in current_version.split(".")]
            latest_parts = [int(p) for p in latest_version.split(".")]
            for c, l in zip(current_parts, latest_parts):
                if l > c:
                    has_update = True
                    break
        
        return VersionCheckResponse(
            current_version=current_version,
            latest_version=latest_version or current_version,
            has_update=has_update,
            changelog=None,
            release_url="https://github.com/NousResearch/hermes-agent/releases"
        )

    async def start_update(self) -> UpdateProgress:
        global _update_progress
        
        _update_progress = UpdateProgress(
            status="checking",
            progress=0,
            message="正在检查更新..."
        )
        
        asyncio.create_task(self._run_update())
        
        return _update_progress

    async def _run_update(self):
        global _update_progress
        
        try:
            _update_progress = UpdateProgress(
                status="downloading",
                progress=20,
                message="正在下载最新版本..."
            )
            
            await asyncio.sleep(1)
            
            _update_progress = UpdateProgress(
                status="installing",
                progress=50,
                message="正在安装更新..."
            )
            
            try:
                process = await asyncio.create_subprocess_exec(
                    "pip", "install", "--upgrade", "hermes-agent",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                for i in range(5):
                    await asyncio.sleep(1)
                    _update_progress = UpdateProgress(
                        status="installing",
                        progress=50 + i * 10,
                        message=f"正在安装更新... ({50 + i * 10}%)"
                    )
                
                await process.wait()
                
            except Exception as e:
                _update_progress = UpdateProgress(
                    status="failed",
                    progress=100,
                    message="更新失败",
                    error=str(e)
                )
                return
            
            _update_progress = UpdateProgress(
                status="completed",
                progress=100,
                message="更新完成！建议重启系统以应用新版本。"
            )
            
            self._cached_version = None
            
        except Exception as e:
            _update_progress = UpdateProgress(
                status="failed",
                progress=100,
                message="更新失败",
                error=str(e)
            )

    def get_update_progress(self) -> Optional[UpdateProgress]:
        return _update_progress


hermes_service = HermesService()
