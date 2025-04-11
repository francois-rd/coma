import pytest

from coma.core.singleton import Coma
from coma import command, wake
import coma


def test_one_procedural(capsys):
    Coma.reset()
    command(name="test", cmd=lambda: print("passed"))
    wake(cli_args=["test"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == ""


def test_one_decorator(capsys):
    Coma.reset()

    @command
    def test():
        print("passed")

    wake(cli_args=["test"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == ""


def test_mix_procedural_decorator(capsys):
    Coma.reset()

    command(name="proc", cmd=lambda: ...)

    @command(name="deco")
    def cmd():
        pass

    with pytest.raises(SystemExit) as exec_info:
        wake(cli_args=["-h"])
    out, err = capsys.readouterr()
    assert exec_info.value.code == 0
    assert "{proc,deco}" in out.strip() and err.strip() == ""


def test_mix_decorator_procedural(capsys):
    Coma.reset()

    @command(name="deco")
    def cmd():
        pass

    command(name="proc", cmd=lambda: ...)
    with pytest.raises(SystemExit) as exec_info:
        wake(cli_args=["-h"])
    out, err = capsys.readouterr()
    assert exec_info.value.code == 0
    assert "{deco,proc}" in out.strip() and err.strip() == ""


def test_duplicate_command_name():
    Coma.reset()
    command(name="test", cmd=lambda: ...)
    with pytest.raises(ValueError) as exec_info:
        command(name="test", cmd=lambda: ...)
    assert "already registered" in str(exec_info.value)


def test_command_overloading():
    Coma.reset()
    with pytest.raises(ValueError) as exec_info:

        @command(name="test", cmd=lambda: print("lambda"))
        def cmd():
            print("function")

    assert "@command decorator with two commands" in str(exec_info.value)
    print(str(exec_info.value))


def test_class_based_command(capsys):
    Coma.reset()

    @command
    class Test1:  # noqa: Unused class
        def __init__(self):
            self.x = 1

        def run(self):
            print("passed test", self.x)

    class Test2:
        def __init__(self):
            self.x = 2

        def run(self):
            print("passed test", self.x)

    command(Test2)
    wake(cli_args=["test1"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed test 1" and err.strip() == ""
    wake(cli_args=["test2"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed test 2" and err.strip() == ""


def test_command_with_config(capsys):
    from dataclasses import dataclass

    Coma.reset()

    @dataclass
    class Config:
        text: str = "passed test {}"

    @command(name="test1")
    class Test:  # noqa: Unused class.
        def __init__(self, cfg: Config):
            self.cfg = cfg

        def run(self):
            print(self.cfg.text.format(str(1)))

    @command(name="test2")
    def cmd(cfg: Config):
        print(cfg.text.format(str(2)))

    no_write = coma.hooks.config_hook.default_factory(write=False)
    wake(cli_args=["test1"], config_hook=no_write)
    out, err = capsys.readouterr()
    assert out.strip() == "passed test 1" and err.strip() == ""
    wake(cli_args=["test2"], config_hook=no_write)
    out, err = capsys.readouterr()
    assert out.strip() == "passed test 2" and err.strip() == ""


def test_noop(capsys):
    @command(parser_hook=None, config_hook=None, init_hook=None, run_hook=None)
    def test():
        assert False

    wake(cli_args=["test"])
    out, err = capsys.readouterr()
    assert out.strip() == "" and err.strip() == ""
