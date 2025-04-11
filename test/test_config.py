from dataclasses import dataclass, field
import os

import pytest

from coma import InstanceKeys, InvocationData, command, wake
from coma.core.singleton import Coma
import coma


@dataclass
class Config:
    x: int = 0
    l: list = field(default_factory=lambda: [1, 2])
    d: dict = field(default_factory=lambda: {"a": {"b": 3}})


config_as_yaml = "x: {}\nl:\n- 1\n- 2\nd:\n  a:\n    b: 3"


def cmd(one: list, two: dict, three: Config, *args, **kwargs):  # noqa: Unused.
    print("passed")


all_cfgs = ["one", "two", "three", "args", "kwargs"]


def test_initialize_default_and_override_disabled_and_no_write(capsys):
    def post_config_hook(data: InvocationData) -> None:
        cfgs = data.parameters.select_config(*all_cfgs)

        # One:
        assert cfgs["one"].back_end == []
        assert cfgs["one"].get(InstanceKeys.BASE) == []
        with pytest.raises(KeyError) as exec_info:
            cfgs["one"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["one"].get(InstanceKeys.OVERRIDE)
        assert InstanceKeys.OVERRIDE in str(exec_info.value)
        one_file = data.persistence_manager.get_file_path("one", data.known_args)
        assert not os.path.exists(one_file)

        # Two: (which is the only config with a pre-existing file before this test)
        assert cfgs["two"].back_end == {}
        assert cfgs["two"].get(InstanceKeys.BASE) == {}
        two_from_file = dict(content="to", initialize="from")
        assert cfgs["two"].get(InstanceKeys.FILE) == two_from_file
        with pytest.raises(KeyError) as exec_info:
            cfgs["two"].get(InstanceKeys.OVERRIDE)
        assert InstanceKeys.OVERRIDE in str(exec_info.value)
        two_file = data.persistence_manager.get_file_path("two", data.known_args)
        assert os.path.exists(two_file)

        # Three:
        assert cfgs["three"].back_end == Config
        assert cfgs["three"].get(InstanceKeys.BASE) == Config()
        with pytest.raises(KeyError) as exec_info:
            cfgs["three"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["three"].get(InstanceKeys.OVERRIDE)
        assert InstanceKeys.OVERRIDE in str(exec_info.value)
        three_file = data.persistence_manager.get_file_path("three", data.known_args)
        assert not os.path.exists(three_file)

        # Args:
        assert cfgs["args"].back_end == []
        assert cfgs["args"].get(InstanceKeys.BASE) == []
        with pytest.raises(KeyError) as exec_info:
            cfgs["args"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["args"].get(InstanceKeys.OVERRIDE)
        assert InstanceKeys.OVERRIDE in str(exec_info.value)
        args_file = data.persistence_manager.get_file_path("args", data.known_args)
        assert not os.path.exists(args_file)

        # Kwargs:
        assert cfgs["kwargs"].back_end == {}
        assert cfgs["kwargs"].get(InstanceKeys.BASE) == {}
        with pytest.raises(KeyError) as exec_info:
            cfgs["kwargs"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["kwargs"].get(InstanceKeys.OVERRIDE)
        assert InstanceKeys.OVERRIDE in str(exec_info.value)
        kwargs_file = data.persistence_manager.get_file_path("kwargs", data.known_args)
        assert not os.path.exists(kwargs_file)

    Coma.reset()
    command(
        name="test",
        cmd=cmd,
        config_hook=coma.config_hook.default_factory(override=None, write=False),
        post_config_hook=post_config_hook,
    )
    wake(cli_args=["test"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == ""


def test_initialize_raise_on_fnf_all(capsys):
    Coma.reset()
    config_hook = coma.config_hook.default_factory(
        raise_on_fnf=True, override=None, write=False
    )
    command(name="test", cmd=cmd, config_hook=config_hook)
    with pytest.raises(FileNotFoundError) as exec_info:
        wake(cli_args=["test"])
    assert "one.yaml" in str(exec_info.value)
    out, err = capsys.readouterr()
    assert "passed" not in out.strip() and err.strip() == ""


def test_initialize_raise_on_fnf_only_where_file_exists(capsys):
    def post_config_hook(data: InvocationData) -> None:
        cfgs = data.parameters.select_config(*all_cfgs)

        # One:
        assert cfgs["one"].back_end == []
        assert cfgs["one"].get(InstanceKeys.BASE) == []
        with pytest.raises(KeyError) as exec_info:
            cfgs["one"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["one"].get(InstanceKeys.OVERRIDE)
        assert InstanceKeys.OVERRIDE in str(exec_info.value)

        # Two:
        assert cfgs["two"].back_end == {}
        assert cfgs["two"].get(InstanceKeys.BASE) == {}
        two_from_file = dict(content="to", initialize="from")
        assert cfgs["two"].get(InstanceKeys.FILE) == two_from_file
        with pytest.raises(KeyError) as exec_info:
            cfgs["two"].get(InstanceKeys.OVERRIDE)
        assert InstanceKeys.OVERRIDE in str(exec_info.value)

        # Three:
        assert cfgs["three"].back_end == Config
        assert cfgs["three"].get(InstanceKeys.BASE) == Config()
        with pytest.raises(KeyError) as exec_info:
            cfgs["three"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["three"].get(InstanceKeys.OVERRIDE)
        assert InstanceKeys.OVERRIDE in str(exec_info.value)

        # Args:
        assert cfgs["args"].back_end == []
        assert cfgs["args"].get(InstanceKeys.BASE) == []
        with pytest.raises(KeyError) as exec_info:
            cfgs["args"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["args"].get(InstanceKeys.OVERRIDE)
        assert InstanceKeys.OVERRIDE in str(exec_info.value)

        # Kwargs:
        assert cfgs["kwargs"].back_end == {}
        assert cfgs["kwargs"].get(InstanceKeys.BASE) == {}
        with pytest.raises(KeyError) as exec_info:
            cfgs["kwargs"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["kwargs"].get(InstanceKeys.OVERRIDE)
        assert InstanceKeys.OVERRIDE in str(exec_info.value)

    Coma.reset()
    command(
        name="test",
        cmd=cmd,
        config_hook=(
            coma.config_hook.default_factory(
                "one", "three", override=None, write=False
            ),
            coma.config_hook.default_factory(
                "two", "args", "kwargs", raise_on_fnf=True, override=None, write=False
            ),
        ),
        post_config_hook=post_config_hook,
    )
    wake(cli_args=["test"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == ""


def test_override_default(capsys):
    def post_config_hook(data: InvocationData) -> None:
        cfgs = data.parameters.select_config(*all_cfgs)

        # One:
        assert cfgs["one"].back_end == []
        assert cfgs["one"].get(InstanceKeys.BASE) == []
        with pytest.raises(KeyError) as exec_info:
            cfgs["one"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        assert cfgs["one"].get(InstanceKeys.OVERRIDE) == ["for_list_and_args"]

        # Two:
        assert cfgs["two"].back_end == {}
        assert cfgs["two"].get(InstanceKeys.BASE) == {}
        two_from_file = dict(content="to", initialize="from")
        assert cfgs["two"].get(InstanceKeys.FILE) == two_from_file
        assert cfgs["two"].get(InstanceKeys.OVERRIDE) == {**two_from_file, "x": 42}

        # Three:
        assert cfgs["three"].back_end == Config
        assert cfgs["three"].get(InstanceKeys.BASE) == Config()
        with pytest.raises(KeyError) as exec_info:
            cfgs["three"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        assert cfgs["three"].get(InstanceKeys.OVERRIDE) == Config(x=42)

        # Args:
        assert cfgs["args"].back_end == []
        assert cfgs["args"].get(InstanceKeys.BASE) == []
        with pytest.raises(KeyError) as exec_info:
            cfgs["args"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        assert cfgs["args"].get(InstanceKeys.OVERRIDE) == ["for_list_and_args"]

        # Kwargs:
        assert cfgs["kwargs"].back_end == {}
        assert cfgs["kwargs"].get(InstanceKeys.BASE) == {}
        with pytest.raises(KeyError) as exec_info:
            cfgs["kwargs"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        assert cfgs["kwargs"].get(InstanceKeys.OVERRIDE) == dict(x=42)

    Coma.reset()
    command(
        name="test",
        cmd=cmd,
        config_hook=coma.config_hook.default_factory(write=False),
        post_config_hook=post_config_hook,
    )
    wake(cli_args=["test", "for_list_and_args", "x=42"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == ""


def test_override_instance_key(capsys):
    def post_config_hook(data: InvocationData) -> None:
        cfgs = data.parameters.select_config(*all_cfgs)

        # One:
        assert cfgs["one"].back_end == []
        assert cfgs["one"].get(InstanceKeys.BASE) == []
        with pytest.raises(KeyError) as exec_info:
            cfgs["one"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        assert cfgs["one"].get(InstanceKeys.OVERRIDE) == ["for_list_and_args"]

        # Two:
        assert cfgs["two"].back_end == {}
        assert cfgs["two"].get(InstanceKeys.BASE) == {}
        two_from_file = dict(content="to", initialize="from")
        assert cfgs["two"].get(InstanceKeys.FILE) == two_from_file
        assert cfgs["two"].get(InstanceKeys.OVERRIDE) == dict(x=42)  # Significant!

        # Three:
        assert cfgs["three"].back_end == Config
        assert cfgs["three"].get(InstanceKeys.BASE) == Config()
        with pytest.raises(KeyError) as exec_info:
            cfgs["three"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        assert cfgs["three"].get(InstanceKeys.OVERRIDE) == Config(x=42)

        # Args:
        assert cfgs["args"].back_end == []
        assert cfgs["args"].get(InstanceKeys.BASE) == []
        with pytest.raises(KeyError) as exec_info:
            cfgs["args"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        assert cfgs["args"].get(InstanceKeys.OVERRIDE) == ["for_list_and_args"]

        # Kwargs:
        assert cfgs["kwargs"].back_end == {}
        assert cfgs["kwargs"].get(InstanceKeys.BASE) == {}
        with pytest.raises(KeyError) as exec_info:
            cfgs["kwargs"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        assert cfgs["kwargs"].get(InstanceKeys.OVERRIDE) == dict(x=42)

    Coma.reset()
    command(
        name="test",
        cmd=cmd,
        config_hook=coma.config_hook.default_factory(
            override_instance_key=InstanceKeys.BASE, write=False
        ),
        post_config_hook=post_config_hook,
    )
    wake(cli_args=["test", "for_list_and_args", "x=42"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == ""


def test_persistence_manager(capsys, tmpdir):
    curr = os.getcwd()
    os.chdir(tmpdir)

    def post_config_hook(data: InvocationData):
        tmpdir_ = tmpdir  # noqa: "Fixture is not requested". Using a closure, though.
        with pytest.raises(AttributeError) as exec_info:
            data.known_args.three  # noqa: "No effect". Testing whether attr exists.
        assert "has no attribute 'three'" in str(exec_info.value)
        assert data.known_args.four
        assert tmpdir_.join("one.json").read().strip() == "[]"
        assert tmpdir_.join("crazy_name_for_two.yml").read().strip() == "{}"
        assert tmpdir_.join("three.yaml").read().strip() == config_as_yaml.format(0)
        assert not tmpdir_.join("args.yaml").exists()
        assert not tmpdir_.join("kwargs.yaml").exists()

    Coma.reset()
    manager = coma.PersistenceManager()
    manager.register("one", extension=coma.Extension.JSON)
    manager.register("two", default="crazy_name_for_two.yml")
    manager.register("three", dest="four")
    command(
        name="test",
        cmd=cmd,
        persistence_manager=manager,
        post_config_hook=post_config_hook,
    )
    wake(cli_args=["test"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == ""
    os.chdir(curr)


def test_write_override_key(capsys, tmpdir):
    curr = os.getcwd()
    os.chdir(tmpdir)
    Coma.reset()
    command(
        name="test",
        cmd=cmd,
        config_hook=coma.config_hook.default_factory(
            write_instance_key=InstanceKeys.OVERRIDE
        ),
    )
    wake(cli_args=["test", "for_list_and_args", "x=42"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == ""
    assert tmpdir.join("one.yaml").read().strip() == "- for_list_and_args"
    assert tmpdir.join("two.yaml").read().strip() == "x: 42"
    assert tmpdir.join("three.yaml").read().strip() == config_as_yaml.format(42)
    assert not tmpdir.join("args.yaml").exists()
    assert not tmpdir.join("kwargs.yaml").exists()
    os.chdir(curr)


def test_skip_write(capsys, tmpdir):
    curr = os.getcwd()
    os.chdir(tmpdir)
    Coma.reset()
    command(
        name="test",
        cmd=cmd,
        config_hook=coma.config_hook.default_factory(
            skip_write=["two", "three"],
        ),
    )
    wake(cli_args=["test", "for_list_and_args", "x=42"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == ""
    assert tmpdir.join("one.yaml").read().strip() == "[]"
    assert not tmpdir.join("two.yaml").exists()
    assert not tmpdir.join("three.yaml").exists()
    assert not tmpdir.join("args.yaml").exists()
    assert not tmpdir.join("kwargs.yaml").exists()
    os.chdir(curr)


def test_write_overwrite(capsys, tmpdir):
    curr = os.getcwd()
    os.chdir(tmpdir)
    tmpdir.join("one.yaml").write("- pre_written")

    def post_config_hook(data: InvocationData) -> None:
        one = data.parameters.get_config("one")
        assert one.back_end == []
        assert one.get(InstanceKeys.BASE) == []
        assert one.get(InstanceKeys.FILE) == ["pre_written"]
        assert one.get(InstanceKeys.OVERRIDE) == [
            "pre_written",
            "for_list_and_args",
        ]

    Coma.reset()
    command(
        name="test",
        cmd=cmd,
        config_hook=coma.config_hook.default_factory(overwrite=True),
        post_config_hook=post_config_hook,
    )
    wake(cli_args=["test", "for_list_and_args", "x=42"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == ""
    assert tmpdir.join("one.yaml").read().strip() == "[]"
    assert tmpdir.join("two.yaml").read().strip() == "{}"
    assert tmpdir.join("three.yaml").read().strip() == config_as_yaml.format(0)
    assert not tmpdir.join("args.yaml").exists()
    assert not tmpdir.join("kwargs.yaml").exists()
    os.chdir(curr)


def test_preload_limited_to_nothing(capsys):
    def pre_config_hook(data: InvocationData):
        with pytest.raises(ValueError) as exec_info:
            coma.preload(data, limited=True)
        assert "at least one config ID must be provided" in str(exec_info.value)

    Coma.reset()
    command(
        name="test",
        cmd=cmd,
        pre_config_hook=pre_config_hook,
        config_hook=coma.config_hook.default_factory(write=False),
    )
    wake(cli_args=["test", "for_list_and_args", "x=42"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == ""


def test_preload_isolation(capsys):
    # In this test, only "two" gets preloaded (including override), whereas
    # the others get loaded normally (with override and write turned off).
    def pre_config_hook(data: InvocationData):
        coma.preload(data, "two", limited=True, raise_on_fnf=True)
        cfgs = data.parameters.select_config(*all_cfgs)

        with pytest.raises(KeyError) as exec_info:
            cfgs["one"].get(InstanceKeys.BASE)
        assert InstanceKeys.BASE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["three"].get(InstanceKeys.BASE)
        assert InstanceKeys.BASE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["args"].get(InstanceKeys.BASE)
        assert InstanceKeys.BASE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["kwargs"].get(InstanceKeys.BASE)
        assert InstanceKeys.BASE in str(exec_info.value)

        # Two: (which is the only config with a pre-existing file before this test)
        assert cfgs["two"].back_end == {}
        assert cfgs["two"].get(InstanceKeys.BASE) == {}
        two_from_file = dict(content="to", initialize="from")
        assert cfgs["two"].get(InstanceKeys.FILE) == two_from_file
        assert cfgs["two"].get(InstanceKeys.OVERRIDE) == {**two_from_file, "x": 42}
        two_file = data.persistence_manager.get_file_path("two", data.known_args)
        assert os.path.exists(two_file)

    def post_config_hook(data: InvocationData):
        cfgs = data.parameters.select_config(*all_cfgs)

        # One:
        assert cfgs["one"].back_end == []
        assert cfgs["one"].get(InstanceKeys.BASE) == []
        with pytest.raises(KeyError) as exec_info:
            cfgs["one"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["one"].get(InstanceKeys.OVERRIDE)
        assert InstanceKeys.OVERRIDE in str(exec_info.value)
        one_file = data.persistence_manager.get_file_path("one", data.known_args)
        assert not os.path.exists(one_file)

        # Two: (which is the only config with a pre-existing file before this test)
        assert cfgs["two"].back_end == {}
        assert cfgs["two"].get(InstanceKeys.BASE) == {}
        two_from_file = dict(content="to", initialize="from")
        assert cfgs["two"].get(InstanceKeys.FILE) == two_from_file
        assert cfgs["two"].get(InstanceKeys.OVERRIDE) == {**two_from_file, "x": 42}
        two_file = data.persistence_manager.get_file_path("two", data.known_args)
        assert os.path.exists(two_file)

        # Three:
        assert cfgs["three"].back_end == Config
        assert cfgs["three"].get(InstanceKeys.BASE) == Config()
        with pytest.raises(KeyError) as exec_info:
            cfgs["three"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["three"].get(InstanceKeys.OVERRIDE)
        assert InstanceKeys.OVERRIDE in str(exec_info.value)
        three_file = data.persistence_manager.get_file_path("three", data.known_args)
        assert not os.path.exists(three_file)

        # Args:
        assert cfgs["args"].back_end == []
        assert cfgs["args"].get(InstanceKeys.BASE) == []
        with pytest.raises(KeyError) as exec_info:
            cfgs["args"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["args"].get(InstanceKeys.OVERRIDE)
        assert InstanceKeys.OVERRIDE in str(exec_info.value)
        args_file = data.persistence_manager.get_file_path("args", data.known_args)
        assert not os.path.exists(args_file)

        # Kwargs:
        assert cfgs["kwargs"].back_end == {}
        assert cfgs["kwargs"].get(InstanceKeys.BASE) == {}
        with pytest.raises(KeyError) as exec_info:
            cfgs["kwargs"].get(InstanceKeys.FILE)
        assert InstanceKeys.FILE in str(exec_info.value)
        with pytest.raises(KeyError) as exec_info:
            cfgs["kwargs"].get(InstanceKeys.OVERRIDE)
        assert InstanceKeys.OVERRIDE in str(exec_info.value)
        kwargs_file = data.persistence_manager.get_file_path("kwargs", data.known_args)
        assert not os.path.exists(kwargs_file)

    Coma.reset()
    command(
        name="test",
        cmd=cmd,
        pre_config_hook=pre_config_hook,
        config_hook=coma.config_hook.default_factory(override=None, write=False),
        post_config_hook=post_config_hook,
    )
    wake(cli_args=["test", "for_list_and_args", "x=42"])
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == ""
