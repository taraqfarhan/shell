# Design Decisions

This document details the design choices and architectural tradeoffs made during the development of **sh**.

---

## 1. Language Choice: Python vs C

While traditional Unix shells are authored in C, Python was selected for this project because Python's standard library modules (`os`, `subprocess`, `pty`, `termios`, `select`, `readline`, `shlex`) provide direct, low-level access to POSIX system calls while facilitating clean code organization and maintainability.

- **System Calls**: `pty.openpty()`, `os.pipe()`, `os.killpg()`, and `os.waitpid()` map directly to their underlying POSIX C equivalents.
- **Robust Parsing**: Modules like `shlex` and `re` allow safe, robust tokenization and string interpolation without risk of memory safety bugs.
- **Rich Interactive Features**: Python's `readline` library enables tab autocompletion and persistent history without requiring external dependencies.

---

## 2. AST-Based Parsing Architecture

Rather than evaluating commands line-by-line using naive string splitting, **sh** uses an Abstract Syntax Tree (AST) constructed via explicit dataclasses (`Pipeline`, `Command`, `Redirection`).

- **Separation of Concerns**: The `Parser` class handles syntax validation, environment variable interpolation (`$?`, `$VAR`), tilde expansion (`~`), and token grouping into AST objects. The `Executor` class receives pure AST data structures to execute.
- **Extensibility**: Abstract syntax representation allows supporting pipelines (`|`), I/O redirections (`>`, `>>`, `<`, etc.), and background execution (`&`) without modifying the core REPL loop.

---

## 3. Dual Execution Engine (PTY vs File Redirection)

Interactive command-line applications (such as `vim`, `top`, or `less`) require a terminal TTY interface to correctly receive keyboard input and render full-screen ANSI sequences.

- **Pseudo-Terminal Allocation**: For standard interactive commands without file redirections, `Executor` allocates a pseudo-terminal pair using `pty.openpty()`. The child process is attached to the slave FD, while the shell reads/writes via the master FD.
- **Raw Mode & Signal Handling**: The parent shell places its stdin into raw mode (`tty.setraw`) and uses `select.select` to asynchronously multiplex I/O. Keyboard signals (`Ctrl+C` / `SIGINT` and `Ctrl+Z` / `SIGTSTP`) are intercepted and forwarded to the child process group via `os.killpg()`.
- **Bypassing PTY on Redirection**: When I/O redirection (e.g., `cmd > out.txt`) is specified, PTY mode is bypassed. Standard file handles are attached directly to child process descriptors to ensure clean file output without PTY control escape characters.

---

## 4. Multi-Stage Pipelines & Builtin Interoperability

Pipelines allow arbitrary chains of processes to stream data sequentially (`cmd1 | cmd2 | cmd3`).

- **Unix Pipes**: Inter-process communication is established using standard `os.pipe()` file descriptors passed into `subprocess.Popen(stdin=..., stdout=...)`.
- **Builtin Integration in Pipelines**: Python builtins (`echo`, `pwd`, `history`, `type`, `cd`) execute within the shell's process rather than separate binaries. When a builtin appears in a pipeline chain, the shell redirects `sys.stdout` into an in-memory buffer (`io.StringIO`), captures the output string, and writes the bytes directly to the pipeline file descriptor.

---

## 5. Non-Blocking Job Control

Background process execution (`command &`) requires tracking child processes without blocking the interactive prompt.

- **Process Group Isolation**: Spawning processes with `start_new_session=True` assigns each process a distinct Process Group ID (PGID), preventing background jobs from receiving signals intended for foreground shell tasks.
- **Non-Blocking Reaping**: The `JobControl` class tracks active PIDs and queries status via non-blocking status calls (`os.waitpid(pid, os.WNOHANG)`) when `jobs` is invoked, reaping zombie processes without introducing background thread overhead or blocking the REPL.

---

## 6. Context-Aware Tab Completion

The tab completion engine (`Environment.get_completer()`) dynamically tailors suggestions based on the cursor position:

