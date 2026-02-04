import shutil
import json
import os
import time
import struct
from pathlib import Path
from datetime import datetime
from src.utils import setup_logging

# Windows Shell API imports
try:
    import win32gui
    import win32con
    import commctrl
    import win32api
    import win32process
    import pythoncom
    import win32com.client
    from win32com.shell import shell, shellcon
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

logger = setup_logging()

class ActionExecutor:
    def __init__(self, config):
        self.config = config
        self.undo_log_path = Path("undo_log.json")
        self.safe_root = Path(config.get("safe_root", "C:/Users/Velix/Documents"))
        
        # Grid settings
        self.col_width = 150
        self.row_height = 100
        self.start_x = 50
        self.start_y = 50
        
        # Track column usage
        self.column_counters = {} # category -> next_row_index

    def _get_desktop_view(self):
        """Finds the SysListView32 window for the desktop."""
        if not HAS_WIN32: return None
        
        progman = win32gui.FindWindow("Progman", "Program Manager")
        shell_view = win32gui.FindWindowEx(progman, 0, "SHELLDLL_DefView", None)
        
        if not shell_view:
            def callback(hwnd, extra):
                if win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None):
                    extra.append(hwnd)
            hwnds = []
            win32gui.EnumWindows(callback, hwnds)
            for hwnd in hwnds:
                shell_view = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
                if shell_view: break
        
        if shell_view:
            return win32gui.FindWindowEx(shell_view, 0, "SysListView32", "FolderView")
        return None

    def disable_auto_arrange(self):
        """Disables 'Auto-arrange' and 'Align to grid' via Windows Messaging and Registry."""
        if not HAS_WIN32: return
        
        lv_hwnd = self._get_desktop_view()
        if lv_hwnd:
            style = win32gui.GetWindowLong(lv_hwnd, win32con.GWL_STYLE)
            # LVS_AUTOARRANGE = 0x0100
            if style & 0x0100:
                win32gui.SetWindowLong(lv_hwnd, win32con.GWL_STYLE, style & ~0x0100)
                logger.info("Visual Setting: Sent Shell message to disable Auto-arrange.")
            
            # Send message to refresh shell view
            # IDM_VIEW_AUTOARRANGE = 0x7041
            # IDM_VIEW_GRIDALIGN = 0x7042
            parent = win32gui.GetParent(lv_hwnd)
            win32gui.PostMessage(parent, win32con.WM_COMMAND, 0x7041, 0)
            win32gui.PostMessage(parent, win32con.WM_COMMAND, 0x7042, 0)
            
            logger.info("Visual Setting: Requested Shell to unlock icon grid.")

    def reposition_icon(self, file_path, category):
        """Moves a desktop icon to a specific column based on category, aligned to the right."""
        if not HAS_WIN32: return False
        
        import ctypes
        from ctypes import wintypes

        label_to_find = Path(file_path).stem
        lv_hwnd = self._get_desktop_view()
        if not lv_hwnd:
            logger.error("Could not find Desktop ListView.")
            return False

        # 1. Screen Metrics
        screen_width = win32api.GetSystemMetrics(0)
        
        # 2. Position Calculation (Right Aligned)
        col_map = {"Gaming": 0, "Productivity": 1, "Apps": 2, "Documents": 3, "Images": 4, "Other": 5}
        col_idx = col_map.get(category, 5)
        row_idx = self.column_counters.get(category, 0)
        self.column_counters[category] = row_idx + 1
        
        margin_right = 200 # Increased margin
        x = screen_width - margin_right - (col_idx * self.col_width)
        y = self.start_y + (row_idx * self.row_height)

        logger.info(f"Visual Move: '{label_to_find}' -> {category} (RIGHT: {x}, {y})")
        
        try:
            # 3. Find Item Index by name (Robust x64)
            t, pid = win32process.GetWindowThreadProcessId(lv_hwnd)
            process_handle = win32api.OpenProcess(win32con.PROCESS_VM_OPERATION | win32con.PROCESS_VM_READ | win32con.PROCESS_VM_WRITE, False, pid)
            
            # Allocate memory for label string
            search_str = label_to_find
            remote_str = win32process.VirtualAllocEx(process_handle, None, len(search_str) + 1, win32con.MEM_COMMIT, win32con.PAGE_READWRITE)
            win32process.WriteProcessMemory(process_handle, remote_str, search_str.encode('ascii') + b'\0')
            
            # LVFINDINFO structure for x64:
            # UINT flags;      (4 bytes)
            # LPCSTR psz;      (8 bytes - pointer)
            # LPARAM lParam;   (8 bytes)
            # POINT pt;        (8 bytes - 2 ints)
            # UINT vkDirection;(4 bytes)
            # Total size: ~32-40 bytes depending on padding
            
            # Flags: LVFI_STRING = 0x0002 | LVFI_PARTIAL = 0x0008
            flags = 0x0002 | 0x0008
            find_info = struct.pack('Q Q Q ii I', flags, remote_str, 0, 0, 0, 0)
            remote_info = win32process.VirtualAllocEx(process_handle, None, len(find_info), win32con.MEM_COMMIT, win32con.PAGE_READWRITE)
            win32process.WriteProcessMemory(process_handle, remote_info, find_info)
            
            # LVM_FINDITEMA = 0x100D
            item_idx = win32gui.SendMessage(lv_hwnd, 0x100D, -1, remote_info)
            
            # Cleanup
            win32process.VirtualFreeEx(process_handle, remote_str, 0, win32con.MEM_RELEASE)
            win32process.VirtualFreeEx(process_handle, remote_info, 0, win32con.MEM_RELEASE)
            win32api.CloseHandle(process_handle)
            
            if item_idx != -1:
                logger.info(f"Matched '{label_to_find}' at index {item_idx}. Sending snap...")
                # LVM_SETITEMPOSITION = 0x100F
                # win32api.MAKELONG(x, y) packs two 16-bit ints into a 32-bit value
                win32gui.SendMessage(lv_hwnd, 0x100F, item_idx, win32api.MAKELONG(int(x), int(y)))
            else:
                logger.warning(f"Could not find index for '{label_to_find}'. Falling back to last item.")
                count = win32gui.SendMessage(lv_hwnd, commctrl.LVM_GETITEMCOUNT, 0, 0)
                win32gui.SendMessage(lv_hwnd, 0x100F, count-1, win32api.MAKELONG(int(x), int(y)))

            # Force Shell Refresh
            win32gui.SendMessage(lv_hwnd, win32con.WM_KEYDOWN, win32con.VK_F5, 0)
            win32gui.SendMessage(lv_hwnd, win32con.WM_KEYUP, win32con.VK_F5, 0)
            
            return True
        except Exception as e:
            logger.error(f"Reposition error: {e}")
            return False

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
        
        base_name = Path(new_filename).stem
        extension = Path(new_filename).suffix
        dest_path = dest_folder_path / new_filename
        
        counter = 1
        while dest_path.exists():
             unique_name = f"{base_name}_{counter}{extension}"
             dest_path = dest_folder_path / unique_name
             counter += 1

        try:
            dest_folder_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Moving {source_path} -> {dest_path}")
            shutil.move(str(source_path), str(dest_path))
            
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

        last_action = log.pop()
        original_path = Path(last_action["original_path"])
        current_path = Path(last_action["new_path"])
        
        if not current_path.exists():
            return None
            
        try:
            shutil.move(str(current_path), str(original_path))
            self._save_undo_log(log)
            return str(original_path)
        except Exception:
            return None
