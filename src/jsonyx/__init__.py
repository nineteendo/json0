# Copyright (C) 2024 Nice Zombies
"""Customizable JSON library for Python."""
# TODO(Nice Zombies): link to v2.0.0 in changelog
# TODO(Nice Zombies): update raised exceptions
# TODO(Nice Zombies): add example with mapping_types and seq_types
from __future__ import annotations

__all__: list[str] = [
    "Decoder",
    "DuplicateKey",
    "Encoder",
    "JSONSyntaxError",
    "Manipulator",
    "apply_patch",
    "detect_encoding",
    "dump",
    "dumps",
    "format_syntax_error",
    "load",
    "load_query_value",
    "loads",
    "make_patch",
    "read",
    "run_filter_query",
    "run_select_query",
    "write",
]
__version__: str = "2.0.0"

from sys import stdout
from typing import TYPE_CHECKING, Any, Literal

from jsonyx._decoder import (
    Decoder, DuplicateKey, JSONSyntaxError, detect_encoding,
)
from jsonyx._differ import make_patch
from jsonyx._encoder import Encoder
from jsonyx._manipulator import Manipulator
from jsonyx.allow import NOTHING

if TYPE_CHECKING:
    from collections.abc import Container

    from _typeshed import StrPath, SupportsRead, SupportsWrite

    _AllowList = Container[Literal[
        "comments", "duplicate_keys", "missing_commas", "nan_and_infinity",
        "surrogates", "trailing_comma",
    ] | str]
    _Node = tuple[dict[Any, Any] | list[Any], int | slice | str]


def format_syntax_error(exc: JSONSyntaxError) -> list[str]:
    """Format a JSON syntax error.

    :param exc: a JSON syntax error
    :type exc: JSONSyntaxError
    :return: a list of strings, each ending in a newline
    :rtype: list[str]

    >>> import jsonyx as json
    >>> try:
    ...     json.loads("[,]")
    ... except json.JSONSyntaxError as exc:
    ...     print("Traceback (most recent call last):")
    ...     print(end="".join(json.format_syntax_error(exc)))
    ...
    Traceback (most recent call last):
      File "<string>", line 1, column 2
        [,]
         ^
    jsonyx.JSONSyntaxError: Expecting value

    .. note::
        Don't use :func:`traceback.format_exception_only`, it displays less
        information.
    """
    if exc.end_lineno == exc.lineno:
        line_range: str = f"{exc.lineno:d}"
    else:
        line_range = f"{exc.lineno:d}-{exc.end_lineno:d}"

    if exc.end_colno == exc.colno:
        column_range: str = f"{exc.colno:d}"
    else:
        column_range = f"{exc.colno:d}-{exc.end_colno:d}"

    caret_indent: str = " " * (exc.offset - 1)  # type: ignore
    caret_selection: str = "^" * (exc.end_offset - exc.offset)  # type: ignore
    return [
        f'  File "{exc.filename}", line {line_range}, column {column_range}\n',
        f"    {exc.text}\n",
        f"    {caret_indent}{caret_selection}\n",
        f"{exc.__module__}.{type(exc).__qualname__}: {exc.msg}\n",
    ]


def read(
    filename: StrPath,
    *,
    allow: _AllowList = NOTHING,
    use_decimal: bool = False,
) -> Any:
    """Deserialize a JSON file to a Python object.

    :param filename: the path to the JSON file
    :type filename: StrPath
    :param allow: the allowed JSON deviations, defaults to
                  :data:`jsonyx.allow.NOTHING`
    :type allow: Container[str], optional
    :param use_decimal: use :class:`decimal.Decimal` instead of :class:`float`,
                        defaults to ``False``
    :type use_decimal: bool, optional
    :raises JSONSyntaxError: if the JSON file is invalid
    :return: a Python object.
    :rtype: Any

    >>> import jsonyx as json
    >>> from pathlib import Path
    >>> from tempfile import TemporaryDirectory
    >>> with TemporaryDirectory() as tmpdir:
    ...     filename = Path(tmpdir) / "file.json"
    ...     _ = filename.write_text('["filesystem API"]', "utf_8")
    ...     json.Decoder().read(filename)
    ...
    ['filesystem API']
    """
    return Decoder(allow=allow, use_decimal=use_decimal).read(filename)


