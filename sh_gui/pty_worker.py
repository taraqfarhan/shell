"""
PTY process wrapper and asynchronous reader thread for sh_gui.
"""

import os
import sys
import pty
import select
import signal
import struct
import fcntl
import termios
import subprocess
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal, QObject

class PTYReader(QThread):
    data_received = pyqtSignal(bytes)
    process_exited = pyqtSignal(int)

    def __init__(self, master_fd, pid):
        super().__init__()
        self.master_fd = master_fd
        self.pid = pid
        self._running = True

    def run(self):
        while self._running:
            try:
                r, _, _ = select.select([self.master_fd], [], [], 0.05)
                if self.master_fd in r:
                    data = os.read(self.master_fd, 4096)
                    if data:
                        self.data_received.emit(data)
                    else:
                        break
            except (OSError, ValueError):
                break

        # Check process exit code
        try:
            _, status = os.waitpid(self.pid, os.WNOHANG)
            exit_code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else 0
        except ChildProcessError:
            exit_code = 0

        self.process_exited.emit(exit_code)

    def stop(self):
        self._running = False
        self.wait(1000)

class PTYSession(QObject):
    data_received = pyqtSignal(bytes)
    process_exited = pyqtSignal(int)
    cwd_changed = pyqtSignal(str)

    def __init__(self, command=None, cwd=None, rows=24, cols=80):
        super().__init__()
        self.rows = rows
        self.cols = cols
        
        # Build environment with project_root in PYTHONPATH and SHELL=sh
        project_root = str(Path(__file__).resolve().parent.parent)
        env = os.environ.copy()
        python_path = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{project_root}:{python_path}" if python_path else project_root
        env["SHELL"] = "sh"


        # Default command is python3 -m sh
        if command is None:
            python_bin = sys.executable
            command = [python_bin, "-m", "sh"]
            if cwd is None:
                cwd = project_root

        self.cwd = cwd or os.getcwd()
        self.command = command

        # Open pseudo terminal pair
        self.master_fd, self.slave_fd = pty.openpty()
        self._set_winsize(self.rows, self.cols)

        # Spawn subprocess attached to slave_fd
        self.process = subprocess.Popen(
            self.command,
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            cwd=self.cwd,
            env=env,
            close_fds=True,
            start_new_session=True
        )

        os.close(self.slave_fd)
        self.pid = self.process.pid

        # Start reader thread
        self.reader = PTYReader(self.master_fd, self.pid)
        self.reader.data_received.connect(self.data_received.emit)
        self.reader.process_exited.connect(self.process_exited.emit)
        self.reader.start()

    def write(self, data: bytes):
        if self.master_fd is not None:
            try:
                os.write(self.master_fd, data)
            except OSError:
                pass

    def resize(self, rows: int, cols: int):
        if rows <= 0 or cols <= 0:
            return
        self.rows = rows
        self.cols = cols
        self._set_winsize(rows, cols)

    def _set_winsize(self, rows: int, cols: int):
        if self.master_fd is not None:
            try:
                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
            except (OSError, AttributeError):
                pass

    def terminate(self):
        if self.reader:
            self.reader.stop()
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None
        if self.process and self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except OSError:
                pass
