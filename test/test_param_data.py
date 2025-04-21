from dataclasses import dataclass, fields
from inspect import signature
from typing import Optional

import pytest

from coma import OverridePolicy, ParamData


def test_empty_signature(capsys):
    def fn():
        print("passed")

    kwargs = dict(
        args_as_config=True,
        kwargs_as_config=True,
        inline_identifier="inline",
        inline=(),
        supplemental_configs={},
    )
    data = ParamData.from_signature(signature(fn), **kwargs)
    assert len(data.configs) == 0
    assert len(data.supplemental_configs) == 0
    assert len(data.other_parameters) == 0
    assert data.args_id is data.kwargs_id is None
    result = data.call_on(fn, OverridePolicy.RAISE)
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == "" and result is None


def test_supplemental_types(capsys):
    @dataclass
    class Config:
        x: int = 0

    def fn():  # noqa: Unused.
        print("passed")
        return -1

    data = ParamData.from_signature(
        signature(fn),
        args_as_config=True,
        kwargs_as_config=True,
        inline_identifier="inline",
        inline=(),
        supplemental_configs=dict(
            list_type_sup=list,
            list_value_sup=[1, 2, 3],
            dict_type_sup=dict,
            dict_value_sup=dict(a=1, b=2),
            struct_type_sup=Config,
            struct_value_sup=Config(42),
        ),
    )
    assert data.supplemental_configs["list_type_sup"].back_end == []
    assert data.supplemental_configs["list_value_sup"].back_end == [1, 2, 3]
    assert data.supplemental_configs["dict_type_sup"].back_end == {}
    assert data.supplemental_configs["dict_value_sup"].back_end == dict(a=1, b=2)
    assert data.supplemental_configs["struct_type_sup"].back_end == Config
    assert data.supplemental_configs["struct_value_sup"].back_end == Config(42)
    assert len(data.configs) == 0
    assert len(data.other_parameters) == 0
    assert data.args_id is data.kwargs_id is None
    result = data.call_on(fn, OverridePolicy.RAISE)
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == "" and result == -1


def test_duplicate_in_supplemental(capsys):
    def fn(repeat):  # noqa: Unused.
        print("passed")

    with pytest.raises(ValueError) as exec_info:
        ParamData.from_signature(
            signature(fn),
            args_as_config=True,
            kwargs_as_config=True,
            inline_identifier="inline",
            inline=(),
            supplemental_configs=dict(repeat=list),
        )
    assert "also appears in supplemental" in str(exec_info.value)
    out, err = capsys.readouterr()
    assert "passed" not in out and err.strip() == ""


def test_inline_name_clash(capsys):
    def fn(inline):  # noqa: Unused.
        print("passed")

    with pytest.raises(ValueError) as exec_info:
        ParamData.from_signature(
            signature(fn),
            args_as_config=True,
            kwargs_as_config=True,
            inline_identifier="inline",
            inline=(),
            supplemental_configs={},
        )
    assert "is a reserved identifier" in str(exec_info.value)
    out, err = capsys.readouterr()
    assert "passed" not in out and err.strip() == ""


def test_duplicate_inline(capsys):
    def fn(repeat: str = ""):  # noqa: Unused.
        print("passed")

    with pytest.raises(ValueError) as exec_info:
        ParamData.from_signature(
            signature(fn),
            args_as_config=True,
            kwargs_as_config=True,
            inline_identifier="inline",
            inline=("repeat", "repeat"),
            supplemental_configs={},
        )
    assert "declared multiple times" in str(exec_info.value)
    out, err = capsys.readouterr()
    assert "passed" not in out and err.strip() == ""

    def fn2(repeat: list):  # noqa: Unused.
        print("passed")

    with pytest.raises(ValueError) as exec_info:
        ParamData.from_signature(
            signature(fn2),
            args_as_config=True,
            kwargs_as_config=True,
            inline_identifier="inline",
            inline=[("repeat", list), ("repeat", dict)],
            supplemental_configs={},
        )
    assert "declared multiple times" in str(exec_info.value)
    out, err = capsys.readouterr()
    assert "passed" not in out and err.strip() == ""

    with pytest.raises(ValueError) as exec_info:
        ParamData.from_signature(
            signature(fn2),
            args_as_config=True,
            kwargs_as_config=True,
            inline_identifier="inline",
            inline=[("repeat", list), "repeat"],
            supplemental_configs={},
        )
    assert "declared multiple times" in str(exec_info.value)
    out, err = capsys.readouterr()
    assert "passed" not in out and err.strip() == ""


