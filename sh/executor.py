import os
import sys
import subprocess
import pty

# Supported redirection operators
REDIRECTIONS = {'>', '1>', '2>', '<', '>>', '1>>', '2>>', '2>&1', '&>', '>&', '&>>', '<<<'}

class Executor:
    def __init__(self, env):
        self.env = env

    def run(self, command_list):
        # If the command involves redirections, fall back to os.system
        if any(part in REDIRECTIONS for part in command_list):
            waitstatus = os.system(' '.join(command_list))
            return os.waitstatus_to_exitcode(waitstatus)

        # Pseudo-terminal controller pair
        master_fd, slave_fd = pty.openpty()

        # Process attached to the pseudo-terminal
        process = subprocess.Popen(
            command_list,
            stdout=slave_fd,
            stderr=slave_fd,  # merge stderr into stdout stream
            text=True,
            close_fds=True
        )

        os.close(slave_fd)

        # Read from the master descriptor in real-time
        while True:
            try:
                data = os.read(master_fd, 1024).decode("utf-8", errors="ignore")
            except OSError:
                break

            if not data:
                break

            print(data, end='')
            sys.stdout.flush()

        os.close(master_fd)
        process.wait()

        return process.returncode