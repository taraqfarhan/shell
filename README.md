# sh — Unix Shell & PyQt6 Terminal Emulator

A simple Unix shell implemented in Python, complete with a full-fledged **PyQt6 Terminal Emulator**.

---

### PyQt6 Desktop Terminal GUI (`sh_gui`).
<a href="terminal.png">
  <img src="terminal.png" alt="PyQt6 Terminal Emulator" width="600" height="650"/>
</a>

## Getting Started

### 1. Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies (PyQt6 & pyte)
pip install PyQt6 pyte
```

### 2. Launch the CLI Shell

```bash
.venv/bin/python3 -m sh
```

### 3. Launch the PyQt6 Desktop GUI Terminal

```bash
.venv/bin/python3 app_gui.py
# or
.venv/bin/python3 -m sh_gui
```

#### GUI Keyboard Shortcuts

| Shortcut | Action |
| --- | --- |
| `Cmd+T` / `Ctrl+T` | Open New Terminal Tab |
| `Cmd+W` / `Ctrl+W` | Close Active Terminal Tab |
| `Cmd+V` / `Ctrl+V` | Paste Clipboard |
| `Cmd+=` / `Cmd+-` | Zoom In / Zoom Out |
| `Cmd+0` | Reset Font Zoom |
| `Ctrl+L` | Clear Terminal Screen |

