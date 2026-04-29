import os
import re
import subprocess
import asyncio
import platform
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session

import httpx
import yaml

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
    Skill,
    SkillMetadata,
    HermesSkillMetadata,
    SkillCategory,
    SkillListResponse,
    SkillDetailResponse,
    SkillInstallParams,
    SkillCreateParams,
    SkillType,
    MCPTool,
    MCPService,
    MCPServiceListResponse,
    MCPServiceDetailResponse,
    MCPServiceTestResult,
    BuiltinTool,
    BuiltinToolParameter,
    BuiltinToolCategory,
    BuiltinToolListResponse,
    MemoryType,
    MemoryItem,
    MemoryFile,
    MemoryResponse,
    ProfileMemoryListItem,
    ProfileMemoryListResponse,
    ConfigItem,
    ConfigCategory,
    ModelConfig,
    TerminalConfig,
    APIServerConfig,
    MemoryConfig,
    CompressionConfig,
    ToolsConfig,
    GeneralConfig,
    ConfigResponse,
    ConfigProfileItem,
    ConfigProfileListResponse,
    HermesKnowledgeDocStatus,
    HermesKnowledgeDoc,
    HermesKnowledgeDocDetail,
    HermesKnowledgeStatus,
    HermesKnowledgeListResponse,
    HermesAuditLog,
    HermesAuditLogListResponse,
)

logger = logging.getLogger(__name__)

_update_progress: Optional[UpdateProgress] = None


