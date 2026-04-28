import os
from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import KnowledgeDoc, KnowledgeConfig
from app.utils import HermesFileHandler


class HermesSyncService:
    def __init__(self, db: Session):
        self.db = db
        self._hermes_handler: Optional[HermesFileHandler] = None
        self._auto_sync: bool = True
        self._init_config()

    def _init_config(self) -> None:
        configs = self.db.query(KnowledgeConfig).all()
        config_dict = {c.config_key: c.config_value for c in configs}
        
        base_path = config_dict.get("storage.base_path", "./data/knowledge_docs")
        base_path = os.path.abspath(base_path)
        
        hermes_path = config_dict.get("hermes.workspace_path", "~/.hermes/workspace/docs")
        self._auto_sync = config_dict.get("sync.auto_sync", "true").lower() == "true"
        
        self._hermes_handler = HermesFileHandler(base_path, hermes_path)

    def get_config(self, key: str, default: str = None) -> str:
        config = self.db.query(KnowledgeConfig).filter(
            KnowledgeConfig.config_key == key
        ).first()
        return config.config_value if config else default

    def should_auto_sync(self) -> bool:
        return self._auto_sync

    def sync_document(self, doc: KnowledgeDoc) -> Tuple[bool, str]:
        if not self._hermes_handler:
            return False, "Hermes handler not initialized"
        
        if not doc.file_path:
            return False, "Document has no file path"
        
        base_path = self.get_config("storage.base_path", "./data/knowledge_docs")
        base_path = os.path.abspath(base_path)
        full_source_path = os.path.join(base_path, doc.file_path)
        
        if not os.path.exists(full_source_path):
            return False, f"Source file not found: {full_source_path}"
        
        dest_filename = f"doc_{doc.id}_{doc.file_name}"
        
        success, result = self._hermes_handler.sync_to_hermes(
            full_source_path, 
            dest_filename
        )
        
        if success:
            doc.sync_status = 1
            doc.hermes_path = result
            doc.synced_at = datetime.utcnow()
            doc.status = 2
            doc.sync_error = None
        else:
            doc.sync_status = 2
            doc.sync_error = result
        
        self.db.commit()
        
        return success, result

    def unsync_document(self, doc: KnowledgeDoc) -> bool:
        if not self._hermes_handler:
            return False
        
        if not doc.hermes_path:
            return True
        
        success = self._hermes_handler.delete_from_hermes(doc.hermes_path)
        
        if success:
            doc.sync_status = 0
            doc.hermes_path = None
            doc.synced_at = None
            doc.status = 1
            self.db.commit()
        
        return success

    def resync_document(self, doc: KnowledgeDoc) -> Tuple[bool, str]:
        if doc.hermes_path:
            self.unsync_document(doc)
        
        return self.sync_document(doc)

    def get_sync_status(self, doc: KnowledgeDoc) -> dict:
        return {
            "doc_id": doc.id,
            "sync_status": doc.sync_status,
            "synced_at": doc.synced_at,
            "hermes_path": doc.hermes_path,
            "sync_error": doc.sync_error,
        }

    def list_hermes_files(self) -> list:
        if not self._hermes_handler:
            return []
        return self._hermes_handler.list_hermes_files()

    def get_max_file_size(self) -> int:
        max_size = self.get_config("file.max_size", "104857600")
        try:
            return int(max_size)
        except ValueError:
            return 104857600

    def get_allowed_types(self) -> list:
        types_str = self.get_config("file.allowed_types", ".pdf,.doc,.docx,.txt,.md,.json,.csv,.xlsx,.xls,.pptx,.ppt,.html,.htm,.xml")
        return [t.strip().lower() for t in types_str.split(",") if t.strip()]

    def is_file_type_allowed(self, filename: str) -> bool:
        import os
        ext = os.path.splitext(filename)[1].lower()
        allowed_types = self.get_allowed_types()
        return ext in allowed_types

    def is_embedding_enabled(self) -> bool:
        enabled = self.get_config("embedding.enabled", "false")
        return enabled.lower() == "true"
