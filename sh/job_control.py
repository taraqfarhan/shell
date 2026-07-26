import os
import signal

class JobControl:
    def __init__(self):
        self.jobs = {}  # Format: {job_id: {"pid": int, "pgid": int, "command": str}}
        self.next_job_id = 1

    def add_job(self, pid: int, pgid: int, command: str) -> int:
        """Registers a new background job."""
        job_id = self.next_job_id
        self.jobs[job_id] = {"pid": pid, "pgid": pgid, "command": command}
        self.next_job_id += 1
        print(f"[{job_id}] {pid}")
        return job_id

    def remove_job(self, job_id: int):
        """Removes a job once it finishes."""
        if job_id in self.jobs:
            del self.jobs[job_id]

    def list_jobs(self):
        """Lists all active background jobs."""
        for job_id, info in self.jobs.items():
            print(f"[{job_id}] {info['pid']} {info['command']}")

    def send_signal_to_pgid(self, pgid: int, sig: int):
        """Sends a signal (like SIGINT) to an entire process group."""
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            pass