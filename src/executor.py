import shutil
import json
import os
from pathlib import Path
from datetime import datetime
from src.utils import setup_logging

logger = setup_logging()

class ActionExecutor:
    def __init__(self, config):
        self.config = config
        self.undo_log_path = Path("undo_log.json")
        self.safe_root = Path(config.get("safe_root", "C:/Users/Velix/Documents"))

    def _load_undo_log(self):
        if self.undo_log_path.exists():
            try:
                with open(self.undo_log_path, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_undo_log(self, log):
        with open(self.undo_log_path, 'w') as f:
            json.dump(log, f, indent=2)

    def move_file(self, source, destination_folder, new_filename):
        source_path = Path(source)
        dest_folder_path = self.safe_root / destination_folder
        
        # Ensure strict unique filename to prevent overwrites
        base_name = Path(new_filename).stem
        extension = Path(new_filename).suffix
        dest_path = dest_folder_path / new_filename
        
        counter = 1
        while dest_path.exists():
             unique_name = f"{base_name}_{counter}{extension}"
             dest_path = dest_folder_path / unique_name
             counter += 1

        try:
            # Create destination folder if it doesn't exist
            dest_folder_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Moving {source_path} -> {dest_path}")
            shutil.move(str(source_path), str(dest_path))
            
            # Log for undo
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "original_path": str(source_path),
                "new_path": str(dest_path),
                "action": "move"
            }
            log = self._load_undo_log()
            log.append(log_entry)
            self._save_undo_log(log)
            
            return str(dest_path)
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            return None

    def undo_last_action(self):
        log = self._load_undo_log()
        if not log:
            return None

        # Pop the last action
        last_action = log.pop()
        
        original_path = Path(last_action["original_path"])
        current_path = Path(last_action["new_path"])
        
        if not current_path.exists():
            logger.error(f"Cannot undo: File {current_path} no longer exists.")
            return None
            
        try:
            # Move back
            logger.info(f"Undoing: {current_path} -> {original_path}")
            shutil.move(str(current_path), str(original_path))
            
            # Save updated log
            self._save_undo_log(log)
            return str(original_path)
        except Exception as e:
            logger.error(f"Failed to undo: {e}")
            return None
