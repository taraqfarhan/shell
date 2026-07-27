# Design Decisions
## 1. Python vs C
While C is traditional for OS projects, Python's os, subprocess, and pty modules provide direct, low-level access to POSIX system calls (like fork behavior via Popen and process group manipulation). This allowed for rapid development of high-level features (like tab completion) while still demonstrating OS module interaction.

## 2. Pseudo-Terminals (PTY)
To ensure interactive programs (like vim or top) run correctly within the shell, the executor allocates a pseudo-terminal pair using pty.openpty(). The child process is attached to the slave end, while the shell reads from the master end. This mimics the behavior of real terminal emulators.

## 3. AST-based Parsing
Rather than executing commands linearly, the shell uses a Parser class to generate an AST. This separates the "what the user typed" from the "how to execute it", allowing for future implementation of control flow (if/while) and proper pipeline management.