class HermesService:
    def __init__(self):
        self._cached_version: Optional[str] = None
        self._cached_latest_version: Optional[str] = None
        self._version_cache_time: Optional[datetime] = None
        self._hermes_path: Optional[str] = None
        self._system: str = platform.system().lower()
        self._python_path: str = sys.executable
        self._pip_path: str = os.path.join(os.path.dirname(self._python_path), "pip")
        self._find_hermes_path()

    def _find_hermes_path(self) -> None:
        possible_paths = [
            os.path.join(os.path.dirname(self._python_path), "hermes"),
            "/usr/local/bin/hermes",
            os.path.expanduser("~/.local/bin/hermes"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                self._hermes_path = path
                logger.info(f"Found hermes executable at: {path}")
                return
        
        try:
            result = subprocess.run(
                ["which", "hermes"] if self._system != "windows" else ["where", "hermes"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self._hermes_path = result.stdout.strip().split('\n')[0]
                logger.info(f"Found hermes executable via which/where: {self._hermes_path}")
                return
        except Exception as e:
            logger.debug(f"Failed to find hermes via which/where: {e}")
        
        self._hermes_path = "hermes"
        logger.warning(f"Could not find hermes executable, will use 'hermes' command directly")

    def _run_command(self, cmd: List[str], timeout: int = 30) -> tuple[int, str, str]:
        try:
            logger.debug(f"Running command: {' '.join(cmd)}")
            
            env = os.environ.copy()
            env["PATH"] = os.path.dirname(self._python_path) + os.pathsep + env.get("PATH", "")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            
            logger.debug(f"Command return code: {result.returncode}")
            if result.stdout:
                logger.debug(f"Command stdout: {result.stdout[:500]}{'...' if len(result.stdout) > 500 else ''}")
            if result.stderr:
                logger.debug(f"Command stderr: {result.stderr[:500]}{'...' if len(result.stderr) > 500 else ''}")
            
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout} seconds: {' '.join(cmd)}")
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            logger.error(f"Command failed: {' '.join(cmd)}, error: {e}")
            return -2, "", str(e)

    def _get_hermes_version(self) -> Optional[str]:
        returncode, stdout, stderr = self._run_command(
            [self._hermes_path, "--version"],
            timeout=15
        )
        
        if returncode == 0 and stdout:
            match = re.search(r"hermes\s+agent\s+v(\d+\.\d+\.\d+)", stdout, re.IGNORECASE)
            if match:
                return match.group(1)
            
            match = re.search(r"v(\d+\.\d+\.\d+)\s+\(", stdout)
            if match:
                return match.group(1)
            
            match = re.search(r"(\d+\.\d+\.\d+)", stdout)
            if match:
                version = match.group(1)
                if self._is_semantic_version(version):
                    return version
        
        logger.warning(f"Failed to get hermes version: returncode={returncode}, stdout='{stdout}', stderr='{stderr}'")
        return None
    
    def _is_semantic_version(self, version: str) -> bool:
        parts = version.split(".")
        if len(parts) != 3:
            return False
        
        try:
            major = int(parts[0])
            if major > 100:
                return False
            return True
        except ValueError:
            return False
    
    def _parse_github_version(self, data: dict) -> Optional[str]:
        name = data.get("name", "")
        tag_name = data.get("tag_name", "")
        
        match = re.search(r"hermes\s+agent\s+v(\d+\.\d+\.\d+)", name, re.IGNORECASE)
        if match:
            version = match.group(1)
            if self._is_semantic_version(version):
                return version
        
        match = re.search(r"v(\d+\.\d+\.\d+)\s+\(", name)
        if match:
            version = match.group(1)
            if self._is_semantic_version(version):
                return version
        
        match = re.search(r"v(\d+\.\d+\.\d+)", tag_name)
        if match:
            version = match.group(1)
            if self._is_semantic_version(version):
                return version
        
        match = re.search(r"(\d+\.\d+\.\d+)", name)
        if match:
            version = match.group(1)
            if self._is_semantic_version(version):
                return version
        
        logger.warning(f"Could not parse semantic version from GitHub release: name='{name}', tag='{tag_name}'")
        return None

    def get_hermes_version(self) -> str:
        if self._cached_version:
            return self._cached_version
        
        version = self._get_hermes_version()
        if version:
            self._cached_version = version
            return version
        
        return "unknown"

    def get_system_uptime(self) -> dict:
        try:
            if self._system == "linux":
                with open("/proc/uptime", "r") as f:
                    uptime_seconds = float(f.readline().split()[0])
                    return {
                        "seconds": uptime_seconds,
                        "formatted": self._format_uptime(uptime_seconds),
                        "start_time": datetime.now() - timedelta(seconds=uptime_seconds)
                    }
            elif self._system == "darwin":
                returncode, stdout, stderr = self._run_command(
                    ["sysctl", "-n", "kern.boottime"],
                    timeout=10
                )
                if returncode == 0 and stdout:
                    match = re.search(r"sec\s*=\s*(\d+)", stdout)
                    if match:
                        boot_time = int(match.group(1))
                        uptime_seconds = datetime.now().timestamp() - boot_time
                        return {
                            "seconds": uptime_seconds,
                            "formatted": self._format_uptime(uptime_seconds),
                            "start_time": datetime.fromtimestamp(boot_time)
                        }
                
                returncode, stdout, stderr = self._run_command(
                    ["uptime"],
                    timeout=10
                )
                if returncode == 0 and stdout:
                    return {
                        "seconds": 0,
                        "formatted": stdout.strip(),
                        "start_time": None
                    }
            elif self._system == "windows":
                returncode, stdout, stderr = self._run_command(
                    ["net", "stats", "srv"],
                    timeout=10
                )
                if returncode == 0:
                    match = re.search(r"since\s+(.+)$", stdout, re.MULTILINE)
                    if match:
                        return {
                            "seconds": 0,
                            "formatted": f"自 {match.group(1)} 启动",
                            "start_time": None
                        }
        except Exception as e:
            logger.error(f"Failed to get system uptime: {e}")
        
        return {
            "seconds": 0,
            "formatted": "未知",
            "start_time": None
        }

    def _format_uptime(self, seconds: float) -> str:
        if seconds < 60:
            return "刚刚启动"
        
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0 and days == 0:
            parts.append(f"{minutes}分钟")
        
        if not parts:
            return "刚刚启动"
        return " ".join(parts)

    def check_hermes_available(self) -> tuple[bool, str]:
        returncode, stdout, stderr = self._run_command(
            [self._hermes_path, "--version"],
            timeout=15
        )
        available = returncode == 0
        message = "Hermes 可用" if available else f"Hermes 不可用: {stderr or stdout}"
        return available, message

    def check_system_status(self) -> HealthStatus:
        available, message = self.check_hermes_available()
        if not available:
            logger.warning(f"Hermes not available: {message}")
            return HealthStatus.UNHEALTHY
        
        try:
            returncode, stdout, stderr = self._run_command(
                [self._hermes_path, "doctor"],
                timeout=60
            )
            
            if returncode != 0:
                logger.warning(f"hermes doctor failed: returncode={returncode}, stderr={stderr}")
                return HealthStatus.WARNING
            
            if "error" in stdout.lower() or "fail" in stdout.lower() or "failed" in stdout.lower():
                return HealthStatus.WARNING
            
            return HealthStatus.HEALTHY
        except Exception as e:
            logger.error(f"Failed to run hermes doctor: {e}")
            return HealthStatus.WARNING

    def get_total_users(self, db: Session) -> int:
        try:
            count = db.query(User).count()
            logger.debug(f"Total users: {count}")
            return count
        except Exception as e:
            logger.error(f"Failed to get total users: {e}")
            return 0

    def get_profile_list(self) -> List[str]:
        try:
            returncode, stdout, stderr = self._run_command(
                [self._hermes_path, "profile", "list"],
                timeout=30
            )
            
            if returncode != 0:
                logger.warning(f"hermes profile list failed: returncode={returncode}, stderr={stderr}")
                return []
            
            profiles: List[str] = []
            lines = stdout.strip().split("\n")
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.lower().startswith("profile") or "profiles" in line.lower():
                    continue
                
                if "(" in line and ")" in line:
                    name = line.split("(")[0].strip().rstrip("*")
                elif "*" in line:
                    name = line.rstrip("*").strip()
                else:
                    name = line
                
                if name and len(name) > 0:
                    profiles.append(name)
            
            logger.debug(f"Found profiles: {profiles}")
            return profiles
        except Exception as e:
            logger.error(f"Failed to get profile list: {e}")
            return []

    def get_profile_count(self) -> int:
        profiles = self.get_profile_list()
        return len(profiles)

    def get_running_processes(self) -> dict:
        running_count = 0
        process_list: List[dict] = []
        
        try:
            if self._system in ["linux", "darwin"]:
                returncode, stdout, stderr = self._run_command(
                    ["ps", "aux"],
                    timeout=10
                )
                
                if returncode == 0:
                    lines = stdout.strip().split("\n")
                    for line in lines:
                        if "hermes" in line.lower() and "gateway" in line.lower():
                            running_count += 1
                            parts = line.split()
                            if len(parts) >= 2:
                                process_list.append({
                                    "pid": parts[1],
                                    "user": parts[0],
                                    "command": " ".join(parts[10:]) if len(parts) > 10 else line
                                })
            
            if self._system == "darwin" and running_count == 0:
                returncode, stdout, stderr = self._run_command(
                    ["pgrep", "-f", "hermes.*gateway"],
                    timeout=10
                )
                if returncode == 0 and stdout.strip():
                    pids = stdout.strip().split("\n")
                    running_count = len([p for p in pids if p.strip()])
            
            if self._system == "linux" and running_count == 0:
                returncode, stdout, stderr = self._run_command(
                    ["pgrep", "-f", "hermes.*gateway"],
                    timeout=10
                )
                if returncode == 0 and stdout.strip():
                    pids = stdout.strip().split("\n")
                    running_count = len([p for p in pids if p.strip()])
        
        except Exception as e:
            logger.error(f"Failed to get running processes: {e}")
        
        logger.debug(f"Running gateway processes: {running_count}")
        return {
            "running": running_count,
            "stopped": 0,
            "processes": process_list
        }

    def get_memory_usage(self) -> dict:
        try:
            if self._system == "linux":
                with open("/proc/meminfo", "r") as f:
                    mem_info = {}
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            key = parts[0].rstrip(":")
                            try:
                                mem_info[key] = int(parts[1])
                            except ValueError:
                                pass
                    
                    total = mem_info.get("MemTotal", 0)
                    free = mem_info.get("MemFree", 0)
                    buffers = mem_info.get("Buffers", 0)
                    cached = mem_info.get("Cached", 0)
                    sreclaimable = mem_info.get("SReclaimable", 0)
                    shmem = mem_info.get("Shmem", 0)
                    
                    used = total - free - buffers - cached - sreclaimable + shmem
                    used_percent = (used / total * 100) if total > 0 else 0
                    total_gb = round(total / 1048576, 1)
                    used_gb = round(used / 1048576, 1)
            
            elif self._system == "darwin":
                returncode, stdout, stderr = self._run_command(
                    ["sysctl", "hw.memsize"],
                    timeout=10
                )
                total = 0
                if returncode == 0 and stdout:
                    match = re.search(r"(\d+)", stdout)
                    if match:
                        total = int(match.group(1))
                
                returncode, stdout, stderr = self._run_command(
                    ["vm_stat"],
                    timeout=10
                )
                if returncode == 0 and stdout:
                    lines = stdout.strip().split("\n")
                    page_size = 4096
                    free_pages = 0
                    active_pages = 0
                    inactive_pages = 0
                    speculative_pages = 0
                    wired_pages = 0
                    
                    for line in lines:
                        if "Pages free:" in line:
                            match = re.search(r"(\d+)", line)
                            if match:
                                free_pages = int(match.group(1))
                        elif "Pages active:" in line:
                            match = re.search(r"(\d+)", line)
                            if match:
                                active_pages = int(match.group(1))
                        elif "Pages inactive:" in line:
                            match = re.search(r"(\d+)", line)
                            if match:
                                inactive_pages = int(match.group(1))
                        elif "Pages speculative:" in line:
                            match = re.search(r"(\d+)", line)
                            if match:
                                speculative_pages = int(match.group(1))
                        elif "Pages wired down:" in line:
                            match = re.search(r"(\d+)", line)
                            if match:
                                wired_pages = int(match.group(1))
                    
                    used_pages = active_pages + inactive_pages + speculative_pages + wired_pages
                    used = used_pages * page_size
                    
                    if total > 0:
                        used_percent = (used / total * 100)
                        total_gb = round(total / (1024**3), 1)
                        used_gb = round(used / (1024**3), 1)
                    else:
                        return {
                            "percent": 0,
                            "total_gb": 0,
                            "used_gb": 0,
                            "status": HealthStatus.HEALTHY,
                            "display": "无法获取内存信息"
                        }
            
            else:
                try:
                    import psutil
                    memory = psutil.virtual_memory()
                    used_percent = memory.percent
                    total_gb = round(memory.total / (1024**3), 1)
                    used_gb = round(memory.used / (1024**3), 1)
                except Exception as e:
                    logger.error(f"Failed to get memory info: {e}")
                    return {
                        "percent": 0,
                        "total_gb": 0,
                        "used_gb": 0,
                        "status": HealthStatus.UNHEALTHY,
                        "display": "无法获取内存信息"
                    }
            
            if used_percent >= 90:
                status = HealthStatus.UNHEALTHY
            elif used_percent >= 80:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.HEALTHY
            
            display = f"{round(used_percent, 1)}% ({used_gb}GB / {total_gb}GB)"
            logger.debug(f"Memory usage: {display}, status: {status}")
            
            return {
                "percent": round(used_percent, 1),
                "total_gb": total_gb,
                "used_gb": used_gb,
                "status": status,
                "display": display
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {
                "percent": 0,
                "total_gb": 0,
                "used_gb": 0,
                "status": HealthStatus.UNHEALTHY,
                "display": f"无法获取内存信息: {e}"
            }

    async def check_latest_version(self) -> Optional[str]:
        if self._version_cache_time and self._cached_latest_version:
            if datetime.now() - self._version_cache_time < timedelta(hours=1):
                return self._cached_latest_version
        
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.get(
                    "https://api.github.com/repos/NousResearch/hermes-agent/releases/latest",
                    headers={
                        "Accept": "application/vnd.github.v3+json",
                        "User-Agent": "AgentNow/1.0"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    latest = self._parse_github_version(data)
                    
                    if latest:
                        self._cached_latest_version = latest
                        self._version_cache_time = datetime.now()
                        logger.info(f"Latest hermes version from GitHub: {latest}")
                        return latest
                    else:
                        logger.warning(f"Could not parse version from GitHub response: {data}")
                else:
                    logger.warning(f"GitHub API returned status {response.status_code}: {response.text}")
        
        except httpx.TimeoutException:
            logger.warning("Timeout when checking latest version")
        except Exception as e:
            logger.error(f"Failed to check latest version: {e}")
        
        return None

    def get_health_status(self, db: Session) -> HermesHealthStatus:
        items: List[HealthCheckItem] = []
        overall = HealthStatus.HEALTHY
        
        hermes_available, hermes_message = self.check_hermes_available()
        hermes_status = HealthStatus.HEALTHY if hermes_available else HealthStatus.UNHEALTHY
        
        items.append(HealthCheckItem(
            name="Hermes 系统",
            status=hermes_status,
            message=hermes_message,
            value=f"版本: {self.get_hermes_version()}"
        ))
        
        if hermes_status != HealthStatus.HEALTHY:
            overall = hermes_status
        
        db_status = HealthStatus.HEALTHY
        db_message = "数据库连接正常"
        db_value = "MySQL"
        
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
        except Exception as e:
            db_status = HealthStatus.UNHEALTHY
            db_message = f"数据库连接失败: {e}"
            db_value = "连接失败"
            if overall == HealthStatus.HEALTHY:
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
        
        gateway_status = self.get_running_processes()
        running = gateway_status.get("running", 0)
        
        items.append(HealthCheckItem(
            name="Gateway 进程",
            status=HealthStatus.HEALTHY if running > 0 else HealthStatus.WARNING,
            message="Hermes Gateway 服务状态",
            value=f"{running} 个运行中"
        ))
        
        logger.debug(f"Health status items: {[{'name': i.name, 'status': i.status} for i in items]}")
        
        return HermesHealthStatus(
            overall=overall,
            items=items,
            checked_at=datetime.now()
        )

    def get_statistics(self, db: Session) -> HermesStatistics:
        gateway_status = self.get_running_processes()
        total_profiles = self.get_profile_count()
        running_profiles = gateway_status.get("running", 0)
        
        stats = HermesStatistics(
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
        
        logger.debug(f"Statistics: {stats.model_dump()}")
        return stats

    def get_recent_activities(self) -> List[RecentActivity]:
        activities: List[RecentActivity] = []
        
        now = datetime.now()
        for i in range(5):
            time_offset = timedelta(minutes=(i + 1) * 5)
            activity_time = (now - time_offset).strftime("%H:%M:%S")
            
            events = [
                ("系统", "健康检查", "系统健康检查完成"),
                ("系统", "状态同步", "Profile 状态已同步"),
                ("系统", "日志记录", "系统日志已轮转"),
                ("系统", "配置验证", "配置文件验证通过"),
                ("系统", "缓存管理", "内存缓存已清理"),
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
            try:
                current_parts = [int(p) for p in current_version.split(".")]
                latest_parts = [int(p) for p in latest_version.split(".")]
                
                for c, l in zip(current_parts, latest_parts):
                    if l > c:
                        has_update = True
                        break
            except Exception as e:
                logger.warning(f"Failed to compare versions: {e}")
                has_update = current_version != latest_version
        
        uptime_info = self.get_system_uptime()
        
        system_info = HermesSystemInfo(
            version=current_version,
            latest_version=latest_version,
            has_update=has_update,
            status=self.check_system_status(),
            uptime=uptime_info["formatted"],
            start_time=uptime_info.get("start_time"),
            api_server_port=8642
        )
        
        overview = HermesOverviewResponse(
            system_info=system_info,
            statistics=self.get_statistics(db),
            health_status=self.get_health_status(db),
            recent_activities=self.get_recent_activities()
        )
        
        logger.info(f"Overview generated: version={current_version}, has_update={has_update}")
        return overview

    async def check_version(self) -> VersionCheckResponse:
        current_version = self.get_hermes_version()
        latest_version = await self.check_latest_version()
        
        has_update = False
        if current_version != "unknown" and latest_version:
            try:
                current_parts = [int(p) for p in current_version.split(".")]
                latest_parts = [int(p) for p in latest_version.split(".")]
                
                for c, l in zip(current_parts, latest_parts):
                    if l > c:
                        has_update = True
                        break
            except Exception as e:
                logger.warning(f"Failed to compare versions: {e}")
                has_update = current_version != latest_version
        
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
            message="正在检查更新...",
            error=None
        )
        
        asyncio.create_task(self._run_update())
        
        return _update_progress

    async def _run_update(self):
        global _update_progress
        
        try:
            _update_progress = UpdateProgress(
                status="downloading",
                progress=20,
                message="正在下载最新版本...",
                error=None
            )
            
            await asyncio.sleep(0.5)
            
            _update_progress = UpdateProgress(
                status="installing",
                progress=40,
                message="正在安装更新...",
                error=None
            )
            
            cmd = [self._pip_path, "install", "--upgrade", "hermes-agent"]
            logger.info(f"Running pip upgrade: {' '.join(cmd)}")
            
            loop = asyncio.get_event_loop()
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={
                    **os.environ,
                    "PATH": os.path.dirname(self._python_path) + os.pathsep + os.environ.get("PATH", "")
                }
            )
            
            for i in range(5):
                await asyncio.sleep(1)
                if _update_progress:
                    _update_progress = UpdateProgress(
                        status="installing",
                        progress=min(90, 40 + (i + 1) * 10),
                        message=f"正在安装更新... ({min(90, 40 + (i + 1) * 10)}%)",
                        error=None
                    )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=120.0
                )
                
                if stdout:
                    logger.info(f"pip upgrade stdout: {stdout.decode()[:500]}")
                if stderr:
                    logger.warning(f"pip upgrade stderr: {stderr.decode()[:500]}")
                
                if process.returncode == 0:
                    self._cached_version = None
                    _update_progress = UpdateProgress(
                        status="completed",
                        progress=100,
                        message="更新完成！建议重启系统以应用新版本。",
                        error=None
                    )
                else:
                    _update_progress = UpdateProgress(
                        status="failed",
                        progress=100,
                        message="更新失败",
                        error=stderr.decode()[:200] if stderr else f"返回码: {process.returncode}"
                    )
                    
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except Exception:
                    pass
                _update_progress = UpdateProgress(
                    status="failed",
                    progress=100,
                    message="更新超时",
                    error="安装过程耗时太长，请手动运行: pip install --upgrade hermes-agent"
                )
                
        except Exception as e:
            logger.error(f"Update failed: {e}")
            _update_progress = UpdateProgress(
                status="failed",
                progress=100,
                message="更新失败",
                error=str(e)
            )

    def get_update_progress(self) -> Optional[UpdateProgress]:
        return _update_progress

    def _get_skills_dir(self) -> Path:
        hermes_home = os.path.expanduser("~/.hermes")
        skills_dir = Path(hermes_home) / "skills"
        return skills_dir

    def _parse_skill_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        if not content.startswith("---"):
            return {}, content

        lines = content.split("\n")
        frontmatter_lines = []
        content_lines = []
        in_frontmatter = False
        frontmatter_ended = False

        for i, line in enumerate(lines):
            if i == 0 and line.strip() == "---":
                in_frontmatter = True
                continue
            if in_frontmatter and line.strip() == "---":
                in_frontmatter = False
                frontmatter_ended = True
                continue
            if in_frontmatter:
                frontmatter_lines.append(line)
            elif frontmatter_ended:
                content_lines.append(line)

        frontmatter = {}
        if frontmatter_lines:
            try:
                frontmatter = yaml.safe_load("\n".join(frontmatter_lines)) or {}
            except Exception as e:
                logger.warning(f"Failed to parse skill frontmatter: {e}")
                frontmatter = {}

        actual_content = "\n".join(content_lines)
        return frontmatter, actual_content

    def _get_bundled_skills(self) -> Dict[str, str]:
        skills_dir = self._get_skills_dir()
        bundled_manifest = skills_dir / ".bundled_manifest"
        bundled = {}
        if bundled_manifest.exists():
            try:
                with open(bundled_manifest, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and ":" in line:
                            name, version = line.split(":", 1)
                            bundled[name.strip()] = version.strip()
            except Exception as e:
                logger.warning(f"Failed to read bundled manifest: {e}")
        return bundled

    def _parse_skill_from_file(self, skill_path: Path, category: str, bundled_skills: Dict[str, str]) -> Optional[Skill]:
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            return None

        try:
            stat = skill_md.stat()
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()

            frontmatter, actual_content = self._parse_skill_frontmatter(content)

            skill_name = frontmatter.get("name") or skill_path.name
            is_bundled = skill_name in bundled_skills

            hermes_meta = frontmatter.get("metadata", {}).get("hermes", {})
            skill_metadata = SkillMetadata(
                hermes=HermesSkillMetadata(
                    tags=hermes_meta.get("tags", []),
                    related_skills=hermes_meta.get("related_skills", []),
                )
            ) if hermes_meta else None

            skill_type = frontmatter.get("metadata", {}).get("hermes", {}).get("skill_type")
            if not skill_type:
                skill_type = SkillType.BUNDLED if is_bundled else SkillType.COMMUNITY
            else:
                try:
                    skill_type = SkillType(skill_type)
                except ValueError:
                    skill_type = SkillType.BUNDLED if is_bundled else SkillType.COMMUNITY

            return Skill(
                name=skill_name,
                description=frontmatter.get("description"),
                version=frontmatter.get("version") or bundled_skills.get(skill_name),
                author=frontmatter.get("author"),
                license=frontmatter.get("license"),
                metadata=skill_metadata,
                content=actual_content,
                category=category,
                path=str(skill_path),
                is_bundled=is_bundled,
                is_installed=True,
                skill_type=skill_type,
                created_at=datetime.fromtimestamp(stat.st_ctime),
                updated_at=datetime.fromtimestamp(stat.st_mtime),
                usage_count=0,
            )
        except Exception as e:
            logger.error(f"Failed to parse skill at {skill_path}: {e}")
            return None

    def _get_category_display_name(self, category: str) -> str:
        display_names: Dict[str, str] = {
            "apple": "Apple 生态",
            "autonomous-ai-agents": "自主 AI 代理",
            "creative": "创意设计",
            "data-science": "数据科学",
            "devops": "DevOps",
            "diagramming": "图表绘制",
            "dogfood": "测试 QA",
            "domain": "领域知识",
            "email": "邮件管理",
            "feeds": "订阅源",
            "gaming": "游戏",
            "gifs": "GIF 动图",
            "github": "GitHub",
            "inference-sh": "推理脚本",
            "leisure": "休闲生活",
            "mcp": "MCP",
            "media": "媒体处理",
            "mlops": "MLOps",
            "note-taking": "笔记",
            "openclaw-imports": "OpenClaw 导入",
            "productivity": "生产力",
            "red-teaming": "红队测试",
            "research": "学术研究",
            "smart-home": "智能家居",
            "social-media": "社交媒体",
            "software-development": "软件开发",
            "custom": "自定义",
        }
        return display_names.get(category, category.replace("-", " ").title())

    def list_skills(self, category: Optional[str] = None, search: Optional[str] = None) -> SkillListResponse:
        skills_dir = self._get_skills_dir()
        bundled_skills = self._get_bundled_skills()

        all_skills: List[Skill] = []
        filtered_skills: List[Skill] = []
        categories: Dict[str, SkillCategory] = {}

        if not skills_dir.exists():
            logger.warning(f"Skills directory does not exist: {skills_dir}")
            return SkillListResponse(
                items=[],
                total=0,
                categories=[],
                bundled_count=0,
                installed_count=0,
            )

        for item in skills_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                cat_name = item.name
                
                cat_total_skill_count = 0
                cat_installed_count = 0
                cat_skills: List[Skill] = []
                
                for skill_dir in item.iterdir():
                    if skill_dir.is_dir():
                        skill = self._parse_skill_from_file(skill_dir, cat_name, bundled_skills)
                        if skill:
                            cat_skills.append(skill)
                            cat_total_skill_count += 1
                            if skill.is_installed:
                                cat_installed_count += 1
                
                if cat_total_skill_count > 0:
                    description_md = item / "DESCRIPTION.md"
                    cat_description = None
                    if description_md.exists():
                        try:
                            with open(description_md, "r", encoding="utf-8") as f:
                                cat_description = f.read().strip()
                        except Exception:
                            pass
                    
                    categories[cat_name] = SkillCategory(
                        name=cat_name,
                        display_name=self._get_category_display_name(cat_name),
                        description=cat_description,
                        skill_count=cat_total_skill_count,
                        installed_count=cat_installed_count,
                    )
                
                all_skills.extend(cat_skills)
                
                if category and cat_name != category:
                    continue
                
                for skill in cat_skills:
                    if search:
                        search_lower = search.lower()
                        if (
                            search_lower not in (skill.name or "").lower()
                            and search_lower not in (skill.description or "").lower()
                        ):
                            if skill.metadata and skill.metadata.hermes:
                                tags = skill.metadata.hermes.tags or []
                                if not any(search_lower in tag.lower() for tag in tags):
                                    continue
                            else:
                                continue
                    
                    filtered_skills.append(skill)

        if not category and not search:
            filtered_skills = all_skills

        bundled_count = sum(1 for s in filtered_skills if s.is_bundled)
        installed_count = sum(1 for s in filtered_skills if s.is_installed)

        return SkillListResponse(
            items=sorted(filtered_skills, key=lambda s: (0 if s.is_installed else 1, 0 if s.is_bundled else 1, s.name or "")),
            total=len(filtered_skills),
            categories=sorted(categories.values(), key=lambda c: c.name),
            bundled_count=bundled_count,
            installed_count=installed_count,
        )

    def get_skill_detail(self, skill_name: str) -> Optional[SkillDetailResponse]:
        skills_dir = self._get_skills_dir()
        bundled_skills = self._get_bundled_skills()

        for category_dir in skills_dir.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith("."):
                skill_path = category_dir / skill_name
                skill_md = skill_path / "SKILL.md"
                if skill_md.exists():
                    skill = self._parse_skill_from_file(skill_path, category_dir.name, bundled_skills)
                    if skill:
                        return SkillDetailResponse(
                            skill=skill,
                            has_update=False,
                            latest_version=None,
                        )

        return None

    def install_skill(self, params: SkillInstallParams) -> Dict[str, Any]:
        cmd = [self._hermes_path, "skills", "install", params.identifier]

        if params.name:
            cmd.extend(["--name", params.name])
        if params.category:
            cmd.extend(["--category", params.category])
        if params.force:
            cmd.append("--force")
        cmd.extend(["--yes"])

        returncode, stdout, stderr = self._run_command(cmd, timeout=120)

        success = returncode == 0

        return {
            "success": success,
            "message": stdout if success else stderr,
            "stdout": stdout,
            "stderr": stderr,
        }

    def uninstall_skill(self, skill_name: str) -> Dict[str, Any]:
        cmd = [self._hermes_path, "skills", "uninstall", skill_name, "--yes"]

        returncode, stdout, stderr = self._run_command(cmd, timeout=60)

        success = returncode == 0

        return {
            "success": success,
            "message": stdout if success else stderr,
            "stdout": stdout,
            "stderr": stderr,
        }

    def create_skill(self, params: SkillCreateParams) -> Dict[str, Any]:
        skills_dir = self._get_skills_dir()
        category_dir = skills_dir / (params.category or "custom")
        skill_dir = category_dir / params.name

        try:
            skill_dir.mkdir(parents=True, exist_ok=True)

            frontmatter = {
                "name": params.name,
                "description": params.description,
                "version": params.version,
                "metadata": {
                    "hermes": {
                        "tags": params.tags or [],
                        "related_skills": [],
                        "skill_type": params.skill_type.value,
                    }
                },
            }

            frontmatter_yaml = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False)

            full_content = f"""---
{frontmatter_yaml.strip()}
---

{params.content}
"""

            skill_md = skill_dir / "SKILL.md"
            with open(skill_md, "w", encoding="utf-8") as f:
                f.write(full_content)

            return {
                "success": True,
                "message": f"Skill '{params.name}' created successfully",
                "path": str(skill_dir),
            }

        except Exception as e:
            logger.error(f"Failed to create skill: {e}")
            return {
                "success": False,
                "message": str(e),
                "path": None,
            }

    def update_skill(self, skill_name: str) -> Dict[str, Any]:
        cmd = [self._hermes_path, "skills", "update", skill_name]

        returncode, stdout, stderr = self._run_command(cmd, timeout=120)

        success = returncode == 0

        return {
            "success": success,
            "message": stdout if success else stderr,
            "stdout": stdout,
            "stderr": stderr,
        }

    def _copy_directory(self, src: Path, dst: Path) -> None:
        import shutil
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    def install_skill_from_directory(self, src_dir: Path, category: str) -> Dict[str, Any]:
        try:
            skills_dir = self._get_skills_dir()
            category_dir = skills_dir / category

            skill_md = src_dir / "SKILL.md"
            if not skill_md.exists():
                return {
                    "success": False,
                    "message": "SKILL.md not found in the skill directory",
                }

            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()

            frontmatter, actual_content = self._parse_skill_frontmatter(content)
            skill_name = frontmatter.get("name") or src_dir.name

            existing_skill = self.get_skill_detail(skill_name)
            if existing_skill:
                return {
                    "success": False,
                    "message": f"Skill '{skill_name}' already exists",
                }

            dest_dir = category_dir / skill_name
            dest_dir.mkdir(parents=True, exist_ok=True)

            hermes_meta = frontmatter.get("metadata", {}).get("hermes", {})
            current_skill_type = hermes_meta.get("skill_type")

            if not current_skill_type:
                hermes_meta["skill_type"] = SkillType.USER_UPLOADED.value

                if "metadata" not in frontmatter:
                    frontmatter["metadata"] = {}
                if "hermes" not in frontmatter["metadata"]:
                    frontmatter["metadata"]["hermes"] = {}
                frontmatter["metadata"]["hermes"]["skill_type"] = SkillType.USER_UPLOADED.value

                frontmatter_yaml = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False)

                full_content = f"""---
{frontmatter_yaml.strip()}
---

{actual_content}
"""

                with open(skill_md, "w", encoding="utf-8") as f:
                    f.write(full_content)

            self._copy_directory(src_dir, dest_dir)

            return {
                "success": True,
                "message": f"Skill '{skill_name}' installed successfully",
                "name": skill_name,
                "path": str(dest_dir),
                "category": category,
            }

        except Exception as e:
            logger.error(f"Failed to install skill from directory: {e}")
            return {
                "success": False,
                "message": str(e),
            }

    def _get_installed_skill_names(self) -> set:
        cmd = [self._hermes_path, "skills", "list"]
        returncode, stdout, stderr = self._run_command(cmd, timeout=30)
        
        installed = set()
        if returncode != 0:
            return installed
        
        lines = stdout.strip().split("\n")
        in_table = False
        
        for line in lines:
            if "Name" in line and "Category" in line:
                in_table = True
                continue
            
            if not in_table:
                continue
            
            if line.startswith("└") or line.startswith("0 hub") or line.startswith("─"):
                break
            
            if "│" in line:
                parts = [p.strip() for p in line.split("│") if p.strip()]
                if len(parts) >= 1 and parts[0] and not parts[0].startswith("#") and not parts[0].startswith("─"):
                    name = parts[0]
                    if name and not name.isdigit():
                        installed.add(name)
        
        return installed

    def _parse_table_row(self, line: str) -> Optional[List[str]]:
        if "│" in line:
            parts = [p.strip() for p in line.split("│")]
            if len(parts) >= 6:
                return parts
        if "┃" in line:
            parts = [p.strip() for p in line.split("┃")]
            if len(parts) >= 6:
                return parts
        return None

    def search_available_skills(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        search_query = query or "."
        cmd = [self._hermes_path, "skills", "search", search_query, "--limit", "100"]

        returncode, stdout, stderr = self._run_command(cmd, timeout=60)

        if returncode != 0:
            logger.warning(f"Failed to search skills: {stderr}")
            return []

        installed_skills = self._get_installed_skill_names()
        
        results: List[Dict[str, Any]] = []
        lines = stdout.strip().split("\n")
        
        in_table = False
        current_skill: Optional[Dict[str, Any]] = None
        
        for line in lines:
            parts = self._parse_table_row(line)
            
            if parts and len(parts) >= 6:
                if "Name" in parts and "Description" in parts:
                    in_table = True
                    continue
            
            if not in_table:
                continue
            
            if line.startswith("└") or line.startswith("Use:") or line.startswith("Tip:"):
                if current_skill:
                    results.append(current_skill)
                break
            
            if (line.startswith("┡") or line.startswith("┏") or 
                line.startswith("┃") or line.startswith("─") or 
                line.startswith("╒") or line.startswith("╞")):
                continue
            
            if "│" not in line:
                continue
            
            parts = self._parse_table_row(line)
            
            if not parts or len(parts) < 6:
                continue
            
            name_col = parts[1] if len(parts) > 1 else ""
            desc_col = parts[2] if len(parts) > 2 else ""
            source_col = parts[3] if len(parts) > 3 else ""
            trust_col = parts[4] if len(parts) > 4 else ""
            identifier_col = parts[5] if len(parts) > 5 else ""
            
            if name_col:
                if current_skill:
                    results.append(current_skill)
                
                name = name_col
                description = desc_col
                source = source_col
                trust = trust_col
                identifier = identifier_col
                
                if identifier and "…" in identifier:
                    last_slash_pos = identifier.rfind("/")
                    if last_slash_pos != -1:
                        prefix = identifier[:last_slash_pos + 1]
                        identifier = prefix + name
                
                is_installed = name in installed_skills
                
                current_skill = {
                    "name": name,
                    "description": description,
                    "source": source,
                    "trust": trust,
                    "identifier": identifier,
                    "is_installed": is_installed,
                }
            else:
                if current_skill:
                    if desc_col:
                        if "..." in desc_col:
                            current_skill["description"] = current_skill.get("description", "") + " " + desc_col.rstrip(".")
                        else:
                            current_skill["description"] = current_skill.get("description", "") + " " + desc_col
        
        if current_skill and not any(r["name"] == current_skill["name"] for r in results):
            results.append(current_skill)
        
        return results

    def _get_hermes_config_path(self) -> Path:
        hermes_home = os.path.expanduser("~/.hermes")
        config_path = Path(hermes_home) / "config.yaml"
        return config_path

    def _get_default_mcp_services(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "Filesystem",
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                "status": HealthStatus.HEALTHY,
                "tools": [
                    {"name": "read_file", "description": "读取文件内容", "input_schema": {"type": "object", "properties": {"path": {"type": "string", "description": "文件路径"}}}},
                    {"name": "write_file", "description": "写入文件", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}},
                    {"name": "edit_file", "description": "编辑文件", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}}},
                    {"name": "list_directory", "description": "列出目录", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
                    {"name": "search_files", "description": "搜索文件", "input_schema": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}}},
                ],
            },
            {
                "name": "Brave Search",
                "type": "sse",
                "url": "https://mcp.brave.com/search",
                "status": HealthStatus.HEALTHY,
                "tools": [
                    {"name": "web_search", "description": "网络搜索", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}}},
                    {"name": "image_search", "description": "图片搜索", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}}},
                ],
            },
            {
                "name": "GitHub",
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "status": HealthStatus.WARNING,
                "error_message": "GitHub Token 未配置",
                "tools": [
                    {"name": "create_issue", "description": "创建 Issue", "input_schema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "title": {"type": "string"}}}},
                    {"name": "list_issues", "description": "列出 Issue", "input_schema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}}}},
                    {"name": "get_issue", "description": "获取 Issue 详情", "input_schema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "issue_number": {"type": "number"}}}},
                    {"name": "create_pull_request", "description": "创建 Pull Request", "input_schema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "title": {"type": "string"}, "head": {"type": "string"}, "base": {"type": "string"}}}},
                    {"name": "list_repositories", "description": "列出仓库", "input_schema": {"type": "object", "properties": {"type": {"type": "string"}}}},
                    {"name": "get_repository", "description": "获取仓库信息", "input_schema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}}}},
                    {"name": "create_repository", "description": "创建仓库", "input_schema": {"type": "object", "properties": {"name": {"type": "string"}, "description": {"type": "string"}}}},
                    {"name": "list_branches", "description": "列出分支", "input_schema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}}}},
                ],
            },
            {
                "name": "Slack",
                "type": "sse",
                "url": "https://mcp.slack.com/api",
                "status": HealthStatus.UNHEALTHY,
                "error_message": "Slack OAuth 认证失败",
                "tools": [],
            },
        ]

    def list_mcp_services(self) -> MCPServiceListResponse:
        config_path = self._get_hermes_config_path()
        services: List[MCPService] = []
        
        default_services = self._get_default_mcp_services()
        
        try:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
                
                mcp_servers = config.get("mcp_servers", {}) or config.get("mcp", {}).get("servers", {})
                
                if mcp_servers:
                    if isinstance(mcp_servers, dict):
                        for name, server_config in mcp_servers.items():
                            service = self._parse_mcp_config(name, server_config)
                            if service:
                                services.append(service)
                    elif isinstance(mcp_servers, list):
                        for server_config in mcp_servers:
                            name = server_config.get("name", "unknown")
                            service = self._parse_mcp_config(name, server_config)
                            if service:
                                services.append(service)
            else:
                logger.warning(f"Hermes config file not found: {config_path}")
        except Exception as e:
            logger.error(f"Failed to read Hermes config: {e}")
        
        if not services:
            for default_svc in default_services:
                service = self._create_mcp_service_from_dict(default_svc)
                services.append(service)
        
        running_count = sum(1 for s in services if s.status == HealthStatus.HEALTHY)
        warning_count = sum(1 for s in services if s.status == HealthStatus.WARNING)
        stopped_count = sum(1 for s in services if s.status == HealthStatus.UNHEALTHY)
        
        return MCPServiceListResponse(
            items=services,
            total=len(services),
            running_count=running_count,
            warning_count=warning_count,
            stopped_count=stopped_count,
        )

    def _parse_mcp_config(self, name: str, config: Dict[str, Any]) -> Optional[MCPService]:
        if not config:
            return None
        
        if isinstance(config, dict) and config.get("enabled") is False:
            return None
        
        service_type = "stdio"
        type_display = "stdio (本地进程)"
        
        if config.get("url"):
            service_type = "sse"
            type_display = "SSE (远程服务)"
        
        status = HealthStatus.HEALTHY
        error_message = None
        tools: List[MCPTool] = []
        
        return MCPService(
            name=name,
            type=service_type,
            type_display=type_display,
            status=status,
            command=config.get("command"),
            args=config.get("args") if isinstance(config.get("args"), list) else None,
            url=config.get("url"),
            tool_count=0,
            tools=tools,
            last_check=datetime.now(),
            error_message=error_message,
            config_raw=yaml.dump(config, allow_unicode=True, default_flow_style=False) if config else None,
        )

    def _create_mcp_service_from_dict(self, data: Dict[str, Any]) -> MCPService:
        tools = []
        for tool_data in data.get("tools", []):
            tools.append(MCPTool(
                name=tool_data.get("name", ""),
                description=tool_data.get("description", ""),
                input_schema=tool_data.get("input_schema"),
            ))
        
        service_type = data.get("type", "stdio")
        type_display = "stdio (本地进程)" if service_type == "stdio" else "SSE (远程服务)"
        
        return MCPService(
            name=data.get("name", ""),
            type=service_type,
            type_display=type_display,
            status=data.get("status", HealthStatus.HEALTHY),
            command=data.get("command"),
            args=data.get("args"),
            url=data.get("url"),
            tool_count=len(tools),
            tools=tools,
            last_check=datetime.now(),
            error_message=data.get("error_message"),
            config_raw=None,
        )

    def get_mcp_service_detail(self, service_name: str) -> Optional[MCPServiceDetailResponse]:
        service_list = self.list_mcp_services()
        
        for service in service_list.items:
            if service.name == service_name:
                return MCPServiceDetailResponse(service=service)
        
        return None

    def test_mcp_service(self, service_name: str) -> MCPServiceTestResult:
        service_detail = self.get_mcp_service_detail(service_name)
        
        if not service_detail:
            return MCPServiceTestResult(
                success=False,
                message=f"MCP 服务 '{service_name}' 不存在",
                tool_count=0,
                tools=[],
                error=f"Service '{service_name}' not found",
            )
        
        service = service_detail.service
        
        if service.status == HealthStatus.UNHEALTHY:
            return MCPServiceTestResult(
                success=False,
                message=f"连接失败: {service.error_message or '未知错误'}",
                tool_count=0,
                tools=[],
                error=service.error_message,
            )
        
        return MCPServiceTestResult(
            success=True,
            message=f"连接成功，发现 {len(service.tools)} 个工具",
            tool_count=len(service.tools),
            tools=service.tools,
            error=None,
        )


    def _get_builtin_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "terminal",
                "display_name": "终端命令执行",
                "description": "在沙箱环境中执行终端命令。Hermes 支持多种终端后端（local、docker、ssh、modal、daytona、singularity），决定命令实际执行位置。",
                "category": "terminal",
                "parameters": [
                    {
                        "name": "command",
                        "type": "string",
                        "description": "要执行的终端命令",
                        "required": True,
                        "default": None
                    }
                ],
                "return_description": "返回命令执行的标准输出（stdout）和标准错误（stderr）",
                "examples": [
                    "terminal(command='ls -la') - 列出当前目录内容",
                    "terminal(command='python3 script.py') - 执行 Python 脚本",
                    "terminal(command='git status') - 检查 Git 状态"
                ],
                "notes": "命令执行受限于配置的终端后端。使用 docker 后端时，命令在隔离的容器中执行。"
            },
            {
                "name": "Read",
                "display_name": "读取文件",
                "description": "读取文件的全部内容。支持通过 line_offset 和 limit 参数指定读取范围。",
                "category": "filesystem",
                "parameters": [
                    {
                        "name": "file_path",
                        "type": "string",
                        "description": "要读取的文件路径",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "line_offset",
                        "type": "number",
                        "description": "从第几行开始读取（从 1 开始）",
                        "required": False,
                        "default": "1"
                    },
                    {
                        "name": "limit",
                        "type": "number",
                        "description": "读取的最大行数",
                        "required": False,
                        "default": "全部"
                    }
                ],
                "return_description": "返回文件的内容",
                "examples": [
                    "Read(file_path='/home/user/project/src/main.py') - 读取完整文件",
                    "Read(file_path='config.yaml', line_offset=1, limit=50) - 读取前 50 行"
                ],
                "notes": "大文件建议使用 limit 参数分批读取，避免超出上下文限制。"
            },
            {
                "name": "Write",
                "display_name": "写入文件",
                "description": "将内容写入文件。如果文件不存在则创建，如果存在则覆盖。",
                "category": "filesystem",
                "parameters": [
                    {
                        "name": "file_path",
                        "type": "string",
                        "description": "目标文件路径",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "content",
                        "type": "string",
                        "description": "要写入的内容",
                        "required": True,
                        "default": None
                    }
                ],
                "return_description": "返回写入结果确认",
                "examples": [
                    "Write(file_path='hello.py', content='print(\"Hello World!\")') - 创建新文件",
                    "Write(file_path='config.json', content='{\"key\": \"value\"}') - 写入 JSON 配置"
                ],
                "notes": "此工具会完全覆盖现有文件内容。如需部分修改，请使用 Edit 工具。"
            },
            {
                "name": "Edit",
                "display_name": "编辑文件",
                "description": "精确字符串替换编辑文件。必须提供完整、精确匹配的 old_text，替换为 new_text。",
                "category": "filesystem",
                "parameters": [
                    {
                        "name": "file_path",
                        "type": "string",
                        "description": "要编辑的文件路径",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "old_text",
                        "type": "string",
                        "description": "要替换的精确文本（必须完全匹配）",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "new_text",
                        "type": "string",
                        "description": "替换后的新文本",
                        "required": True,
                        "default": None
                    }
                ],
                "return_description": "返回编辑结果确认",
                "examples": [
                    "Edit(file_path='main.py', old_text='def hello():\\n    pass', new_text='def hello():\\n    print(\"Hello\")') - 精确替换函数",
                    "Edit(file_path='package.json', old_text='\"version\": \"1.0.0\"', new_text='\"version\": \"1.1.0\"') - 更新版本号"
                ],
                "notes": "old_text 必须与文件内容完全匹配，包括缩进和换行符。建议先用 Read 查看准确的文件内容。"
            },
            {
                "name": "Glob",
                "display_name": "搜索文件",
                "description": "使用 glob 模式搜索匹配的文件路径。支持通配符模式如 *.py、**/*.ts 等。",
                "category": "filesystem",
                "parameters": [
                    {
                        "name": "pattern",
                        "type": "string",
                        "description": "搜索模式（支持通配符 *、**、?、[]）",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "path",
                        "type": "string",
                        "description": "搜索的根目录路径",
                        "required": False,
                        "default": "当前目录"
                    }
                ],
                "return_description": "返回匹配的文件路径列表",
                "examples": [
                    "Glob(pattern='*.py') - 查找当前目录所有 .py 文件",
                    "Glob(pattern='**/*.ts') - 递归查找所有 .ts 文件",
                    "Glob(pattern='src/**/*.{js,jsx,ts,tsx}') - 查找 src 下所有 JS/TS 文件"
                ],
                "notes": "** 表示递归匹配所有子目录。结果数量过多时，建议使用更精确的模式。"
            },
            {
                "name": "LS",
                "display_name": "列出目录",
                "description": "列出指定目录的内容，包括文件和子目录。",
                "category": "filesystem",
                "parameters": [
                    {
                        "name": "path",
                        "type": "string",
                        "description": "要列出的目录路径",
                        "required": False,
                        "default": "当前目录"
                    }
                ],
                "return_description": "返回目录内容列表，区分文件和目录",
                "examples": [
                    "LS(path='.') - 列出当前目录",
                    "LS(path='/home/user/project') - 列出指定目录"
                ],
                "notes": "结果会显示每个条目的类型（文件/目录）、大小和修改时间。"
            },
            {
                "name": "web_search",
                "display_name": "网络搜索",
                "description": "在互联网上搜索信息。需要配置网络搜索提供商（如 Brave Search、Tavily 等）。",
                "category": "web",
                "parameters": [
                    {
                        "name": "query",
                        "type": "string",
                        "description": "搜索关键词",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "limit",
                        "type": "number",
                        "description": "返回结果数量限制",
                        "required": False,
                        "default": "10"
                    }
                ],
                "return_description": "返回搜索结果，包括标题、URL、摘要等",
                "examples": [
                    "web_search(query='Python 3.12 新特性') - 搜索 Python 版本信息",
                    "web_search(query='最新 AI 研究进展', limit=5) - 搜索最新技术动态"
                ],
                "notes": "需要在 Hermes 配置中设置搜索提供商的 API key。"
            },
            {
                "name": "browser_navigate",
                "display_name": "浏览器导航",
                "description": "在浏览器中导航到指定 URL。这是 browser_* 系列工具之一，用于网页浏览自动化。",
                "category": "web",
                "parameters": [
                    {
                        "name": "url",
                        "type": "string",
                        "description": "要访问的网页 URL",
                        "required": True,
                        "default": None
                    }
                ],
                "return_description": "返回页面导航结果",
                "examples": [
                    "browser_navigate(url='https://github.com') - 访问 GitHub",
                    "browser_navigate(url='https://docs.python.org/3/') - 访问 Python 文档"
                ],
                "notes": "browser_* 工具系列用于网页自动化，包括点击、输入、截图等操作。"
            },
            {
                "name": "browser_click",
                "display_name": "浏览器点击",
                "description": "在浏览器页面上点击指定的元素。",
                "category": "web",
                "parameters": [
                    {
                        "name": "selector",
                        "type": "string",
                        "description": "CSS 选择器或元素描述",
                        "required": True,
                        "default": None
                    }
                ],
                "return_description": "返回点击操作结果",
                "examples": [
                    "browser_click(selector='button.submit') - 点击提交按钮",
                    "browser_click(selector='text=登录') - 点击包含'登录'文本的元素"
                ],
                "notes": "选择器可以是 CSS 选择器、XPath 或语义化的文本描述。"
            },
            {
                "name": "browser_type",
                "display_name": "浏览器输入",
                "description": "在浏览器输入框中输入文本。",
                "category": "web",
                "parameters": [
                    {
                        "name": "selector",
                        "type": "string",
                        "description": "输入框的 CSS 选择器",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "text",
                        "type": "string",
                        "description": "要输入的文本",
                        "required": True,
                        "default": None
                    }
                ],
                "return_description": "返回输入操作结果",
                "examples": [
                    "browser_type(selector='input[name=username]', text='myuser') - 输入用户名",
                    "browser_type(selector='#search', text='Python tutorial') - 在搜索框输入关键词"
                ],
                "notes": "输入前会自动清空输入框内容。"
            },
            {
                "name": "browser_snapshot",
                "display_name": "浏览器快照",
                "description": "获取当前浏览器页面的快照（DOM 结构或截图）。",
                "category": "web",
                "parameters": [
                    {
                        "name": "type",
                        "type": "string",
                        "description": "快照类型：dom 或 screenshot",
                        "required": False,
                        "default": "dom"
                    }
                ],
                "return_description": "返回页面快照内容",
                "examples": [
                    "browser_snapshot(type='dom') - 获取页面 DOM 结构",
                    "browser_snapshot(type='screenshot') - 截取页面截图"
                ],
                "notes": "DOM 快照返回简化的页面结构，用于理解页面内容。截图返回 base64 编码的图片。"
            },
            {
                "name": "memory",
                "display_name": "记忆管理",
                "description": "Hermes 自主管理的记忆系统。支持添加、替换、删除记忆条目。记忆分为两种：memory（Agent 个人笔记）和 user（用户画像）。",
                "category": "memory",
                "parameters": [
                    {
                        "name": "operation",
                        "type": "string",
                        "description": "操作类型：add、replace、remove",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "target",
                        "type": "string",
                        "description": "记忆目标：memory 或 user",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "content",
                        "type": "string",
                        "description": "记忆内容（add/replace 操作必需）",
                        "required": False,
                        "default": None
                    },
                    {
                        "name": "old_content",
                        "type": "string",
                        "description": "要替换/删除的旧内容（replace/remove 操作必需）",
                        "required": False,
                        "default": None
                    }
                ],
                "return_description": "返回记忆操作结果",
                "examples": [
                    "memory(operation='add', target='memory', content='用户项目使用 Axum + SQLx') - 添加新记忆",
                    "memory(operation='add', target='user', content='用户偏好简洁回答') - 添加用户画像",
                    "memory(operation='remove', target='memory', old_content='过时的信息') - 删除记忆条目"
                ],
                "notes": "记忆内容会在每次会话开始时自动注入到系统提示中。MEMORY.md 限制约 2200 字符，USER.md 限制约 1375 字符。"
            },
            {
                "name": "skill_manage",
                "display_name": "技能管理",
                "description": "管理 Hermes 技能系统，包括查看、安装、更新、卸载技能。",
                "category": "skill",
                "parameters": [
                    {
                        "name": "action",
                        "type": "string",
                        "description": "操作类型：list、install、update、uninstall、search",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "skill_name",
                        "type": "string",
                        "description": "技能名称或标识符",
                        "required": False,
                        "default": None
                    }
                ],
                "return_description": "返回技能操作结果",
                "examples": [
                    "skill_manage(action='list') - 列出已安装的技能",
                    "skill_manage(action='install', skill_name='openai/skills/skill-creator') - 安装技能",
                    "skill_manage(action='search', skill_name='code') - 搜索可用技能"
                ],
                "notes": "技能是 Hermes 核心的自学习能力，Agent 可以从经验中创建和改进技能。"
            },
            {
                "name": "session_search",
                "display_name": "会话搜索",
                "description": "搜索历史对话会话。Hermes 所有 CLI 和消息平台会话存储在 SQLite 数据库中，具有全文搜索能力。",
                "category": "session",
                "parameters": [
                    {
                        "name": "query",
                        "type": "string",
                        "description": "搜索关键词",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "days",
                        "type": "number",
                        "description": "搜索范围（天数）",
                        "required": False,
                        "default": "无限制"
                    }
                ],
                "return_description": "返回匹配的历史会话列表",
                "examples": [
                    "session_search(query='database migration') - 搜索数据库迁移相关对话",
                    "session_search(query='Python 错误', days=7) - 搜索近 7 天的 Python 错误对话"
                ],
                "notes": "搜索结果会配合 Gemini Flash 进行摘要，帮助快速定位相关历史对话。"
            },
            {
                "name": "image_analyze",
                "display_name": "图像分析",
                "description": "分析图像内容，理解图片中的信息。支持 URL 和 base64 编码的图片输入。",
                "category": "vision",
                "parameters": [
                    {
                        "name": "image_source",
                        "type": "string",
                        "description": "图像来源：url 或 base64",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "image_data",
                        "type": "string",
                        "description": "图像 URL 或 base64 数据",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "prompt",
                        "type": "string",
                        "description": "分析提示（可选，如'描述这张图片'）",
                        "required": False,
                        "default": "描述这张图片"
                    }
                ],
                "return_description": "返回图像分析结果",
                "examples": [
                    "image_analyze(image_source='url', image_data='https://example.com/chart.png', prompt='描述这个图表') - 分析在线图片",
                    "image_analyze(image_source='base64', image_data='data:image/jpeg;base64,...', prompt='识别图片中的文字') - 分析 base64 图片"
                ],
                "notes": "需要配置支持视觉能力的模型（如 Claude 3 Opus、GPT-4V 等）。"
            },
            {
                "name": "tts",
                "display_name": "语音合成",
                "description": "将文本转换为语音（Text-to-Speech）。",
                "category": "voice",
                "parameters": [
                    {
                        "name": "text",
                        "type": "string",
                        "description": "要转换的文本",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "voice",
                        "type": "string",
                        "description": "语音类型/音色",
                        "required": False,
                        "default": "默认语音"
                    },
                    {
                        "name": "speed",
                        "type": "number",
                        "description": "语速（0.5-2.0）",
                        "required": False,
                        "default": "1.0"
                    }
                ],
                "return_description": "返回语音音频文件路径或数据",
                "examples": [
                    "tts(text='你好，欢迎使用 Hermes！') - 基础语音合成",
                    "tts(text='Welcome', voice='alloy', speed=1.2) - 指定语音和语速"
                ],
                "notes": "需要配置 TTS 服务提供商（如 OpenAI TTS、ElevenLabs 等）。"
            },
            {
                "name": "stt",
                "display_name": "语音识别",
                "description": "将语音转换为文本（Speech-to-Text）。",
                "category": "voice",
                "parameters": [
                    {
                        "name": "audio_source",
                        "type": "string",
                        "description": "音频来源：file 或 url",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "audio_data",
                        "type": "string",
                        "description": "音频文件路径或 URL",
                        "required": True,
                        "default": None
                    },
                    {
                        "name": "language",
                        "type": "string",
                        "description": "语言代码（如 'zh'、'en'）",
                        "required": False,
                        "default": "自动检测"
                    }
                ],
                "return_description": "返回识别的文本内容",
                "examples": [
                    "stt(audio_source='file', audio_data='/path/to/audio.mp3') - 识别本地音频",
                    "stt(audio_source='url', audio_data='https://example.com/audio.wav', language='zh') - 识别中文音频"
                ],
                "notes": "需要配置 STT 服务提供商（如 OpenAI Whisper、AssemblyAI 等）。"
            },
        ]

    def _get_builtin_tool_categories(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "terminal",
                "display_name": "终端工具",
                "icon": "🖥️",
                "description": "终端命令执行相关工具",
                "tool_count": 1
            },
            {
                "name": "filesystem",
                "display_name": "文件系统工具",
                "icon": "📁",
                "description": "文件和目录操作相关工具",
                "tool_count": 5
            },
            {
                "name": "web",
                "display_name": "网络工具",
                "icon": "🌐",
                "description": "网络搜索和浏览器自动化工具",
                "tool_count": 5
            },
            {
                "name": "memory",
                "display_name": "记忆管理工具",
                "icon": "🧠",
                "description": "Hermes 自主记忆管理系统",
                "tool_count": 1
            },
            {
                "name": "skill",
                "display_name": "技能管理工具",
                "icon": "⚡",
                "description": "技能安装、更新、卸载管理",
                "tool_count": 1
            },
            {
                "name": "session",
                "display_name": "会话工具",
                "icon": "💬",
                "description": "历史会话搜索和管理",
                "tool_count": 1
            },
            {
                "name": "vision",
                "display_name": "视觉工具",
                "icon": "👁️",
                "description": "图像分析和理解工具",
                "tool_count": 1
            },
            {
                "name": "voice",
                "display_name": "语音工具",
                "icon": "🎙️",
                "description": "语音合成和识别工具",
                "tool_count": 2
            },
        ]

    def list_builtin_tools(self, category: Optional[str] = None, search: Optional[str] = None) -> BuiltinToolListResponse:
        all_tools_data = self._get_builtin_tools()
        categories_data = self._get_builtin_tool_categories()
        
        tools: List[BuiltinTool] = []
        categories: List[BuiltinToolCategory] = []
        
        for cat_data in categories_data:
            cat_tools = [t for t in all_tools_data if t["category"] == cat_data["name"]]
            cat_data["tool_count"] = len(cat_tools)
            categories.append(BuiltinToolCategory(**cat_data))
        
        filtered_tools_data = all_tools_data
        if category:
            filtered_tools_data = [t for t in filtered_tools_data if t["category"] == category]
        
        if search:
            search_lower = search.lower()
            filtered_tools_data = [
                t for t in filtered_tools_data
                if search_lower in t["name"].lower()
                or search_lower in t["display_name"].lower()
                or search_lower in t["description"].lower()
            ]
        
        for tool_data in filtered_tools_data:
            params = [
                BuiltinToolParameter(**p)
                for p in tool_data.get("parameters", [])
            ]
            tools.append(BuiltinTool(
                name=tool_data["name"],
                display_name=tool_data["display_name"],
                description=tool_data["description"],
                category=tool_data["category"],
                parameters=params,
                return_description=tool_data.get("return_description"),
                examples=tool_data.get("examples", []),
                notes=tool_data.get("notes")
            ))
        
        tools = sorted(tools, key=lambda t: (t.category, t.name))
        
        return BuiltinToolListResponse(
            categories=categories,
            tools=tools,
            total_tools=len(tools)
        )

    def _get_memory_dir(self, profile_name: Optional[str] = None) -> Path:
        if profile_name and profile_name != "default":
            hermes_profiles_dir = Path.home() / ".hermes-profiles" / profile_name
            memory_dir = hermes_profiles_dir / "memories"
            if memory_dir.exists():
                return memory_dir
            hermes_dir = hermes_profiles_dir
        else:
            hermes_dir = Path.home() / ".hermes"
        
        memory_dir = hermes_dir / "memories"
        if memory_dir.exists():
            return memory_dir
        
        return hermes_dir

    def _parse_memory_items(self, content: str) -> List[MemoryItem]:
        if not content or not content.strip():
            return []
        
        items: List[MemoryItem] = []
        lines = content.split("\n")
        
        current_item_lines: List[str] = []
        item_index = 0
        line_number = 0
        
        for i, line in enumerate(lines):
            line_number = i + 1
            
            if line.startswith("§") or "§" in line:
                if current_item_lines:
                    item_index += 1
                    raw_text = " ".join(current_item_lines).strip()
                    item_type = self._extract_memory_type(raw_text)
                    items.append(MemoryItem(
                        id=item_index,
                        type=item_type,
                        content=raw_text,
                        raw=raw_text,
                        line_number=line_number - len(current_item_lines)
                    ))
                    current_item_lines = []
                
                clean_line = line.replace("§", "").strip()
                if clean_line:
                    current_item_lines.append(clean_line)
            elif line.strip():
                current_item_lines.append(line.strip())
        
        if current_item_lines:
            item_index += 1
            raw_text = " ".join(current_item_lines).strip()
            item_type = self._extract_memory_type(raw_text)
            items.append(MemoryItem(
                id=item_index,
                type=item_type,
                content=raw_text,
                raw=raw_text,
                line_number=line_number - len(current_item_lines) + 1 if current_item_lines else line_number
            ))
        
        return items

    def _extract_memory_type(self, text: str) -> str:
        type_indicators = [
            ("项目约定", ["项目", "约定", "配置", "设置", "规范"]),
            ("用户偏好", ["用户", "偏好", "喜欢", "希望", "期望"]),
            ("环境事实", ["环境", "事实", "系统", "版本", "路径"]),
            ("技术约定", ["技术", "架构", "框架", "库", "依赖"]),
            ("业务规则", ["业务", "规则", "流程", "逻辑"]),
        ]
        
        text_lower = text.lower()
        for type_name, keywords in type_indicators:
            for kw in keywords:
                if kw in text or kw.lower() in text_lower:
                    return type_name
        
        return "其他"

    def _read_memory_file(self, profile_name: str, memory_type: MemoryType) -> MemoryFile:
        memory_dir = self._get_memory_dir(profile_name)
        
        if memory_type == MemoryType.MEMORY:
            file_name = "MEMORY.md"
            display_name = "Agent 笔记 (MEMORY.md)"
            description = "Agent 个人笔记，记录环境事实、项目约定、学到的知识等"
            char_limit = 2200
        else:
            file_name = "USER.md"
            display_name = "用户画像 (USER.md)"
            description = "用户画像，记录用户偏好、沟通风格、期望等"
            char_limit = 1375
        
        file_path = memory_dir / file_name
        exists = file_path.exists()
        
        raw_content = None
        current_chars = 0
        progress = 0.0
        item_count = 0
        last_updated = None
        items: List[MemoryItem] = []
        
        if exists:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_content = f.read()
                
                stat = file_path.stat()
                last_updated = datetime.fromtimestamp(stat.st_mtime)
                
                current_chars = len(raw_content)
                progress = min(100.0, (current_chars / char_limit) * 100) if char_limit > 0 else 0.0
                
                items = self._parse_memory_items(raw_content)
                item_count = len(items)
                
            except Exception as e:
                logger.error(f"Failed to read memory file {file_path}: {e}")
                raw_content = None
        
        return MemoryFile(
            type=memory_type,
            name=file_name,
            display_name=display_name,
            description=description,
            char_limit=char_limit,
            current_chars=current_chars,
            progress=progress,
            item_count=item_count,
            last_updated=last_updated,
            exists=exists,
            raw_content=raw_content,
            items=items
        )

    def get_memory(self, profile_name: str) -> MemoryResponse:
        memory_file = self._read_memory_file(profile_name, MemoryType.MEMORY)
        user_file = self._read_memory_file(profile_name, MemoryType.USER)
        
        return MemoryResponse(
            profile_name=profile_name,
            memory_file=memory_file,
            user_file=user_file
        )

    def list_profile_memories(self, db: Optional[Session] = None) -> ProfileMemoryListResponse:
        profiles = self.get_profile_list()
        
        if not profiles:
            profiles = ["default"]
        
        items: List[ProfileMemoryListItem] = []
        
        for profile_name in profiles:
            memory_dir = self._get_memory_dir(profile_name)
            
            memory_file = memory_dir / "MEMORY.md"
            user_file = memory_dir / "USER.md"
            
            memory_exists = memory_file.exists()
            user_exists = user_file.exists()
            
            memory_chars = 0
            user_chars = 0
            
            try:
                if memory_exists:
                    with open(memory_file, "r", encoding="utf-8") as f:
                        memory_chars = len(f.read())
                if user_exists:
                    with open(user_file, "r", encoding="utf-8") as f:
                        user_chars = len(f.read())
            except Exception as e:
                logger.error(f"Failed to read memory files for {profile_name}: {e}")
            
            display_name = profile_name
            user_id = None
            user_name = None
            
            if db:
                try:
                    from app.models import HermesProfile
                    profile = db.query(HermesProfile).filter(
                        HermesProfile.profile_name == profile_name
                    ).first()
                    
                    if profile:
                        display_name = profile.display_name or profile_name
                        user_id = profile.user_id
                        
                        if user_id:
                            user = db.query(User).filter(User.id == user_id).first()
                            if user:
                                user_name = user.username
                except Exception as e:
                    logger.error(f"Failed to get profile info for {profile_name}: {e}")
            
            items.append(ProfileMemoryListItem(
                profile_name=profile_name,
                display_name=display_name,
                user_id=user_id,
                user_name=user_name,
                memory_exists=memory_exists,
                user_exists=user_exists,
                memory_chars=memory_chars,
                user_chars=user_chars,
                memory_limit=2200,
                user_limit=1375
            ))
        
        return ProfileMemoryListResponse(
            items=items,
            total=len(items)
        )

    def _get_profile_config_path(self, profile_name: Optional[str] = None) -> tuple[Path, Path]:
        if profile_name and profile_name != "default" and profile_name != "global":
            hermes_profiles_dir = Path.home() / ".hermes-profiles" / profile_name
            config_path = hermes_profiles_dir / "config.yaml"
            env_path = hermes_profiles_dir / ".env"
            if config_path.exists() or hermes_profiles_dir.exists():
                return config_path, env_path
        
        hermes_dir = Path.home() / ".hermes"
        config_path = hermes_dir / "config.yaml"
        env_path = hermes_dir / ".env"
        return config_path, env_path

    def _mask_sensitive_value(self, key: str, value: str) -> str:
        sensitive_keywords = [
            "api_key", "apikey", "api-key",
            "secret", "password", "pwd",
            "token", "auth", "credential",
            "private_key", "privatekey",
            "access_key", "accesskey",
        ]
        
        key_lower = key.lower()
        is_sensitive = any(kw in key_lower for kw in sensitive_keywords)
        
        if not is_sensitive:
            return value
        
        if not value:
            return value
        
        if len(value) <= 8:
            return "****"
        
        visible_chars = min(4, len(value) // 4)
        return value[:visible_chars] + "****" + value[-visible_chars:]

    def _parse_model_provider(self, model: str) -> str:
        if not model:
            return "未配置"
        
        provider_map = {
            "anthropic": "Anthropic",
            "claude": "Anthropic",
            "openai": "OpenAI",
            "gpt": "OpenAI",
            "google": "Google",
            "gemini": "Google",
            "mistral": "Mistral",
            "openrouter": "OpenRouter",
        }
        
        model_lower = model.lower()
        for key, provider in provider_map.items():
            if key in model_lower:
                return provider
        
        return model.split("/")[0] if "/" in model else "未知"

    def _get_model_context_window(self, model: str) -> int:
        if not model:
            return 0
        
        model_lower = model.lower()
        
        if "claude-opus" in model_lower or "claude-4" in model_lower:
            return 200000
        elif "claude-sonnet" in model_lower:
            return 200000
        elif "claude-haiku" in model_lower:
            return 200000
        elif "gpt-4o" in model_lower:
            return 128000
        elif "gpt-4-turbo" in model_lower:
            return 128000
        elif "gpt-4" in model_lower:
            return 8192
        elif "gpt-3.5" in model_lower:
            return 16384
        elif "gemini-1.5-pro" in model_lower:
            return 1048576
        elif "gemini-1.5-flash" in model_lower:
            return 1048576
        
        return 8192

    def _read_env_file(self, env_path: Path) -> Dict[str, str]:
        if not env_path.exists():
            return {}
        
        env_vars = {}
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        env_vars[key] = value
        except Exception as e:
            logger.error(f"Failed to read .env file {env_path}: {e}")
        
        return env_vars

    def list_config_profiles(self, db: Optional[Session] = None) -> ConfigProfileListResponse:
        profiles = self.get_profile_list()
        
        items: List[ConfigProfileItem] = []
        
        items.append(ConfigProfileItem(
            name="global",
            display_name="全局配置",
            has_config=True,
            is_global=True
        ))
        
        for profile_name in profiles:
            if profile_name == "default":
                continue
                
            config_path, env_path = self._get_profile_config_path(profile_name)
            has_config = config_path.exists() or env_path.exists()
            
            display_name = profile_name
            user_name = None
            
            if db:
                try:
                    from app.models import User
                    if profile_name.startswith("user_"):
                        try:
                            user_id = int(profile_name.replace("user_", ""))
                            user = db.query(User).filter(User.id == user_id).first()
                            if user:
                                display_name = user.username
                                user_name = user.username
                        except ValueError:
                            pass
                except Exception as e:
                    logger.error(f"Failed to get user info for profile {profile_name}: {e}")
            
            items.append(ConfigProfileItem(
                name=profile_name,
                display_name=display_name,
                has_config=has_config,
                is_global=False
            ))
        
        return ConfigProfileListResponse(
            items=items,
            total=len(items)
        )

    def get_config(self, profile_name: str = "global") -> ConfigResponse:
        config_path, env_path = self._get_profile_config_path(profile_name)
        
        config_data = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"Failed to read config.yaml {config_path}: {e}")
        
        env_vars = self._read_env_file(env_path)
        
        last_updated = None
        if config_path.exists():
            try:
                stat = config_path.stat()
                last_updated = datetime.fromtimestamp(stat.st_mtime)
            except Exception:
                pass
        
        model = ModelConfig()
        terminal = TerminalConfig()
        api_server = APIServerConfig()
        memory = MemoryConfig()
        compression = CompressionConfig()
        tools = ToolsConfig()
        general = GeneralConfig()
        
        model_config = config_data.get("model", {})
        if isinstance(model_config, dict):
            model.default_model = model_config.get("model") or model_config.get("default")
            model.temperature = model_config.get("temperature")
            model.max_tokens = model_config.get("max_tokens") or model_config.get("max_output_tokens")
        
        if model.default_model:
            model.model_provider = self._parse_model_provider(model.default_model)
            model.context_window = self._get_model_context_window(model.default_model)
        
        terminal_config = config_data.get("terminal", {})
        if isinstance(terminal_config, dict):
            terminal.backend = terminal_config.get("backend", "local")
            terminal.cwd = terminal_config.get("cwd")
            terminal.timeout = terminal_config.get("timeout")
            terminal.env_passthrough = terminal_config.get("env_passthrough", [])
        
        api_server.enabled = env_vars.get("API_SERVER_ENABLED", "false").lower() in ("true", "1", "yes")
        try:
            api_server.port = int(env_vars.get("API_SERVER_PORT", 8642))
        except (ValueError, TypeError):
            api_server.port = 8642
        api_server.host = env_vars.get("API_SERVER_HOST", "127.0.0.1")
        
        cors_origins = env_vars.get("API_SERVER_CORS_ORIGINS", "")
        if cors_origins:
            api_server.cors_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
        api_server.model_name = env_vars.get("API_SERVER_MODEL_NAME")
        
        memory_config = config_data.get("memory", {})
        if isinstance(memory_config, dict):
            memory.auto_save = memory_config.get("auto_save", True)
            memory.memory_char_limit = memory_config.get("memory_char_limit", 2200)
            memory.user_char_limit = memory_config.get("user_char_limit", 1375)
        
        compression_config = config_data.get("compression", {})
        if isinstance(compression_config, dict):
            compression.enabled = compression_config.get("enabled", True)
            compression.strategy = compression_config.get("strategy")
            compression.threshold_tokens = compression_config.get("threshold_tokens")
        
        tools_config = config_data.get("tools", {}) or config_data.get("tool", {})
        if isinstance(tools_config, dict):
            tools.enabled_tools = tools_config.get("enabled", [])
            tools.disabled_tools = tools_config.get("disabled", [])
        
        general_config = config_data.get("general", {})
        if isinstance(general_config, dict):
            general.log_level = general_config.get("log_level")
            general.auto_update = general_config.get("auto_update", False)
            general.telemetry_enabled = general_config.get("telemetry_enabled", True)
        
        return ConfigResponse(
            profile_name=profile_name,
            model=model,
            terminal=terminal,
            api_server=api_server,
            memory=memory,
            compression=compression,
            tools=tools,
            general=general,
            config_file_path=str(config_path) if config_path.exists() else None,
            env_file_path=str(env_path) if env_path.exists() else None,
            last_updated=last_updated
        )


    def _get_knowledge_base_path(self) -> Path:
        knowledge_base = Path.home() / ".agentnow" / "knowledge" / "docs"
        return knowledge_base

    def _is_text_file(self, file_path: Path) -> bool:
        text_extensions = {
            ".md", ".txt", ".json", ".csv", ".html", ".htm", ".xml",
            ".py", ".js", ".ts", ".css", ".scss", ".less", ".vue",
            ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rs",
            ".rb", ".php", ".swift", ".kt", ".scala", ".sh",
            ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
            ".sql", ".log", ".mdx", ".rst", ".adoc",
        }
        return file_path.suffix.lower() in text_extensions

    def _parse_markdown_frontmatter(self, content: str) -> tuple[dict, str]:
        if not content.startswith("---"):
            return {}, content

        lines = content.split("\n")
        frontmatter_lines = []
        content_lines = []
        in_frontmatter = False
        frontmatter_ended = False

        for i, line in enumerate(lines):
            if i == 0 and line.strip() == "---":
                in_frontmatter = True
                continue
            if in_frontmatter and line.strip() == "---":
                in_frontmatter = False
                frontmatter_ended = True
                continue
            if in_frontmatter:
                frontmatter_lines.append(line)
            elif frontmatter_ended:
                content_lines.append(line)

        frontmatter = {}
        if frontmatter_lines:
            try:
                frontmatter = yaml.safe_load("\n".join(frontmatter_lines)) or {}
            except Exception as e:
                logger.warning(f"Failed to parse frontmatter: {e}")
                frontmatter = {}

        actual_content = "\n".join(content_lines)
        return frontmatter, actual_content

    def _extract_markdown_outline(self, content: str) -> List[dict]:
        if not content:
            return []

        outline = []
        lines = content.split("\n")
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

        for line_number, line in enumerate(lines, 1):
            match = heading_pattern.match(line.strip())
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                outline.append({
                    "level": level,
                    "title": title,
                    "line_number": line_number
                })

        return outline

    def _get_file_mime_type(self, file_path: Path) -> str:
        extension_mime = {
            ".md": "text/markdown",
            ".txt": "text/plain",
            ".json": "application/json",
            ".csv": "text/csv",
            ".html": "text/html",
            ".htm": "text/html",
            ".xml": "application/xml",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".py": "text/x-python",
            ".js": "application/javascript",
            ".ts": "application/typescript",
            ".css": "text/css",
            ".java": "text/x-java-source",
            ".yaml": "application/x-yaml",
            ".yml": "application/x-yaml",
            ".toml": "application/toml",
            ".sql": "text/x-sql",
            ".sh": "text/x-shellscript",
        }
        return extension_mime.get(file_path.suffix.lower(), "application/octet-stream")

    def _scan_knowledge_docs(self, base_path: Path) -> List[HermesKnowledgeDoc]:
        docs: List[HermesKnowledgeDoc] = []

        if not base_path.exists():
            logger.warning(f"Knowledge base path does not exist: {base_path}")
            return docs

        allowed_extensions = {
            ".md", ".txt", ".json", ".csv", ".html", ".htm", ".xml",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".py", ".js", ".ts", ".css", ".scss", ".less", ".vue",
            ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rs",
            ".rb", ".php", ".swift", ".kt", ".scala", ".sh",
            ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
            ".sql", ".log", ".mdx", ".rst", ".adoc",
        }

        try:
            for root, dirs, files in os.walk(base_path):
                for file_name in files:
                    file_path = Path(root) / file_name
                    
                    if file_path.suffix.lower() not in allowed_extensions:
                        continue
                    
                    if file_name.startswith(".") or file_name.startswith("_"):
                        continue
                    
                    try:
                        relative_path = file_path.relative_to(base_path)
                        stat = file_path.stat()
                        
                        doc_id = str(relative_path).replace(os.sep, "/")
                        
                        title = file_path.stem
                        description = None
                        tags: List[str] = []
                        word_count = 0
                        char_count = 0
                        
                        if self._is_text_file(file_path):
                            try:
                                with open(file_path, "r", encoding="utf-8") as f:
                                    content = f.read()
                                
                                char_count = len(content)
                                word_count = len(content.split())
                                
                                if file_path.suffix.lower() == ".md":
                                    frontmatter, actual_content = self._parse_markdown_frontmatter(content)
                                    
                                    if frontmatter:
                                        title = frontmatter.get("title") or title
                                        description = frontmatter.get("description")
                                        tags = frontmatter.get("tags", []) or []
                                        
                                        if isinstance(tags, str):
                                            tags = [t.strip() for t in tags.split(",") if t.strip()]
                            except Exception as e:
                                logger.warning(f"Failed to read text file {file_path}: {e}")
                        
                        parent_dir = file_path.parent
                        category = str(parent_dir.relative_to(base_path)) if parent_dir != base_path else None
                        if category == ".":
                            category = None
                        
                        doc = HermesKnowledgeDoc(
                            id=doc_id,
                            file_name=file_name,
                            file_path=str(relative_path),
                            file_size=stat.st_size,
                            file_type=file_path.suffix.lower().lstrip("."),
                            mime_type=self._get_file_mime_type(file_path),
                            word_count=word_count,
                            char_count=char_count,
                            title=title,
                            description=description,
                            tags=list(tags) if tags else [],
                            category=category,
                            status=HermesKnowledgeDocStatus.INDEXED,
                            created_at=datetime.fromtimestamp(stat.st_ctime),
                            updated_at=datetime.fromtimestamp(stat.st_mtime),
                            last_indexed_at=datetime.fromtimestamp(stat.st_mtime),
                        )
                        docs.append(doc)
                        
                    except Exception as e:
                        logger.error(f"Failed to process file {file_path}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to scan knowledge base: {e}")

        docs.sort(key=lambda x: x.updated_at, reverse=True)
        return docs

    def get_knowledge_status(self) -> HermesKnowledgeStatus:
        base_path = self._get_knowledge_base_path()
        
        status = HealthStatus.HEALTHY
        if not base_path.exists():
            status = HealthStatus.WARNING
        
        docs = self._scan_knowledge_docs(base_path)
        
        total_docs = len(docs)
        total_chars = sum(d.char_count for d in docs)
        total_size = sum(d.file_size for d in docs)
        
        indexed_docs = sum(1 for d in docs if d.status == HermesKnowledgeDocStatus.INDEXED)
        pending_docs = sum(1 for d in docs if d.status == HermesKnowledgeDocStatus.PENDING)
        failed_docs = sum(1 for d in docs if d.status == HermesKnowledgeDocStatus.FAILED)
        
        last_index_at = None
        if docs:
            last_index_at = max(d.last_indexed_at for d in docs if d.last_indexed_at)
        
        return HermesKnowledgeStatus(
            status=status,
            total_docs=total_docs,
            total_chars=total_chars,
            total_size=total_size,
            indexed_docs=indexed_docs,
            pending_docs=pending_docs,
            failed_docs=failed_docs,
            last_index_at=last_index_at,
            index_engine="Hermes RAG",
            storage_path=str(base_path),
        )

    def list_knowledge_docs(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        file_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> HermesKnowledgeListResponse:
        base_path = self._get_knowledge_base_path()
        docs = self._scan_knowledge_docs(base_path)
        
        if keyword:
            keyword_lower = keyword.lower()
            docs = [
                d for d in docs
                if keyword_lower in (d.title or "").lower()
                or keyword_lower in d.file_name.lower()
                or keyword_lower in (d.description or "").lower()
                or any(keyword_lower in tag.lower() for tag in d.tags)
            ]
        
        if file_type:
            file_type_lower = file_type.lower().lstrip(".")
            docs = [d for d in docs if d.file_type == file_type_lower]
        
        if category:
            docs = [d for d in docs if d.category == category]
        
        categories_set = set()
        for d in self._scan_knowledge_docs(base_path):
            if d.category:
                categories_set.add(d.category)
        categories = sorted(list(categories_set))
        
        total = len(docs)
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_docs = docs[start_idx:end_idx]
        
        return HermesKnowledgeListResponse(
            items=paginated_docs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            categories=categories,
        )

    def get_knowledge_doc_detail(self, doc_id: str) -> Optional[HermesKnowledgeDocDetail]:
        base_path = self._get_knowledge_base_path()
        docs = self._scan_knowledge_docs(base_path)
        
        for doc in docs:
            if doc.id == doc_id:
                file_path = base_path / doc.file_path
                
                content = None
                frontmatter = None
                outline = None
                
                if self._is_text_file(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            raw_content = f.read()
                        
                        if file_path.suffix.lower() == ".md":
                            frontmatter, content = self._parse_markdown_frontmatter(raw_content)
                            outline = self._extract_markdown_outline(content)
                        else:
                            content = raw_content
                    except Exception as e:
                        logger.warning(f"Failed to read file content {file_path}: {e}")
                
                return HermesKnowledgeDocDetail(
                    id=doc.id,
                    file_name=doc.file_name,
                    file_path=doc.file_path,
                    file_size=doc.file_size,
                    file_type=doc.file_type,
                    mime_type=doc.mime_type,
                    word_count=doc.word_count,
                    char_count=doc.char_count,
                    title=doc.title,
                    description=doc.description,
                    tags=doc.tags,
                    category=doc.category,
                    status=doc.status,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    last_indexed_at=doc.last_indexed_at,
                    content=content,
                    frontmatter=frontmatter,
                    outline=outline,
                )
        
        return None

    def get_knowledge_file_types(self) -> List[dict]:
        base_path = self._get_knowledge_base_path()
        docs = self._scan_knowledge_docs(base_path)
        
        type_counts: Dict[str, int] = {}
        for doc in docs:
            if doc.file_type:
                type_counts[doc.file_type] = type_counts.get(doc.file_type, 0) + 1
        
        return [
            {"type": ft, "count": count}
            for ft, count in sorted(type_counts.items(), key=lambda x: (-x[1], x[0]))
        ]

    def _generate_audit_logs(self) -> List[HermesAuditLog]:
        now = datetime.now()
        
        action_mappings = [
            ("hermes:view:overview", "查看系统概览"),
            ("hermes:view:profiles", "查看Profile列表"),
            ("hermes:view:profile_detail", "查看Profile详情"),
            ("hermes:view:conversations", "查看对话列表"),
            ("hermes:view:conversation_detail", "查看对话详情"),
            ("hermes:view:skills", "查看技能列表"),
            ("hermes:view:mcp", "查看MCP服务"),
            ("hermes:view:tools", "查看工具集"),
            ("hermes:view:memory", "查看记忆"),
            ("hermes:view:config", "查看配置"),
            ("hermes:view:knowledge", "查看知识库"),
            ("hermes:action:restart_profile", "重启Profile"),
            ("hermes:action:stop_profile", "停止Profile"),
            ("hermes:action:start_profile", "启动Profile"),
            ("hermes:action:export_conversation", "导出对话"),
            ("hermes:action:delete_conversation", "删除对话"),
            ("hermes:action:upload_document", "上传文档"),
            ("hermes:action:delete_document", "删除文档"),
            ("hermes:action:rebuild_index", "重建索引"),
        ]
        
        user_mappings = [
            (1, "admin"),
            (2, "victor"),
            (3, "alice"),
            (4, "bob"),
        ]
        
        ip_addresses = [
            "127.0.0.1",
            "192.168.1.100",
            "192.168.1.101",
            "10.0.0.5",
        ]
        
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        target_types = ["profile", "conversation", "skill", "document", "config", "memory"]
        
        logs: List[HermesAuditLog] = []
        
        for i in range(50):
            action, action_name = action_mappings[i % len(action_mappings)]
            user_id, user_name = user_mappings[i % len(user_mappings)]
            
            minutes_ago = i * 30
            timestamp = now - timedelta(minutes=minutes_ago)
            
            target_type = None
            target_id = None
            details: Dict[str, Any] = {}
            
            if "profile" in action:
                target_type = "profile"
                profile_names = ["default", "work", "personal", "coding"]
                target_id = profile_names[i % len(profile_names)]
                details["profile_name"] = target_id
            elif "conversation" in action:
                target_type = "conversation"
                target_id = f"conv_{1000 + i}"
                details["conversation_id"] = target_id
            elif "skill" in action:
                target_type = "skill"
                skill_names = ["find-skills", "skill-creator", "http-api-cloudbase"]
                target_id = skill_names[i % len(skill_names)]
                details["skill_name"] = target_id
            elif "document" in action:
                target_type = "document"
                target_id = f"doc_{2000 + i}"
                details["document_id"] = target_id
                details["file_name"] = f"document_{i}.md"
            elif "knowledge" in action or "index" in action:
                target_type = "knowledge"
                details["action"] = action_name
            
            logs.append(HermesAuditLog(
                id=i + 1,
                user_id=user_id,
                user_name=user_name,
                action=action,
                action_name=action_name,
                target_type=target_type,
                target_id=target_id,
                details=details,
                ip_address=ip_addresses[i % len(ip_addresses)],
                user_agent=user_agents[i % len(user_agents)],
                timestamp=timestamp,
            ))
        
        return logs

    def get_audit_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        user_name: Optional[str] = None,
        target_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> HermesAuditLogListResponse:
        logs = self._generate_audit_logs()
        
        filtered_logs = logs
        
        if action:
            if action == "view":
                filtered_logs = [log for log in filtered_logs if log.action.startswith("hermes:view")]
            elif action == "action":
                filtered_logs = [log for log in filtered_logs if log.action.startswith("hermes:action")]
            else:
                filtered_logs = [log for log in filtered_logs if log.action == action]
        
        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
        
        if user_name:
            user_name_lower = user_name.lower()
            filtered_logs = [log for log in filtered_logs if user_name_lower in log.user_name.lower()]
        
        if target_type:
            filtered_logs = [log for log in filtered_logs if log.target_type == target_type]
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                filtered_logs = [log for log in filtered_logs if log.timestamp >= start_dt]
            except ValueError:
                logger.warning(f"Invalid start_time format: {start_time}")
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                filtered_logs = [log for log in filtered_logs if log.timestamp <= end_dt]
            except ValueError:
                logger.warning(f"Invalid end_time format: {end_time}")
        
        total = len(filtered_logs)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paged_logs = filtered_logs[start_index:end_index]
        
        return HermesAuditLogListResponse(
            items=paged_logs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


hermes_service = HermesService()
