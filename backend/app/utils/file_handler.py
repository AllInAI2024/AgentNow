import os
import hashlib
import shutil
import uuid
from typing import Optional, Tuple
from datetime import datetime
from pathlib import Path

import mimetypes


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def get_file_extension(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return ext


def get_mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


class FileHandler:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self._ensure_directory_exists(base_path)

    def _ensure_directory_exists(self, path: str) -> None:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    def _get_unique_filename(self, original_filename: str) -> Tuple[str, str]:
        ext = get_file_extension(original_filename)
        unique_name = f"{uuid.uuid4().hex}{ext}"
        return unique_name, ext

    def _get_date_path(self) -> str:
        now = datetime.now()
        return f"{now.year}/{now.month:02d}/{now.day:02d}"

    def save_file(
        self, 
        file_content: bytes, 
        original_filename: str,
        subdirectory: Optional[str] = None
    ) -> dict:
        unique_name, ext = self._get_unique_filename(original_filename)
        
        if subdirectory:
            relative_dir = os.path.join(subdirectory, self._get_date_path())
        else:
            relative_dir = self._get_date_path()
        
        full_dir = os.path.join(self.base_path, relative_dir)
        self._ensure_directory_exists(full_dir)
        
        relative_path = os.path.join(relative_dir, unique_name)
        full_path = os.path.join(self.base_path, relative_path)
        
        with open(full_path, "wb") as f:
            f.write(file_content)
        
        file_size = os.path.getsize(full_path)
        content_hash = calculate_file_hash(full_path)
        mime_type = get_mime_type(original_filename)
        
        return {
            "original_filename": original_filename,
            "unique_filename": unique_name,
            "relative_path": relative_path,
            "full_path": full_path,
            "file_size": file_size,
            "file_type": ext,
            "mime_type": mime_type,
            "content_hash": content_hash,
        }

    def copy_file(self, source_path: str, dest_path: str) -> bool:
        try:
            dest_dir = os.path.dirname(dest_path)
            self._ensure_directory_exists(dest_dir)
            shutil.copy2(source_path, dest_path)
            return True
        except Exception:
            return False

    def move_file(self, source_path: str, dest_path: str) -> bool:
        try:
            dest_dir = os.path.dirname(dest_path)
            self._ensure_directory_exists(dest_dir)
            shutil.move(source_path, dest_path)
            return True
        except Exception:
            return False

    def delete_file(self, file_path: str) -> bool:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception:
            return False

    def file_exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)

    def get_file_size(self, file_path: str) -> int:
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0

    def read_file(self, file_path: str) -> bytes:
        with open(file_path, "rb") as f:
            return f.read()


class HermesFileHandler(FileHandler):
    def __init__(self, base_path: str, hermes_workspace_path: str):
        super().__init__(base_path)
        self.hermes_workspace_path = os.path.expanduser(hermes_workspace_path)
        self._ensure_directory_exists(self.hermes_workspace_path)

    def sync_to_hermes(self, source_path: str, dest_filename: str) -> Tuple[bool, str]:
        try:
            dest_path = os.path.join(self.hermes_workspace_path, dest_filename)
            success = self.copy_file(source_path, dest_path)
            relative_dest = os.path.relpath(dest_path, self.hermes_workspace_path)
            return success, relative_dest
        except Exception as e:
            return False, str(e)

    def delete_from_hermes(self, relative_path: str) -> bool:
        full_path = os.path.join(self.hermes_workspace_path, relative_path)
        return self.delete_file(full_path)

    def list_hermes_files(self) -> list:
        files = []
        if os.path.exists(self.hermes_workspace_path):
            for filename in os.listdir(self.hermes_workspace_path):
                filepath = os.path.join(self.hermes_workspace_path, filename)
                if os.path.isfile(filepath):
                    files.append({
                        "filename": filename,
                        "size": os.path.getsize(filepath),
                        "modified": datetime.fromtimestamp(os.path.getmtime(filepath)),
                    })
        return files
