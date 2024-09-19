# Copyright (C) 2024 Nice Zombies
"""JSON run_select_query tests."""
# TODO(Nice Zombies): add more tests
from __future__ import annotations

__all__: list[str] = []

from typing import TYPE_CHECKING, Any

import pytest

from jsonyx import JSONSyntaxError, run_select_query
# pylint: disable-next=W0611
from jsonyx.test import get_big_num  # type: ignore # noqa: F401
from jsonyx.test import check_syntax_err

if TYPE_CHECKING:
    _Target = dict[Any, Any] | list[Any]
    _Key = int | slice | str
    _Node = tuple[_Target, _Key]


# pylint: disable-next=R0903
class _Slicer:
    @staticmethod
    def __getitem__(item: slice) -> slice:
        return item


_slicer: _Slicer = _Slicer()


@pytest.mark.parametrize(("node", "keep"), [
    # List
    (([], slice(0)), True),
    (([], 0), False),
    (([0], 0), True),

    # Dict
    (({}, ""), False),
    (({"": 0}, ""), True),
])  # type: ignore
def test_optional_marker(node: _Node, keep: bool) -> None:  # noqa: FBT001
    """Test optional marker."""
    expected: list[_Node] = [node] if keep else []
    assert run_select_query(node, "$?", allow_slice=True) == expected


def test_optional_marker_not_allowed() -> None:
    """Test optional marker when not allowed."""
    with pytest.raises(JSONSyntaxError) as exc_info:
        run_select_query([], "$?", mapping=True)

    check_syntax_err(exc_info, "Optional marker is not allowed", 2, 3)


@pytest.mark.parametrize("key", [
    # First character
    "A", "_", "\u16ee", "\u1885", "\u2118",

    # Remaining characters
    "A0", "AA", "A_", "A\u0300", "A\u2118",
])
def test_property(key: str) -> None:
    """Test property."""
    assert run_select_query(([{}], 0), f"$.{key}") == [({}, key)]


@pytest.mark.parametrize("query", ["$.a.b", "$.a[0]"])
def test_list_property(query: str) -> None:
    """Test property on a list."""
    match: str = "List index must be int or slice, not"
    with pytest.raises(TypeError, match=match):
        run_select_query(([[]], 0), query)


@pytest.mark.parametrize("query", [
    # At the end
    "$.a",

    # In the middle
    "$.a.b", "$.a[0]",
])
def test_list_property_mapping(query: str) -> None:
    """Test property on a list."""
    with pytest.raises(TypeError, match="List index must be int, not"):
        run_select_query(([[]], 0), query, mapping=True)


@pytest.mark.parametrize("key", [
    # First character
    "\x00", " ", "!", "$", "0", "\xb2", "\u0300", "\u037a", "\u0488",

    # Remaining characters
    "A\xb2", "A\u037a", "A\u0488",
])
def test_invalid_property(key: str) -> None:
    """Test invalid property."""
    with pytest.raises(JSONSyntaxError) as exc_info:
        run_select_query([], f"$.{key}")

    check_syntax_err(exc_info, "Expecting property", 3)


@pytest.mark.parametrize(("query", "expected"), [
    # Slice
    ("$[:]", _slicer[:]),
    ("$[-1:]", _slicer[-1:]),
    ("$[0:]", _slicer[0:]),
    ("$[1:]", _slicer[1:]),
    ("$[10:]", _slicer[10:]),
    ("$[11:]", _slicer[11:]),
    ("$[:-1]", _slicer[:-1]),
    ("$[:0]", _slicer[:0]),
    ("$[:1]", _slicer[:1]),
    ("$[:10]", _slicer[:10]),
    ("$[:11]", _slicer[:11]),

    # Extended slice
    ("$[::]", _slicer[::]),
    ("$[-1::]", _slicer[-1::]),
    ("$[0::]", _slicer[0::]),
    ("$[1::]", _slicer[1::]),
    ("$[10::]", _slicer[10::]),
    ("$[11::]", _slicer[11::]),
    ("$[:-1:]", _slicer[:-1:]),
    ("$[:0:]", _slicer[:0:]),
    ("$[:1:]", _slicer[:1:]),
    ("$[:10:]", _slicer[:10:]),
    ("$[:11:]", _slicer[:11:]),
    ("$[::-1]", _slicer[::-1]),
    ("$[::0]", _slicer[::0]),
    ("$[::1]", _slicer[::1]),
    ("$[::10]", _slicer[::10]),
    ("$[::11]", _slicer[::11]),
])
def test_slice(query: str, expected: slice) -> None:
    """Test slice."""
    node: _Node = [[]], 0
    assert run_select_query(node, query, allow_slice=True) == [([], expected)]


