import sys
import os
import shlex
import readline

from sh.utils import RED, GREEN, RESET
from sh.environment import Environment
from sh.executor import Executor
from sh.builtins import BUILTIN_REGISTRY

class Shell:
    def __init__(self):
        self.env = Environment()
        self.executor = Executor(self.env)
        self.exit_code = 0
        self._setup_readline()

    def _setup_readline(self):
        """Configures readline for tab completion and history."""
        readline.set_completer(self.env.get_completer())
        if sys.platform == 'linux':
            readline.parse_and_bind("tab: complete")
        else:
            # macOS default binding
            readline.parse_and_bind("bind ^I rl_complete")

    def run(self):
        while True:
            color = RED if self.exit_code else GREEN
            status = f" {color}{self.exit_code}{RESET}"

            try:
                raw_user_input = input(f"${status} ")
            except KeyboardInterrupt:  # ctrl-c
                self.exit_code = 130
                print()
                continue
            except EOFError:  # ctrl-d
                self.exit_code = 0
                print()
                break

            if not raw_user_input.strip():
                continue

            # Split the data using shell-like syntax
            try:
                user_input_list = shlex.split(raw_user_input)
            except ValueError as e:
                print(f"Syntax error: {e}")
                self.exit_code = 2
                continue

            command = user_input_list[0]
            args = user_input_list[1:]

            # Handle built-ins
            if command == "exit":
                break
                
            if command in BUILTIN_REGISTRY:
                self.exit_code = BUILTIN_REGISTRY[command](args, self.env)
            else:
                # Handle external executables
                filepath = self.env.is_in_path(command)
                if filepath and os.access(filepath, os.X_OK):
                    self.exit_code = self.executor.run(user_input_list)
                elif os.access(command, os.X_OK):
                    self.exit_code = self.executor.run(user_input_list)
                else:
                    self.exit_code = 127
                    print(f"{command}: command not found")

def main():
    shell = Shell()
    shell.run()