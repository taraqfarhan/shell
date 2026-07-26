import os

def cd(args, env):
    if not args:
        # Default to home directory if no path is provided
        path = os.path.expanduser("~")
    else:
        path = os.path.expanduser(args[0])
        
    if os.path.exists(path):
        os.chdir(path)
        return 0
    else:
        print(f"cd: {path}: No such file or directory")
        return 1

def pwd(args, env):
    print(os.getcwd())
    return 0

def type_cmd(args, env):
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

def echo(args, env):
    print(' '.join(args))
    return 0

# Registry mapping command names to functions
BUILTIN_REGISTRY = {
    "cd": cd,
    "pwd": pwd,
    "type": type_cmd,
    "echo": echo,
    # "exit" is handled directly in the REPL loop
}