# sh/shell.py
import sys
import os
import readline

from sh.utils import RED, GREEN, RESET
from sh.environment import Environment
from sh.executor import Executor
from sh.parser import Parser
from sh.builtins import BUILTIN_REGISTRY

class Shell:
    def __init__(self):
        self.env = Environment()
        self.executor = Executor(self.env)
        self.exit_code = 0
        self._setup_readline()

    def _setup_readline(self):
        # Tell readline NOT to break words on '/' so paths complete correctly
        readline.set_completer_delims(' \t\n/')

        readline.set_completer(self.env.get_completer())
        if sys.platform == 'linux':
            readline.parse_and_bind("tab: complete")
        else:
            # macOS default binding
            readline.parse_and_bind("bind ^I rl_complete")

    def execute_builtin(self, cmd):
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
                elif r.op == '2>&1':
                    sys.stderr = sys.stdout

            self.exit_code = BUILTIN_REGISTRY[cmd.name](cmd.args, self)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            for f in files_to_close:
                f.close()

    def run(self):
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

def main():
    shell = Shell()
    shell.run()
