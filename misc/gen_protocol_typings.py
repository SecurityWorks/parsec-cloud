#!/usr/bin/env python3
# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import NotRequired, TypedDict, cast

BASEDIR = Path(__file__).parent.parent.resolve()
PROTOCOL_SCHEMA_DIR = BASEDIR / "libparsec/crates/protocol/schema/"
OUTPUT_PROTOCOL_TYPING_DIR = BASEDIR / "server/parsec/_parsec_pyi/protocol"
OUTPUT_TEST_RPC_FILE = BASEDIR / "server/tests/common/rpc.py"

SELF_RELATIVE_PATH = Path(__file__).resolve().relative_to(BASEDIR)
AUTOGENERATED_BANNER = (
    f"# /!\\ Autogenerated by {SELF_RELATIVE_PATH}, any modification will be lost !"
)


class CmdSpec(TypedDict):
    major_versions: list[MajorVersion]
    cmd: str
    req: CmdReq
    reps: list[CmdRep]
    nested_types: list[NestedType]


type MajorVersion = int


class CmdReq(TypedDict):
    fields: list[Field]
    unit: NotRequired[str]


class Field(TypedDict):
    name: str
    type: str
    introduced_in: NotRequired[str]


class CmdRep(TypedDict):
    status: str
    fields: list[Field]


class NestedType(TypedDict):
    name: str
    discriminant_field: str
    variants: list[Variant]


class Variant(TypedDict):
    name: str
    discriminant_value: str
    fields: list[Field]


type CmdSpecs = list[CmdSpec]

type SpecsByMajor = dict[MajorVersion, CmdSpecs]
type SpecsByFamily = dict[str, SpecsByMajor]


def snake_case_to_upper_camel_case(name: str) -> str:
    words = name.split("_")

    if len(words) == 1:
        return words[0].title()

    return words[0].title() + "".join(word.title() for word in words[1:])


def camel_case_to_snake_case(name: str) -> str:
    out = ""
    for c in name:
        if c.isupper():
            out += "_"
        out += c.lower()
    if out.startswith("_"):
        return out[1:]
    return out


def cook_field_type(
    raw_type: str, field_parse_callback: Callable[[str | None, bool | None], str]
) -> str:
    for candidate, py_type_name in [
        ("Boolean", "bool"),
        ("String", "str"),
        ("Bytes", "bytes"),
        ("Integer", "int"),
        ("Float", "float"),
        ("Version", "int"),
        ("Size", "int"),
        ("Index", "int"),
        ("NonZeroInteger", "int"),
        ("NonZeroU8", "int"),
    ]:
        if raw_type == candidate:
            return py_type_name

    def _test_container(container: str):
        assert container.endswith("<")
        if raw_type.startswith(container):
            assert raw_type.endswith(">")
            return raw_type[len(container) : -1]

    is_list = _test_container("List<")
    if is_list:
        return f"list[{cook_field_type(is_list, field_parse_callback)}]"

    is_set = _test_container("Set<")
    if is_set:
        return f"set[{cook_field_type(is_set, field_parse_callback)}]"

    is_required_option = _test_container("RequiredOption<")
    if is_required_option:
        return f"{cook_field_type(is_required_option, field_parse_callback)} | None"

    is_non_required_option = _test_container("NonRequiredOption<")
    if is_non_required_option:
        return f"{cook_field_type(is_non_required_option, field_parse_callback)} | None"

    is_option = _test_container("Option<")
    if is_option:
        return f"{cook_field_type(is_option, field_parse_callback)} | None"

    is_map = _test_container("Map<")
    if is_map:
        key_type, value_type = [
            cook_field_type(x.strip(), field_parse_callback) for x in is_map.split(",", 1)
        ]
        return f"dict[{key_type}, {value_type}]"

    if raw_type.startswith("("):
        assert raw_type.endswith(")")
        items_types = [
            cook_field_type(x.strip(), field_parse_callback) for x in raw_type[1:-1].split(",")
        ]
        return f"tuple[{', '.join(items_types)}]"

    return field_parse_callback(raw_type, None)


def cook_field(
    field: Field, field_parse_callback: Callable[[str | None, bool | None], str]
) -> tuple[str, str]:
    field_parse_callback(None, "introduced_in" in field)
    return (field["name"], cook_field_type(field["type"], field_parse_callback))


