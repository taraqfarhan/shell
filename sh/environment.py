import os

class Environment:
    def __init__(self):
        self.executables = set()
        self.executable_paths = set()
        self.builtins = {"echo", "type", "exit", "pwd", "cd"}
        self.all_execs = set()
        self._scan_path()

    def _scan_path(self):
        """Scans the system PATH to find all executable files."""
        path_env = os.getenv("PATH", "")
        for path in path_env.split(os.pathsep):
            if not os.path.exists(path):
                continue
            
            try:
                for executable in os.listdir(path):
                    filepath = os.path.join(path, executable)
                    if os.access(filepath, os.X_OK):
                        self.executable_paths.add(filepath)
                        self.executables.add(executable)
            except PermissionError:
                continue

        self.all_execs = self.builtins.union(self.executables)

    def is_in_path(self, command):
        """Checks if a command exists in the scanned PATH."""
        for path in self.executable_paths:
            # Extract the filename from the full path
            basename = os.path.basename(path)
            if command == basename:
                return path
        return None

    def get_completer(self):
        """Returns a callback function for readline tab completion."""
        all_execs = self.all_execs

        def tab_completer(text, state):
            matches = [cmd for cmd in all_execs if cmd.startswith(text)]
            if state < len(matches):
                return matches[state] + ' '
            return None

        return tab_completer