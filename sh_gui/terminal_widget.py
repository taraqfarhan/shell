"""
Native Canvas Terminal Widget for sh_gui providing terminal emulation.
"""

import sys
import pyte
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QFont, QColor, QPainter, QFontMetrics, QClipboard
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRect

from sh_gui.themes import THEMES, DEFAULT_THEME
from sh_gui.pty_worker import PTYSession

def parse_pyte_color(color_name, default_color, theme):
    if color_name == "default":
        return QColor(default_color)
    
    ansi_map = theme.get("ansi", {})
    if color_name in ansi_map:
        return QColor(ansi_map[color_name])
    
    if isinstance(color_name, str):
        if color_name.startswith("#"):
            return QColor(color_name)
        if len(color_name) == 6:
            return QColor(f"#{color_name}")
        
    return QColor(default_color)

class TerminalWidget(QWidget):
    title_changed = pyqtSignal(str)
    process_exited = pyqtSignal(int)

    def __init__(self, theme_name=DEFAULT_THEME, font_family="Menlo", font_size=21, parent=None):
        super().__init__(parent)
        self.theme_name = theme_name
        self.theme = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
        self.font_family = font_family
        self.font_size = font_size

        
        self.cols = 80
        self.rows = 24
        self.margin_x = 8
        self.margin_y = 8
        self.screen = pyte.HistoryScreen(self.cols, self.rows, history=5000)
        self.stream = pyte.ByteStream(self.screen)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.update_font_metrics()

        self.pty_session = PTYSession(rows=self.rows, cols=self.cols)
        self.pty_session.data_received.connect(self.on_data_received)
        self.pty_session.process_exited.connect(self.on_process_exited)

        self.cursor_visible = True
        self.blink_timer = QTimer(self)
        self.blink_timer.setInterval(600)
        self.blink_timer.timeout.connect(self.toggle_cursor_blink)
        self.blink_timer.start()

        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        self._is_zooming = False

    def update_font_metrics(self):
        self.font = QFont(self.font_family, self.font_size)
        self.font.setStyleHint(QFont.StyleHint.Monospace)
        self.font.setFixedPitch(True)
        font_metrics = QFontMetrics(self.font)
        
        # Use precise floating point width and height advances
        self.char_width_float = max(1.0, float(font_metrics.horizontalAdvance('M')))
        self.char_height_float = max(1.0, float(font_metrics.height()))
        self.ascent = font_metrics.ascent()

    def get_col_x(self, col: int) -> int:
        return self.margin_x + round(col * self.char_width_float)

    def get_row_y(self, row: int) -> int:
        return self.margin_y + round(row * self.char_height_float)

    def get_cell_width(self, col: int) -> int:
        return self.get_col_x(col + 1) - self.get_col_x(col)

    def get_cell_height(self, row: int) -> int:
        return self.get_row_y(row + 1) - self.get_row_y(row)

    def set_theme(self, theme_name):
        if theme_name in THEMES:
            self.theme_name = theme_name
            self.theme = THEMES[theme_name]
            self.update()

    def set_font_size(self, size):
        if 8 <= size <= 48:
            self._is_zooming = True
            try:
                self.font_size = size
                self.update_font_metrics()
                
                win = self.window()
                if win and not win.isMaximized():
                    target_w = int(self.cols * self.char_width_float + (2 * self.margin_x) + 30)
                    target_h = int(self.rows * self.char_height_float + (2 * self.margin_y) + 70)
                    win.resize(max(500, target_w), max(350, target_h))
            finally:
                self._is_zooming = False
            self.update()

    def zoom_in(self):
        self.set_font_size(self.font_size + 1)

    def zoom_out(self):
        self.set_font_size(self.font_size - 1)

    def reset_zoom(self):
        self.set_font_size(21)

    def toggle_cursor_blink(self):
        self.cursor_visible = not self.cursor_visible
        cursor_col = max(0, min(self.screen.cursor.x, self.cols - 1))
        cursor_row = max(0, min(self.screen.cursor.y, self.rows - 1))
        cx = self.get_col_x(cursor_col)
        cy = self.get_row_y(cursor_row)
        cw = self.get_cell_width(cursor_col)
        ch = self.get_cell_height(cursor_row)
        self.update(QRect(cx, cy, cw, ch))


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.calculate_grid_dimensions()

    def calculate_grid_dimensions(self):
        if getattr(self, "_is_zooming", False):
            return

        avail_w = max(200, self.width() - (2 * self.margin_x))
        avail_h = max(100, self.height() - (2 * self.margin_y))

        cols = max(20, int(avail_w // self.char_width_float))
        rows = max(5, int(avail_h // self.char_height_float))

        if cols != self.cols or rows != self.rows:
            old_rows = self.rows
            self.cols = cols
            self.rows = rows
            
            history_top_before = len(self.screen.history.top) if hasattr(self.screen, "history") else 0
            self.screen.resize(rows, cols)
            history_top_after = len(self.screen.history.top) if hasattr(self.screen, "history") else 0

            # Correct cursor.y according to pyte line buffer shift direction
            if rows < old_rows:
                # Shrinking: pyte shifted lines up by (old_rows - rows)
                self.screen.cursor.y = max(0, self.screen.cursor.y - (old_rows - rows))
            elif history_top_before > history_top_after:
                # Expanding & restoring history: pyte shifted lines down
                restored_lines = history_top_before - history_top_after
                self.screen.cursor.y = max(0, min(self.rows - 1, self.screen.cursor.y + restored_lines))

            self.screen.cursor.x = max(0, min(self.screen.cursor.x, cols - 1))
            self.screen.cursor.y = max(0, min(self.screen.cursor.y, rows - 1))
            self.pty_session.resize(rows, cols)
            self.update()



    def on_data_received(self, data: bytes):
        self.stream.feed(data)
        self.update()

    def on_process_exited(self, exit_code: int):
        self.process_exited.emit(exit_code)

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.MouseButton.LeftButton:
            col = int((event.position().x() - self.margin_x) / self.char_width_float)
            row = int((event.position().y() - self.margin_y) / self.char_height_float)
            self.selection_start = (max(0, row), max(0, col))
            self.selection_end = self.selection_start
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            col = int((event.position().x() - self.margin_x) / self.char_width_float)
            row = int((event.position().y() - self.margin_y) / self.char_height_float)
            self.selection_end = (max(0, row), max(0, col))
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_selecting = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(self.font)

        bg_color = QColor(self.theme["bg"])
        fg_default = self.theme["fg"]
        bg_default = self.theme["bg"]
        cursor_color = QColor(self.theme["cursor"])
        selection_color = QColor(self.theme["selection"])

        # Fill background
        painter.fillRect(self.rect(), bg_color)

        # Draw cells safely with sub-pixel alignment
        max_lines = min(self.screen.lines, self.rows)
        max_cols = min(self.screen.columns, self.cols)

        for row in range(max_lines):
            y = self.get_row_y(row)
            cell_h = self.get_cell_height(row)
            line = self.screen.buffer[row]

            for col in range(max_cols):
                x = self.get_col_x(col)
                cell_w = self.get_cell_width(col)
                char_obj = line[col]

                fg = parse_pyte_color(char_obj.fg, fg_default, self.theme)
                bg = parse_pyte_color(char_obj.bg, bg_default, self.theme)

                if char_obj.reverse:
                    fg, bg = bg, fg

                # Selection highlight
                is_selected = False
                if self.selection_start and self.selection_end:
                    s_r1, s_c1 = min(self.selection_start, self.selection_end)
                    s_r2, s_c2 = max(self.selection_start, self.selection_end)
                    if s_r1 <= row <= s_r2:
                        c1 = s_c1 if row == s_r1 else 0
                        c2 = s_c2 if row == s_r2 else self.cols - 1
                        if c1 <= col <= c2:
                            is_selected = True

                if is_selected:
                    bg = selection_color

                # Fill background cell if non-default
                if bg != bg_color:
                    cell_rect = QRect(x, y, cell_w, cell_h)
                    painter.fillRect(cell_rect, bg)

                # Draw character
                char_str = char_obj.data
                if char_str and char_str != ' ':
                    painter.setPen(fg)
                    painter.drawText(x, y + self.ascent, char_str)

                # Underscore styling
                if char_obj.underscore:
                    painter.setPen(fg)
                    painter.drawLine(x, y + cell_h - 1, x + cell_w, y + cell_h - 1)

        # Draw Terminal Cursor with 100% exact pixel positioning
        cursor_col = max(0, min(self.screen.cursor.x, self.cols - 1))
        cursor_row = max(0, min(self.screen.cursor.y, self.rows - 1))

        if 0 <= cursor_col < self.cols and 0 <= cursor_row < self.rows:
            cx = self.get_col_x(cursor_col)
            cy = self.get_row_y(cursor_row)
            cw = self.get_cell_width(cursor_col)
            ch = self.get_cell_height(cursor_row)
            cursor_rect = QRect(cx, cy, cw, ch)

            if self.hasFocus():
                if self.cursor_visible:
                    painter.fillRect(cursor_rect, cursor_color)
                    # Draw inverted character under cursor
                    try:
                        char_under = self.screen.buffer[cursor_row][cursor_col].data
                        if char_under and char_under != ' ':
                            painter.setPen(bg_color)
                            painter.drawText(cx, cy + self.ascent, char_under)
                    except (IndexError, KeyError):
                        pass
            else:
                # Hollow rectangle when window is out of focus
                painter.setPen(cursor_color)
                painter.drawRect(cursor_rect.adjusted(0, 0, -1, -1))



    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        text = event.text()

        # Restart cursor blink on typing
        self.cursor_visible = True
        self.blink_timer.start()

        # Handle Copy / Paste / Shortcuts
        is_cmd_or_ctrl = bool(modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier))

        if is_cmd_or_ctrl:
            if key == Qt.Key.Key_T:
                win = self.window()
                if win and hasattr(win, "add_new_tab"):
                    win.add_new_tab()
                return
            elif key == Qt.Key.Key_W:
                win = self.window()
                if win and hasattr(win, "close_tab") and hasattr(win, "tab_widget"):
                    win.close_tab(win.tab_widget.currentIndex())
                return
            elif key == Qt.Key.Key_C:


                if self.selection_start and self.selection_end:
                    self.copy_selection()
                    return
                else:
                    self.pty_session.write(b'\x03')  # SIGINT (Ctrl+C)
                    return
            elif key == Qt.Key.Key_V:
                clipboard_text = QApplication.clipboard().text()
                if clipboard_text:
                    self.pty_session.write(clipboard_text.encode('utf-8'))
                return
            elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                self.zoom_in()
                return
            elif key == Qt.Key.Key_Minus:
                self.zoom_out()
                return
            elif key == Qt.Key.Key_0:
                self.reset_zoom()
                return
            elif key == Qt.Key.Key_Z:


                self.pty_session.write(b'\x1a')  # SIGTSTP (Ctrl+Z)
                return
            elif key == Qt.Key.Key_D:
                self.pty_session.write(b'\x04')  # EOF (Ctrl+D)
                return
            elif key == Qt.Key.Key_L:
                self.screen.reset()
                self.pty_session.write(b'\x0c')  # Clear screen (Ctrl+L)
                return

        # Key map for terminal escape codes
        key_map = {
            Qt.Key.Key_Return: b'\r',
            Qt.Key.Key_Enter: b'\r',
            Qt.Key.Key_Backspace: b'\x7f',
            Qt.Key.Key_Tab: b'\t',
            Qt.Key.Key_Escape: b'\x1b',
            Qt.Key.Key_Up: b'\x1b[A',
            Qt.Key.Key_Down: b'\x1b[B',
            Qt.Key.Key_Right: b'\x1b[C',
            Qt.Key.Key_Left: b'\x1b[D',
            Qt.Key.Key_Home: b'\x1b[H',
            Qt.Key.Key_End: b'\x1b[F',
            Qt.Key.Key_PageUp: b'\x1b[5~',
            Qt.Key.Key_PageDown: b'\x1b[6~',
            Qt.Key.Key_Delete: b'\x1b[3~',
        }

        if key in key_map:
            self.pty_session.write(key_map[key])
        elif text:
            self.pty_session.write(text.encode('utf-8'))

    def copy_selection(self):
        if not (self.selection_start and self.selection_end):
            return
        
        s_r1, s_c1 = min(self.selection_start, self.selection_end)
        s_r2, s_c2 = max(self.selection_start, self.selection_end)

        selected_lines = []
        for r in range(s_r1, s_r2 + 1):
            if 0 <= r < self.screen.lines:
                line_str = "".join(self.screen.buffer[r][c].data for c in range(self.screen.columns))
                c1 = s_c1 if r == s_r1 else 0
                c2 = (s_c2 + 1) if r == s_r2 else len(line_str)
                selected_lines.append(line_str[c1:c2])

        text = "\n".join(selected_lines)
        QApplication.clipboard().setText(text)

    def focusNextPrevChild(self, next):
        # Prevent Qt from consuming Tab key for widget focus navigation
        return False

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.update()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.update()


    def closeEvent(self, event):
        self.pty_session.terminate()
        super().closeEvent(event)
