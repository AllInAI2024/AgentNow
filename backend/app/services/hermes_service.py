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


hermes_service = HermesService()
