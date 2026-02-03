import os
import datetime
from pathlib import Path

# Windows specific for shortcuts
try:
    import win32com.client
    import pythoncom
    HAS_PYWIN32 = True
except ImportError:
    HAS_PYWIN32 = False

class FileProcessor:
    def __init__(self, config):
        self.config = config
        self.max_file_size = config.get("max_file_size_mb", 50) * 1024 * 1024

    def get_metadata(self, file_path):
        path = Path(file_path)
        if not path.exists():
            return None

        stat = path.stat()
        metadata = {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "created_at": datetime.datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d'),
            "size_bytes": stat.st_size,
            "path": str(path.absolute()),
            "is_directory": path.is_dir()
        }

        # Resolve shortcuts on Windows
        if HAS_PYWIN32 and path.suffix.lower() == '.lnk':
            try:
                pythoncom.CoInitialize()
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(str(path.absolute()))
                metadata["shortcut_target"] = shortcut.Targetpath
            except Exception:
                pass
            finally:
                pythoncom.CoUninitialize()

        return metadata

    def extract_excerpt(self, file_path):
        path = Path(file_path)
        if not path.exists():
            return ""

        # Skip if too large
        if path.stat().st_size > self.max_file_size:
            return ""

        # Only try to read text from likely text files
        text_extensions = {'.txt', '.md', '.csv', '.json', '.xml', '.logger', '.log'}
        if path.suffix.lower() not in text_extensions:
             # Basic support for reading the beginning of a file as a fallback, 
             # but keeping it safe (binary files might output garbage)
             return ""

        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(1000) # Read first 1000 chars
        except Exception:
            return ""
