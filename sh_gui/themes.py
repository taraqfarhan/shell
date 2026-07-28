"""
Theme manager and color palettes for sh_gui.
"""

THEMES = {
    "Catppuccin Mocha": {
        "bg": "#1e1e2e",
        "fg": "#cdd6f4",
        "cursor": "#f5e0dc",
        "selection": "#45475a",
        "tab_bg": "#181825",
        "tab_active": "#313244",
        "tab_fg": "#a6adc8",
        "tab_active_fg": "#89b4fa",
        "border": "#313244",
        "toolbar_bg": "#181825",
        "statusbar_bg": "#11111b",
        "accent": "#89b4fa",
        "green": "#a6e3a1",
        "red": "#f38ba8",
        "yellow": "#f9e2af",
        "ansi": {
            "black": "#45475a",
            "red": "#f38ba8",
            "green": "#a6e3a1",
            "yellow": "#f9e2af",
            "blue": "#89b4fa",
            "magenta": "#f5c2e7",
            "cyan": "#94e2d5",
            "white": "#bac2de",
            "bright_black": "#585b70",
            "bright_red": "#f38ba8",
            "bright_green": "#a6e3a1",
            "bright_yellow": "#f9e2af",
            "bright_blue": "#89b4fa",
            "bright_magenta": "#f5c2e7",
            "bright_cyan": "#94e2d5",
            "bright_white": "#a6adc8"
        }
    },
    "One Dark Pro": {
        "bg": "#282c34",
        "fg": "#abb2bf",
        "cursor": "#528bff",
        "selection": "#3e4451",
        "tab_bg": "#21252b",
        "tab_active": "#282c34",
        "tab_fg": "#5c6370",
        "tab_active_fg": "#61afef",
        "border": "#181a1f",
        "toolbar_bg": "#21252b",
        "statusbar_bg": "#181a1f",
        "accent": "#61afef",
        "green": "#98c379",
        "red": "#e06c75",
        "yellow": "#e5c07b",
        "ansi": {
            "black": "#3e4451",
            "red": "#e06c75",
            "green": "#98c379",
            "yellow": "#e5c07b",
            "blue": "#61afef",
            "magenta": "#c678dd",
            "cyan": "#56b6c2",
            "white": "#abb2bf",
            "bright_black": "#5c6370",
            "bright_red": "#e06c75",
            "bright_green": "#98c379",
            "bright_yellow": "#e5c07b",
            "bright_blue": "#61afef",
            "bright_magenta": "#c678dd",
            "bright_cyan": "#56b6c2",
            "bright_white": "#ffffff"
        }
    },
    "Nord": {
        "bg": "#2e3440",
        "fg": "#d8dee9",
        "cursor": "#d8dee9",
        "selection": "#434c5e",
        "tab_bg": "#242933",
        "tab_active": "#3b4252",
        "tab_fg": "#4c566a",
        "tab_active_fg": "#88c0d0",
        "border": "#3b4252",
        "toolbar_bg": "#242933",
        "statusbar_bg": "#1e222a",
        "accent": "#88c0d0",
        "green": "#a3be8c",
        "red": "#bf616a",
        "yellow": "#ebcb8b",
        "ansi": {
            "black": "#3b4252",
            "red": "#bf616a",
            "green": "#a3be8c",
            "yellow": "#ebcb8b",
            "blue": "#81a1c1",
            "magenta": "#b48ead",
            "cyan": "#88c0d0",
            "white": "#e5e9f0",
            "bright_black": "#4c566a",
            "bright_red": "#bf616a",
            "bright_green": "#a3be8c",
            "bright_yellow": "#ebcb8b",
            "bright_blue": "#81a1c1",
            "bright_magenta": "#b48ead",
            "bright_cyan": "#8fbcbb",
            "bright_white": "#eceff4"
        }
    },
    "Dracula": {
        "bg": "#282a36",
        "fg": "#f8f8f2",
        "cursor": "#f8f8f2",
        "selection": "#44475a",
        "tab_bg": "#191a21",
        "tab_active": "#343746",
        "tab_fg": "#6272a4",
        "tab_active_fg": "#bd93f9",
        "border": "#343746",
        "toolbar_bg": "#191a21",
        "statusbar_bg": "#15161e",
        "accent": "#bd93f9",
        "green": "#50fa7b",
        "red": "#ff5555",
        "yellow": "#f1fa8c",
        "ansi": {
            "black": "#21222c",
            "red": "#ff5555",
            "green": "#50fa7b",
            "yellow": "#f1fa8c",
            "blue": "#bd93f9",
            "magenta": "#ff79c6",
            "cyan": "#8be9fd",
            "white": "#f8f8f2",
            "bright_black": "#6272a4",
            "bright_red": "#ff6e6e",
            "bright_green": "#69ff94",
            "bright_yellow": "#ffffa5",
            "bright_blue": "#d6acff",
            "bright_magenta": "#ff92d0",
            "bright_cyan": "#a4ffff",
            "bright_white": "#ffffff"
        }
    },
    "Cyberpunk": {
        "bg": "#120e24",
        "fg": "#37f6ff",
        "cursor": "#ff007f",
        "selection": "#2a1f4e",
        "tab_bg": "#0a0718",
        "tab_active": "#231842",
        "tab_fg": "#755ca7",
        "tab_active_fg": "#ff007f",
        "border": "#231842",
        "toolbar_bg": "#0a0718",
        "statusbar_bg": "#060410",
        "accent": "#ff007f",
        "green": "#00ff9f",
        "red": "#ff0055",
        "yellow": "#ffe600",
        "ansi": {
            "black": "#1d153a",
            "red": "#ff0055",
            "green": "#00ff9f",
            "yellow": "#ffe600",
            "blue": "#37f6ff",
            "magenta": "#ff007f",
            "cyan": "#00f0ff",
            "white": "#e0f6ff",
            "bright_black": "#47347a",
            "bright_red": "#ff3377",
            "bright_green": "#33ffb2",
            "bright_yellow": "#ffeb33",
            "bright_blue": "#66f8ff",
            "bright_magenta": "#ff3399",
            "bright_cyan": "#33f3ff",
            "bright_white": "#ffffff"
        }
    }
}

