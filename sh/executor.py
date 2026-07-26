import os
import sys
import subprocess
import pty
from sh.parser import Pipeline, Command
from sh.job_control import JobControl

REDIRECTIONS = {'>', '1>', '2>', '<', '>>', '1>>', '2>>', '2>&1', '&>', '>&', '&>>', '<<<'}

class Executor:
    def __init__(self, env):
        self.env = env
        self.job_control = JobControl()

    def run(self, pipeline: Pipeline):
        """Executes a parsed pipeline."""
        if not pipeline.commands:
            return 0

        # For MVP, we only execute the first command (no actual piping yet)
        # But the structure is ready for it!
        cmd = pipeline.commands[0]
        command_list = [cmd.name] + cmd.args

        # Handle redirections (basic fallback to os.system)
        if any(part in REDIRECTIONS for part in command_list):
            waitstatus = os.system(' '.join(command_list))
            return os.waitstatus_to_exitcode(waitstatus)

        # Pseudo-terminal controller pair
        master_fd, slave_fd = pty.openpty()

        # Process attached to the pseudo-terminal
        process = subprocess.Popen(
            command_list,
            stdout=slave_fd,
            stderr=slave_fd,
            text=True,
            close_fds=True,
            start_new_session=True  # Creates a new process group!
        )

        os.close(slave_fd)

        if cmd.background:
            # If backgrounded, don't wait for it. Add to job table.
            self.job_control.add_job(process.pid, os.getpgid(process.pid), ' '.join(command_list))
            os.close(master_fd)
            return 0

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