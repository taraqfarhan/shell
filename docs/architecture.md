# Architecture: sh

This document outlines the architecture of **sh**, a custom Python-based Unix shell designed for structured programming, AST parsing, and OS-level system interaction.

---

## High-Level Architecture Overview

```
                      +-------------------+
                      |   User Interface  |
                      |     (REPL)        |
                      +---------+---------+
                                |
                          Raw User Input
                                |
                                v
                      +-------------------+
                      |   Lexer & Parser  | <--- Expands $?, $VAR, ~
                      +---------+---------+
                                |
                          Pipeline AST
                                |
                                v
                      +-------------------+
                      |     Executor      | <--- Tab Completion & PATH (Environment)
                      +----+---------+----+
                           |         |
         Single Command    |         | Multi-Command Pipeline
       (PTY / Redirection) |         | (os.pipe & io.StringIO)
                           v         v
                      +----+---------+----+
                      |    Job Control    | <--- Background jobs (&) & os.waitpid
                      +-------------------+
```

---

## System Modules & Responsibilities

The shell follows a modular architecture that cleanly isolates input processing, parsing, environment resolution, process execution, job control, and builtin command handling:

### 1. REPL (`sh/shell.py`)
- **Main Loop**: Drives the interactive Read-Eval-Print Loop (REPL).
- **Prompt Rendering**: Dynamically displays the current working directory name and the color-coded exit status of the previous command (`GREEN` for `0`, `RED` for non-zero exit codes).
- **Readline Integration**: Initializes tab completion, configures completer word delimiters (` \t\n/`), and binds completion keys per OS platform.
- **History Management**: Loads and persists command history up to 1,000 entries to `~/.mysh_history`.
- **Builtin Redirection Handling**: Intercepts standard output and error descriptors to support file redirections directly for builtin commands.

### 2. Lexer & Parser (`sh/parser.py`)
- **Variable & Path Expansion**: Automatically expands exit codes (`$?`), environment variables (`$VAR`), and tilde home directories (`~`).
- **Tokenization**: Uses `shlex.split` for safe handling of quoted strings and escaped characters.
- **AST Generation**: Converts flat tokens into an Abstract Syntax Tree composed of `Pipeline`, `Command`, and `Redirection` dataclasses.
- **Pipeline & Operator Identification**: Detects background markers (`&`), pipeline splitters (`|`), and input/output redirection operators (`>`, `1>`, `2>`, `<`, `>>`, `1>>`, `2>>`, `2>&1`, `&>`, `>&`, `&>>`, `<<<`).

### 3. Environment & Completion (`sh/environment.py`)
- **PATH Resolution**: Scans system `PATH` directories on initialization, building a set of available executables and their absolute file paths.
- **Context-Aware Completion**: 
  - *Command Position*: Offers completion matching builtins and system executables.
  - *File/Path Position*: Offers directory and file autocompletion with trailing slashes (`/`) for directories and spaces for files.
  - *Tilde Expansion*: Supports completion on `~` paths.

### 4. Process Executor (`sh/executor.py`)
- **Single Process Execution**:
  - **Pseudo-Terminal (PTY)**: Allocates a pseudo-terminal pair via `pty.openpty()` for interactive commands (e.g., `vim`, `top`), putting the child process in a new session (`start_new_session=True`).
  - **Terminal Raw Mode & Signal Forwarding**: Configures stdin to raw mode (`tty.setraw`) and uses `select.select` to forward keyboard interrupts (`Ctrl+C` / `SIGINT`) and suspend signals (`Ctrl+Z` / `SIGTSTP`) to the active process group (`os.killpg`).
- **File Redirection Mode**: When redirections are detected, bypasses PTY allocation and routes standard file descriptors directly to files.
- **Pipeline Execution (`_run_pipeline`)**:
  - Connects multiple commands in a chain using Unix pipes (`os.pipe()`).
  - Interoperates cleanly with builtins in pipeline chains by executing builtins in-process, capturing output in an in-memory buffer (`io.StringIO`), and writing to pipe file descriptors.

### 5. Job Control (`sh/job_control.py`)
- **Background Tracking**: Manages background job records (Job ID, PID, Process Group ID, command string) when executed with trailing `&`.
- **Non-Blocking Reaping**: Uses `os.waitpid(pid, os.WNOHANG)` inside the `jobs` command to reap finished background processes without stalling the REPL.
- **Process Group Signals**: Provides helper routines (`os.killpg`) to deliver signals to entire process groups.

### 6. Builtin Commands (`sh/builtins.py`)
- Implements shell builtins: `cd`, `pwd`, `type`, `echo`, `jobs`, `history`, and `exit`.
- Registered via `BUILTIN_REGISTRY` dispatch table for modular lookup and invocation.

### 7. Utilities (`sh/utils.py`)
- Encapsulates ANSI color code strings (`RED`, `GREEN`, `RESET`) for prompt status styling.

---

## Key Data Structures

```python
@dataclass
class Redirection:
    op: str       # Redirection operator (e.g., '>', '>>', '<', '2>&1')
    target: str   # File path or descriptor target

@dataclass
class Command:
    name: str                   # Command executable or builtin name
    args: List[str]             # List of command arguments
    background: bool = False    # Run in background flag (&)
    redirects: List[Redirection] # Associated I/O redirections

@dataclass
class Pipeline:
    commands: List[Command]     # Sequential commands connected by pipes (|)
```

---

## Data Flow Lifecycle

1. **User Input**: Input line is read by `Shell.run()` via `input(prompt)`.
2. **Parsing**: `Parser` preprocesses variables (`$?`, `$VAR`), tokenizes with `shlex`, resolves tildes (`~`), and constructs a `Pipeline` AST.
3. **Dispatch**:
   - If single builtin and no pipeline: executed in-process by `Shell.execute_builtin()`.
   - If external program or pipeline: handed off to `Executor.run(pipeline)`.
4. **Execution**:
   - Single external command: spawned using `subprocess.Popen` attached to a pseudo-terminal pair (`pty.openpty()`) or redirected file handles.
   - Pipeline (`cmd1 | cmd2`): connected via inter-process pipes (`os.pipe()`) in `Executor._run_pipeline()`.
5. **Job Control**: Background processes (`&`) are assigned a Job ID, logged, and tracked asynchronously.
6. **Prompt Refresh**: The shell captures the return status code and updates the prompt color for the next iteration.