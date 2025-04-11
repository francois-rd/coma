from dataclasses import dataclass, field

import pytest

from coma.core.singleton import Coma
from coma import command, wake
import coma


def test_unknown_prefix():
    Coma.reset()

    @command(inline=["x"])
    def cmd(x: int = 0):  # noqa: Unused.
        assert False

    with pytest.raises(ValueError) as exec_info:
        wake(cli_args=["cmd", "unknown::x=42"])
    assert "Unknown override prefix" in str(exec_info.value)


def test_prefix_with_wrong_dot_list_type():
    Coma.reset()

    @command(inline=["x"])
    def cmd(x: int = 0):  # noqa: Unused.
        assert False

    with pytest.raises(ValueError) as exec_info:
        wake(cli_args=["cmd", "inline::42"])  # Forgot "x=" is what we are testing here.
    assert "cannot accept override" in str(exec_info.value)


def test_exclusive_prefix_true():
    Coma.reset()

    @command(
        config_hook=coma.config_hook.default_factory(
            override=coma.Override(exclusive_prefixed=True),
            write=False,
        ),
        inline=["x"],
    )
    def cmd(insert_dict: dict, x: int = 0):  # noqa: Unused.
        assert False

    with pytest.raises(ValueError) as exec_info:
        wake(cli_args=["cmd", "in::x=42"])
    assert "Non-exclusive prefix" in str(exec_info.value)


def test_exclusive_prefix_false():
    Coma.reset()

    @command(
        config_hook=coma.config_hook.default_factory(
            override=coma.Override(exclusive_prefixed=False),
            write=False,
        ),
        inline=["x"],
    )
    def cmd(insert_dict: dict, x: int = 0):
        assert insert_dict == dict(x=42) and x == 42

    wake(cli_args=["cmd", "in::x=42"])


def test_exclusive_shared_true():
    Coma.reset()

    @command(
        config_hook=coma.config_hook.default_factory(
            override=coma.Override(exclusive_shared=True),
            write=False,
        ),
        inline=["x"],
    )
    def cmd(insert_dict: dict, x: int = 0):  # noqa: Unused.
        assert False

    with pytest.raises(ValueError) as exec_info:
        wake(cli_args=["cmd", "x=42"])

    msg = (
        "Non-exclusive override. "
        "Override 'x=42' matches configs: ['inline', 'insert_dict']"
    )
    assert msg in str(exec_info.value)


def test_exclusive_shared_false():
    Coma.reset()

    @command(
        config_hook=coma.config_hook.default_factory(
            override=coma.Override(exclusive_shared=False),
            write=False,
        ),
        inline=["x"],
    )
    def cmd(insert_dict: dict, x: int = 0):
        assert insert_dict == dict(x=42) and x == 42

    wake(cli_args=["cmd", "x=42"])


def test_unique_true():
    Coma.reset()

    @command(
        config_hook=coma.config_hook.default_factory(
            override=coma.Override(
                exclusive_prefixed=False,
                exclusive_shared=False,
                unique_overrides=True,
            ),
            write=False,
        ),
        inline=["x"],
    )
    def cmd(insert_dict: dict, x: int = 0):  # noqa: Unused.
        assert False

    with pytest.raises(ValueError) as exec_info:
        wake(cli_args=["cmd", "inline::x=1", "x=2", "in::x=3"])
    assert "defined multiple times" in str(exec_info.value)


def test_unique_false():
    Coma.reset()

    @command(
        config_hook=coma.config_hook.default_factory(
            override=coma.Override(
                exclusive_prefixed=False,
                exclusive_shared=False,
                unique_overrides=False,
            ),
            write=False,
        ),
        inline=["x"],
    )
    def cmd(insert_dict: dict, x: int = 0):
        assert insert_dict == dict(x=2) and x == 2

    wake(cli_args=["cmd", "inline::x=1", "x=2"])


def test_known_limitation_with_unique_prefixes_before_shared_default_options():
    Coma.reset()

    @command(
        config_hook=coma.config_hook.default_factory(
            override=coma.Override(unique_overrides=False), write=False
        ),
        inline=["x"],
    )
    def cmd(x: int = 0):
        assert x == 2

    wake(cli_args=["cmd", "inline::x=1", "x=2", "in::x=3"])


def test_known_limitation_with_unique_prefixes_before_shared_all_options_false():
    Coma.reset()

    @command(
        config_hook=coma.config_hook.default_factory(
            override=coma.Override(
                exclusive_prefixed=False,
                exclusive_shared=False,
                unique_overrides=False,
            ),
            write=False,
        ),
        inline=["x"],
    )
    def cmd(insert_dict: dict, x: int = 0):
        assert insert_dict == dict(x=2) and x == 2

    wake(cli_args=["cmd", "inline::x=1", "x=2", "in::x=3"])


def test_known_limitation_with_unique_string_matching_vs_exec():
    Coma.reset()

    @command(
        config_hook=coma.config_hook.default_factory(
            override=coma.Override(
                exclusive_prefixed=False,
                exclusive_shared=False,
                unique_overrides=True,
            ),
            write=False,
        ),
    )
    def cmd(insert_dict: dict):
        assert insert_dict == dict(a=dict(b=2))

    wake(cli_args=["cmd", "insert::a.b=1", "in::a={'b': 2}"])


def test_multiple_sep_tokens():
    Coma.reset()

    @command(
        config_hook=coma.config_hook.default_factory(
            override=coma.Override(sep=":"), write=False
        ),
    )
    def cmd(insert_dict: dict):  # noqa: Unused.
        assert False

    with pytest.raises(ValueError) as exec_info:
        wake(cli_args=["cmd", "insert:a={'b': 1}"])
    assert "Too many separators" in str(exec_info.value)


def test_replace_list_and_merge_dict_on_merge():
    Coma.reset()

    @dataclass
    class Config:
        x: int = 0
        l: list = field(default_factory=lambda: [1, 2])
        d: dict = field(default_factory=lambda: {"a": {"b": 3}})

    @command(config_hook=coma.config_hook.default_factory(write=False))
    def cmd(cfg: Config):
        assert cfg == Config(42, [3, 4], dict(a=dict(b=3, c=4)))

    wake(cli_args=["cmd", "x=42", "l=[3,4]", "d.a={'c': 4}"])
