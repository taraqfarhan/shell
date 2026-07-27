# Architecture: sh
This document outlines the architecture of the custom shell, designed to fulfill CSE 3200 requirements for structured programming and OS module interaction.

## Data Flow
The shell operates on a standard Read-Eval-Print Loop (REPL) architecture, but separates concerns into distinct modules:

1. REPL (shell.py): Captures user input via readline.
2. Lexer/Parser (parser.py): Converts raw text into an Abstract Syntax Tree (AST) consisting of Pipeline and Command objects. This satisfies the "Structured Program" requirement.
3. Environment (environment.py): Tracks the system $PATH and available executables for tab completion.
4. Executor (executor.py): Takes the AST and handles process creation using subprocess.Popen and pty.openpty().
5. Job Control (job_control.py): Manages background processes using POSIX process groups (start_new_session=True).

## Future Extensibility
Because the parser builds an AST, adding support for if/else statements, for loops, and multi-stage pipes (|) simply requires expanding the Parser and Executor classes, without modifying the core REPL.