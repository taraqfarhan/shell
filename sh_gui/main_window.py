"""
Main application window for sh_gui featuring clean tabs, search, and status bar.
"""

import os
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QToolBar, 
    QStatusBar, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtCore import Qt, QSize


from sh_gui.terminal_widget import TerminalWidget
from sh_gui.themes import get_app_stylesheet, DEFAULT_THEME

class TerminalTab(QWidget):
    def __init__(self, theme_name=DEFAULT_THEME, font_family="Menlo", font_size=13, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Native Terminal Canvas Widget
        self.terminal = TerminalWidget(
            theme_name=theme_name,
            font_family=font_family,
            font_size=font_size,
            parent=self
        )
        layout.addWidget(self.terminal)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.settings = {
            "theme": DEFAULT_THEME,
            "font_family": "Menlo",
            "font_size": 21,
            "scrollback_lines": 5000
        }

        self.setWindowTitle("Barber - Terminal")
        self.resize(1200, 780)

        # Central Tab Widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.South)
        self.tab_widget.setElideMode(Qt.TextElideMode.ElideNone)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tab_widget)

        # Setup ToolBar & StatusBar
        self.setup_toolbar()
        self.setup_statusbar()
        self.apply_theme()

        # Create initial terminal tab
        self.add_new_tab()

    def apply_theme(self):
        theme_name = self.settings.get("theme", DEFAULT_THEME)
        self.setStyleSheet(get_app_stylesheet(theme_name))
        
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, TerminalTab):
                tab.terminal.set_theme(theme_name)

    def setup_toolbar(self):
        toolbar = QToolBar("Controls", self)
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        # New Tab Action
        act_new = QAction("New Tab", self)
        act_new.setShortcut(QKeySequence("Ctrl+T"))
        act_new.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        act_new.setToolTip("Open new shell tab (Cmd+T)")
        act_new.triggered.connect(self.add_new_tab)
        toolbar.addAction(act_new)

        # Close Tab Action
        act_close = QAction("Close Tab", self)
        act_close.setShortcut(QKeySequence("Ctrl+W"))
        act_close.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        act_close.setToolTip("Close current tab (Cmd+W)")
        act_close.triggered.connect(lambda: self.close_tab(self.tab_widget.currentIndex()))
        toolbar.addAction(act_close)

        toolbar.addSeparator()

        # Clear Screen
        act_clear = QAction("Clear", self)
        act_clear.setShortcut(QKeySequence("Ctrl+L"))
        act_clear.setToolTip("Clear screen (Ctrl+L)")
        act_clear.triggered.connect(self.clear_current_terminal)
        toolbar.addAction(act_clear)

        toolbar.addSeparator()

        # Zoom In / Out / Reset
        act_zoom_in = QAction("Zoom In", self)
        act_zoom_in.setShortcut(QKeySequence("Ctrl+="))
        act_zoom_in.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        act_zoom_in.setToolTip("Zoom In (Cmd+=)")
        act_zoom_in.triggered.connect(self.zoom_in_current)
        toolbar.addAction(act_zoom_in)

        act_zoom_out = QAction("Zoom Out", self)
        act_zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        act_zoom_out.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        act_zoom_out.setToolTip("Zoom Out (Cmd+-)")
        act_zoom_out.triggered.connect(self.zoom_out_current)
        toolbar.addAction(act_zoom_out)

        act_zoom_reset = QAction("Reset Zoom", self)
        act_zoom_reset.setShortcut(QKeySequence("Ctrl+0"))
        act_zoom_reset.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        act_zoom_reset.setToolTip("Reset Zoom (Cmd+0)")
        act_zoom_reset.triggered.connect(self.reset_zoom_current)
        toolbar.addAction(act_zoom_reset)

        toolbar.addSeparator()

        # Export Log Action
        act_export = QAction("Save Log", self)
        act_export.setToolTip("Export terminal buffer to file")
        act_export.triggered.connect(self.export_log)
        toolbar.addAction(act_export)

    def zoom_in_current(self):
        tab = self.get_current_tab()
        if tab: tab.terminal.zoom_in()

    def zoom_out_current(self):
        tab = self.get_current_tab()
        if tab: tab.terminal.zoom_out()

    def reset_zoom_current(self):
        tab = self.get_current_tab()
        if tab: tab.terminal.reset_zoom()


    def setup_statusbar(self):
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.lbl_pid = QLabel("PID: —", self)
        self.lbl_cwd = QLabel(f"Dir: {os.path.basename(os.getcwd())}", self)
        self.lbl_tabs = QLabel("Tabs: 0", self)
        self.lbl_status = QLabel("Active", self)

        self.statusbar.addPermanentWidget(self.lbl_pid)
        self.statusbar.addPermanentWidget(self.lbl_cwd)
        self.statusbar.addPermanentWidget(self.lbl_tabs)
        self.statusbar.addPermanentWidget(self.lbl_status)

    def add_new_tab(self):
        tab_count = self.tab_widget.count() + 1
        tab = TerminalTab(
            theme_name=self.settings["theme"],
            font_family=self.settings["font_family"],
            font_size=self.settings["font_size"],
            parent=self
        )
        
        index = self.tab_widget.addTab(tab, f"Shell {tab_count}")
        self.tab_widget.setCurrentIndex(index)
        tab.terminal.setFocus()
        self.update_statusbar()

    def close_tab(self, index):
        if self.tab_widget.count() <= 1:
            self.close()
            return
        
        tab = self.tab_widget.widget(index)
        if isinstance(tab, TerminalTab):
            tab.terminal.close()
        self.tab_widget.removeTab(index)
        self.update_statusbar()

    def get_current_tab(self):
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, TerminalTab):
            return widget
        return None

    def get_active_tab_cwd(self, tab):
        if not tab or not hasattr(tab.terminal, "pty_session"):
            return os.getcwd()
        pid = tab.terminal.pty_session.pid
        try:
            import subprocess
            out = subprocess.check_output(
                ["lsof", "-a", "-d", "cwd", "-p", str(pid), "-Fn"],
                stderr=subprocess.DEVNULL,
                text=True
            )
            for line in out.splitlines():
                if line.startswith("n") and len(line) > 1:
                    return line[1:]
        except Exception:
            pass
        return getattr(tab.terminal.pty_session, "cwd", os.getcwd())

    def clear_current_terminal(self):
        tab = self.get_current_tab()
        if tab:
            tab.terminal.screen.reset()
            tab.terminal.pty_session.write(b'\x0c')

    def export_log(self):

        tab = self.get_current_tab()
        if not tab: return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Terminal Log", "", "Log Files (*.log *.txt);;All Files (*)"
        )
        if file_path:
            lines = []
            screen = tab.terminal.screen
            for row in range(screen.lines):
                line_str = "".join(screen.buffer[row][col].data for col in range(screen.columns))
                lines.append(line_str.rstrip())
            content = "\n".join(lines)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Export Successful", f"Log saved to {file_path}")

    def on_tab_changed(self, index):
        tab = self.get_current_tab()
        if tab:
            tab.terminal.setFocus()
        self.update_statusbar()

    def update_statusbar(self):
        count = self.tab_widget.count()
        self.lbl_tabs.setText(f"Tabs: {count}")
        
        tab = self.get_current_tab()
        if tab:
            pid = tab.terminal.pty_session.pid
            self.lbl_pid.setText(f"PID: {pid}")
            self.lbl_status.setText("🟢 Active")
            cwd = self.get_active_tab_cwd(tab)
            self.lbl_cwd.setText(f"Dir: {os.path.basename(cwd) or '/'}")
