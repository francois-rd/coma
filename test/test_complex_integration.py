from dataclasses import asdict, dataclass
from enum import Enum
import os

import pytest

from coma import (
    InstanceKeys,
    InvocationData,
    SignatureInspector,
    command,
    preload,
    wake,
)
from coma.core.singleton import Coma
import coma


class Strategy:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        print(f"Do something with {self.args} and {self.kwargs}")


@dataclass
class Strat3:
    info: str = "some strategy initialization info"


strategies = dict(strat1=dict, strat2=list, strat3=Strat3)


class StrategyChoices(Enum):
    STRAT1 = "STRAT1"
    STRAT2 = "STRAT2"
    STRAT3 = "STRAT3"
    MISSING = "MISSING"


def setup(cli_args):
    Coma.reset()

    # This is done just for the sake of not writing some configs to file as a gimmick
    # to find some reason to add more hooks. In practice, you would typically only include
    # the strategy_builder_factory_hook (if at all).
    def strategize_hook(data: InvocationData) -> None:
        preload(data, *strategies.keys(), "which")
        which = data.parameters.get_config("which").get_latest()
        if which.choice == StrategyChoices.MISSING:
            raise ValueError(f"Missing strategy")
        drop = [c for c in strategies if c != which.choice.value.lower()]
        data.parameters.delete(*drop)

    # This is genuinely more useful as a hook than 'strategize_hook' is. However, you can
    # just put equivalent builder factory code directly in the command itself, so long as
    # you migrate the strategy configs from supplemental to proper command configs.
    def strategy_builder_factory_hook(data: InvocationData) -> None:
        which = data.parameters.get_config("which").get_latest()
        strat_data = data.parameters.get_config(which.choice.value.lower())
        strat_data = strat_data.as_primitive(strat_data.get_latest_key())
        if isinstance(strat_data, dict):
            args, kwargs = (), strat_data
        elif isinstance(strat_data, Strat3):
            args, kwargs = (), asdict(strat_data)
        else:
            args, kwargs = strat_data, {}
        data.parameters.replace("strategy", Strategy(*args, **kwargs))

    @command(
        pre_config_hook=strategize_hook,
        pre_init_hook=strategy_builder_factory_hook,
        signature_inspector=SignatureInspector(
            inline_identifier="which", inline=["choice"]
        ),
        **strategies,
    )
    def cmd(strategy: Strategy, choice: StrategyChoices = StrategyChoices.MISSING):
        print(f"Chosen strategy: {choice}")
        print(f"Running strategy...")
        strategy()

    def overwrite_hook(data: InvocationData) -> None:
        kwargs = {}
        if data.known_args.overwrite:
            kwargs = dict(
                overwrite=data.known_args.overwrite,
                write_instance_key=InstanceKeys.OVERRIDE,
            )
        coma.config_hook.default_factory(**kwargs)(data)

    def create_hook(data: InvocationData) -> None:
        if data.known_args.create:
            print("Config files created. Quitting.")
            quit(0)

    def dry_run_hook(data: InvocationData) -> None:
        if data.known_args.dry_run:
            print("Dry run. Stopping after initialization.")
            quit(0)

    wake(
        cli_args=cli_args,
        parser_hook=(
            coma.DEFAULT,
            coma.add_argument_factory("--overwrite", action="store_true"),
            coma.add_argument_factory("--create", action="store_true"),
            coma.add_argument_factory("--dry-run", action="store_true"),
        ),
        config_hook=overwrite_hook,
        post_config_hook=create_hook,
        post_init_hook=dry_run_hook,
    )


def test_no_strat():
    with pytest.raises(ValueError) as exec_info:
        setup(["cmd"])
    assert "Missing strategy" in str(exec_info.value)


def test_strat1(capsys, tmpdir):
    curr = os.getcwd()
    os.chdir(tmpdir)
    setup(["cmd", "which::choice=STRAT1", "random=input", "for=strat1"])
    args, kwargs = (), {"random": "input", "for": "strat1"}
    out, err = capsys.readouterr()
    assert f"Chosen strategy: {StrategyChoices.STRAT1}" in out
    assert "Running strategy..." in out
    assert f"Do something with {args} and {kwargs}" in out
    assert err.strip() == ""
    assert tmpdir.join("strat1.yaml").read().strip() == "{}"
    assert not tmpdir.join("strat2.yaml").exists()
    assert not tmpdir.join("strat3.yaml").exists()
    assert not tmpdir.join("which.yaml").exists()
    os.chdir(curr)


