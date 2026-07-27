import os

class JobControl:
    def __init__(self):
        self.jobs = {}
        self.next_job_id = 1

    def add_job(self, pid: int, pgid: int, command: str) -> int:
        job_id = self.next_job_id
        self.jobs[job_id] = {"pid": pid, "pgid": pgid, "command": command}
        self.next_job_id += 1
        print(f"[{job_id}] {pid}")
        return job_id

    def remove_job(self, job_id: int):
        if job_id in self.jobs:
            del self.jobs[job_id]

    def list_jobs(self):
        """Lists active background jobs and reaps finished zombies."""
        active_jobs = {}
        for job_id, info in self.jobs.items():
            try:
                # Wait for process with WNOHANG (non-blocking) to see if it finished
                pid, status = os.waitpid(info['pid'], os.WNOHANG)
                if pid == 0:
                    # Process is still running
                    active_jobs[job_id] = info
                    print(f"[{job_id}] {info['pid']} {info['command']}")
                else:
                    # Process finished, print done message
                    print(f"[{job_id}] Done {info['command']}")
            except ChildProcessError:
                # Process was already reaped
                pass

        # Update the jobs dictionary to only contain active jobs
        self.jobs = active_jobs

    def send_signal_to_pgid(self, pgid: int, sig: int):
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            pass

