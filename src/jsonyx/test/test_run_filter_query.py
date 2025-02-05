"""JSON run_filter_query tests."""
from __future__ import annotations

__all__: list[str] = []

from typing import TYPE_CHECKING, Any

import pytest

from jsonyx import JSONSyntaxError, run_filter_query
from jsonyx.test import check_syntax_err

if TYPE_CHECKING:
    _Node = tuple[dict[Any, Any] | list[Any], int | slice | str]


@pytest.mark.parametrize(("obj", "keep"), [
    # Missing key
    ([], False),

    # Key present
    ([0], True),
])
def test_has_key(obj: list[Any], keep: bool) -> None:  # noqa: FBT001
    """Test has key."""
    expected: list[_Node] = [(obj, 0)] if keep else []
    assert run_filter_query((obj, 0), "@") == expected


@pytest.mark.parametrize(("obj", "keep"), [
    # Missing key
    ([], True),

    # Key present
    ([0], False),
])
def test_has_not_key(obj: list[Any], keep: bool) -> None:  # noqa: FBT001
    """Test has not key."""
    expected: list[_Node] = [(obj, 0)] if keep else []
    assert run_filter_query((obj, 0), "!@") == expected


@pytest.mark.parametrize(("query", "keep"), [
    # Less than or equal to
    ("@ <= -1", False),
    ("@ <= 0", True),
    ("@ <= 1", True),

    # Less than
    ("@ < -1", False),
    ("@ < 0", False),
    ("@ < 1", True),

    # Equal to
    ("@ == 1", False),
    ("@ == 0", True),

    # Not equal to
    ("@ != 0", False),
    ("@ != 1", True),

    # Greater than or equal to
    ("@ >= 1", False),
    ("@ >= 0", True),
    ("@ >= -1", True),

    # Greater than
    ("@ > 1", False),
    ("@ > 0", False),
    ("@ > -1", True),
])
def test_operator(query: str, keep: bool) -> None:  # noqa: FBT001
    """Test operator."""
    expected: list[_Node] = [([0], 0)] if keep else []
    assert run_filter_query(([0], 0), query) == expected


@pytest.mark.parametrize("query", [
    # No whitespace
    "@==0",

    # Before operator
    "@ ==0",

    # After operator
    "@== 0",
])
def test_operator_whitespace(query: str) -> None:
    """Test whitespace around operator."""
    assert not run_filter_query([], query)


def test_and() -> None:
    """Test and."""
    query: str = "@ != 1 && @ != 2 && @ != 3"
    assert run_filter_query(([0], 0), query) == [([0], 0)]


@pytest.mark.parametrize("query", [
    # Before and
    "@!=1 &&@!=2 &&@!=3",

    # After and
    "@!=1&& @!=2&& @!=3",
])
def test_whitespace(query: str) -> None:
    """Test whitespace around and."""
    assert run_filter_query(([0], 0), query) == [([0], 0)]


@pytest.mark.parametrize(("query", "msg", "colno", "end_colno"), [
    ("", "Expecting a relative query", 1, -1),  # relative=True
    ("@?", "Optional marker is not allowed", 2, 3),  # mapping=True
    ("@ == ", "Expecting value", 6, -1),
    ("@ && ", "Expecting a relative query", 6, -1),
    ("!@ == 0", "Unexpected operator", 4, 6),
    ("@ @ @", "Expecting end of file", 2, -1),
])
def test_invalid_query(
    query: str, msg: str, colno: int, end_colno: int,
) -> None:
    """Test invalid query."""
    with pytest.raises(JSONSyntaxError) as exc_info:
        run_filter_query([], query)

    check_syntax_err(exc_info, msg, colno, end_colno)


def test_slice() -> None:
    """Test slice."""
    with pytest.raises(TypeError, match="List index must be int"):
        run_filter_query(([[]], 0), "@[:]")
