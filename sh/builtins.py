import os
import readline

def cd(args, shell):
    # Track current working directory for OLDPWD
    old_pwd = os.getcwd()

    # Case 1: No arguments -> Go to HOME (~)
    if not args:
        path = os.path.expanduser("~")
    # Case 2: cd - -> Go to previous working directory (OLDPWD)
    elif args[0] == "-":
        oldpwd_val = os.getenv("OLDPWD") or getattr(shell, "oldpwd", None)
        if not oldpwd_val:
            print("cd: OLDPWD not set")
            return 1
        path = oldpwd_val
        print(path)
    # Case 3: Flag handling (-L logical vs -P physical)
    elif args[0] in ("-L", "-P") and len(args) > 1:
        physical = (args[0] == "-P")
        target_path = os.path.expanduser(args[1])
        path = os.path.realpath(target_path) if physical else target_path
    else:
        path = os.path.expanduser(args[0])

    # Change directory
    try:
        if os.path.islink(path) and os.path.isdir(os.path.realpath(path)):
            path = os.path.realpath(path)
            
        os.chdir(path)
        # Update OLDPWD and PWD environment variables
        os.environ["OLDPWD"] = old_pwd
        shell.oldpwd = old_pwd
        os.environ["PWD"] = os.getcwd()
        return 0
    except NotADirectoryError:
        print(f"cd: {args[0]}: Not a directory")
        return 1
    except FileNotFoundError:
        if os.path.islink(path):
            print(f"cd: {args[0]}: No such file or directory (broken symlink)")
        else:
            print(f"cd: {args[0]}: No such file or directory")
        return 1
    except PermissionError:
        print(f"cd: {args[0]}: Permission denied")
        return 1
    except OSError as e:
        print(f"cd: {args[0]}: {e.strerror}")
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

def history(args, shell):
    """Prints the command history stored by readline"""
    length = readline.get_current_history_length()
    for i in range(1, length+1):
        item = readline.get_history_item(i)
        if item:
            print(f"{i}  {item}")
    return 0


BUILTIN_REGISTRY = {
    "cd": cd,
    "pwd": pwd,
    "type": type_cmd,
    "echo": echo,
    "jobs": jobs,
    "history": history
}
