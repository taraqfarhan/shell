# sh/builtins.py (Replace the entire file)
import os

def cd(args, shell):
    if not args:
        path = os.path.expanduser("~")
    else:
        path = os.path.expanduser(args[0])

    if os.path.exists(path):
        try:
            os.chdir(path)
            return 0
        except NotADirectoryError:
            print(f"cd: {path}: Not a directory")
            return 1
    else:
        print(f"cd: {path}: No such file or directory")
        return 1

def pwd(args, shell):
    print(os.getcwd())
    return 0

def type_cmd(args, shell):
    env = shell.env
    exit_code = 0
    for arg in args:
        if arg in env.builtins:
            print(f"{arg} is a shell builtin")
            continue

        filepath = env.is_in_path(arg)
        if filepath:
            print(f"{arg} is {filepath}")
        else:
            print(f"{arg}: not found")
            exit_code = 1
    return exit_code

def echo(args, shell):
    print(' '.join(args))
    return 0

def jobs(args, shell):
    shell.executor.job_control.list_jobs()
    return 0

BUILTIN_REGISTRY = {
    "cd": cd,
    "pwd": pwd,
    "type": type_cmd,
    "echo": echo,
    "jobs": jobs,
}
