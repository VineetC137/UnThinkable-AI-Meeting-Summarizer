"""
File handling utilities for meeting audio files.
"""

import os
import hashlib
import magic
from typing import Tuple, Optional
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FileHandler:
    """Utility class for file operations."""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
        self.logger = logger
        
    def validate_file_type(self, file_path: str) -> bool:
        """Validate file type using python-magic."""
        try:
            mime_type = magic.from_file(file_path, mime=True)
            
            # Audio MIME types
            valid_audio_types = {
                'audio/mpeg',        # MP3
                'audio/wav',         # WAV
                'audio/wave',        # WAV alternative
                'audio/x-wav',       # WAV alternative
                'audio/mp4',         # M4A
                'audio/x-m4a',       # M4A alternative
                'audio/ogg',         # OGG
                'audio/vorbis',      # OGG Vorbis
                'audio/flac',        # FLAC
                'audio/x-flac',      # FLAC alternative
                'audio/aac',         # AAC
                'audio/x-aac',       # AAC alternative
            }
            
            return mime_type in valid_audio_types
            
        except Exception as e:
            self.logger.error(f"Error validating file type: {e}")
            return False
    
    def get_file_hash(self, file_path: str) -> str:
        """Generate SHA256 hash of file."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Error generating file hash: {e}")
            return ""
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Replace potentially dangerous characters
        dangerous_chars = '<>:"/\\|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def get_safe_file_path(self, original_filename: str, user_id: int) -> str:
        """Generate safe file path for storage."""
        # Sanitize filename
        safe_filename = self.sanitize_filename(original_filename)
        
        # Add user ID prefix and timestamp for uniqueness
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        name, ext = os.path.splitext(safe_filename)
        unique_filename = f"{user_id}_{timestamp}_{name}{ext}"
        
        return str(self.upload_dir / unique_filename)
    
    def cleanup_file(self, file_path: str) -> bool:
        """Safely delete a file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_size_human(self, size_bytes: int) -> str:
        """Convert bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def check_disk_space(self, required_bytes: int) -> bool:
        """Check if enough disk space is available."""
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.upload_dir)
            return free >= required_bytes
        except Exception as e:
            self.logger.error(f"Error checking disk space: {e}")
            return True  # Assume we have space if we can't check


# Global instance
file_handler = FileHandler()