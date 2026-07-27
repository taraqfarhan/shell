import sys
import os
import readline
from pathlib import Path

from sh.utils import RED, GREEN, RESET
from sh.environment import Environment
from sh.executor import Executor
from sh.parser import Parser
from sh.builtins import BUILTIN_REGISTRY

HISTORY_FILE = Path.home() / ".mysh_history"

class Shell:
    def __init__(self):
        self.env = Environment()
        self.executor = Executor(self.env)
        self.exit_code = 0
        self._setup_readline()
        self._load_history()

    def _setup_readline(self):
        # Tell readline to break words on spaces and slashes
        readline.set_completer_delims(' \t\n/')

        readline.set_completer(self.env.get_completer())
        if sys.platform == 'linux':
            readline.parse_and_bind("tab: complete")
        else:
            readline.parse_and_bind("bind ^I rl_complete")

    def _load_history(self):
        """Load history from ~/.mysh_history"""
        if HISTORY_FILE.exists():
            readline.read_history_file(str(HISTORY_FILE))

    def _save_history(self):
        """Save history to ~/.mysh_history"""
        # Limit history to 1000 entries
        readline.set_history_length(1000)
        try:
            readline.write_history_file(str(HISTORY_FILE))
        except OSError:  # permission issues, filesystem errors
            pass

    def execute_builtin(self, cmd):
        old_stdin = sys.stdin
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        files_to_close = []

        try:
            for r in cmd.redirects:
                if r.op in ('>', '1>', '>>', '1>>', '&>', '&>>'):
                    mode = 'a' if '>>' in r.op else 'w'
                    f = open(r.target, mode)
                    sys.stdout = f
                    if '&' in r.op:
                        sys.stderr = f
                    files_to_close.append(f)
                elif r.op in ('2>', '2>>'):
                    mode = 'a' if '>>' in r.op else 'w'
                    f = open(r.target, mode)
                    sys.stderr = f
                    files_to_close.append(f)
                elif r.op == '<':
                    f = open(r.target, 'r')
                    sys.stdin = f
                    files_to_close.append(f)
                elif r.op == '2>&1':
                    sys.stderr = sys.stdout

            self.exit_code = BUILTIN_REGISTRY[cmd.name](cmd.args, self)
        finally:
            sys.stdin = old_stdin
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            for f in files_to_close:
                f.close()

    def run(self):
        try:
            while True:
                color = RED if self.exit_code else GREEN
                cwd = os.path.basename(os.getcwd()) or "/"
                prompt = f"$ {cwd} {color}{self.exit_code}{RESET} "

                try:
                    raw_user_input = input(prompt)
                except KeyboardInterrupt:
                    self.exit_code = 130
                    print()
                    continue
                except EOFError:
                    self.exit_code = 0
                    print()
                    break

                if not raw_user_input.strip():
                    continue

                parser = Parser(raw_user_input, self.exit_code)
                pipeline = parser.parse()

                if not pipeline.commands:
                    self.exit_code = 2
                    continue

                cmd = pipeline.commands[0]

                if cmd.name == "exit":
                    break

                if cmd.name in BUILTIN_REGISTRY:
                    self.execute_builtin(cmd)
                else:
                    filepath = self.env.is_in_path(cmd.name)
                    if filepath and os.access(filepath, os.X_OK):
                        self.exit_code = self.executor.run(pipeline)
                    elif os.access(cmd.name, os.X_OK):
                        self.exit_code = self.executor.run(pipeline)
                    else:
                        self.exit_code = 127
                        print(f"{cmd.name}: command not found")
        finally:
            # Save history on exit
            self._save_history()

def main():
    shell = Shell()
    shell.run()