def load(
    fp: SupportsRead[bytes | str],
    *,
    allow: _AllowList = NOTHING,
    root: StrPath = ".",
    use_decimal: bool = False,
) -> Any:
    """Deserialize an open JSON file to a Python object.

    :param fp: an open JSON file
    :type fp: SupportsRead[bytes | str]
    :param allow: the allowed JSON deviations, defaults to
                  :data:`jsonyx.allow.NOTHING`
    :type allow: Container[str], optional
    :param root: the path to the archive containing this JSON file, defaults to
                 ``"."``
    :type root: StrPath, optional
    :param use_decimal: use :class:`decimal.Decimal` instead of :class:`float`,
                        defaults to ``False``
    :type use_decimal: bool, optional
    :raises JSONSyntaxError: if the JSON file is invalid
    :return: a Python object
    :rtype: Any

    >>> import jsonyx as json
    >>> from io import StringIO
    >>> io = StringIO('["streaming API"]')
    >>> json.load(io)
    ['streaming API']
    """
    return Decoder(allow=allow, use_decimal=use_decimal).load(fp, root=root)


def loads(
    s: bytearray | bytes | str,
    *,
    allow: _AllowList = NOTHING,
    filename: StrPath = "<string>",
    use_decimal: bool = False,
) -> Any:
    """Deserialize a JSON string to a Python object.

    :param s: a JSON string
    :type s: bytearray | bytes | str
    :param allow: the allowed JSON deviations, defaults to
                  :data:`jsonyx.allow.NOTHING`
    :type allow: Container[str], optional
    :param filename: the path to the JSON file, defaults to ``"<string>"``
    :type filename: StrPath, optional
    :param use_decimal: use :class:`decimal.Decimal` instead of :class:`float`,
                        defaults to ``False``
    :type use_decimal: bool, optional
    :raises JSONSyntaxError: if the JSON string is invalid
    :return: a Python object
    :rtype: Any

    >>> import jsonyx as json
    >>> json.loads('{"foo": ["bar", null, 1.0, 2]}')
    {'foo': ['bar', None, 1.0, 2]}

    .. tip::
        Specify *filename* to display the filename in error messages.
    """
    return Decoder(allow=allow, use_decimal=use_decimal).loads(
        s, filename=filename,
    )


def write(
    obj: object,
    filename: StrPath,
    *,
    allow: _AllowList = NOTHING,
    commas: bool = True,
    end: str = "\n",
    ensure_ascii: bool = False,
    indent: int | str | None = None,
    indent_leaves: bool = False,
    mapping_types: type | tuple[type] = dict,
    quoted_keys: bool = True,
    separators: tuple[str, str] = (", ", ": "),
    seq_types: type | tuple[type] = list,
    sort_keys: bool = False,
    trailing_comma: bool = False,
) -> None:
    r"""Serialize a Python object to a JSON file.

    :param obj: a Python object
    :type obj: object
    :param filename: the path to the JSON file
    :type filename: StrPath
    :param allow: the allowed JSON deviations, defaults to
                  :data:`jsonyx.allow.NOTHING`
    :type allow: Container[str], optional
    :param commas: separate items by commas when indented, defaults to ``True``
    :type commas: bool, optional
    :param end: the string to append at the end, defaults to ``"\n"``
    :type end: str, optional
    :param ensure_ascii: escape non-ASCII characters, defaults to ``False``
    :type ensure_ascii: bool, optional
    :param indent: the number of spaces or string to indent with, defaults to
                   ``None``
    :type indent: int | str | None, optional
    :param indent_leaves: indent leaf objects and arrays, defaults to ``False``
    :type indent_leaves: bool, optional
    :param mapping_types: the mapping type or tuple of mapping types, defaults
                          to :class:`dict`
    :type mapping_types: type | tuple[type], optional
    :param quoted_keys: quote keys which are identifiers, defaults to ``True``
    :type quoted_keys: bool, optional
    :param separators: the item and key separator, defaults to ``(", ", ": ")``
    :type separators: tuple[str, str], optional
    :param seq_types: the sequence type or tuple of sequence types, defaults
                      to :class:`list`
    :type seq_types: type | tuple[type], optional
    :param sort_keys: sort the keys of objects, defaults to ``False``
    :type sort_keys: bool, optional
    :param trailing_comma: add a trailing comma when indented, defaults to
                           ``False``
    :type trailing_comma: bool, optional
    :raises TypeError: for unserializable values
    :raises ValueError: for invalid values

    >>> import jsonyx as json
    >>> from pathlib import Path
    >>> from tempfile import TemporaryDirectory
    >>> with TemporaryDirectory() as tmpdir:
    ...     filename = Path(tmpdir) / "file.json"
    ...     json.write(["filesystem API"], filename)
    ...     filename.read_text("utf_8")
    ...
    '["filesystem API"]\n'

    .. note::
        The item separator is automatically stripped when indented.

    .. versionchanged:: 2.0
        Added *commas*, *indent_leaves*, *mapping_types*, *seq_types* and
        *quoted_keys*.
        Merged *item_separator* and *key_separator* as *separators*.
    """
    return Encoder(
        allow=allow,
        commas=commas,
        end=end,
        ensure_ascii=ensure_ascii,
        indent=indent,
        indent_leaves=indent_leaves,
        mapping_types=mapping_types,
        quoted_keys=quoted_keys,
        separators=separators,
        seq_types=seq_types,
        sort_keys=sort_keys,
        trailing_comma=trailing_comma,
    ).write(obj, filename)


