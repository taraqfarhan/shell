import shlex
import os
import re
from dataclasses import dataclass, field
from typing import List

@dataclass
class Redirection:
    op: str
    target: str

@dataclass
class Command:
    name: str
    args: List[str]
    background: bool = False
    redirects: List[Redirection] = field(default_factory=list)

@dataclass
class Pipeline:
    commands: List[Command] = field(default_factory=list)

REDIRECTIONS = {'>', '1>', '2>', '<', '>>', '1>>', '2>>', '2>&1', '&>', '>&', '&>>', '<<<'}

class Parser:
    def __init__(self, text: str, exit_code: int = 0):
        # 1. Expand $? to the last exit code
        text = text.replace('$?', str(exit_code))

        # 2. Expand $VAR (e.g., $USER, $PATH) using regex
        def replace_env(match):
            var_name = match.group(1)
            # If the variable doesn't exist, return empty string instead of the original text
            return os.getenv(var_name, "")
        text = re.sub(r'\$(\w+)', replace_env, text)

        self.text = text

    def parse(self) -> Pipeline:
        try:
            tokens = shlex.split(self.text)
        except ValueError as e:
            print(f"Syntax Error: {e}")
            return Pipeline(commands=[])

        if not tokens:
            return Pipeline(commands=[])

        # 3. Expand ~ to home directory for all tokens
        tokens = [os.path.expanduser(t) for t in tokens]

        background = False
        if tokens[-1] == '&':
            background = True
            tokens = tokens[:-1]

        pipeline = Pipeline()
        current_cmd_tokens = []
        current_redirects = []

        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token == '|':
                if current_cmd_tokens:
                    pipeline.commands.append(
                        Command(name=current_cmd_tokens[0], args=current_cmd_tokens[1:], redirects=current_redirects)
                    )
                    current_cmd_tokens = []
                    current_redirects = []
            elif token in REDIRECTIONS:
                if i + 1 < len(tokens):
                    current_redirects.append(Redirection(op=token, target=tokens[i+1]))
                    i += 1  # skip target
                else:
                    print("Syntax Error: missing redirect target")
                    return Pipeline(commands=[])
            else:
                current_cmd_tokens.append(token)
            i += 1

        if current_cmd_tokens:
            cmd = Command(name=current_cmd_tokens[0], args=current_cmd_tokens[1:], redirects=current_redirects)
            if background:
                cmd.background = True
            pipeline.commands.append(cmd)

        return pipeline

