import shlex
from dataclasses import dataclass, field
from typing import List

@dataclass
class Command:
    """Represents a single command and its arguments."""
    name: str
    args: List[str]
    background: bool = False  # Set to True if command ends with '&'

@dataclass
class Pipeline:
    """Represents a chain of commands connected by pipes."""
    commands: List[Command] = field(default_factory=list)

class Parser:
    def __init__(self, text: str):
        self.text = text

    def parse(self) -> Pipeline:
        """Parses the input text into a Pipeline AST."""
        try:
            tokens = shlex.split(self.text)
        except ValueError as e:
            print(f"Syntax Error: {e}")
            return Pipeline(commands=[])

        if not tokens:
            return Pipeline(commands=[])

        # Handle background execution '&'
        background = False
        if tokens[-1] == '&':
            background = True
            tokens = tokens[:-1]

        # Split tokens by '|' to identify pipelines
        pipeline = Pipeline()
        current_cmd_tokens = []
        
        for token in tokens:
            if token == '|':
                if current_cmd_tokens:
                    pipeline.commands.append(
                        Command(name=current_cmd_tokens[0], args=current_cmd_tokens[1:])
                    )
                    current_cmd_tokens = []
            else:
                current_cmd_tokens.append(token)
        
        # Add the final command in the pipeline
        if current_cmd_tokens:
            cmd = Command(name=current_cmd_tokens[0], args=current_cmd_tokens[1:])
            if background:
                cmd.background = True
            pipeline.commands.append(cmd)

        return pipeline