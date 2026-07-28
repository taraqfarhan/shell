RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"


def parse_redirections(redirects):
    """
    Parses a list of Redirection objects, opens target files,
    and returns (stdin_target, stdout_target, stderr_target, files_to_close).
    """
    stdin_target = None
    stdout_target = None
    stderr_target = None
    files_to_close = []

    for r in redirects:
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
            f = open(r.target, 'r')
            stdin_target = f
            files_to_close.append(f)
        elif r.op == '2>&1':
            stderr_target = "STDOUT"

    return stdin_target, stdout_target, stderr_target, files_to_close


