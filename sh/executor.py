import os
import sys
import subprocess
import pty
import termios
import tty
import select
import signal
import io
from sh.parser import Pipeline, Command
from sh.job_control import JobControl
from sh.builtins import BUILTIN_REGISTRY

class _DummyShell:
    """A dummy shell object to allow builtins to run inside pipelines."""
    def __init__(self, env, job_control):
        self.env = env
        self.exit_code = 0
        self.executor = self
        self.job_control = job_control

class Executor:
    def __init__(self, env):
        self.env = env
        self.job_control = JobControl()
        self.shell_obj = _DummyShell(env, self.job_control)

    def run(self, pipeline: Pipeline):
        if not pipeline.commands:
            return 0

        # If there are multiple commands, route to the pipeline executor
        if len(pipeline.commands) > 1:
            return self._run_pipeline(pipeline)

        # Single Command Execution
        cmd = pipeline.commands[0]
        command_list = [cmd.name] + cmd.args

        use_pty = not cmd.redirects

        stdin_target = None
        stdout_target = None
        stderr_target = None
        files_to_close = []

        if not use_pty:
            for r in cmd.redirects:
                if r.op in ('>', '1>', '>>', '1>>', '&>', '&>>'):
                    mode = 'a' if '>>' in r.op else 'w'
                    f = open(r.target, mode)
                    stdout_target = f
                    if '&' in r.op:
                        stderr_target = f
                    files_to_close.append(f)
                elif r.op in ('2>', '2>>'):
                    mode = 'a' if '>>' in r.op else 'w'
                    f = open(r.target, mode)
                    stderr_target = f
                    files_to_close.append(f)
                elif r.op == '<':
                    stdin_target = open(r.target, 'r')
                    files_to_close.append(stdin_target)
                elif r.op == '2>&1':
                    stderr_target = subprocess.STDOUT

        try:
            if use_pty:
                master_fd, slave_fd = pty.openpty()
                stdin_target = slave_fd
                stdout_target = slave_fd
                stderr_target = slave_fd

            process = subprocess.Popen(
                command_list,
                stdin=stdin_target,
                stdout=stdout_target,
                stderr=stderr_target,
                text=True,
                close_fds=True,
                start_new_session=True
            )

            if use_pty:
                os.close(slave_fd)

            if cmd.background:
                self.job_control.add_job(process.pid, process.pid, ' '.join(command_list))
                if use_pty: os.close(master_fd)
                return 0

            if use_pty:
                old_settings = termios.tcgetattr(sys.stdin)
                try:
                    tty.setraw(sys.stdin.fileno())
                    while process.poll() is None:
                        r, _, _ = select.select([sys.stdin, master_fd], [], [])
                        if sys.stdin in r:
                            d = os.read(sys.stdin.fileno(), 1024)
                            if d:
                                if b'\x03' in d:
                                    try: os.killpg(process.pid, signal.SIGINT)
                                    except ProcessLookupError: pass
                                    d = d.replace(b'\x03', b'')
                                elif b'\x1a' in d:
                                    try: os.killpg(process.pid, signal.SIGTSTP)
                                    except ProcessLookupError: pass
                                    d = d.replace(b'\x1a', b'')
                                if d: os.write(master_fd, d)
                        if master_fd in r:
                            try:
                                d = os.read(master_fd, 1024)
                                if d: os.write(sys.stdout.fileno(), d)
                                else: break
                            except OSError:
                                break
                finally:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    os.close(master_fd)

            # always wait for the process to finish completely to get the return code
            process.wait()

            if process.returncode is not None and process.returncode < 0:
                return 128 + (-process.returncode)
            if process.returncode is None:
                return 1   # Fallback just in case
            return process.returncode

        finally:
            for f in files_to_close:
                f.close()

    def _run_pipeline(self, pipeline: Pipeline):
        """Executes a chain of commands connected by pipes."""
        processes = []
        prev_read_fd = None
        last_stdout = sys.stdout
        files_to_close = []
        last_stage_exit_code = None

        last_cmd = pipeline.commands[-1]

        # Handle redirects on the LAST command of the pipeline (e.g., `ls | grep x > out.txt`)
        for r in last_cmd.redirects:
            if r.op in ('>', '1>', '>>', '1>>'):
                mode = 'a' if '>>' in r.op else 'w'
                f = open(r.target, mode)
                last_stdout = f
                files_to_close.append(f)

        try:
            for i, cmd in enumerate(pipeline.commands):
                command_list = [cmd.name] + cmd.args
                stdin_target = prev_read_fd if prev_read_fd else None

                # If not the last command, create a pipe for stdout
                if i < len(pipeline.commands) - 1:
                    read_fd, write_fd = os.pipe()
                    stdout_target = write_fd
                else:
                    stdout_target = last_stdout

                # If the command is a builtin, we have to run it manually and capture output
                if cmd.name in BUILTIN_REGISTRY:
                    old_stdout = sys.stdout
                    buffer = io.StringIO()
                    sys.stdout = buffer

                    try:
                        self.shell_obj.exit_code = 0
                        builtin_exit_code = BUILTIN_REGISTRY[cmd.name](cmd.args, self.shell_obj)
                        self.shell_obj.exit_code = builtin_exit_code if builtin_exit_code is not None else 0
                    except Exception as e:
                        print(f"Shell Error: {e}", file=sys.stderr)
                        self.shell_obj.exit_code = 1

                    sys.stdout = old_stdout
                    output_str = buffer.getvalue()

                    if i == len(pipeline.commands) - 1:
                        last_stage_exit_code = self.shell_obj.exit_code

                    # Write the builtin's output to the pipe (or terminal)
                    if isinstance(stdout_target, int):
                        os.write(stdout_target, output_str.encode())
                    else:
                        stdout_target.write(output_str)
                else:
                    # External command
                    process = subprocess.Popen(
                        command_list,
                        stdin=stdin_target,
                        stdout=stdout_target,
                        stderr=sys.stderr,
                        close_fds=True
                    )
                    processes.append(process)
                    if i == len(pipeline.commands) - 1:
                        last_stage_exit_code = process

                # Close file descriptors in the parent process
                if prev_read_fd:
                    os.close(prev_read_fd)
                if i < len(pipeline.commands) - 1:
                    os.close(write_fd)
                    prev_read_fd = read_fd

            # Wait for all external processes to finish
            for p in processes:
                p.wait()

            if isinstance(last_stage_exit_code, subprocess.Popen):
                return last_stage_exit_code.returncode if last_stage_exit_code.returncode is not None else 1
            if last_stage_exit_code is None:
                return 1
            return last_stage_exit_code

        finally:
            for f in files_to_close:
                f.close()

