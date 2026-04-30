import os
import re
import subprocess
import platform
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class HermesProfileService:
    def __init__(self):
        self._system = platform.system().lower()
        self._python_path = os.path.dirname(os.path.dirname(os.path.dirname(os.__file__)))
        self._hermes_path: Optional[str] = None
        self._hermes_home: Path = self._get_hermes_home()
        self._hermes_profiles_home: Path = self._get_hermes_profiles_home()
        self._find_hermes_path()
        
        logger.info(f"Hermes home: {self._hermes_home}")
        logger.info(f"Hermes profiles home: {self._hermes_profiles_home}")
    
    def _get_hermes_home(self) -> Path:
        hermes_home = os.environ.get("HERMES_HOME")
        if hermes_home:
            return Path(hermes_home)
        return Path.home() / ".hermes"
    
    def _get_hermes_profiles_home(self) -> Path:
        profiles_home = os.environ.get("HERMES_PROFILES_HOME")
        if profiles_home:
            return Path(profiles_home)
        return Path.home() / ".hermes-profiles"
    
    def _find_hermes_path(self) -> None:
        possible_paths = [
            os.path.join(self._python_path, "bin", "hermes"),
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
    
    def _run_command(self, cmd: List[str], timeout: int = 30) -> Tuple[int, str, str]:
        try:
            logger.debug(f"Running command: {' '.join(cmd)}")
            
            env = os.environ.copy()
            if self._python_path:
                env["PATH"] = os.path.join(self._python_path, "bin") + os.pathsep + env.get("PATH", "")
            
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
    
    def generate_profile_name(self, user_id: int, tenant_id: int = 1) -> str:
        return f"corp_{tenant_id}_user_{user_id}"
    
    def get_all_profiles(self) -> List[str]:
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
            
            table_border_chars = {
                "─", "┌", "┐", "├", "┤", "└", "┘", 
                "│", "┏", "┓", "┣", "┫", "┗", "┛",
                "-", "+", "|"
            }
            
            def _is_table_border(line: str) -> bool:
                if not line:
                    return True
                stripped = line.strip()
                if not stripped:
                    return True
                
                if all(c in table_border_chars for c in stripped):
                    return True
                
                if stripped.startswith("──") or stripped.endswith("──"):
                    return True
                
                if stripped.startswith("┌") or stripped.startswith("├") or stripped.startswith("└"):
                    return True
                if stripped.endswith("┐") or stripped.endswith("┤") or stripped.endswith("┘"):
                    return True
                
                return False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if _is_table_border(line):
                    continue
                
                if line.lower().startswith("profile") or "profiles" in line.lower():
                    continue
                
                if "name" in line.lower() and "active" in line.lower():
                    continue
                
                if "(" in line and ")" in line:
                    name = line.split("(")[0].strip().rstrip("*")
                elif "*" in line:
                    name = line.rstrip("*").strip()
                else:
                    name = line
                
                if "│" in name:
                    parts = [p.strip() for p in name.split("│") if p.strip()]
                    if parts:
                        name = parts[0].rstrip("*").strip()
                
                if name and len(name) > 0 and not _is_table_border(name):
                    profiles.append(name)
            
            logger.debug(f"Found profiles: {profiles}")
            return profiles
        except Exception as e:
            logger.error(f"Failed to get profile list: {e}")
            return []
    
    def profile_exists(self, profile_name: str) -> bool:
        profiles = self.get_all_profiles()
        return profile_name in profiles
    
    def create_profile(self, profile_name: str) -> Tuple[bool, str]:
        if self.profile_exists(profile_name):
            logger.info(f"Profile '{profile_name}' already exists")
            return True, "Profile 已存在"
        
        logger.info(f"Creating profile: {profile_name}")
        
        returncode, stdout, stderr = self._run_command(
            [self._hermes_path, "profile", "create", profile_name],
            timeout=60
        )
        
        if returncode == 0:
            logger.info(f"Profile '{profile_name}' created successfully")
            return True, "Profile 创建成功"
        else:
            error_msg = stderr or stdout or "未知错误"
            logger.error(f"Failed to create profile '{profile_name}': {error_msg}")
            return False, f"Profile 创建失败: {error_msg}"
    
    def ensure_profile(self, user_id: int, tenant_id: int = 1) -> Tuple[str, bool, str]:
        profile_name = self.generate_profile_name(user_id, tenant_id)
        
        exists = self.profile_exists(profile_name)
        
        if not exists:
            success, message = self.create_profile(profile_name)
            if not success:
                return profile_name, False, message
            return profile_name, True, "Profile 创建成功"
        
        return profile_name, False, "Profile 已存在"
    
    def get_profile_path(self, profile_name: str) -> Optional[Path]:
        profile_dir = self._hermes_profiles_home / profile_name
        if profile_dir.exists():
            return profile_dir
        return None
    
    def get_profile_config_path(self, profile_name: str) -> Tuple[Path, Path]:
        profile_dir = self._hermes_profiles_home / profile_name
        config_path = profile_dir / "config.yaml"
        env_path = profile_dir / ".env"
        return config_path, env_path
    
    def get_profile_memory_dir(self, profile_name: str) -> Path:
        profile_dir = self._hermes_profiles_home / profile_name
        return profile_dir / "memory"
    
    def get_profile_config(self, profile_name: str) -> Optional[Dict[str, Any]]:
        config_path, _ = self.get_profile_config_path(profile_name)
        if not config_path.exists():
            return None
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to read config for profile {profile_name}: {e}")
            return None
    
    def update_profile_config(self, profile_name: str, config_updates: Dict[str, Any]) -> Tuple[bool, str]:
        config_path, _ = self.get_profile_config_path(profile_name)
        
        try:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {}
            
            config.update(config_updates)
            
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Profile '{profile_name}' config updated")
            return True, "配置更新成功"
        except Exception as e:
            logger.error(f"Failed to update config for profile {profile_name}: {e}")
            return False, f"配置更新失败: {e}"
    
    def set_profile_user_info(
        self,
        profile_name: str,
        user_id: int,
        username: str,
        department: Optional[str] = None,
    ) -> Tuple[bool, str]:
        user_md_path = self.get_profile_memory_dir(profile_name) / "USER.md"
        
        try:
            memory_dir = user_md_path.parent
            memory_dir.mkdir(parents=True, exist_ok=True)
            
            content = f"""# 用户信息

## 基本信息
- 用户ID: {user_id}
- 用户名: {username}
"""
            
            if department:
                content += f"- 部门: {department}\n"
            
            content += f"""
## 记录时间
- 创建时间: {datetime.now().isoformat()}
"""
            
            with open(user_md_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"User info set for profile '{profile_name}'")
            return True, "用户信息设置成功"
        except Exception as e:
            logger.error(f"Failed to set user info for profile {profile_name}: {e}")
            return False, f"用户信息设置失败: {e}"
