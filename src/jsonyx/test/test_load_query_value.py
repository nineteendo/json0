# Copyright (C) 2024 Nice Zombies
"""JSON load_query_value tests."""
# TODO(Nice Zombies): add more tests
from __future__ import annotations

__all__: list[str] = []

from decimal import Decimal
from typing import Any

import pytest

# pylint: disable-next=W0611
from jsonyx import JSONSyntaxError, load_query_value
from jsonyx.allow import NAN_AND_INFINITY


def _check_syntax_err(
    exc_info: pytest.ExceptionInfo[Any], msg: str, colno: int = 1,
    end_colno: int = -1,
) -> None:
    exc: Any = exc_info.value
    if end_colno < 0:
        end_colno = colno

    assert exc.msg == msg
    assert exc.lineno == 1
    assert exc.end_lineno == 1
    assert exc.colno == colno
    assert exc.end_colno == end_colno


@pytest.mark.parametrize(("s", "expected"), [
    ("true", True),
    ("false", False),
    ("null", None),
])
def test_literal_names(s: str, expected: bool | None) -> None:  # noqa: FBT001
    """Test literal names."""
    assert load_query_value(s) is expected


@pytest.mark.parametrize("s", ["Infinity", "-Infinity"])
@pytest.mark.parametrize("use_decimal", [True, False])
def test_infinity(s: str, use_decimal: bool) -> None:  # noqa: FBT001
    """Test infinity."""
    obj: object = load_query_value(
        s, allow=NAN_AND_INFINITY, use_decimal=use_decimal,
    )
    expected_type: type[Decimal | float] = Decimal if use_decimal else float
    expected: Decimal | float = expected_type(s)
    assert isinstance(obj, expected_type)
    assert obj == expected


@pytest.mark.parametrize("s", ["Infinity", "-Infinity"])
@pytest.mark.parametrize("use_decimal", [True, False])
def test_infinity_not_allowed(
    s: str, use_decimal: bool,  # noqa: FBT001
) -> None:
    """Test infinity when not allowed."""
    with pytest.raises(JSONSyntaxError) as exc_info:
        load_query_value(s, use_decimal=use_decimal)

    _check_syntax_err(exc_info, f"{s} is not allowed", 1, len(s) + 1)


@pytest.mark.parametrize("s", [
    # Sign
    "-1",

    # Integer
    "0", "1", "10", "11",
])
def test_int(s: str) -> None:
    """Test integer."""
    obj: object = load_query_value(s)
    assert isinstance(obj, int)
    assert obj == int(s)


@pytest.mark.parametrize("s", [
    # Sign
    "-1.0",

    # Fraction
    "1.0", "1.01", "1.1", "1.11",

    # Fraction with trailing zeros
    "1.00", "1.10",

    # Exponent e
    "1E1",

    # Exponent sign
    "1e-1", "1e+1",

    # Exponent power
    "1e0", "1e1", "1e10", "1e11",

    # Exponent power with leading zeros
    "1e00", "1e01",

    # Parts
    "1.1e1", "-1e1", "-1.1", "-1.1e1",
])
@pytest.mark.parametrize("use_decimal", [True, False])
def test_rational_number(s: str, use_decimal: bool) -> None:  # noqa: FBT001
    """Test rational number."""
    obj: object = load_query_value(s, use_decimal=use_decimal)
    expected_type: type[Decimal | float] = Decimal if use_decimal else float
    assert isinstance(obj, expected_type)
    assert obj == expected_type(s)


@pytest.mark.parametrize("s", ["1e400", "-1e400"])
def test_big_number_decimal(s: str) -> None:
    """Test big JSON number with decimal."""
    assert load_query_value(s, use_decimal=True) == Decimal(s)


@pytest.mark.parametrize("s", ["1e400", "-1e400"])
def test_big_number_float(s: str) -> None:
    """Test big JSON number with float."""
    with pytest.raises(JSONSyntaxError) as exc_info:
        load_query_value(s)

    _check_syntax_err(exc_info, "Big numbers require decimal", 1, len(s) + 1)


@pytest.mark.parametrize(
    "s", ["1e1000000000000000000", "-1e1000000000000000000"],
)
def test_too_big_number(s: str) -> None:
    """Test too big JSON number."""
    with pytest.raises(JSONSyntaxError) as exc_info:
        load_query_value(s, use_decimal=True)

    _check_syntax_err(exc_info, "Number is too big", 1, len(s) + 1)


@pytest.mark.parametrize("s", ["", "foo"])
def test_expecting_value(s: str) -> None:
    """Test expecting JSON value."""
    with pytest.raises(JSONSyntaxError) as exc_info:
        load_query_value(s)

    _check_syntax_err(exc_info, "Expecting value")
