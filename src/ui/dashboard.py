from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QListWidget, QFrame, QComboBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont

class Dashboard(QMainWindow):
    # Signals
    start_requested = pyqtSignal()   # Auto-Pilot ON
    stop_requested = pyqtSignal()    # Auto-Pilot OFF
    scan_requested = pyqtSignal()    # Quick Scan
    mode_changed = pyqtSignal(str)
    undo_requested = pyqtSignal()
    approve_requested = pyqtSignal(int)
    reject_requested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VORTEX")
        self.resize(1100, 750)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main Container (Rounded edges)
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Header (Title + Status + Window Controls)
        self._setup_header()
        
        # 2. Hero Section (Controls)
        self._setup_hero()
        
        # 3. Content Area (Table)
        self._setup_content()
        
        # 4. Footer (Logs + Stats)
        self._setup_footer()
        
        # Dragging state
        self._drag_pos = None

    def _setup_header(self):
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(100)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 20, 20, 20) # Slightly less right margin for buttons
        
        # Title
        title_layout = QVBoxLayout()
        title = QLabel("VORTEX")
        title.setObjectName("AppTitle")
        subtitle = QLabel("AI Workspace Organizer")
        subtitle.setObjectName("AppSubtitle")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        # Status Indication
        self.status_dot = QLabel("●")
        self.status_dot.setObjectName("StatusDot")
        self.status_label = QLabel("SYSTEM IDLE")
        self.status_label.setObjectName("StatusLabel")
        
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_dot)
        status_layout.addWidget(self.status_label)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        layout.addLayout(status_layout)
        layout.addSpacing(20)
        
        # Window Controls
        win_controls = QHBoxLayout()
        win_controls.setSpacing(10)
        
        btn_min = QPushButton("─")
        btn_min.setObjectName("BtnWinMin")
        btn_min.setFixedSize(30, 30)
        btn_min.clicked.connect(self.showMinimized)
        
        btn_close = QPushButton("✕")
        btn_close.setObjectName("BtnWinClose")
        btn_close.setFixedSize(30, 30)
        btn_close.clicked.connect(self.close)
        
        win_controls.addWidget(btn_min)
        win_controls.addWidget(btn_close)
        
        layout.addLayout(win_controls)
        
        self.main_layout.addWidget(header)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _setup_hero(self):
        hero = QFrame()
        hero.setObjectName("HeroSection")
        hero.setFixedHeight(100)
        layout = QHBoxLayout(hero)
        layout.setContentsMargins(30, 10, 30, 10)
        layout.setSpacing(20)

        # Left: Scan Action
        self.btn_scan = QPushButton("  QUICK SCAN")
        self.btn_scan.setObjectName("BtnScan")
        self.btn_scan.setFixedSize(160, 50)
        self.btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scan.clicked.connect(self.scan_requested.emit)

        # Mode Selector (Subtle)
        self.combo_mode = QComboBox()
        self.combo_mode.setObjectName("ModeSelect")
        self.combo_mode.addItems(["observe", "suggest", "auto"])
        self.combo_mode.setCurrentText("suggest")
        self.combo_mode.setFixedSize(120, 40)
        self.combo_mode.currentTextChanged.connect(self.mode_changed.emit)

        # Right: Auto-Pilot Toggle
        self.btn_pilot = QPushButton("ACTIVATE AUTO-PILOT")
        self.btn_pilot.setObjectName("BtnPilot")
        self.btn_pilot.setCheckable(True)
        self.btn_pilot.setFixedSize(200, 50)
        self.btn_pilot.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pilot.clicked.connect(self._toggle_pilot)

        layout.addWidget(self.btn_scan)
        layout.addWidget(self.combo_mode)
        layout.addStretch()
        layout.addWidget(self.btn_pilot)
        
        self.main_layout.addWidget(hero)

    def _setup_content(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 10, 30, 10)
        
        # Section Title with Undo
        top_bar = QHBoxLayout()
        lbl = QLabel("PENDING ACTIONS")
        lbl.setObjectName("SectionTitle")
        
        self.btn_undo = QPushButton("↺ UNDO LAST")
        self.btn_undo.setObjectName("BtnUndo")
        self.btn_undo.setFixedSize(100, 30)
        self.btn_undo.clicked.connect(self.undo_requested.emit)
        
        top_bar.addWidget(lbl)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_undo)
        layout.addLayout(top_bar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["FILE", "CONFIDENCE", "SUGGESTED PATH", "ACTIONS"])
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.verticalHeader().setVisible(False)
        
        # Header sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 150)
        
        layout.addWidget(self.table)
        self.main_layout.addWidget(content)

    def _setup_footer(self):
        # Footer contains Toggle Logs button and Version
        footer = QFrame()
        footer.setObjectName("Footer")
        footer.setFixedHeight(40)
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(30, 0, 30, 0)
        
        self.btn_logs = QPushButton("Show Logs")
        self.btn_logs.setObjectName("BtnToggleLogs")
        self.btn_logs.setCheckable(True)
        self.btn_logs.clicked.connect(self._toggle_logs)
        
        lbl_ver = QLabel("v1.0.0 Vortex")
        lbl_ver.setStyleSheet("color: #45475a;")
        
        layout.addWidget(self.btn_logs)
        layout.addStretch()
        layout.addWidget(lbl_ver)
        
        self.main_layout.addWidget(footer)
        
        # Hidden Log Console (Initially Hidden)
        self.log_container = QFrame()
        self.log_container.setObjectName("LogBox")
        self.log_container.hide()
        self.log_container.setFixedHeight(150)
        log_layout = QVBoxLayout(self.log_container)
        log_layout.setContentsMargins(30, 0, 30, 20)
        
        self.console = QListWidget()
        self.console.setObjectName("Console")
        log_layout.addWidget(self.console)
        
        self.main_layout.addWidget(self.log_container)

    def _toggle_pilot(self, checked):
        if checked:
            self.btn_pilot.setText("DEACTIVATE")
            self.btn_pilot.setStyleSheet("background-color: #f38ba8; color: #1e1e2e;")
            self.start_requested.emit()
        else:
            self.btn_pilot.setText("ACTIVATE AUTO-PILOT")
            self.btn_pilot.setStyleSheet("") # Reverts to QSS
            self.stop_requested.emit()

    def _toggle_logs(self, checked):
        if checked:
            self.log_container.show()
            self.btn_logs.setText("Hide Logs")
        else:
            self.log_container.hide()
            self.btn_logs.setText("Show Logs")

    def update_status(self, running):
        if running:
            self.status_label.setText("ACTIVE MONITORING")
            self.status_dot.setStyleSheet("color: #a6e3a1;") # Green
        else:
            self.status_label.setText("SYSTEM IDLE")
            self.status_dot.setStyleSheet("color: #45475a;") # Grey

    def log(self, message):
        self.console.addItem(message)
        self.console.scrollToBottom()

    def update_stats(self, files, decisions, actions):
        pass # Disabling stats for now as requested to clean UI

    def update_pending_actions(self, pending_dict):
        self.table.setRowCount(0)
        
        for action_id, data in pending_dict.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 60)
            
            # File
            item_file = QTableWidgetItem(data['filename'])
            item_file.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row, 0, item_file)
            
            # Confidence
            conf = data['confidence']
            item_conf = QTableWidgetItem(f"{int(conf*100)}%")
            item_conf.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, item_conf)
            
            # Path
            path_str = f"{data['target_folder']}/{data['target_name']}"
            item_path = QTableWidgetItem(path_str)
            self.table.setItem(row, 2, item_path)
            
            # Actions
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(5, 5, 5, 5)
            btn_layout.setSpacing(10)
            
            btn_approve = QPushButton("✔")
            btn_approve.setFixedSize(40, 40)
            btn_approve.setObjectName("BtnApprove")
            btn_approve.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_approve.clicked.connect(lambda _, aid=action_id: self.approve_requested.emit(aid))
            
            btn_reject = QPushButton("✘")
            btn_reject.setFixedSize(40, 40)
            btn_reject.setObjectName("BtnReject")
            btn_reject.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_reject.clicked.connect(lambda _, aid=action_id: self.reject_requested.emit(aid))
            
            btn_layout.addWidget(btn_approve)
            btn_layout.addWidget(btn_reject)
            
            self.table.setCellWidget(row, 3, btn_widget)
