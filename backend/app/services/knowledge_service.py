import os
import math
from typing import Optional, Tuple, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models import KnowledgeDoc, KnowledgeDocChunk, User
from app.schemas import (
    KnowledgeDocCreate,
    KnowledgeDocUpdate,
    KnowledgeDocResponse,
    KnowledgeDocListResponse,
)
from app.services.hermes_sync_service import HermesSyncService
from app.utils import FileHandler


class KnowledgeService:
    def __init__(self, db: Session):
        self.db = db
        self._file_handler: Optional[FileHandler] = None
        self._sync_service = HermesSyncService(db)
        self._init_file_handler()

    def _init_file_handler(self) -> None:
        from app.models import KnowledgeConfig
        config = self.db.query(KnowledgeConfig).filter(
            KnowledgeConfig.config_key == "storage.base_path"
        ).first()
        base_path = config.config_value if config else "./data/knowledge_docs"
        base_path = os.path.abspath(base_path)
        self._file_handler = FileHandler(base_path)

    def get_document_by_id(self, doc_id: int) -> Optional[KnowledgeDoc]:
        return self.db.query(KnowledgeDoc).filter(
            KnowledgeDoc.id == doc_id,
            KnowledgeDoc.deleted_at.is_(None)
        ).first()

    def get_document_list(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[int] = None,
        sync_status: Optional[int] = None,
    ) -> KnowledgeDocListResponse:
        query = self.db.query(KnowledgeDoc).filter(KnowledgeDoc.deleted_at.is_(None))
        
        if keyword:
            query = query.filter(
                or_(
                    KnowledgeDoc.title.contains(keyword),
                    KnowledgeDoc.file_name.contains(keyword),
                    KnowledgeDoc.description.contains(keyword),
                )
            )
        
        if category:
            query = query.filter(KnowledgeDoc.category == category)
        
        if status is not None:
            query = query.filter(KnowledgeDoc.status == status)
        
        if sync_status is not None:
            query = query.filter(KnowledgeDoc.sync_status == sync_status)
        
        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        
        offset = (page - 1) * page_size
        docs = query.order_by(KnowledgeDoc.created_at.desc()).offset(offset).limit(page_size).all()
        
        return KnowledgeDocListResponse(
            items=[KnowledgeDocResponse.model_validate(doc) for doc in docs],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def create_document(
        self,
        file_content: bytes,
        original_filename: str,
        doc_data: KnowledgeDocCreate,
        created_by: int,
    ) -> Tuple[Optional[KnowledgeDoc], str]:
        if not self._file_handler:
            return None, "File handler not initialized"
        
        if not self._sync_service.is_file_type_allowed(original_filename):
            allowed = self._sync_service.get_allowed_types()
            return None, f"File type not allowed. Allowed types: {', '.join(allowed)}"
        
        max_size = self._sync_service.get_max_file_size()
        if len(file_content) > max_size:
            return None, f"File too large. Max size: {max_size / 1024 / 1024} MB"
        
        existing = self.db.query(KnowledgeDoc).filter(
            KnowledgeDoc.title == doc_data.title,
            KnowledgeDoc.deleted_at.is_(None)
        ).first()
        if existing:
            return None, f"Document with title '{doc_data.title}' already exists"
        
        try:
            file_info = self._file_handler.save_file(file_content, original_filename)
        except Exception as e:
            return None, f"Failed to save file: {str(e)}"
        
        doc = KnowledgeDoc(
            title=doc_data.title,
            file_name=file_info["original_filename"],
            file_path=file_info["relative_path"],
            file_size=file_info["file_size"],
            file_type=file_info["file_type"],
            mime_type=file_info["mime_type"],
            content_hash=file_info["content_hash"],
            status=1,
            sync_status=0,
            description=doc_data.description,
            tags=doc_data.tags if doc_data.tags else [],
            category=doc_data.category,
            created_by=created_by,
            is_public=doc_data.is_public,
        )
        
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        
        sync_message = "Uploaded successfully, not synced to Hermes"
        if self._sync_service.should_auto_sync():
            success, message = self._sync_service.sync_document(doc)
            if success:
                sync_message = "Uploaded and synced to Hermes successfully"
            else:
                sync_message = f"Uploaded but failed to sync to Hermes: {message}"
        
        return doc, sync_message

    def update_document(
        self,
        doc_id: int,
        update_data: KnowledgeDocUpdate,
        user_id: int,
        is_admin: bool = False,
    ) -> Tuple[Optional[KnowledgeDoc], str]:
        doc = self.get_document_by_id(doc_id)
        if not doc:
            return None, "Document not found"
        
        if not is_admin and doc.created_by != user_id:
            return None, "No permission to update this document"
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(doc, key, value)
        
        self.db.commit()
        self.db.refresh(doc)
        
        return doc, "Document updated successfully"

    def delete_document(
        self,
        doc_id: int,
        user_id: int,
        is_admin: bool = False,
    ) -> Tuple[bool, str]:
        doc = self.get_document_by_id(doc_id)
        if not doc:
            return False, "Document not found"
        
        if not is_admin and doc.created_by != user_id:
            return False, "No permission to delete this document"
        
        self._sync_service.unsync_document(doc)
        
        if doc.file_path and self._file_handler:
            base_path = self._file_handler.base_path
            full_path = os.path.join(base_path, doc.file_path)
            self._file_handler.delete_file(full_path)
        
        doc.deleted_at = datetime.utcnow()
        self.db.commit()
        
        return True, "Document deleted successfully"

    def download_document(
        self,
        doc_id: int,
    ) -> Tuple[Optional[bytes], Optional[str], str]:
        doc = self.get_document_by_id(doc_id)
        if not doc:
            return None, None, "Document not found"
        
        if not doc.file_path or not self._file_handler:
            return None, None, "Document file not found"
        
        base_path = self._file_handler.base_path
        full_path = os.path.join(base_path, doc.file_path)
        
        if not os.path.exists(full_path):
            return None, None, "Document file not found on disk"
        
        try:
            file_content = self._file_handler.read_file(full_path)
            return file_content, doc.mime_type, doc.file_name
        except Exception as e:
            return None, None, f"Failed to read file: {str(e)}"

    def sync_document(
        self,
        doc_id: int,
    ) -> Tuple[bool, str]:
        doc = self.get_document_by_id(doc_id)
        if not doc:
            return False, "Document not found"
        
        return self._sync_service.resync_document(doc)

    def get_categories(self) -> List[str]:
        categories = self.db.query(KnowledgeDoc.category).filter(
            KnowledgeDoc.deleted_at.is_(None),
            KnowledgeDoc.category.isnot(None),
            KnowledgeDoc.category != ""
        ).distinct().all()
        
        return [c[0] for c in categories if c[0]]

    def can_edit(self, doc: KnowledgeDoc, user: User) -> bool:
        if user.is_super_admin:
            return True
        return doc.created_by == user.id

    def can_delete(self, doc: KnowledgeDoc, user: User) -> bool:
        if user.is_super_admin:
            return True
        return doc.created_by == user.id