@pytest.mark.parametrize("query", [
    # At the end
    "$[:]",

    # In the middle
    "$[:].b", "$[:][0]",
])
def test_slice_not_allowed(query: str) -> None:
    """Test slice when not allowed."""
    with pytest.raises(TypeError, match="List index must be int, not"):
        run_select_query(([[]], 0), query, mapping=True)


@pytest.mark.parametrize("query", [
    # At the end
    "$[:]",

    # In the middle
    "$[:].b", "$[:][0]",
])
def test_dict_slice(query: str) -> None:
    """Test slice on a dict."""
    with pytest.raises(TypeError, match="Dict key must be str, not"):
        run_select_query(([{}], 0), query)


@pytest.mark.parametrize(("query", "msg", "colno"), [
    # Start
    ("$[{big_num}:]", "Start is too big", 3),
    ("$[{big_num}::]", "Start is too big", 3),

    # Stop
    ("$[:{big_num}]", "Stop is too big", 4),
    ("$[:{big_num}:]", "Stop is too big", 4),

    # Step
    ("$[::{big_num}]", "Step is too big", 5),
])
def test_too_big_slice_idx(
    big_num: str, query: str, msg: str, colno: int,
) -> None:
    """Test too big slice index."""
    with pytest.raises(JSONSyntaxError) as exc_info:
        run_select_query([], query.format(big_num=big_num))

    check_syntax_err(exc_info, msg, colno, colno + len(big_num))


@pytest.mark.parametrize("num", [
    # Sign
    "-1",

    # Integer
    "0", "1", "10", "11",
])
def test_idx(num: str) -> None:
    """Test index."""
    assert run_select_query(([[]], 0), f"$[{num}]") == [([], int(num))]


@pytest.mark.parametrize("query", [
    # At the end
    "$[0]",

    # In the middle
    "$[0].b", "$[0][0]",
])
def test_dict_idx(query: str) -> None:
    """Test index on a dict."""
    with pytest.raises(TypeError, match="Dict key must be str, not"):
        run_select_query(([{}], 0), query)


def test_too_big_idx(big_num: str) -> None:
    """Test too big index."""
    with pytest.raises(JSONSyntaxError) as exc_info:
        run_select_query([], f"$[{big_num}]")

    check_syntax_err(exc_info, "Index is too big", 3, 3 + len(big_num))


@pytest.mark.parametrize(("obj", "query", "keys"), [
    ([1, 2, 3], "$[@]", [0, 1, 2]),
    ({"a": 1, "b": 2, "c": 3}, "$[@]", ["a", "b", "c"]),
])
def test_filter(obj: _Target, query: str, keys: list[_Key]) -> None:
    """Test filter."""
    assert run_select_query(([obj], 0), query) == [(obj, key) for key in keys]


def test_filter_not_allowed() -> None:
    """Test filter when not allowed."""
    with pytest.raises(JSONSyntaxError) as exc_info:
        run_select_query([], "$[@]", mapping=True)

    check_syntax_err(exc_info, "Filter is not allowed", 3)


@pytest.mark.parametrize(("obj", "query", "expected"), [
    # Root
    (0, "$", ([0], 0)),

    # Key
    ({}, "$['']", ({}, "")),

    # Multiple levels
    ([[[0]]], "$[0][0][0]", ([0], 0)),
])  # type: ignore
def test_query(obj: _Target, query: str, expected: _Node) -> None:
    """Test root."""
    assert run_select_query(([obj], 0), query) == [expected]


@pytest.mark.parametrize(("query", "msg", "colno"), [
    ("", "Expecting an absolute query", 1),
    ("@", "Expecting an absolute query", 1),
    ("$[0", "Expecting a closing bracket", 4),
    ("$ $ $", "Expecting end of file", 2),
])
def test_invalid_query(query: str, msg: str, colno: int) -> None:
    """Test invalid query."""
    with pytest.raises(JSONSyntaxError) as exc_info:
        run_select_query([], query)

    check_syntax_err(exc_info, msg, colno)


@pytest.mark.parametrize("query", ["", "$"])
def test_invalid_relative_query(query: str) -> None:
    """Test invalid relative query."""
    with pytest.raises(JSONSyntaxError) as exc_info:
        run_select_query([], query, relative=True)

    check_syntax_err(exc_info, "Expecting a relative query")
