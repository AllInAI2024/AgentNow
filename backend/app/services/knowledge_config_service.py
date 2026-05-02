from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models import KnowledgeConfig
from app.config import settings


class KnowledgeConfigService:
    def __init__(self, db: Session):
        self.db = db
        self._config_cache: Dict[str, str] = {}
        self._load_configs()

    def _load_configs(self) -> None:
        configs = self.db.query(KnowledgeConfig).all()
        self._config_cache = {c.config_key: c.config_value for c in configs}

    def _get_config(self, key: str, default_value: str) -> str:
        if key not in self._config_cache:
            self._load_configs()
        return self._config_cache.get(key, default_value)

    def refresh_cache(self) -> None:
        self._load_configs()

    def get_storage_base_path(self) -> str:
        default_path = settings.KNOWLEDGE_BASE_PATH
        return self._get_config("storage.base_path", default_path)

    def get_max_file_size(self) -> int:
        default_size = settings.KNOWLEDGE_MAX_FILE_SIZE
        value = self._get_config("file.max_size", str(default_size))
        try:
            return int(value)
        except (ValueError, TypeError):
            return default_size

    def get_allowed_types(self) -> str:
        default_types = settings.KNOWLEDGE_ALLOWED_TYPES
        return self._get_config("file.allowed_types", default_types)

    def get_allowed_types_list(self) -> list:
        types_str = self.get_allowed_types()
        return [t.strip().lower() for t in types_str.split(',') if t.strip()]

    def is_mcp_enabled(self) -> bool:
        value = self._get_config("mcp.enabled", "true")
        return value.lower() in ("true", "1", "yes", "on")

    def get_all_configs(self) -> Dict[str, str]:
        return dict(self._config_cache)

    def update_config(self, key: str, value: str) -> bool:
        config = self.db.query(KnowledgeConfig).filter(
            KnowledgeConfig.config_key == key
        ).first()
        
        if config:
            config.config_value = value
            self.db.commit()
            self.db.refresh(config)
            self._config_cache[key] = value
            return True
        return False

    def get_config_by_key(self, key: str) -> Optional[KnowledgeConfig]:
        return self.db.query(KnowledgeConfig).filter(
            KnowledgeConfig.config_key == key
        ).first()
