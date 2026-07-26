import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sh.parser import Parser, Pipeline, Command

def test_simple_command():
    p = Parser("ls -l /tmp")
    ast = p.parse()
    assert len(ast.commands) == 1
    assert ast.commands[0].name == "ls"
    assert ast.commands[0].args == ["-l", "/tmp"]
    assert ast.commands[0].background == False

def test_background_command():
    p = Parser("sleep 5 &")
    ast = p.parse()
    assert len(ast.commands) == 1
    assert ast.commands[0].name == "sleep"
    assert ast.commands[0].args == ["5"]
    assert ast.commands[0].background == True

def test_empty_input():
    p = Parser("")
    ast = p.parse()
    assert len(ast.commands) == 0

def test_syntax_error_handling():
    # Unmatched quote should not crash the shell
    p = Parser('echo "unterminated')
    ast = p.parse()
    assert len(ast.commands) == 0