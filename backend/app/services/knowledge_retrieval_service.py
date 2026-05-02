import re
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import KnowledgeDoc
from app.utils import FileHandler
from app.config import settings
from app.services.knowledge_config_service import KnowledgeConfigService


class KnowledgeRetrievalService:
    """
    知识检索服务
    负责从知识库中检索与用户问题相关的内容
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._config_service: Optional[KnowledgeConfigService] = None
        self._file_handler: Optional[FileHandler] = None
        self._init_config_service()
        self._init_file_handler()
    
    def _init_config_service(self) -> None:
        self._config_service = KnowledgeConfigService(self.db)
    
    def _init_file_handler(self) -> None:
        if self._config_service:
            base_path = self._config_service.get_storage_base_path()
        else:
            base_path = settings.KNOWLEDGE_BASE_PATH
        self._file_handler = FileHandler(base_path)
    
    @property
    def file_handler(self) -> FileHandler:
        if self._file_handler is None:
            self._init_file_handler()
        return self._file_handler
    
    def retrieve(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        max_results: int = 5,
        include_content: bool = True
    ) -> List[Dict[str, Any]]:
        """
        检索与查询相关的知识文档
        
        Args:
            query: 用户查询文本
            categories: 限制检索的知识分类列表（为空则检索全部）
            max_results: 最大返回结果数
            include_content: 是否包含文档内容
        
        Returns:
            相关文档列表，按相关性排序
        """
        if not query or not query.strip():
            return []
        
        keywords = self._extract_keywords(query)
        if not keywords:
            return []
        
        query_builder = self.db.query(KnowledgeDoc).filter(
            KnowledgeDoc.deleted_at.is_(None),
            KnowledgeDoc.is_public == True
        )
        
        if categories and len(categories) > 0:
            query_builder = query_builder.filter(
                KnowledgeDoc.category.in_(categories)
            )
        
        or_conditions = []
        for keyword in keywords:
            or_conditions.append(KnowledgeDoc.title.contains(keyword))
            or_conditions.append(KnowledgeDoc.description.contains(keyword))
            or_conditions.append(KnowledgeDoc.file_name.contains(keyword))
        
        if or_conditions:
            query_builder = query_builder.filter(or_(*or_conditions))
        
        docs = query_builder.limit(max_results * 2).all()
        
        scored_docs = []
        for doc in docs:
            score = self._calculate_relevance_score(doc, keywords)
            if score > 0:
                scored_docs.append((doc, score))
        
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for doc, score in scored_docs[:max_results]:
            doc_dict = {
                "id": doc.id,
                "title": doc.title,
                "file_name": doc.file_name,
                "category": doc.category,
                "description": doc.description,
                "tags": doc.tags,
                "relevance_score": score,
            }
            
            if include_content and doc.is_text_file():
                try:
                    if self._file_handler:
                        content = self._file_handler.read_file_as_text(doc.file_path)
                        doc_dict["content"] = self._extract_relevant_snippets(content, keywords)
                        doc_dict["full_content"] = content
                except Exception:
                    doc_dict["content"] = None
            
            results.append(doc_dict)
        
        return results
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词
        使用简单的规则提取：
        1. 去掉停用词
        2. 保留有意义的名词和动词
        """
        stopwords = {
            "的", "了", "是", "在", "有", "和", "与", "或", "及",
            "我", "你", "他", "她", "它", "们",
            "这", "那", "哪", "谁", "什么", "怎么", "如何", "为什么",
            "做", "帮", "给", "要", "想", "需要", "可以", "应该",
            "一个", "一份", "一些", "关于", "对于",
            "PPT", "ppt", "页", "份",
        }
        
        words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', text)
        
        keywords = []
        for word in words:
            if word.lower() not in stopwords and len(word) >= 2:
                keywords.append(word)
        
        if not keywords and len(text) >= 2:
            keywords.append(text[:10])
        
        return list(set(keywords))
    
    def _calculate_relevance_score(self, doc: KnowledgeDoc, keywords: List[str]) -> float:
        """
        计算文档与关键词的相关性分数
        """
        score = 0.0
        text_to_search = (
            (doc.title or "") + " " +
            (doc.description or "") + " " +
            (doc.file_name or "")
        )
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            title_lower = (doc.title or "").lower()
            desc_lower = (doc.description or "").lower()
            
            if keyword_lower in title_lower:
                score += 3.0
            
            if keyword_lower in desc_lower:
                score += 1.5
            
            if keyword_lower in text_to_search.lower():
                score += 0.5
        
        return score
    
    def _extract_relevant_snippets(self, content: str, keywords: List[str], max_snippets: int = 3) -> str:
        """
        从文档内容中提取与关键词相关的片段
        """
        if not content:
            return ""
        
        lines = content.split('\n')
        relevant_lines = []
        
        for i, line in enumerate(lines):
            for keyword in keywords:
                if keyword.lower() in line.lower():
                    snippet_start = max(0, i - 2)
                    snippet_end = min(len(lines), i + 3)
                    snippet = '\n'.join(lines[snippet_start:snippet_end])
                    relevant_lines.append(snippet)
                    break
        
        if not relevant_lines:
            return content[:500] + ("..." if len(content) > 500 else "")
        
        return '\n\n---\n\n'.join(relevant_lines[:max_snippets])
    
    def get_knowledge_context(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        max_docs: int = 3
    ) -> Dict[str, Any]:
        """
        获取知识上下文，用于生成提示词
        
        Returns:
            {
                "has_knowledge": bool,
                "knowledge_text": str,
                "sources": list,
                "categories_used": list
            }
        """
        results = self.retrieve(
            query=query,
            categories=categories,
            max_results=max_docs,
            include_content=True
        )
        
        if not results:
            return {
                "has_knowledge": False,
                "knowledge_text": "",
                "sources": [],
                "categories_used": categories or []
            }
        
        knowledge_parts = []
        sources = []
        
        for i, doc in enumerate(results, 1):
            source_info = {
                "id": doc["id"],
                "title": doc["title"],
                "category": doc["category"]
            }
            sources.append(source_info)
            
            part = f"【参考资料 {i}】{doc['title']}"
            if doc["category"]:
                part += f"（分类：{doc['category']}）"
            part += "\n"
            
            if doc.get("content"):
                part += doc["content"]
            elif doc.get("full_content"):
                part += doc["full_content"][:1000]
            
            knowledge_parts.append(part)
        
        knowledge_text = "\n\n".join(knowledge_parts)
        
        return {
            "has_knowledge": True,
            "knowledge_text": knowledge_text,
            "sources": sources,
            "categories_used": categories or []
        }
    
    def format_output_with_knowledge(
        self,
        base_output: str,
        knowledge_context: Dict[str, Any],
        topic: Optional[str] = None
    ) -> str:
        """
        将知识上下文整合到输出中
        如果有知识库内容，标注来源；如果没有，说明是通用建议
        """
        output = base_output
        
        if knowledge_context.get("has_knowledge"):
            sources = knowledge_context.get("sources", [])
            if sources:
                output += "\n\n---\n\n📚 参考依据："
                for i, source in enumerate(sources, 1):
                    ref = f"\n{i}. 《{source['title']}》"
                    if source.get("category"):
                        ref += f"（{source['category']}）"
                    output += ref
        else:
            output += "\n\n---\n\n⚠️ 说明："
            if topic:
                output += f"关于「{topic}」"
            else:
                output += "本内容"
            output += "未找到企业知识库中的相关资料，以上为通用建议。"
            output += "\n如需更贴合企业实际的内容，请上传相关资料到知识库。"
        
        return output