- **Command Completer**: If tab is pressed on the first token of a line, completions are drawn from both shell builtins and system executables located across `PATH`.
- **Path & Directory Completer**: If tab is pressed on subsequent arguments or file paths, the completer scans local disk paths, expanding `~` to the user's home directory and appending `/` to directory matches and space (` `) to regular files.

---

## 7. Persistent Command History & Status-Aware Prompt

- **History File**: Shell history is loaded on startup from `~/.mysh_history` and flushed on exit, maintaining up to 1,000 commands across sessions.
- **Visual Exit Status**: The shell prompt displays the current working directory along with the exit status of the previously executed command, highlighted in **GREEN** for code `0` and **RED** for error status codes.

---

## 8. Native PyQt6 Desktop GUI Architecture (`sh_gui`)

Rather than relying on web/Electron wrappers or external terminal emulators, **sh** features a native PyQt6 Desktop GUI (`app_gui.py` / `sh_gui`).

- **Design Language**: Sleek dark/light theme palettes, bottom-positioned left-aligned tab bar (`TabPosition.South`), clean status bar metrics, and no emoji clutter.
- **Sub-Process PTY Integration**: Launches `python3 -m sh` in a dedicated pseudo-terminal worker thread (`PTYSession`), setting `SHELL=sh` and injecting `PYTHONPATH` so the GUI natively runs the custom shell engine.

---

## 9. Native QPainter Grid Rendering & Sub-Pixel Precision

Rather than wrapping heavy text-editing widgets (`QTextEdit`), the terminal interface uses a custom `QPainter` 2D grid character canvas (`TerminalWidget`) backed by `pyte` VT100 screen parsing.

- **Floating-Point Advance Metrics**: Calculates character and cursor pixel coordinates using floating-point advance widths (`char_width_float`), preventing rounding drift over multiple text columns.
- **Unified Cell & Cursor Mapping**: Both character text and the block cursor derive positions from shared coordinate helper functions (`get_col_x` and `get_row_y`), ensuring 100% pixel-perfect text/cursor alignment at every font size and zoom level.
- **Targeted Cell Repainting**: Invokes `self.update(QRect)` on the specific cursor bounding cell during cursor blink cycles, completely eliminating full-screen repaints and text flickering.

---

## 10. Focus Navigation Interception (`focusNextPrevChild`)

Standard Qt container widgets intercept the <kbd>Tab</kbd> key for focus navigation between controls.

- **Focus Navigation Override**: Overrides `focusNextPrevChild` on `TerminalWidget` to return `False`. This prevents Qt from trapping tab focus, allowing `b'\t'` to pass directly to the underlying PTY for shell tab completion.

---

## 11. Bidirectional `pyte` Line Buffer Synchronization

When terminal window dimensions or font sizes change, `pyte.HistoryScreen.resize()` shifts buffer lines.

- **Cursor Position Tracking**: Tracks history line deltas during grid resizes, shifting `screen.cursor.y` up when grid height shrinks and down when lines are restored from history. This prevents the cursor block from drifting away from active prompt lines.

---

## 12. Readline Escape Sequence Protection (`\001` & `\002`)

Python's `readline` module calculates prompt length by counting characters. Raw ANSI color escape codes (`\033[92m`) cause `readline` to overestimate visual prompt width, resulting in text overwriting on multi-line inputs.

- **Non-Printing Character Wrapping**: Wraps all ANSI prompt escape sequences in Readline's `\001` (start ignore) and `\002` (end ignore) markers in `sh/shell.py`. `readline` ignores color codes when computing prompt width, enabling clean multi-line wrapping.

---

## 13. POSIX Symlink & `cd` Navigation

- **Logical vs Physical Path Resolution**: `cd` preserves logical symlink directory paths in `$PWD` by default (`cd -L`), while supporting physical resolution via `-P`.
- **Previous Directory Toggle (`cd -`)**: Toggles to `$OLDPWD` and prints the path.
- **Diagnostic Error Handling**: Detects symlinks to regular files and broken symlinks, returning clear diagnostic messages (`cd: <path>: Not a directory` or `cd: <path>: No such file or directory (broken symlink)`).