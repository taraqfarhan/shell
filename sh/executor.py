# sh/executor.py
import os
import sys
import subprocess
import pty
import termios
import tty
import select
import signal
from sh.parser import Pipeline, Command
from sh.job_control import JobControl

class Executor:
    def __init__(self, env):
        self.env = env
        self.job_control = JobControl()

    def run(self, pipeline: Pipeline):
        if not pipeline.commands:
            return 0

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
                                # Check for Ctrl-C (0x03) and Ctrl-Z (0x1a)
                                if b'\x03' in d:
                                    try:
                                        os.killpg(process.pid, signal.SIGINT)
                                    except ProcessLookupError:
                                        pass
                                    d = d.replace(b'\x03', b'')
                                elif b'\x1a' in d:
                                    try:
                                        os.killpg(process.pid, signal.SIGTSTP)
                                    except ProcessLookupError:
                                        pass
                                    d = d.replace(b'\x1a', b'')

                                if d:
                                    os.write(master_fd, d)
                        if master_fd in r:
                            try:
                                d = os.read(master_fd, 1024)
                                if d:
                                    os.write(sys.stdout.fileno(), d)
                                else:
                                    break
                            except OSError:
                                break
                finally:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    os.close(master_fd)

            process.wait()

            if process.returncode is not None and process.returncode < 0:
                return 128 + (-process.returncode)

            return process.returncode

        finally:
            for f in files_to_close:
                f.close()


# import os
# import sys
# import subprocess
# import pty
# import termios
# import tty
# import select
# from sh.parser import Pipeline, Command
# from sh.job_control import JobControl

# class Executor:
#     def __init__(self, env):
#         self.env = env
#         self.job_control = JobControl()

#     def run(self, pipeline: Pipeline):
#         if not pipeline.commands:
#             return 0

#         cmd = pipeline.commands[0]
#         command_list = [cmd.name] + cmd.args

#         use_pty = not cmd.redirects

#         stdin_target = None
#         stdout_target = None
#         stderr_target = None
#         files_to_close = []

#         if not use_pty:
#             for r in cmd.redirects:
#                 if r.op in ('>', '1>', '>>', '1>>', '&>', '&>>'):
#                     mode = 'a' if '>>' in r.op else 'w'
#                     f = open(r.target, mode)
#                     stdout_target = f
#                     if '&' in r.op:
#                         stderr_target = f
#                     files_to_close.append(f)
#                 elif r.op in ('2>', '2>>'):
#                     mode = 'a' if '>>' in r.op else 'w'
#                     f = open(r.target, mode)
#                     stderr_target = f
#                     files_to_close.append(f)
#                 elif r.op == '<':
#                     stdin_target = open(r.target, 'r')
#                     files_to_close.append(stdin_target)
#                 elif r.op == '2>&1':
#                     stderr_target = subprocess.STDOUT

#         try:
#             if use_pty:
#                 master_fd, slave_fd = pty.openpty()
#                 stdin_target = slave_fd
#                 stdout_target = slave_fd
#                 stderr_target = slave_fd

#             process = subprocess.Popen(
#                 command_list,
#                 stdin=stdin_target,
#                 stdout=stdout_target,
#                 stderr=stderr_target,
#                 text=True,
#                 close_fds=True,
#                 start_new_session=True
#             )

#             if use_pty:
#                 os.close(slave_fd)

#             if cmd.background:
#                 # start_new_session=True makes the PID the PGID
#                 self.job_control.add_job(process.pid, process.pid, ' '.join(command_list))
#                 if use_pty: os.close(master_fd)
#                 return 0

#             if use_pty:
#                 old_settings = termios.tcgetattr(sys.stdin)
#                 try:
#                     tty.setraw(sys.stdin.fileno())
#                     while process.poll() is None:
#                         # Block indefinitely until I/O is ready (prevents 100% CPU usage)
#                         r, _, _ = select.select([sys.stdin, master_fd], [], [])
#                         if sys.stdin in r:
#                             d = os.read(sys.stdin.fileno(), 1024)
#                             if d:
#                                 os.write(master_fd, d)
#                         if master_fd in r:
#                             try:
#                                 d = os.read(master_fd, 1024)
#                                 if d:
#                                     os.write(sys.stdout.fileno(), d)
#                                 else:
#                                     break
#                             except OSError:
#                                 break
#                 finally:
#                     termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
#                     os.close(master_fd)

#             process.wait()

#             if process.returncode is not None and process.returncode < 0:
#                 return 128 + (-process.returncode)

#             return process.returncode

#         finally:
#             for f in files_to_close:
#                 f.close()
