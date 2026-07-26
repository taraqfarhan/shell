import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sh.builtins import cd, pwd, echo, type_cmd
from sh.environment import Environment

@pytest.fixture
def env():
    return Environment()

def test_echo(env, capsys):
    exit_code = echo(["hello", "world"], env)
    captured = capsys.readouterr()
    assert captured.out == "hello world\n"
    assert exit_code == 0

def test_pwd(env, capsys, tmp_path, monkeypatch):
    # Change to a temporary directory to test pwd
    monkeypatch.chdir(tmp_path)
    exit_code = pwd([], env)
    captured = capsys.readouterr()
    assert captured.out == f"{tmp_path}\n"
    assert exit_code == 0

def test_cd(env, tmp_path):
    exit_code = cd([str(tmp_path)], env)
    assert exit_code == 0
    assert os.getcwd() == str(tmp_path)

def test_cd_invalid_path(env, capsys):
    exit_code = cd(["/this/path/does/not/exist"], env)
    captured = capsys.readouterr()
    assert "No such file or directory" in captured.out
    assert exit_code == 1

def test_type_builtin(env, capsys):
    exit_code = type_cmd(["cd"], env)
    captured = capsys.readouterr()
    assert "cd is a shell builtin" in captured.out
    assert exit_code == 0