DEFAULT_THEME = "Catppuccin Mocha"

def get_app_stylesheet(theme_name=DEFAULT_THEME):
    theme = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    
    return f"""
    QMainWindow {{
        background-color: {theme['bg']};
        color: {theme['fg']};
    }}
    
    QTabWidget::pane {{
        border: 1px solid {theme['border']};
        background: {theme['bg']};
        border-radius: 0px;
    }}
    
    QTabWidget::tab-bar {{
        alignment: left;
    }}
    
    QTabBar {{
        alignment: left;
    }}

    QTabBar::tab {{
        background: {theme['tab_bg']};
        color: {theme['tab_fg']};
        padding: 6px 16px;
        min-width: 85px;
        border-bottom-left-radius: 6px;
        border-bottom-right-radius: 6px;
        border: 1px solid {theme['border']};
        border-top: none;
        margin-right: 4px;
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-weight: 500;
        font-size: 12px;
    }}

    
    QTabBar::tab:selected {{
        background: {theme['tab_active']};
        color: {theme['tab_active_fg']};
        border-bottom: 2px solid {theme['accent']};
        font-weight: 600;
    }}
    
    QTabBar::tab:hover:!selected {{
        background: {theme['border']};
        color: {theme['fg']};
    }}

    
    QToolBar {{
        background: {theme['toolbar_bg']};
        border-bottom: 1px solid {theme['border']};
        padding: 6px;
        spacing: 8px;
    }}
    
    QToolButton {{
        background: {theme['tab_active']};
        color: {theme['fg']};
        border: 1px solid {theme['border']};
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: 500;
        font-size: 12px;
    }}
    
    QToolButton:hover {{
        background: {theme['accent']};
        color: #11111b;
    }}
    
    QToolButton:pressed {{
        background: {theme['selection']};
    }}
    
    QStatusBar {{
        background: {theme['statusbar_bg']};
        color: {theme['tab_fg']};
        font-size: 11px;
        border-top: 1px solid {theme['border']};
    }}
    
    QDialog {{
        background-color: {theme['bg']};
        color: {theme['fg']};
    }}
    
    QLabel {{
        color: {theme['fg']};
    }}
    
    QLineEdit, QComboBox, QSpinBox {{
        background-color: {theme['tab_bg']};
        color: {theme['fg']};
        border: 1px solid {theme['border']};
        border-radius: 6px;
        padding: 6px 10px;
        selection-background-color: {theme['selection']};
    }}
    
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border: 1px solid {theme['accent']};
    }}
    
    QPushButton {{
        background-color: {theme['accent']};
        color: #11111b;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
    }}
    
    QPushButton:hover {{
        opacity: 0.9;
    }}
    
    QScrollBar:vertical {{
        border: none;
        background: {theme['bg']};
        width: 10px;
        margin: 0px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {theme['border']};
        min-height: 20px;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {theme['selection']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    """
