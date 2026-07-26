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
        readline.set_completer(self.env.get_completer())
        if sys.platform == 'linux':
            readline.parse_and_bind("tab: complete")
        else:
            readline.parse_and_bind("bind ^I rl_complete")

    def run(self):
        while True:
            color = RED if self.exit_code else GREEN
            status = f" {color}{self.exit_code}{RESET}"

            try:
                raw_user_input = input(f"${status} ")
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

            # 1. PARSE: Convert string to AST
            parser = Parser(raw_user_input)
            pipeline = parser.parse()

            if not pipeline.commands:
                self.exit_code = 2
                continue

            cmd = pipeline.commands[0]

            # 2. EXECUTE: Builtins vs External
            if cmd.name == "exit":
                break
                
            if cmd.name in BUILTIN_REGISTRY:
                self.exit_code = BUILTIN_REGISTRY[cmd.name](cmd.args, self.env)
            else:
                # Pass the AST to the executor
                filepath = self.env.is_in_path(cmd.name)
                if filepath and os.access(filepath, os.X_OK):
                    self.exit_code = self.executor.run(pipeline)
                elif os.access(cmd.name, os.X_OK):
                    self.exit_code = self.executor.run(pipeline)
                else:
                    self.exit_code = 127
                    print(f"{cmd.name}: command not found")

def main():
    """Entry point for the shell."""
    shell = Shell()
    shell.run()