def gen_req(
    req: CmdReq,
    collected_items: list[str],
    field_parse_callback: Callable[[str | None, bool | None], str],
) -> str:
    collected_items.append("Req")

    fields = [cook_field(f, field_parse_callback) for f in req.get("fields", ())]
    unit_type_name = req.get("unit")
    if unit_type_name:
        fields.append(("unit", unit_type_name))

    code = f"""class Req:
    def __init__(self, {",".join(n + ": " + t for n, t in fields)}) -> None: ...

    def dump(self) -> bytes: ...
"""
    for field_name, field_type in sorted(fields, key=lambda x: x[0]):
        code += f"""
    @property
    def {field_name}(self) -> {field_type}: ...
"""

    return code


def gen_reps(
    reps: list[CmdRep],
    collected_items: list[str],
    field_parse_callback: Callable[[str | None, bool | None], str],
) -> str:
    collected_items.append("Rep")
    collected_items.append("RepUnknownStatus")

    code = """class Rep:
    @staticmethod
    def load(raw: bytes) -> Rep: ...
    def dump(self) -> bytes: ...


class RepUnknownStatus(Rep):
    def __init__(self, status: str, reason: str | None) -> None: ...

    @property
    def status(self) -> str: ...

    @property
    def reason(self) -> str | None: ...
"""

    for rep in reps:
        rep_cls_name = f"Rep{snake_case_to_upper_camel_case(rep['status'])}"
        collected_items.append(rep_cls_name)

        fields = [cook_field(f, field_parse_callback) for f in rep.get("fields", ())]
        unit_type_name = rep.get("unit")
        if unit_type_name:
            fields.append(("unit", unit_type_name))

        code += f"""

class {rep_cls_name}(Rep):
    def __init__(self, {",".join(n + ": " + t for n, t in fields)}) -> None: ...
"""

        for field_name, field_type in sorted(fields, key=lambda x: x[0]):
            code += f"""
    @property
    def {field_name}(self) -> {field_type}: ...
"""

    return code


def gen_nested_type(
    nested_type: NestedType,
    collected_items: list[str],
    field_parse_callback: Callable[[str | None, bool | None], str],
) -> str:
    if "variants" in nested_type:
        return gen_nested_type_variant(nested_type, collected_items, field_parse_callback)
    else:
        return gen_nested_type_struct(nested_type, collected_items, field_parse_callback)


def gen_nested_type_variant(
    nested_type: NestedType,
    collected_items: list[str],
    field_parse_callback: Callable[[str | None, bool | None], str],
) -> str:
    class_name = nested_type["name"]
    collected_items.append(class_name)

    # Is a literal variant ?
    if all(not variants.get("fields", ()) for variants in nested_type["variants"]):
        code = f"""class {class_name}:
    VALUES: tuple[{class_name}]
"""
        for variant in nested_type["variants"]:
            name = camel_case_to_snake_case(variant["name"]).upper()
            code += f"    {name}: {class_name}\n"

        code += f"""
    @classmethod
    def from_str(cls, value: str) -> {class_name}: ...
    @property
    def str(self) -> str: ...
"""

    else:
        code = f"""class {class_name}:
    pass
"""
        for variant in nested_type["variants"]:
            subclass_name = f"{class_name}{variant['name']}"
            collected_items.append(subclass_name)
            fields = [cook_field(f, field_parse_callback) for f in variant.get("fields", ())]

            code += f"""
class {subclass_name}({class_name}):
    def __init__(self, {",".join(n + ": " + t for n, t in fields)}) -> None: ...
"""

            for field_name, field_type in sorted(fields, key=lambda x: x[0]):
                code += f"""
    @property
    def {field_name}(self) -> {field_type}: ...
"""

    return code


def gen_nested_type_struct(
    nested_type: NestedType,
    collected_items: list[str],
    field_parse_callback: Callable[[str | None, bool | None], str],
) -> str:
    class_name = nested_type["name"]
    collected_items.append(class_name)

    fields = [cook_field(f, field_parse_callback) for f in nested_type.get("fields", ())]

    code = f"""class {class_name}:
    def __init__(self, {",".join(n + ": " + t for n, t in fields)}) -> None: ...
"""

    for field_name, field_type in sorted(fields, key=lambda x: x[0]):
        code += f"""
    @property
    def {field_name}(self) -> {field_type}: ...
"""

    return code