def dump(
    obj: object,
    fp: SupportsWrite[str] = stdout,
    *,
    allow: _AllowList = NOTHING,
    commas: bool = True,
    end: str = "\n",
    ensure_ascii: bool = False,
    indent: int | str | None = None,
    indent_leaves: bool = False,
    mapping_types: type | tuple[type] = dict,
    quoted_keys: bool = True,
    separators: tuple[str, str] = (", ", ": "),
    seq_types: type | tuple[type] = list,
    sort_keys: bool = False,
    trailing_comma: bool = False,
) -> None:
    r"""Serialize a Python object to an open JSON file.

    :param obj: a Python object
    :type obj: object
    :param fp: an open JSON file, defaults to :data:`sys.stdout`
    :type fp: SupportsWrite[str], optional
    :param allow: the allowed JSON deviations, defaults to
                  :data:`jsonyx.allow.NOTHING`
    :type allow: Container[str], optional
    :param commas: separate items by commas when indented, defaults to ``True``
    :type commas: bool, optional
    :param end: the string to append at the end, defaults to ``"\n"``
    :type end: str, optional
    :param ensure_ascii: escape non-ASCII characters, defaults to ``False``
    :type ensure_ascii: bool, optional
    :param indent: the number of spaces or string to indent with, defaults to
                   ``None``
    :type indent: int | str | None, optional
    :param indent_leaves: indent leaf objects and arrays, defaults to ``False``
    :type indent_leaves: bool, optional
    :param mapping_types: the mapping type or tuple of mapping types, defaults
                          to :class:`dict`
    :type mapping_types: type | tuple[type], optional
    :param quoted_keys: quote keys which are identifiers, defaults to ``True``
    :type quoted_keys: bool, optional
    :param separators: the item and key separator, defaults to ``(", ", ": ")``
    :type separators: tuple[str, str], optional
    :param seq_types: the sequence type or tuple of sequence types, defaults
                      to :class:`list`
    :type seq_types: type | tuple[type], optional
    :param sort_keys: sort the keys of objects, defaults to ``False``
    :type sort_keys: bool, optional
    :param trailing_comma: add a trailing comma when indented, defaults to
                           ``False``
    :type trailing_comma: bool, optional
    :raises TypeError: for unserializable values
    :raises ValueError: for invalid values

    >>> import jsonyx as json
    >>> json.dump({"foo": ["bar", None, 1.0, 2]})
    {"foo": ["bar", null, 1.0, 2]}
    >>> from io import StringIO
    >>> io = StringIO()
    >>> json.dump(["streaming API"], io)
    >>> io.getvalue()
    '["streaming API"]\n'

    .. note::
        The item separator is automatically stripped when indented.

    .. warning::
        To pretty-print unpaired surrogates, you need to use
        :data:`jsonyx.allow.SURROGATES` and ``ensure_ascii=True``.

    .. versionchanged:: 2.0
        Added *commas*, *indent_leaves*, *mapping_types*, *seq_types* and
        *quoted_keys*.
        Merged *item_separator* and *key_separator* as *separators*.
    """
    Encoder(
        allow=allow,
        commas=commas,
        end=end,
        ensure_ascii=ensure_ascii,
        indent=indent,
        indent_leaves=indent_leaves,
        mapping_types=mapping_types,
        quoted_keys=quoted_keys,
        separators=separators,
        seq_types=seq_types,
        sort_keys=sort_keys,
        trailing_comma=trailing_comma,
    ).dump(obj, fp)


