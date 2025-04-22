import pytest

from coma import WakeException, command, wake
from coma.core.singleton import Coma
import coma


def test_some_command_no_cli():
    Coma.reset()
    command(name="test", cmd=lambda: ...)
    with pytest.raises(WakeException) as exec_info:
        wake(cli_args=[])
    assert "command line" in str(exec_info.value)


def test_no_cmd_no_cli():
    Coma.reset()
    with pytest.raises(WakeException) as exec_info:
        wake(cli_args=[])
    assert "no commands registered" in str(exec_info.value)


def test_some_command_garbage_cli(capsys):
    Coma.reset()
    command(name="test", cmd=lambda: ...)
    with pytest.raises(SystemExit) as exec_info:
        wake(cli_args=["garbage"])
    _, err = capsys.readouterr()
    assert exec_info.value.code == 2
    assert "invalid choice: 'garbage'" in err


def test_no_cmd_garbage_cli(capsys):
    Coma.reset()
    with pytest.raises(WakeException) as exec_info:
        wake(cli_args=["garbage"])
    _, err = capsys.readouterr()
    assert "no commands registered" in str(exec_info.value)


def test_some_command_correct_cli(capsys):
    Coma.reset()
    command(name="test", cmd=lambda: print("passed"))
    wake(cli_args=["test"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == ""


def test_retry_default(capsys):
    Coma.reset()
    command(name="test", cmd=lambda: print("Shouldn't print"))
    command(name="default", cmd=lambda: print("passed"))
    try:
        wake(cli_args=[])
    except coma.WakeException:
        wake(cli_args=["default"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == ""


def test_parser(capsys):
    from argparse import ArgumentParser

    Coma.reset()
    command(name="test", cmd=lambda: print("Shouldn't print"))
    with pytest.raises(SystemExit) as exec_info:
        wake(
            parser=ArgumentParser(usage="Some usage text", epilog="Epilog"),
            cli_args=["-h"],
        )
    out, err = capsys.readouterr()
    assert "Some usage text" in out
    assert "Epilog" in out
    assert "{test}" in out
    assert "Shouldn't print" not in out
    assert err.strip() == ""
    assert exec_info.value.code == 0


def test_subparser(capsys):
    Coma.reset()
    command(name="test", cmd=lambda: print("Shouldn't print"))
    command(name="test2", cmd=lambda: print("Shouldn't print"))
    with pytest.raises(SystemExit) as exec_info:
        wake(cli_args=["-h"], description="Some description")
    out, err = capsys.readouterr()
    assert "Some description" in out
    assert "{test,test2}" in out
    assert "Shouldn't print" not in out
    assert err.strip() == ""
    assert exec_info.value.code == 0


def test_subparser_with_command_kwargs(capsys):
    Coma.reset()
    kwargs = dict(usage="Some usage", epilog="Epilog")
    command(name="test", cmd=lambda: print("Shouldn't print"), parser_kwargs=kwargs)
    with pytest.raises(SystemExit) as exec_info:
        wake(cli_args=["test", "-h"])
    out, err = capsys.readouterr()
    assert "Some usage" in out
    assert "Epilog" in out
    assert "Shouldn't print" not in out
    assert err.strip() == ""
    assert exec_info.value.code == 0