def test_missing_inline(capsys):
    def fn():
        print("passed")

    with pytest.raises(ValueError) as exec_info:
        ParamData.from_signature(
            signature(fn),
            args_as_config=True,
            kwargs_as_config=True,
            inline_identifier="inline",
            inline=["missing"],
            supplemental_configs={},
        )
    assert "missing from signature" in str(exec_info.value)
    out, err = capsys.readouterr()
    assert "passed" not in out and err.strip() == ""

    with pytest.raises(ValueError) as exec_info:
        ParamData.from_signature(
            signature(fn),
            args_as_config=True,
            kwargs_as_config=True,
            inline_identifier="inline",
            inline=[("missing", list)],
            supplemental_configs={},
        )
    assert "missing from signature" in str(exec_info.value)
    out, err = capsys.readouterr()
    assert "passed" not in out and err.strip() == ""


def test_inline_declaration_error(capsys):
    def fn(no_default):  # noqa: Unused.
        print("passed")

    with pytest.raises(ValueError) as exec_info:
        ParamData.from_signature(
            signature(fn),
            args_as_config=True,
            kwargs_as_config=True,
            inline_identifier="inline",
            inline=["no_default"],
            supplemental_configs={},
        )
    assert "Missing mandatory default value" in str(exec_info.value)
    out, err = capsys.readouterr()
    assert "passed" not in out and err.strip() == ""

    def fn2(double_default="bad"):  # noqa: Unused.
        print("passed")

    with pytest.raises(ValueError) as exec_info:
        ParamData.from_signature(
            signature(fn2),
            args_as_config=True,
            kwargs_as_config=True,
            inline_identifier="inline",
            inline=[("double_default", lambda: "still bad")],
            supplemental_configs={},
        )
    assert "Duplicate default declaration" in str(exec_info.value)
    out, err = capsys.readouterr()
    assert "passed" not in out and err.strip() == ""

    def fn2(no_hint="bad"):  # noqa: Unused.
        print("passed")

    with pytest.raises(ValueError) as exec_info:
        ParamData.from_signature(
            signature(fn2),
            args_as_config=True,
            kwargs_as_config=True,
            inline_identifier="inline",
            inline=["no_hint"],
            supplemental_configs={},
        )
    assert "Missing mandatory type annotation" in str(exec_info.value)
    out, err = capsys.readouterr()
    assert "passed" not in out and err.strip() == ""


def test_variadic_config(capsys):
    def fn(*_, **__):
        print("passed")

    data = ParamData.from_signature(
        signature(fn),
        args_as_config=True,
        kwargs_as_config=True,
        inline_identifier="inline",
        inline=(),
        supplemental_configs={},
    )
    assert set(data.configs.keys()) == {"_", "__"}
    assert len(data.supplemental_configs) == 0
    assert len(data.other_parameters) == 0
    assert data.args_id == "_" and data.kwargs_id == "__"
    with pytest.raises(ValueError) as exec_info:
        data.call_on(fn, OverridePolicy.RAISE)
    assert "from which to retrieve the latest" in str(exec_info.value)
    out, err = capsys.readouterr()
    assert "passed" not in out and err.strip() == ""


def test_variadic_non_config(capsys):
    def fn(*_, **__):
        print("passed")

    data = ParamData.from_signature(
        signature(fn),
        args_as_config=False,
        kwargs_as_config=False,
        inline_identifier="inline",
        inline=(),
        supplemental_configs={},
    )
    assert len(data.configs) == 0
    assert len(data.supplemental_configs) == 0
    assert set(data.other_parameters.keys()) == {"_", "__"}
    assert data.args_id == "_" and data.kwargs_id == "__"
    result = data.call_on(fn, OverridePolicy.RAISE)
    out, err = capsys.readouterr()
    assert out.strip() == "passed" and err.strip() == "" and result is None


def test_variadic_inline(capsys):
    def fn(*_, **__):
        print("passed")

    with pytest.raises(ValueError) as exec_info:
        ParamData.from_signature(
            signature(fn),
            args_as_config=True,
            kwargs_as_config=False,
            inline_identifier="inline",
            inline=["_", "__"],
            supplemental_configs={},
        )
    assert "cannot be inline" in str(exec_info.value)