def dumps(
    obj: object,
    *,
    allow: _AllowList = NOTHING,
    commas: bool = True,
    end: str = "\n",
    ensure_ascii: bool = False,
    indent: int | str | None = None,
    indent_leaves: bool = False,
    mapping_types: type | tuple[type] = dict,
    quoted_keys: bool = True,
    separators: tuple[str, str] = (", ", ": "),
    seq_types: type | tuple[type] = list,
    sort_keys: bool = False,
    trailing_comma: bool = False,
) -> str:
    r"""Serialize a Python object to a JSON string.

    :param obj: a Python object
    :type obj: object
    :param allow: the allowed JSON deviations, defaults to
                  :data:`jsonyx.allow.NOTHING`
    :type allow: Container[str], optional
    :param commas: separate items by commas when indented, defaults to ``True``
    :type commas: bool, optional
    :param end: the string to append at the end, defaults to ``"\n"``
    :type end: str, optional
    :param ensure_ascii: escape non-ASCII characters, defaults to ``False``
    :type ensure_ascii: bool, optional
    :param indent: the number of spaces or string to indent with, defaults to
                   ``None``
    :type indent: int | str | None, optional
    :param indent_leaves: indent leaf objects and arrays, defaults to ``False``
    :type indent_leaves: bool, optional
    :param mapping_types: the mapping type or tuple of mapping types, defaults
                          to :class:`dict`
    :type mapping_types: type | tuple[type], optional
    :param quoted_keys: quote keys which are identifiers, defaults to ``True``
    :type quoted_keys: bool, optional
    :param separators: the item and key separator, defaults to ``(", ", ": ")``
    :type separators: tuple[str, str], optional
    :param seq_types: the sequence type or tuple of sequence types, defaults
                      to :class:`list`
    :type seq_types: type | tuple[type], optional
    :param sort_keys: sort the keys of objects, defaults to ``False``
    :type sort_keys: bool, optional
    :param trailing_comma: add a trailing comma when indented, defaults to
                           ``False``
    :type trailing_comma: bool, optional
    :raises TypeError: for unserializable values
    :raises ValueError: for invalid values
    :return: a JSON string
    :rtype: str

    >>> import jsonyx as json
    >>> json.dumps({"foo": ["bar", None, 1.0, 2]})
    '{"foo": ["bar", null, 1.0, 2]}\n'

    .. note::
        The item separator is automatically stripped when indented.

    .. versionchanged:: 2.0
        Added *commas*, *indent_leaves*, *mapping_types*, *seq_types* and
        *quoted_keys*.
        Merged *item_separator* and *key_separator* as *separators*.
    """
    return Encoder(
        allow=allow,
        commas=commas,
        end=end,
        ensure_ascii=ensure_ascii,
        indent=indent,
        indent_leaves=indent_leaves,
        mapping_types=mapping_types,
        quoted_keys=quoted_keys,
        separators=separators,
        seq_types=seq_types,
        sort_keys=sort_keys,
        trailing_comma=trailing_comma,
    ).dumps(obj)


def apply_patch(
    obj: Any,
    patch: dict[str, Any] | list[dict[str, Any]],
    *,
    allow: _AllowList = NOTHING,
    use_decimal: bool = False,
) -> Any:
    """Apply a JSON patch to a Python object.

    :param obj: a Python object
    :type obj: Any
    :param patch: a JSON patch
    :type patch: dict[str, Any] | list[dict[str, Any]]
    :param allow: the allowed JSON deviations, defaults to
                  :data:`jsonyx.allow.NOTHING`
    :type allow: Container[str], optional
    :param use_decimal: use :class:`decimal.Decimal` instead of :class:`float`,
                        defaults to ``False``
    :type use_decimal: bool, optional
    :raises AssertionError: if an assertion fails
    :raises SyntaxError: if a query is invalid
    :raises TypeError: if a value has the wrong type
    :raises ValueError: if a value is invalid
    :return: the patched Python object
    :rtype: Any

    >>> import jsonyx as json
    >>> json.apply_patch([1, 2, 3], {'op': 'del', 'path': '$[1]'})
    [1, 3]

    .. tip::
        Using queries instead of indices is more robust.

    .. versionadded:: 2.0
    """
    return Manipulator(allow=allow, use_decimal=use_decimal).apply_patch(
        obj, patch,
    )


