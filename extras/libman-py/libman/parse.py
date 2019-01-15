"""
Module for parsing libman files
"""

from os import PathLike
from pathlib import Path
from contextlib import contextmanager
from typing import IO, Iterable, Optional, Union, cast, ContextManager, Generator

from . import data


def parse_line(line: str) -> Optional[data.Field]:
    """
    Parse a single line from a libman document
    """
    if isinstance(line, bytes):
        line = line.decode()
    line = line.strip()
    if line.startswith('#'):
        # Comment, so ignore
        return None
    if line == '':
        # Empty line
        return None
    col_pos = line.find(': ')
    if col_pos == -1:
        col_pos = line.find(':')
        if col_pos == -1 or col_pos != len(line) - 1:
            raise ValueError(f'Invalid libman line: "{line}"')
    key, value = line[:col_pos], line[col_pos + 1:]
    key, value = key.strip(), value.strip()
    return data.Field(key, value)


def iter_fields_from_lines(lines: Iterable[str]) -> Iterable[data.Field]:
    """
    Lazily iterate over the fields present in the given string lines of a
    libman-format file.
    """
    for line in lines:
        field = parse_line(line)
        if field:
            yield field


def iter_string_fields(doc: str) -> Iterable[data.Field]:
    """
    Lazily parse fields from the given document string
    """
    return iter_fields_from_lines(doc.splitlines())


def parse_string(doc: str) -> data.FieldSequence:
    """
    Parse all of the fields in the given string and return a FieldSequence
    """
    return data.FieldSequence(iter_string_fields(doc))


#: Type for things which can be "opened" or treated like files
LibmanFile = Union[str, PathLike, IO]


@contextmanager
def _fake_file_ctx_man(item: IO) -> Generator[IO, None, None]:
    yield item


def open_as_file(what: LibmanFile) -> ContextManager[IO]:
    """
    Given a "file-like," return an IO object for reading.

    If given a path or string, opens the file.

    If given a file object, returns the file.

    This should be used in a context-manager fashion. The file will only be
    closed if we opened it within this function.
    """
    if hasattr(what, '__fspath__') or isinstance(what, str):
        return Path(cast(PathLike, what)).open('rb')
    # If not a string or path, we expect a file-like object
    assert hasattr(what, 'readlines'), \
        f'Expected a file-like object or file path, got: {repr(what)}'
    # We wrap the file so that people that use this as a context manager do
    # not close the file that we didn't open ourselves
    return _fake_file_ctx_man(cast(IO, what))


def iter_file_fields(doc: LibmanFile) -> Iterable[data.Field]:
    """
    Lazily parse the fields from the given file or filepath
    """
    with open_as_file(doc) as fd:
        return iter_fields_from_lines(fd.readlines())


def parse_file(doc: LibmanFile) -> data.FieldSequence:
    """
    Parse the given file into a FieldSequence
    """
    return data.FieldSequence(iter_file_fields(doc))


def parse_index_string(doc: str, filepath: Path) -> data.Index:
    """
    Parse an index from the given string
    """
    return data.Index.from_fields(parse_string(doc), filepath)


def parse_index_file(fpath: Path) -> data.Index:
    """
    Parse an index from a file
    """
    return data.Index.from_fields(parse_file(fpath), fpath)


def parse_package_string(doc: str, filepath: Path) -> data.Package:
    """
    Parse a package from the given string
    """
    return data.Package.from_fields(parse_string(doc), filepath)


def parse_package_file(fpath: Path) -> data.Package:
    """
    Parse a package from the given file
    """
    return data.Package.from_fields(parse_file(fpath), fpath)


def parse_library_string(doc: str, filepath: Path) -> data.Library:
    """
    Parse a library from the given string
    """
    return data.Library.from_fields(parse_string(doc), filepath)


def parse_library_file(fpath: Path) -> data.Library:
    """
    Parse a library from the given file
    """
    return data.Library.from_fields(parse_file(fpath), fpath)
