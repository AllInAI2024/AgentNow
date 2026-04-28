import os
import hashlib
import shutil
import re
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
from pathlib import Path

import mimetypes


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def calculate_content_hash(content: bytes, algorithm: str = "sha256") -> str:
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(content)
    return hash_obj.hexdigest()


def get_file_extension(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return ext


def get_mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def get_safe_filename(filename: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', '_', filename)
    return safe.strip()


def is_text_file(filename: str) -> bool:
    ext = get_file_extension(filename).lstrip('.')
    text_exts = {'txt', 'md', 'json', 'csv', 'xml', 'html', 'htm', 'css', 'js', 'py', 'java', 'c', 'cpp', 'h', 'sh', 'bat', 'cmd', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf', 'log'}
    return ext in text_exts


def is_markdown_file(filename: str) -> bool:
    return get_file_extension(filename).lower() == '.md'


def count_words(text: str) -> int:
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    return chinese_chars + english_words


class FileHandler:
    def __init__(self, base_path: str):
        self.base_path = os.path.abspath(os.path.expanduser(base_path))
        self._ensure_directory_exists(self.base_path)

    def _ensure_directory_exists(self, path: str) -> None:
        abs_path = os.path.abspath(os.path.expanduser(path))
        if not os.path.exists(abs_path):
            os.makedirs(abs_path, exist_ok=True)

    def _get_unique_filename(self, original_filename: str, existing_files: Optional[List[str]] = None) -> str:
        safe_name = get_safe_filename(original_filename)
        name, ext = os.path.splitext(safe_name)
        
        if existing_files is None:
            existing_files = []
        
        if safe_name not in existing_files:
            return safe_name
        
        counter = 1
        while True:
            new_name = f"{name}_{counter}{ext}"
            if new_name not in existing_files:
                return new_name
            counter += 1

    def get_full_path(self, relative_path: str) -> str:
        return os.path.join(self.base_path, relative_path)

    def get_relative_path(self, full_path: str) -> str:
        return os.path.relpath(full_path, self.base_path)

    def save_file(
        self, 
        file_content: bytes, 
        original_filename: str,
        category: Optional[str] = None,
        force_unique: bool = True
    ) -> Dict[str, Any]:
        safe_name = get_safe_filename(original_filename)
        ext = get_file_extension(original_filename)
        
        if category:
            safe_category = get_safe_filename(category).strip()
            if safe_category:
                relative_dir = safe_category
            else:
                relative_dir = ""
        else:
            relative_dir = ""
        
        full_dir = os.path.join(self.base_path, relative_dir)
        self._ensure_directory_exists(full_dir)
        
        if force_unique:
            existing_files = os.listdir(full_dir) if os.path.exists(full_dir) else []
            final_name = self._get_unique_filename(safe_name, existing_files)
        else:
            final_name = safe_name
        
        if relative_dir:
            relative_path = os.path.join(relative_dir, final_name)
        else:
            relative_path = final_name
        
        full_path = os.path.join(self.base_path, relative_path)
        
        with open(full_path, "wb") as f:
            f.write(file_content)
        
        file_size = os.path.getsize(full_path)
        content_hash = calculate_file_hash(full_path)
        mime_type = get_mime_type(original_filename)
        
        word_count = None
        if is_text_file(original_filename):
            try:
                text_content = file_content.decode('utf-8')
                word_count = count_words(text_content)
            except Exception:
                pass
        
        file_modified_at = datetime.fromtimestamp(os.path.getmtime(full_path))
        
        return {
            "original_filename": original_filename,
            "final_filename": final_name,
            "relative_path": relative_path,
            "full_path": full_path,
            "file_size": file_size,
            "file_type": ext,
            "mime_type": mime_type,
            "content_hash": content_hash,
            "word_count": word_count,
            "file_modified_at": file_modified_at,
        }

    def update_file_content(
        self,
        relative_path: str,
        content: bytes,
    ) -> Dict[str, Any]:
        full_path = self.get_full_path(relative_path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {relative_path}")
        
        with open(full_path, "wb") as f:
            f.write(content)
        
        file_size = os.path.getsize(full_path)
        content_hash = calculate_content_hash(content)
        
        word_count = None
        filename = os.path.basename(relative_path)
        if is_text_file(filename):
            try:
                text_content = content.decode('utf-8')
                word_count = count_words(text_content)
            except Exception:
                pass
        
        file_modified_at = datetime.fromtimestamp(os.path.getmtime(full_path))
        
        return {
            "relative_path": relative_path,
            "full_path": full_path,
            "file_size": file_size,
            "content_hash": content_hash,
            "word_count": word_count,
            "file_modified_at": file_modified_at,
        }

    def read_file(self, relative_path: str) -> bytes:
        full_path = self.get_full_path(relative_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {relative_path}")
        with open(full_path, "rb") as f:
            return f.read()

    def read_file_as_text(self, relative_path: str, encoding: str = "utf-8") -> str:
        content = self.read_file(relative_path)
        return content.decode(encoding)

    def copy_file(self, source_path: str, dest_path: str) -> bool:
        try:
            source_full = self.get_full_path(source_path) if not os.path.isabs(source_path) else source_path
            dest_full = self.get_full_path(dest_path) if not os.path.isabs(dest_path) else dest_path
            
            dest_dir = os.path.dirname(dest_full)
            self._ensure_directory_exists(dest_dir)
            shutil.copy2(source_full, dest_full)
            return True
        except Exception:
            return False

    def move_file(self, source_path: str, dest_path: str) -> bool:
        try:
            source_full = self.get_full_path(source_path) if not os.path.isabs(source_path) else source_path
            dest_full = self.get_full_path(dest_path) if not os.path.isabs(dest_path) else dest_path
            
            dest_dir = os.path.dirname(dest_full)
            self._ensure_directory_exists(dest_dir)
            shutil.move(source_full, dest_full)
            return True
        except Exception:
            return False

    def delete_file(self, relative_path: str) -> bool:
        try:
            full_path = self.get_full_path(relative_path)
            if os.path.exists(full_path):
                os.remove(full_path)
            return True
        except Exception:
            return False

    def file_exists(self, relative_path: str) -> bool:
        full_path = self.get_full_path(relative_path)
        return os.path.exists(full_path)

    def get_file_info(self, relative_path: str) -> Optional[Dict[str, Any]]:
        full_path = self.get_full_path(relative_path)
        if not os.path.exists(full_path):
            return None
        
        stat = os.stat(full_path)
        filename = os.path.basename(relative_path)
        
        return {
            "relative_path": relative_path,
            "full_path": full_path,
            "filename": filename,
            "file_size": stat.st_size,
            "file_type": get_file_extension(filename),
            "mime_type": get_mime_type(filename),
            "created_at": datetime.fromtimestamp(stat.st_ctime),
            "modified_at": datetime.fromtimestamp(stat.st_mtime),
            "is_text": is_text_file(filename),
            "is_markdown": is_markdown_file(filename),
        }

    def list_directory(self, directory: str = "") -> List[Dict[str, Any]]:
        full_dir = self.get_full_path(directory)
        if not os.path.exists(full_dir):
            return []
        
        results = []
        for name in os.listdir(full_dir):
            if name.startswith('.'):
                continue
            
            full_path = os.path.join(full_dir, name)
            relative_path = os.path.join(directory, name) if directory else name
            
            if os.path.isdir(full_path):
                results.append({
                    "name": name,
                    "relative_path": relative_path,
                    "type": "directory",
                })
            else:
                info = self.get_file_info(relative_path)
                if info:
                    info["type"] = "file"
                    results.append(info)
        
        return results

    def get_storage_stats(self) -> Dict[str, Any]:
        total_size = 0
        total_files = 0
        total_dirs = 0
        
        for root, dirs, files in os.walk(self.base_path):
            total_dirs += len(dirs)
            for filename in files:
                if filename.startswith('.'):
                    continue
                filepath = os.path.join(root, filename)
                if os.path.isfile(filepath):
                    total_files += 1
                    total_size += os.path.getsize(filepath)
        
        try:
            statvfs = os.statvfs(self.base_path)
            free_space = statvfs.f_frsize * statvfs.f_bavail
        except Exception:
            free_space = 0
        
        return {
            "base_path": self.base_path,
            "total_files": total_files,
            "total_directories": total_dirs,
            "total_size": total_size,
            "free_space": free_space,
        }
