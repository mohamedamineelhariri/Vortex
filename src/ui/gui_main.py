import sys
import logging
import time
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

from src.main import AntigravitySystem, load_config
from src.ui.dashboard import Dashboard

# --- Logging Handler to Emit Signals ---
class QtSignaler(QObject):
    message_emitted = pyqtSignal(str)

class QtLogHandler(logging.Handler):
    def __init__(self, signaler):
        super().__init__()
        self.signaler = signaler

    def emit(self, record):
        msg = self.format(record)
        self.signaler.message_emitted.emit(msg)

# --- Worker Thread for Agent ---
class AntigravityWorker(QObject):
    finished = pyqtSignal()
    stats_updated = pyqtSignal(int, int, int) # files, decisions, actions
    pending_updated = pyqtSignal(dict) # pending actions dict
    
    def __init__(self):
        super().__init__()
        self.config = load_config(str(project_root / "config.yaml"))
        if not self.config:
             self.config = {"mode": "observe", "watch_paths": []}
             
        self.system = AntigravitySystem(self.config)
        # Connect system callbacks
        self.system.on_stats_change = self._on_stats_change
        self.system.on_pending_change = self._on_pending_change
        
        self._is_running = False

    def _on_stats_change(self, stats):
        self.stats_updated.emit(
            stats.get("files_processed", 0),
            stats.get("decisions_made", 0),
            stats.get("actions_taken", 0)
        )

    def _on_pending_change(self, pending):
        self.pending_updated.emit(pending)

    @pyqtSlot()
    def start_agent(self):
        if self._is_running:
            return
        self.system.start()
        self._is_running = True

    @pyqtSlot()
    def stop_agent(self):
        if not self._is_running:
            return
        self.system.stop()
        self._is_running = False
        self.finished.emit()

    @pyqtSlot()
    def scan_files(self):
        self.system.scan_existing_files()
        
    @pyqtSlot(str)
    def set_mode(self, mode):
        self.system.set_mode(mode)

    @pyqtSlot()
    def undo_last(self):
        self.system.undo_last()

    @pyqtSlot(int)
    def approve_action(self, action_id):
        self.system.approve_action(action_id)

    @pyqtSlot(int)
    def reject_action(self, action_id):
        self.system.reject_action(action_id)

    @pyqtSlot(dict)
    def update_targets(self, targets):
        self.system.update_config("organization_targets", targets)

# --- Main Application ---
def main():
    app = QApplication(sys.argv)
    
    # Load Styles
    style_path = Path(__file__).parent / "styles.qss"
    if style_path.exists():
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    
    # Setup Signal Bridge for Logging
    signaler = QtSignaler()
    handler = QtLogHandler(signaler)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S'))
    
    # Add handler to root logger
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Initialize Dashboard
    window = Dashboard()
    window.show()

    # Initialize Thread & Worker
    thread = QThread()
    worker = AntigravityWorker()
    worker.moveToThread(thread)
    
    # Connect Controls
    window.start_requested.connect(worker.start_agent)
    window.stop_requested.connect(worker.stop_agent)
    window.scan_requested.connect(worker.scan_files)
    
    # Connect New Features
    window.mode_changed.connect(worker.set_mode)
    window.undo_requested.connect(worker.undo_last)
    window.approve_requested.connect(worker.approve_action)
    window.reject_requested.connect(worker.reject_action)
    window.targets_changed.connect(worker.update_targets)
    
    # Connect Logging to Console
    signaler.message_emitted.connect(window.log)
    
    # Connect Updates
    worker.stats_updated.connect(window.update_stats)
    worker.pending_updated.connect(window.update_pending_actions)
    
    # Connect Status Updates
    window.start_requested.connect(lambda: window.update_status(True))
    window.stop_requested.connect(lambda: window.update_status(False))

    # Thread Management
    thread.start()
    
    # Cleanup on Exit
    app.aboutToQuit.connect(worker.stop_agent)
    app.aboutToQuit.connect(thread.quit)
    app.aboutToQuit.connect(thread.wait)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
