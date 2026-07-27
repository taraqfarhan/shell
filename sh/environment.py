# sh/environment.py
import os
import readline

class Environment:
    def __init__(self):
        self.executables = set()
        self.executable_paths = set()
        self.builtins = {"echo", "type", "exit", "pwd", "cd"}
        self.all_execs = set()
        self._scan_path()

    def _scan_path(self):
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
        for path in self.executable_paths:
            basename = os.path.basename(path)
            if command == basename:
                return path
        return None

    def get_completer(self):
        all_execs = self.all_execs

        def tab_completer(text, state):
            line = readline.get_line_buffer()
            begin = readline.get_begidx()
            end = readline.get_endidx()

            # 1. Handle standalone tilde completion (e.g., "~" or "~user")
            if text.startswith('~') and '/' not in text:
                if state == 0:
                    return text + '/'
                return None

            matches = []

            # 2. Determine if we are completing the first word (a command)
            # It's a command if there is nothing before the cursor except spaces
            is_command = (line[:begin].strip() == '')

            # If it's a command, check builtins and PATH executables
            if is_command and '/' not in text and not text.startswith('~'):
                for cmd in all_execs:
                    if cmd.startswith(text):
                        matches.append(cmd + ' ')

            # 3. File/Path completion
            # Reconstruct the full word being typed to handle paths correctly
            word_start = begin
            while word_start > 0 and line[word_start-1] not in (' ', '\t'):
                word_start -= 1
            current_word = line[word_start:end]

            # Expand ~ for the whole word (e.g., "~/Desk")
            expanded_word = os.path.expanduser(current_word)
            dirname, basename = os.path.split(expanded_word)

            # Determine the absolute directory to search in
            if not dirname:
                search_dir = os.getcwd()
            elif os.path.isabs(dirname):
                search_dir = dirname
            else:
                search_dir = os.path.join(os.getcwd(), dirname)

            # Scan the directory for matches
            if os.path.isdir(search_dir):
                try:
                    for f in os.listdir(search_dir):
                        if f.startswith(basename):
                            # Reconstruct full path on disk to check if it's a dir
                            full_disk_path = os.path.join(search_dir, f)
                            if os.path.isdir(full_disk_path):
                                matches.append(f + '/')
                            else:
                                matches.append(f + ' ')
                except PermissionError:
                    pass

            # Remove duplicates (e.g., if a command and a file share a name)
            seen = set()
            unique_matches = []
            for m in matches:
                if m not in seen:
                    seen.add(m)
                    unique_matches.append(m)

            if state < len(unique_matches):
                return unique_matches[state]
            return None

        return tab_completer