def test_strat2(capsys, tmpdir):
    curr = os.getcwd()
    os.chdir(tmpdir)
    setup(["cmd", "which::choice=STRAT2", "random", "input", "for", "strat2"])
    args, kwargs = ("random", "input", "for", "strat2"), {}
    out, err = capsys.readouterr()
    assert f"Chosen strategy: {StrategyChoices.STRAT2}" in out
    assert "Running strategy..." in out
    assert f"Do something with {args} and {kwargs}" in out
    assert err.strip() == ""
    assert tmpdir.join("strat2.yaml").read().strip() == "[]"
    assert not tmpdir.join("strat1.yaml").exists()
    assert not tmpdir.join("strat3.yaml").exists()
    assert not tmpdir.join("which.yaml").exists()
    os.chdir(curr)


def test_strat3(capsys, tmpdir):
    curr = os.getcwd()
    os.chdir(tmpdir)
    setup(["cmd", "which::choice=STRAT3", "info='random input for strat3'"])
    args, kwargs = (), {"info": "random input for strat3"}
    out, err = capsys.readouterr()
    assert f"Chosen strategy: {StrategyChoices.STRAT3}" in out
    assert "Running strategy..." in out
    assert f"Do something with {args} and {kwargs}" in out
    assert err.strip() == ""
    assert tmpdir.join("strat3.yaml").read().strip() == f"info: {Strat3().info}"
    assert not tmpdir.join("strat1.yaml").exists()
    assert not tmpdir.join("strat2.yaml").exists()
    assert not tmpdir.join("which.yaml").exists()
    os.chdir(curr)


def test_overwrite(capsys, tmpdir):
    curr = os.getcwd()
    os.chdir(tmpdir)
    args, kwargs = ("random", "input", "for", "strat2"), {}
    setup(["cmd", "which::choice=STRAT2", *args, "--overwrite"])
    out, err = capsys.readouterr()
    assert f"Chosen strategy: {StrategyChoices.STRAT2}" in out
    assert "Running strategy..." in out
    assert f"Do something with {args} and {kwargs}" in out
    assert err.strip() == ""
    assert tmpdir.join("strat2.yaml").read().strip() == "- " + "\n- ".join(args)
    assert not tmpdir.join("strat1.yaml").exists()
    assert not tmpdir.join("strat3.yaml").exists()
    assert not tmpdir.join("which.yaml").exists()
    os.chdir(curr)


def test_create(capsys, tmpdir):
    curr = os.getcwd()
    os.chdir(tmpdir)
    with pytest.raises(SystemExit) as exec_info:
        setup(["cmd", "which::choice=STRAT1", "random=input", "for=strat1", "--create"])
    assert exec_info.value.code == 0
    out, err = capsys.readouterr()
    assert "Config files created. Quitting." in out
    assert "Chosen strategy:" not in out
    assert "Running strategy..." not in out
    assert "Do something" not in out
    assert err.strip() == ""
    assert tmpdir.join("strat1.yaml").read().strip() == "{}"
    assert not tmpdir.join("strat2.yaml").exists()
    assert not tmpdir.join("strat3.yaml").exists()
    assert not tmpdir.join("which.yaml").exists()
    os.chdir(curr)


def test_dry_run(capsys, tmpdir):
    curr = os.getcwd()
    os.chdir(tmpdir)
    with pytest.raises(SystemExit) as exec_info:
        setup(["cmd", "which::choice=STRAT3", "info='input for strat3'", "--dry-run"])
    assert exec_info.value.code == 0
    out, err = capsys.readouterr()
    assert "Dry run. Stopping after initialization." in out
    assert "Chosen strategy" not in out
    assert "Running strategy..." not in out
    assert "Do something with" not in out
    assert err.strip() == ""
    assert tmpdir.join("strat3.yaml").read().strip() == f"info: {Strat3().info}"
    assert not tmpdir.join("strat1.yaml").exists()
    assert not tmpdir.join("strat2.yaml").exists()
    assert not tmpdir.join("which.yaml").exists()
    os.chdir(curr)