def run_select_query(
    nodes: _Node | list[_Node],
    query: str,
    *,
    allow: _AllowList = NOTHING,
    allow_slice: bool = False,
    mapping: bool = False,
    relative: bool = False,
    use_decimal: bool = False,
) -> list[_Node]:
    """Run a JSON select query on a node or a list of nodes.

    :param nodes: a node or a list of nodes
    :type nodes: _Node | list[_Node]
    :param query: a JSON select query
    :type query: str
    :param allow: the allowed JSON deviations, defaults to
                  :data:`jsonyx.allow.NOTHING`
    :type allow: Container[str], optional
    :param allow_slice: allow slice, defaults to ``False``
    :type allow_slice: bool, optional
    :param mapping: map every input node to a single output node, defaults to
                    ``False``
    :type mapping: bool, optional
    :param relative: query must start with ``"@"`` instead of ``"$"``, defaults
                     to ``False``
    :type relative: bool, optional
    :param use_decimal: use :class:`decimal.Decimal` instead of :class:`float`,
                        defaults to ``False``
    :type use_decimal: bool, optional
    :raises SyntaxError: if the select query is invalid
    :raises ValueError: if a value is invalid
    :return: the selected list of nodes
    :rtype: list[_Node]

    >>> import jsonyx as json
    >>> root = [[1, 2, 3, 4, 5, 6]]
    >>> node = root, 0
    >>> for target, key in json.run_select_query(node, "$[@ > 3]"):
    ...     target[key] = None
    ...
    >>> root[0]
    [1, 2, 3, None, None, None]

    .. tip::
        Using queries instead of indices is more robust.

    .. versionadded:: 2.0
    """
    return Manipulator(allow=allow, use_decimal=use_decimal).run_select_query(
        nodes,
        query,
        allow_slice=allow_slice,
        mapping=mapping,
        relative=relative,
    )


def run_filter_query(
    nodes: _Node | list[_Node],
    query: str,
    *,
    allow: _AllowList = NOTHING,
    use_decimal: bool = False,
) -> list[_Node]:
    """Run a JSON filter query on a node or a list of nodes.

    :param nodes: a node or a list of nodes
    :type nodes: _Node | list[_Node]
    :param query: a JSON filter query
    :type query: str
    :param allow: the allowed JSON deviations, defaults to
                  :data:`jsonyx.allow.NOTHING`
    :type allow: Container[str], optional
    :param use_decimal: use :class:`decimal.Decimal` instead of :class:`float`,
                        defaults to ``False``
    :type use_decimal: bool, optional
    :raises SyntaxError: if the filter query is invalid
    :return: the filtered list of nodes
    :rtype: list[_Node]

    >>> import jsonyx as json
    >>> node = [None], 0
    >>> assert json.run_filter_query(node, "@ == null")

    .. versionadded:: 2.0
    """
    return Manipulator(allow=allow, use_decimal=use_decimal).run_filter_query(
        nodes, query,
    )


def load_query_value(
    s: str,
    *,
    allow: _AllowList = NOTHING,
    use_decimal: bool = False,
) -> Any:
    """Deserialize a JSON query value to a Python object.

    :param s: a JSON query value
    :type s: str
    :param allow: the allowed JSON deviations, defaults to
                  :data:`jsonyx.allow.NOTHING`
    :type allow: Container[str], optional
    :param use_decimal: use :class:`decimal.Decimal` instead of :class:`float`,
                        defaults to ``False``
    :type use_decimal: bool, optional
    :raises JSONSyntaxError: if the query value is invalid
    :return: a Python object
    :rtype: Any

    >>> import jsonyx as json
    >>> json.load_query_value("'~'foo'")
    "'foo"

    .. versionadded:: 2.0
    """
    return Manipulator(allow=allow, use_decimal=use_decimal).load_query_value(
        s,
    )
