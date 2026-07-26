import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sh.parser import Parser
from sh.executor import Executor
from sh.environment import Environment

def test_executor_runs_command(capsys):
    env = Environment()
    executor = Executor(env)
    
    parser = Parser("echo testing_execution")
    pipeline = parser.parse()
    
    exit_code = executor.run(pipeline)
    captured = capsys.readouterr()
    
    assert "testing_execution" in captured.out
    assert exit_code == 0

def test_executor_returns_nonzero_exit_code():
    env = Environment()
    executor = Executor(env)
    
    # 'false' is a coreutil that always returns exit code 1
    parser = Parser("false")
    pipeline = parser.parse()
    
    exit_code = executor.run(pipeline)
    assert exit_code == 1