def test_all_valid_param_declarations(capsys):
    @dataclass
    class Mock:
        pass

    def fn(
        non_config_no_hint,  # noqa: Unused.
        non_config_wrong_type: tuple,  # noqa: Unused.
        list_config: list,  # noqa: Unused.
        dict_config: dict,  # noqa: Unused.
        struct_config: Mock,  # noqa: Unused.
        list_non_config_wrong_hint: Optional[list],  # noqa: Unused.
        dict_non_config_wrong_hint: Optional[dict],  # noqa: Unused.
        struct_non_config_wrong_hint: Optional[Mock],  # noqa: Unused.
        inline_non_config_type_default_factory: tuple,  # noqa: Unused.
        inline_list_default_factory: list,  # noqa: Unused.
        inline_dict_default_factory: dict,  # noqa: Unused.
        inline_struct_default_factory: Mock,  # noqa: Unused.
        non_config_no_hint_with_default=(),  # noqa: Unused.
        non_config_wrong_type_with_default: tuple = (),  # noqa: Unused.
        list_non_config_default: list = None,  # noqa: Unused.
        dict_non_config_default: dict = None,  # noqa: Unused.
        struct_non_config_default: Mock = None,  # noqa: Unused.
        list_non_config_wrong_hint_with_default: Optional[list] = None,  # noqa: Unused.
        dict_non_config_wrong_hint_with_default: Optional[dict] = None,  # noqa: Unused.
        struct_non_config_wrong_hint_with_default: Optional[Mock] = None,  # noqa
        inline_non_config_type_with_default: tuple = (),  # noqa: Unused.
        inline_list_none_default: Optional[list] = None,  # noqa: Unused.
        inline_dict_none_default: Optional[dict] = None,  # noqa: Unused.
        inline_struct_none_default: Optional[Mock] = None,  # noqa: Unused.
    ):
        print("passed")

    inline = [
        ("inline_non_config_type_default_factory", tuple),
        ("inline_list_default_factory", list),
        ("inline_dict_default_factory", dict),
        ("inline_struct_default_factory", Mock),
        "inline_non_config_type_with_default",
        "inline_list_none_default",
        "inline_dict_none_default",
        "inline_struct_none_default",
    ]
    config_ids = ["list_config", "dict_config", "struct_config"]
    inline_ids = [
        "inline_non_config_type_default_factory",
        "inline_list_default_factory",
        "inline_dict_default_factory",
        "inline_struct_default_factory",
        "inline_non_config_type_with_default",
        "inline_list_none_default",
        "inline_dict_none_default",
        "inline_struct_none_default",
    ]
    param_ids = [
        "non_config_no_hint",
        "non_config_wrong_type",
        "list_non_config_wrong_hint",
        "dict_non_config_wrong_hint",
        "struct_non_config_wrong_hint",
        "non_config_no_hint_with_default",
        "non_config_wrong_type_with_default",
        "list_non_config_default",
        "dict_non_config_default",
        "struct_non_config_default",
        "list_non_config_wrong_hint_with_default",
        "dict_non_config_wrong_hint_with_default",
        "struct_non_config_wrong_hint_with_default",
    ]

    data = ParamData.from_signature(
        signature(fn),
        args_as_config=True,
        kwargs_as_config=True,
        inline_identifier="inline",
        inline=inline,
        supplemental_configs={},
    )
    assert set(data.configs.keys()) == set(config_ids)
    assert len(data.supplemental_configs) == 0
    assert set(data.other_parameters.keys()) == set(param_ids)
    inline = data.inline_config
    assert inline is not None
    assert set(f.name for f in fields(inline.back_end)) == set(inline_ids)
    with pytest.raises(ValueError) as exec_info:
        data.call_on(fn, OverridePolicy.RAISE)
    assert "from which to retrieve the latest" in str(exec_info.value)
    out, err = capsys.readouterr()
    assert "passed" not in out and err.strip() == ""


def test_non_config_call_on(capsys):
    # Config-based call-on tests are done as part of config integration tests.
    def fn(x, y: int, *args, z: float = 3.14, **kw) -> int:
        print(x, y, *args, z, kw)
        return -1

    data = ParamData.from_signature(
        signature(fn),
        args_as_config=False,
        kwargs_as_config=False,
        inline_identifier="inline",
        inline=(),
        supplemental_configs={},
    )
    assert len(data.configs) == 0
    assert len(data.supplemental_configs) == 0
    assert set(data.other_parameters.keys()) == {"x", "y", "args", "z", "kw"}
    assert data.args_id == "args" and data.kwargs_id == "kw"
    with pytest.raises(ValueError) as exec_info:
        data.call_on(fn, OverridePolicy.RAISE)
    assert "Parameter was never filled:" in str(exec_info.value)
    data.replace("x", 42)
    data.replace("y", 0)
    data.replace("args", (1, 2, 3))
    data.replace("kw", dict(w=4))
    r = data.call_on(fn, OverridePolicy.RAISE)
    out, err = capsys.readouterr()
    assert out.strip() == "42 0 1 2 3 3.14 {'w': 4}" and err.strip() == "" and r == -1