def gen_single_version_cmd_spec(
    output_dir: Path,
    family_name: str,
    spec: CmdSpec,
    v_version: str,
    collected_items: dict[str, dict[str, list[str]]],
) -> bool:
    # Protocol code generator force separation if a field is marked `introduced_in`
    can_be_reused = True

    need_import_types: set[str] = set()

    def _field_parse_callback(field_type: str | None, introduced_in: bool | None) -> str:
        nonlocal can_be_reused
        if introduced_in is True:
            can_be_reused = False
        if field_type is None:
            return ""
        for nested_type in spec.get("nested_types", ()):
            if field_type == nested_type["name"]:
                return field_type
        need_import_types.add(field_type)
        return field_type

    cmd_name = spec["cmd"]

    cmd_collected_items: list[str] = []
    version_dir = output_dir / family_name / v_version
    version_dir.mkdir(exist_ok=True, parents=True)

    typing_file = version_dir / f"{cmd_name}.pyi"

    code = ""
    for nested_type in spec.get("nested_types", ()):
        code += gen_nested_type(nested_type, cmd_collected_items, _field_parse_callback)
        code += "\n\n"
    code += gen_req(spec["req"], cmd_collected_items, _field_parse_callback)
    code += "\n\n"
    code += gen_reps(spec["reps"], cmd_collected_items, _field_parse_callback)
    collected_items[v_version][cmd_name] = sorted(cmd_collected_items)

    code_prefix = f"{AUTOGENERATED_BANNER}\n\nfrom __future__ import annotations\n\n"
    if need_import_types:
        code_prefix += f"from parsec._parsec import {', '.join(need_import_types)}\n\n"
    code_prefix += "\n"

    typing_file.write_text(code_prefix + code, encoding="utf8")

    return can_be_reused


def gen_pyi_file_for_cmd_spec(
    output_dir: Path,
    family_name: str,
    spec: CmdSpec,
    collected_items: dict[str, dict[str, list[str]]],
) -> None:
    first_version = None
    other_versions: list[str] = []
    for version in sorted(spec["major_versions"]):
        v_version = f"v{version}"
        collected_items.setdefault(v_version, {})
        if first_version:
            other_versions.append(v_version)
        else:
            first_version = v_version
    assert first_version is not None

    can_be_reused = gen_single_version_cmd_spec(
        output_dir, family_name, spec, first_version, collected_items
    )
    if not can_be_reused:
        for other_version in other_versions:
            gen_single_version_cmd_spec(
                output_dir, family_name, spec, other_version, collected_items
            )

    else:
        cmd_name = spec["cmd"]
        for other_version in other_versions:
            reexported_items = collected_items[first_version][cmd_name]
            collected_items[other_version][cmd_name] = reexported_items
            code = (
                f"""
from ..{first_version}.{cmd_name} import {", ".join(reexported_items)}


__all__ = ["""
                + ", ".join(f'"{x}"' for x in reexported_items)
                + "]\n"
            )

            version_dir = output_dir / family_name / other_version
            version_dir.mkdir(exist_ok=True, parents=True)
            typing_file = version_dir / f"{cmd_name}.pyi"
            typing_file.write_text(code, encoding="utf8")


