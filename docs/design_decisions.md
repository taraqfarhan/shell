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