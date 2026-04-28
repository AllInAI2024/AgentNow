import os
import math
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import KnowledgeDoc, User
from app.schemas import (
    KnowledgeDocCreate,
    KnowledgeDocUpdate,
    KnowledgeDocResponse,
    KnowledgeDocDetailResponse,
    KnowledgeDocListResponse,
)
from app.utils import FileHandler
from app.config import settings


class KnowledgeService:
    def __init__(self, db: Session):
        self.db = db
        self._file_handler: Optional[FileHandler] = None
        self._init_file_handler()

    def _init_file_handler(self) -> None:
        base_path = settings.KNOWLEDGE_BASE_PATH
        self._file_handler = FileHandler(base_path)

    @property
    def file_handler(self) -> FileHandler:
        if self._file_handler is None:
            self._init_file_handler()
        return self._file_handler

    def get_document_by_id(self, doc_id: int) -> Optional[KnowledgeDoc]:
        return self.db.query(KnowledgeDoc).filter(
            KnowledgeDoc.id == doc_id,
            KnowledgeDoc.deleted_at.is_(None)
        ).first()

    def get_document_by_path(self, relative_path: str) -> Optional[KnowledgeDoc]:
        return self.db.query(KnowledgeDoc).filter(
            KnowledgeDoc.file_path == relative_path,
            KnowledgeDoc.deleted_at.is_(None)
        ).first()

    def get_document_list(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        is_public: Optional[bool] = None,
        created_by: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
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
        
        if tag:
            query = query.filter(KnowledgeDoc.tags.contains(tag))
        
        if is_public is not None:
            query = query.filter(KnowledgeDoc.is_public == is_public)
        
        if created_by:
            query = query.filter(KnowledgeDoc.created_by == created_by)
        
        sort_column = getattr(KnowledgeDoc, sort_by, KnowledgeDoc.created_at)
        if sort_order.lower() == "desc":
            sort_column = sort_column.desc()
        
        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        
        offset = (page - 1) * page_size
        docs = query.order_by(sort_column).offset(offset).limit(page_size).all()
        
        return KnowledgeDocListResponse(
            items=[KnowledgeDocResponse.model_validate(doc) for doc in docs],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_document_detail(self, doc_id: int, include_content: bool = False) -> Tuple[Optional[KnowledgeDocDetailResponse], str]:
        doc = self.get_document_by_id(doc_id)
        if not doc:
            return None, "文档不存在"
        
        content = None
        if include_content and doc.is_text_file():
            try:
                if self._file_handler:
                    content = self._file_handler.read_file_as_text(doc.file_path)
            except Exception:
                pass
        
        response = KnowledgeDocDetailResponse.model_validate(doc)
        if content:
            response.content = content
        
        return response, "获取成功"

    def _is_file_type_allowed(self, filename: str) -> bool:
        allowed_types = settings.KNOWLEDGE_ALLOWED_TYPES.split(',')
        allowed_types = [t.strip().lower() for t in allowed_types if t.strip()]
        
        ext = os.path.splitext(filename)[1].lower()
        return ext in allowed_types if allowed_types else True

    def _is_file_size_allowed(self, file_size: int) -> bool:
        return file_size <= settings.KNOWLEDGE_MAX_FILE_SIZE

    def create_document(
        self,
        file_content: bytes,
        original_filename: str,
        doc_data: KnowledgeDocCreate,
        created_by: int,
    ) -> Tuple[Optional[KnowledgeDoc], str]:
        if not self._file_handler:
            return None, "文件处理器未初始化"
        
        if not self._is_file_type_allowed(original_filename):
            allowed = settings.KNOWLEDGE_ALLOWED_TYPES
            return None, f"不允许的文件类型。允许的类型：{allowed}"
        
        if not self._is_file_size_allowed(len(file_content)):
            max_mb = settings.KNOWLEDGE_MAX_FILE_SIZE / 1024 / 1024
            return None, f"文件太大。最大允许：{max_mb} MB"
        
        existing = self.db.query(KnowledgeDoc).filter(
            KnowledgeDoc.title == doc_data.title,
            KnowledgeDoc.deleted_at.is_(None)
        ).first()
        if existing:
            return None, f"标题为 '{doc_data.title}' 的文档已存在"
        
        try:
            file_info = self._file_handler.save_file(
                file_content=file_content,
                original_filename=original_filename,
                category=doc_data.category,
                force_unique=True
            )
        except Exception as e:
            return None, f"保存文件失败：{str(e)}"
        
        doc = KnowledgeDoc(
            title=doc_data.title,
            file_name=file_info["final_filename"],
            file_path=file_info["relative_path"],
            file_size=file_info["file_size"],
            file_type=file_info["file_type"],
            mime_type=file_info["mime_type"],
            content_hash=file_info["content_hash"],
            description=doc_data.description,
            tags=doc_data.tags if doc_data.tags else [],
            category=doc_data.category,
            created_by=created_by,
            updated_by=created_by,
            is_public=doc_data.is_public,
            word_count=file_info.get("word_count"),
            file_modified_at=file_info.get("file_modified_at"),
        )
        
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        
        return doc, "上传成功"

    def create_markdown_document(
        self,
        content: str,
        filename: str,
        doc_data: KnowledgeDocCreate,
        created_by: int,
    ) -> Tuple[Optional[KnowledgeDoc], str]:
        if not filename.endswith('.md'):
            filename = f"{filename}.md"
        
        file_content = content.encode('utf-8')
        
        return self.create_document(
            file_content=file_content,
            original_filename=filename,
            doc_data=doc_data,
            created_by=created_by,
        )

    def update_document(
        self,
        doc_id: int,
        update_data: KnowledgeDocUpdate,
        user_id: int,
        is_admin: bool = False,
    ) -> Tuple[Optional[KnowledgeDoc], str]:
        doc = self.get_document_by_id(doc_id)
        if not doc:
            return None, "文档不存在"
        
        if not is_admin and doc.created_by != user_id:
            return None, "无权限编辑此文档"
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(doc, key, value)
        
        doc.updated_by = user_id
        
        self.db.commit()
        self.db.refresh(doc)
        
        return doc, "更新成功"

    def update_document_content(
        self,
        doc_id: int,
        content: str,
        user_id: int,
        is_admin: bool = False,
    ) -> Tuple[Optional[KnowledgeDoc], str]:
        doc = self.get_document_by_id(doc_id)
        if not doc:
            return None, "文档不存在"
        
        if not is_admin and doc.created_by != user_id:
            return None, "无权限编辑此文档"
        
        if not doc.is_text_file():
            return None, "只能编辑文本类型文件"
        
        if not self._file_handler:
            return None, "文件处理器未初始化"
        
        try:
            file_content = content.encode('utf-8')
            file_info = self._file_handler.update_file_content(
                relative_path=doc.file_path,
                content=file_content,
            )
        except Exception as e:
            return None, f"更新文件内容失败：{str(e)}"
        
        doc.file_size = file_info["file_size"]
        doc.content_hash = file_info["content_hash"]
        doc.word_count = file_info.get("word_count")
        doc.file_modified_at = file_info.get("file_modified_at")
        doc.updated_by = user_id
        
        self.db.commit()
        self.db.refresh(doc)
        
        return doc, "内容更新成功"

    def delete_document(
        self,
        doc_id: int,
        user_id: int,
        is_admin: bool = False,
        hard_delete: bool = False,
    ) -> Tuple[bool, str]:
        doc = self.get_document_by_id(doc_id)
        if not doc:
            return False, "文档不存在"
        
        if not is_admin and doc.created_by != user_id:
            return False, "无权限删除此文档"
        
        if self._file_handler:
            try:
                self._file_handler.delete_file(doc.file_path)
            except Exception:
                pass
        
        if hard_delete:
            self.db.delete(doc)
        else:
            doc.deleted_at = datetime.utcnow()
        
        self.db.commit()
        
        return True, "删除成功"

    def download_document(
        self,
        doc_id: int,
    ) -> Tuple[Optional[bytes], Optional[str], str]:
        doc = self.get_document_by_id(doc_id)
        if not doc:
            return None, None, "文档不存在"
        
        if not doc.file_path or not self._file_handler:
            return None, None, "文档文件不存在"
        
        try:
            file_content = self._file_handler.read_file(doc.file_path)
            return file_content, doc.mime_type, doc.file_name
        except Exception as e:
            return None, None, f"读取文件失败：{str(e)}"

    def get_all_categories(self) -> List[str]:
        results = self.db.query(KnowledgeDoc.category).filter(
            KnowledgeDoc.deleted_at.is_(None),
            KnowledgeDoc.category.isnot(None),
            KnowledgeDoc.category != ""
        ).distinct().all()
        
        categories = [r[0] for r in results if r[0]]
        return sorted(categories)

    def get_all_tags(self) -> List[str]:
        results = self.db.query(KnowledgeDoc.tags).filter(
            KnowledgeDoc.deleted_at.is_(None),
            KnowledgeDoc.tags.isnot(None),
        ).all()
        
        all_tags = set()
        for (tags,) in results:
            if tags:
                for tag in tags:
                    if tag:
                        all_tags.add(tag)
        
        return sorted(list(all_tags))

    def get_statistics(self) -> Dict[str, Any]:
        total_docs = self.db.query(KnowledgeDoc).filter(
            KnowledgeDoc.deleted_at.is_(None)
        ).count()
        
        public_docs = self.db.query(KnowledgeDoc).filter(
            KnowledgeDoc.deleted_at.is_(None),
            KnowledgeDoc.is_public == True
        ).count()
        
        from datetime import timedelta
        recent_docs = self.db.query(KnowledgeDoc).filter(
            KnowledgeDoc.deleted_at.is_(None),
            KnowledgeDoc.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        categories = self.get_all_categories()
        tags = self.get_all_tags()
        
        total_size = 0
        docs = self.db.query(KnowledgeDoc).filter(
            KnowledgeDoc.deleted_at.is_(None)
        ).all()
        for doc in docs:
            if doc.file_size:
                total_size += doc.file_size
        
        return {
            "total_docs": total_docs,
            "total_size": total_size,
            "total_categories": len(categories),
            "total_tags": len(tags),
            "public_docs": public_docs,
            "recent_uploads": recent_docs,
        }

    def get_storage_info(self) -> Optional[Dict[str, Any]]:
        if not self._file_handler:
            return None
        return self._file_handler.get_storage_stats()

    def can_edit(self, doc: KnowledgeDoc, user: User) -> bool:
        if user.is_super_admin:
            return True
        return doc.created_by == user.id

    def can_delete(self, doc: KnowledgeDoc, user: User) -> bool:
        if user.is_super_admin:
            return True
        return doc.created_by == user.id
