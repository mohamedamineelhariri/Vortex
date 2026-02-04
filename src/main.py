import time
import yaml
import sys
import datetime
import json
from pathlib import Path

# Add project root to sys.path to allow running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.utils import setup_logging
from src.watcher import start_watcher
from src.processor import FileProcessor
from src.brain_client import BrainClient
from src.executor import ActionExecutor
from src.safety import SafetyChecker

logger = setup_logging()

def load_config(config_path="config.yaml"):
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        logger.info("Configuration loaded successfully.")
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return None

class AntigravitySystem:
    def __init__(self, config):
        self.config = config
        self.processor = FileProcessor(config)
        self.brain = BrainClient(config)
        self.executor = ActionExecutor(config)
        self.safety = SafetyChecker(config)
        
        self.mode = config.get("mode", "observe")
        self.confidence_threshold = config.get("confidence_threshold", 0.8)
        
        # Stats
        self.stats = {
            "files_processed": 0,
            "decisions_made": 0,
            "actions_taken": 0
        }
        
        # Pending Actions (Suggest Mode) - id: {data}
        self._action_counter = 0
        self.pending_actions = {}
        
        # Callbacks
        self.on_stats_change = None 
        self.on_pending_change = None # Called when pending list changes

    def set_mode(self, mode):
        if mode in ["observe", "suggest", "auto"]:
            self.mode = mode
            logger.info(f"Mode changed to: {self.mode}")

    def update_config(self, key, value):
        self.config[key] = value
        logger.info(f"Configuration updated: {key} = {value}")

    def undo_last(self):
        result = self.executor.undo_last_action()
        if result:
            logger.info(f"Undo successful. File restored to {result}")
        else:
             logger.warning("Undo failed or nothing to undo.")

    def approve_action(self, action_id):
        action = self.pending_actions.pop(action_id, None)
        if not action:
            return
        
        logger.info(f"Action {action_id} approved.")
        if self.on_pending_change:
            self.on_pending_change(self.pending_actions)
            
        # Execute
        source_path = action['source_path']
        is_shortcut = source_path.lower().endswith(".lnk")
        behavior = self.config.get("shortcuts_behavior", "move")

        if is_shortcut and behavior == "reposition":
            success = self.executor.reposition_icon(source_path, action.get('category', 'Other'))
            if success:
                logger.info(f"Action executed: Shortcut repositioned on Desktop.")
                self.stats["actions_taken"] += 1
                if self.on_stats_change:
                    self.on_stats_change(self.stats)
        else:
            new_path = self.executor.move_file(
                source_path, 
                action['target_folder'], 
                action['target_name']
            )
            if new_path:
                logger.info(f"Action executed: Moved to {new_path}")
                self.stats["actions_taken"] += 1
                if self.on_stats_change:
                    self.on_stats_change(self.stats)

    def reject_action(self, action_id):
        if self.pending_actions.pop(action_id, None):
            logger.info(f"Action {action_id} rejected.")
            if self.on_pending_change:
                self.on_pending_change(self.pending_actions)

    def on_file_event(self, file_path, override_mode=None):
        logger.info(f"Processing event for: {file_path}")
        
        # 1. Safety Check (Source)
        if not self.safety.is_safe_file(file_path):
            logger.info(f"Skipping unsafe or ignored file: {file_path}")
            return

        # 1.5 Type Filter (Files / Shortcuts / Folders)
        targets = self.config.get("organization_targets", {"files": True, "shortcuts": True, "folders": True})
        is_dir = Path(file_path).is_dir()
        is_shortcut = file_path.lower().endswith(".lnk")

        if is_dir and not targets.get("folders"):
            logger.info(f"Skipping folder: {file_path}")
            return
        if is_shortcut and not targets.get("shortcuts"):
            logger.info(f"Skipping shortcut: {file_path}")
            return
        if not is_dir and not is_shortcut and not targets.get("files"):
            logger.info(f"Skipping file: {file_path}")
            return

        self.stats["files_processed"] += 1
        if self.on_stats_change:
            self.on_stats_change(self.stats)

        # 2. Extract Context
        metadata = self.processor.get_metadata(file_path)
        excerpt = self.processor.extract_excerpt(file_path)
        
        if not metadata:
            return

        context = metadata
        context["text_excerpt"] = excerpt

        # 3. Ask Brain
        logger.info("Asking Brain for decision...")
        decision = self.brain.ask_brain(context)
        
        if not decision:
            logger.warning("No decision received from Brain.")
            return

        logger.info(f"Brain decision: {decision}")
        self.stats["decisions_made"] += 1
        if self.on_stats_change:
            self.on_stats_change(self.stats)

        # 4. Handle Decision based on Mode
        self._handle_decision(file_path, decision, override_mode)

    def _handle_decision(self, source_path, decision, override_mode=None):
        folder = decision.get("folder")
        suggested_name = decision.get("suggested_name")
        confidence = decision.get("confidence", 0.0)
        
        current_mode = override_mode if override_mode else self.mode

        logger.info(f"Evaluating decision (Confidence: {confidence}). Mode: {current_mode}")

        # Apply Naming Rules
        is_shortcut = source_path.lower().endswith(".lnk")
        target_folder = folder
        
        if is_shortcut:
            # Shortcut Branding: [Category]-Name.lnk
            category = decision.get("category", "Other")
            clean_name = suggested_name if suggested_name else Path(source_path).name
            if not clean_name.startswith("["):
                target_name = f"[{category}]-{clean_name}"
            else:
                target_name = clean_name
            
            # KEEP ON DESKTOP (Root of Safe Root)
            target_folder = "" 
        else:
            # Regular File Branding: [YYYY-MM-DD] Name
            creation_time = Path(source_path).stat().st_ctime
            date_str = datetime.datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d')
            date_prefix = f"[{date_str}] "
            
            if suggested_name and not suggested_name.startswith("["):
                target_name = f"{date_prefix}{suggested_name}"
            else:
                target_name = suggested_name if suggested_name else Path(source_path).name

        # Safety Check (Destination)
        if not self.safety.is_safe_action(source_path, str(Path(self.config["safe_root"]) / target_folder)):
             logger.error(f"Unsafe destination rejected: {target_folder}")
             return

        if current_mode == "observe":
            logger.info(f"[OBSERVE] Would move {source_path} -> {target_folder}/{target_name}")
            return

        if current_mode == "suggest":
            self._action_counter += 1
            action_id = self._action_counter
            
            # Format display path for UI
            display_target = f"{target_folder}/{target_name}"

            self.pending_actions[action_id] = {
                "id": action_id,
                "source_path": source_path,
                "target_folder": target_folder,
                "target_name": target_name,
                "display_target": display_target,
                "confidence": confidence,
                "category": decision.get("category", "Other"),
                "filename": Path(source_path).name
            }
            
            logger.info(f"[SUGGEST] Action {action_id} queued: {source_path} -> {display_target}")
            
            if self.on_pending_change:
                self.on_pending_change(self.pending_actions)
            return

        if current_mode == "auto":
            if confidence >= self.confidence_threshold:
                logger.info(f"[AUTO] Executing action...")
                
                is_shortcut = source_path.lower().endswith(".lnk")
                behavior = self.config.get("shortcuts_behavior", "move")

                if is_shortcut and behavior == "reposition":
                    success = self.executor.reposition_icon(source_path, decision.get("category", "Other"))
                    if success:
                         self.stats["actions_taken"] += 1
                else:
                    new_path = self.executor.move_file(source_path, target_folder, target_name)
                    if new_path:
                        self.stats["actions_taken"] += 1
                
                if self.on_stats_change:
                    self.on_stats_change(self.stats)
            else:
                logger.info(f"[AUTO] Confidence {confidence} too low (Threshold: {self.confidence_threshold}). Action skipped.")

    def start(self):
        """Starts the file watcher."""
        if hasattr(self, 'observer') and self.observer and self.observer.is_alive():
            logger.warning("Observer already running.")
            return

        logger.info("Starting Antigravity Local Agent...")
        self.observer = start_watcher(self.on_file_event, self.config)
        if not self.observer:
            logger.error("Failed to start observer.")
            
            self.observer.stop()
            self.observer.join()
            self.observer = None

    def stop(self):
        """Stops the file watcher."""
        if hasattr(self, 'observer') and self.observer:
            logger.info("Stopping Antigravity Local Agent...")
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Agent stopped.")

    def scan_existing_files(self):
        """Scans all existing files in watched paths."""
        logger.info("Starting manual scan of existing files...")
        
        paths = self.config.get("watch_paths", [])
        count = 0
        
        for root_path in paths:
            p = Path(root_path)
            if not p.exists():
                continue
                
            for file_path in p.iterdir():
                if file_path.is_file():
                    self.on_file_event(str(file_path), override_mode="suggest")
                    count += 1
        
        logger.info(f"Manual scan complete. Processed {count} files.")

def main():
    logger.info("Starting Antigravity Local Agent...")
    
    config = load_config()
    if not config:
        return

    system = AntigravitySystem(config)

    logger.info(f"Mode: {config.get('mode', 'observe')}")
    logger.info(f"Watching paths: {config.get('watch_paths', [])}")

    system.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        system.stop()

if __name__ == "__main__":
    main()