def collect_specs() -> SpecsByFamily:
    specs: SpecsByFamily = {}
    for family_path in PROTOCOL_SCHEMA_DIR.iterdir():
        family_specs: dict[int, CmdSpecs] = {}
        for cmd_path in family_path.glob("*.json5"):
            cmd_specs: CmdSpecs = json.loads(
                "\n".join(
                    [
                        x
                        for x in cmd_path.read_text(encoding="utf8").splitlines()
                        if not x.strip().startswith("//")
                    ]
                )
            )
            assert isinstance(cmd_specs, list), f"{repr(cmd_specs)[:100]}..."
            for cmd_spec in cmd_specs:
                assert isinstance(cmd_spec, dict), f"{repr(cmd_spec)[:100]}..."
                assert "major_versions" in cmd_spec, f"{repr(cmd_spec)[:100]}..."
                for version in cmd_spec["major_versions"]:
                    family_specs.setdefault(version, [])
                    family_specs[version].append(cmd_spec)
        assert family_path.name.endswith("_cmds")
        family_name = family_path.name[: -len("_cmds")]
        specs[family_name] = family_specs
    return specs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate code from templates")
    parser.add_argument(
        "--skip-style",
        action="store_true",
        help="Don't run pre-commit on the output",
    )
    args = parser.parse_args()
    arg_skip_style = cast(bool, args.skip_style)

    print(f"1/4 Cleaning old .pyi in {OUTPUT_PROTOCOL_TYPING_DIR}")

    for to_remove in OUTPUT_PROTOCOL_TYPING_DIR.glob("**/*.pyi"):
        to_remove.unlink()

    print("2/4 Generating .pyi files")

    # {<family>: {<version>: {<cmd>: [<collected items>]}}}
    collected_items: dict[str, dict[str, dict[str, list[str]]]] = {}
    for family_path in PROTOCOL_SCHEMA_DIR.iterdir():
        family_name = family_path.name
        collected_items[family_name] = {}
        for cmd_path in family_path.glob("*.json5"):
            cmd_specs: CmdSpecs = json.loads(
                "\n".join(
                    [
                        x
                        for x in cmd_path.read_text(encoding="utf8").splitlines()
                        if not x.strip().startswith("//")
                    ]
                )
            )
            assert isinstance(cmd_specs, list), f"{repr(cmd_specs)[:100]}..."
            for cmd_spec in cmd_specs:
                assert isinstance(cmd_spec, dict), f"{repr(cmd_spec)[:100]}..."
                assert "major_versions" in cmd_spec, f"{repr(cmd_spec)[:100]}..."
                gen_pyi_file_for_cmd_spec(
                    OUTPUT_PROTOCOL_TYPING_DIR,
                    family_path.name,
                    cmd_spec,
                    collected_items[family_name],
                )

    protocol_code = f"{AUTOGENERATED_BANNER}\n\nfrom __future__ import annotations\n\n"
    for family in collected_items.keys():
        protocol_code += f"from . import {family}\n"
    protocol_code += """

class ActiveUsersLimit:
    NO_LIMIT: ActiveUsersLimit

    @classmethod
    def from_maybe_int(cls, count: int | None) -> ActiveUsersLimit: ...
    "`ValueError` is raised if `count` is not a u64"
    @classmethod
    def limited_to(cls, user_count_limit: int) -> ActiveUsersLimit: ...
    "`ValueError` is raised if `count` is not a u64"
    def to_maybe_int(self) -> int | None: ...
    "Returns the user limit count as an integer or None if there's no limit specified"

    def __eq__(self, other: object) -> bool: ...
    def __ge__(self, other: object) -> bool: ...
    def __gt__(self, other: object) -> bool: ...
    def __le__(self, other: object) -> bool: ...
    def __lt__(self, other: object) -> bool: ...
    def __ne__(self, other: object) -> bool: ...
"""
    protocol_code += (
        '\n\n__all__ =["ActiveUsersLimit", '
        + ", ".join(f'"{f}"' for f in sorted(collected_items.keys()))
        + "]\n"
    )
    (OUTPUT_PROTOCOL_TYPING_DIR / "__init__.pyi").write_text(protocol_code, encoding="utf8")

    for family, versions in collected_items.items():
        ordered_versions = sorted(versions.keys())
        family_code = f"{AUTOGENERATED_BANNER}\n\nfrom __future__ import annotations\n\n"
        version = ""
        for version in ordered_versions:
            family_code += f"from . import {version}\n"
        family_code += f"from . import {version} as latest\n"
        family_code += (
            '\n\n__all__ =["latest", ' + ", ".join(f'"{v}"' for v in ordered_versions) + "]\n"
        )
        (OUTPUT_PROTOCOL_TYPING_DIR / family / "__init__.pyi").write_text(
            family_code, encoding="utf8"
        )

        for version, cmds in versions.items():
            version_code = f"""{AUTOGENERATED_BANNER}\n\nfrom __future__ import annotations

"""
            cmds_names = sorted(cmds.keys())
            for cmd in cmds_names:
                version_code += f"from . import {cmd}\n"

            version_code += f"""

class AnyCmdReq:
    @classmethod
    def load(cls, raw: bytes) -> {"|".join(cmd + ".Req" for cmd in cmds_names)}: ...
"""
            version_code += (
                '\n\n__all__ =["AnyCmdReq", ' + ", ".join(f'"{c}"' for c in cmds_names) + "]\n"
            )
            (OUTPUT_PROTOCOL_TYPING_DIR / family / version / "__init__.pyi").write_text(
                version_code, encoding="utf8"
            )

    print(f"3/4 Generating {OUTPUT_TEST_RPC_FILE}")

    # TODO: This is a hack hasty put together, in theory we should have json parsing
    # separated from protocol typing generation, which would make the generation of this
    # code much cleaner...

    test_rpc_code_headers: list[str] = []
    test_rpc_code_headers.append(AUTOGENERATED_BANNER)
    test_rpc_code_headers.append("")
    test_rpc_code_headers.append("from __future__ import annotations")
    test_rpc_code_headers.append("")
    test_rpc_code_body: list[str] = []
    test_rpc_code_need_import_types: set[str] = set()
    for family_name, specs in sorted(collect_specs().items()):
        family_mod_name = f"{family_name}_cmds"
        camel_case_family_name = snake_case_to_upper_camel_case(family_name)
        test_rpc_code_need_import_types.add(family_mod_name)
        test_rpc_code_body.append("")
        test_rpc_code_body.append(f"class Base{camel_case_family_name}RpcClient:")
        test_rpc_code_body.append(
            "    async def _do_request(self, req: bytes, family: str) -> bytes:"
        )
        test_rpc_code_body.append("        raise NotImplementedError")
        test_rpc_code_body.append("")
        last_version = max(specs.keys())
        v_version = f"v{last_version}"
        last_version_specs = specs[max(specs.keys())]
        for cmd_spec in sorted(last_version_specs, key=lambda x: x["cmd"]):
            req_spec = cmd_spec["req"]
            cmd_name = cmd_spec["cmd"]
            nested_types = {s["name"] for s in cmd_spec.get("nested_types", ())}
            if "unit" in req_spec:
                req_fields = {
                    "unit": f"{family_mod_name}.{v_version}.{cmd_name}.{req_spec['unit']}"
                }
            else:
                req_fields = {}
                for field in req_spec.get("fields", ()):

                    def _field_parse_callback(
                        field_type: str | None, introduced_in: bool | None
                    ) -> str:
                        if field_type is not None and field_type not in nested_types:
                            test_rpc_code_need_import_types.add(field_type)
                        if field_type is not None and field_type in nested_types:
                            return f"{family_mod_name}.latest.{cmd_name}.{field_type}"
                        else:
                            return field_type or ""

                    req_fields[field["name"]] = cook_field_type(
                        field["type"], _field_parse_callback
                    )
            fn_params = [f"{k}: {v}" for k, v in req_fields.items()]
            call_params = [f"{k}={k}" for k in req_fields.keys()]
            test_rpc_code_body.append("")
            test_rpc_code_body.append(
                f"    async def {cmd_name}(self, {','.join(fn_params)}) -> {family_mod_name}.latest.{cmd_name}.Rep:"
            )
            test_rpc_code_body.append(
                f"        req = {family_mod_name}.latest.{cmd_name}.Req({', '.join(call_params)})"
            )
            test_rpc_code_body.append(
                f'        raw_rep = await self._do_request(req.dump(), "{family_name}")'
            )
            test_rpc_code_body.append(
                f"        return {family_mod_name}.latest.{cmd_name}.Rep.load(raw_rep)"
            )

    test_rpc_code = [
        *test_rpc_code_headers,
        f"from parsec._parsec import {','.join(test_rpc_code_need_import_types)}",
        "",
        *test_rpc_code_body,
    ]
    OUTPUT_TEST_RPC_FILE.write_text("\n".join(test_rpc_code), encoding="utf8")

    if not arg_skip_style:
        print("4/4 Fix style")
        subprocess.call(
            [
                "pre-commit",
                "run",
                "--files",
                OUTPUT_TEST_RPC_FILE,
                *OUTPUT_PROTOCOL_TYPING_DIR.glob("**/*.pyi"),
            ],
            env={**os.environ, "SKIP": "mypy"},
            stdout=subprocess.PIPE,
        )
