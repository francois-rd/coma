import pytest

from coma import InvocationData, command, wake
from coma.core.singleton import Coma
import coma


def test_shared_hook_sentinel():
    Coma.reset()
    command(name="test", cmd=lambda: print("passed"))
    with pytest.raises(ValueError) as exec_info:
        wake(cli_args=["test"], run_hook=coma.SHARED)
    assert "cannot itself be the SHARED sentinel" in str(exec_info.value)


def test_pipe_with_default_hook_sentinel(capsys):
    def third(data: InvocationData) -> InvocationData:
        args = {k: v for k, v in vars(data.known_args).items() if k != "func"}
        print(f"{args=}    unknown={data.unknown_args}")
        return data

    Coma.reset()
    command(name="test", cmd=lambda: print("second"))
    wake(
        cli_args=["test", "extra", "more=less"],
        run_hook=(lambda data: print("first"), coma.DEFAULT, third),
    )
    out, err = capsys.readouterr()
    assert "first\nsecond\nargs={}    unknown=['extra', 'more=less']" in out
    assert err.strip() == ""


def test_deeply_nested_hooks(capsys):
    Coma.reset()
    nested_hook_sequence = (
        ((coma.SHARED,), coma.DEFAULT),
        ([lambda data: print("post")],),
    )
    command(
        name="test",
        cmd=lambda: print("passed"),
        run_hook=nested_hook_sequence,  # noqa: Linter apparently can't parse this.
    )
    wake(cli_args=["test"], run_hook=((None,), coma.DEFAULT))
    out, err = capsys.readouterr()
    assert "passed\npassed\npost" in out and err.strip() == ""


def test_all_tuple_nesting(capsys):
    @command(
        pre_run_hook=(
            coma.DEFAULT,
            (None, coma.SHARED, lambda d: print("First") or d),
            lambda d: print("Second"),
            ((((lambda d: print("Third") or d),),),),
            None,
            (),
            lambda d: print("Fourth"),
        ),
        run_hook=None,
    )
    def nested():
        print("This should NOT print because run_hook=None")
        assert False

    wake(cli_args=["nested"])
    out, err = capsys.readouterr()
    assert "First\nSecond\nThird\nFourth" in out and err.strip() == ""


def test_parser_hook(capsys):
    Coma.reset()
    command(
        name="test",
        cmd=lambda: print("Shouldn't print"),
        parser_hook=(
            coma.SHARED,
            coma.add_argument_factory("--dry-run", action="store_true"),
        ),
        pre_run_hook=(
            coma.SHARED,
            lambda d: (print("Dry run.") or quit(42) if d.known_args.dry_run else d),
        ),
    )
    with pytest.raises(SystemExit) as exec_info:
        wake(cli_args=["test", "--dry-run"])
    out, err = capsys.readouterr()
    assert "Dry run." in out and "Shouldn't print" not in out and err.strip() == ""
    assert exec_info.value.code == 42


def test_none_hook(capsys):
    Coma.reset()

    def run_hook(data: InvocationData) -> InvocationData:
        assert getattr(data.command, "run", None) is None
        return data

    command(name="test", cmd=lambda: print("passed"), init_hook=None, run_hook=run_hook)
    wake(cli_args=["test"])
    out, err = capsys.readouterr()
    assert out.strip() == "" and err.strip() == ""
