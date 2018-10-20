"""
Data types for dealing with libman files
"""

from typing import Iterable, Dict, Optional, List, Tuple, Set, Mapping, cast, Iterator, Type
from pathlib import Path

import dataclasses as dc


class InvalidDataError(RuntimeError):
    """Base class for libman data validation errors"""


class InvalidIndexError(InvalidDataError):
    """Exception for data validation failures with a libman index"""


class InvalidPackageError(InvalidDataError):
    """Exception for data validation failures in a libman package file"""


class InvalidLibraryError(InvalidDataError):
    """Exception for data validation failures in a libman library file"""


class Field:
    """
    Represents a field in a libman file
    """

    def __init__(self, key: str, value: str) -> None:
        self._key = key
        self._value = value

    @property
    def key(self) -> str:
        """The key for the field"""
        return self._key

    @property
    def value(self) -> str:
        """The value string of of the field"""
        return self._value

    def __hash__(self):
        return hash((self.key, self.value))

    def __repr__(self):
        return f'<libman.data.Field key="{self.key}" value = "{self.value}">'


class FieldSequence:
    """
    Represents an ordered sequence of fields
    """

    def __init__(self, fields: Iterable[Field]):
        self._fields = list(fields)
        self._by_key: Dict[str, List[Field]] = {}
        for field in self._fields:
            seq = self._by_key[field.key] = self._by_key.get(field.key, [])
            seq.append(field)

    @property
    def fields(self) -> Iterable[Field]:
        """The fields in the sequence"""
        return (f for f in self._fields)

    def __iter__(self) -> Iterator[Field]:
        for field in self._fields:
            yield field

    def for_key(self, key: str) -> Iterable[Field]:
        """Iterable of all fields in the sequence with the given key"""
        found = self._by_key.get(key)
        if not found:
            return ()
        return found

    def get_at_most_one(
            self,
            key: str,
            exc: Type[RuntimeError] = RuntimeError,
    ) -> Optional[Field]:
        """
        Get the value of the given field, if present.

        If the field is absent, returns ``None``.

        If more than one instance of the field occurs, raises ``exc``
        """
        found = self._by_key.get(key)
        if not found:
            return None
        if len(found) != 1:
            raise exc(f'Field "{key}" provided more than once')
        return found[0]

    def get_exactly_one(
            self,
            key: str,
            exc: Type[RuntimeError] = RuntimeError,
    ) -> Field:
        """
        Get _exactly_ the value of the given field.

        If the field is not present or appears multiple times, raises ``exc``
        """
        found = self.get_at_most_one(key, exc)
        if not found:
            raise exc(f'Missing field "{key}"')
        return found


class IndexEntry:
    """
    An entry in the libman index
    """

    def __init__(self, name: str, path: Path) -> None:
        self._name = name
        self._path = path

    @property
    def name(self):
        """The name of the package for this index entry"""
        return self._name

    @property
    def path(self):
        """The path to the file for this package"""
        return self._path

    def __hash__(self):
        return hash((self.name, self.path))

    def __repr__(self):
        return f'<libman.data.IndexEntry name="{self.name}"  path="{self.name}"'


@dc.dataclass(frozen=True)
class Index:
    """
    A libman index
    """

    entries: Mapping[str, IndexEntry]
    fields: FieldSequence

    def __iter__(self):
        for entry in self.entries.values():
            yield entry

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, key: str) -> IndexEntry:
        return self.entries[key]

    def get(self, key: str) -> Optional[IndexEntry]:
        "Get the index entry for the given package name"
        return self.entries.get(key)

    def __contains__(self, key: str) -> bool:
        return key in self.entries

    @classmethod
    def from_fields(cls, fields: FieldSequence, filepath: Path) -> 'Index':
        """
        Convert a sequence of fields into an Index
        """
        # Singular values
        type_ = fields.get_exactly_one('Type', InvalidIndexError).value
        if type_ != 'Index':
            raise InvalidIndexError(f'Invlaid "Type" for index file: {type_}')
        # Parse the index entries
        entries: List[IndexEntry] = []
        already: Set[str] = set()
        for field in fields:
            if field.key == 'Package':
                if not ';' in field.value:
                    raise InvalidIndexError(
                        f'Invalid "Package" field in index file: {repr(field)}'
                    )
                pkg_name, pkg_path_str = field.value.split(';', 1)
                pkg_name, pkg_path = pkg_name.strip(), \
                    filepath.parent / Path(pkg_path_str.strip())
                if pkg_name in already:
                    raise InvalidIndexError(
                        'Cannot provided package name "{}" multiple times'.
                        format(pkg_name))
                already.add(pkg_name)
                entries.append(IndexEntry(pkg_name, pkg_path))

        return cls({e.name: e for e in entries}, fields)


@dc.dataclass(frozen=True)
class Package:
    """
    A libman package
    """
    name: str
    namespace: str
    requires: Iterable[str]
    libraries: Iterable[Path]
    fields: FieldSequence

    @classmethod
    def from_fields(cls, fields: FieldSequence, filepath: Path) -> 'Package':
        """
        Convert the given fields into a ``Package`` definition
        """
        # Check that we are a package type
        type_ = fields.get_exactly_one('Type', InvalidPackageError).value
        if type_ != 'Package':
            raise InvalidPackageError(
                f'Package file declares incorrect Type "{type_}"')
        namespace = fields.get_exactly_one('Namespace',
                                           InvalidPackageError).value
        name = fields.get_exactly_one('Name', InvalidPackageError).value
        libraries: List[Path] = [
            filepath.parent / f.value for f in fields.for_key('Library')
        ]
        requires: List[str] = [f.value for f in fields.for_key('Requires')]
        return cls(
            name,
            namespace,
            list(requires),
            list(libraries),
            fields,
        )


@dc.dataclass(frozen=True)
class Library:
    """
    A libman library
    """
    name: str
    path: Optional[Path]
    includes: Iterable[Path]
    defines: Iterable[str]
    uses: Iterable[Tuple[str, str]]
    links: Iterable[Tuple[str, str]]
    fields: FieldSequence

    @classmethod
    def from_fields(cls, fields: FieldSequence, filepath: Path) -> 'Library':
        """
        Create a ``Library`` instance from a list of fields, assuming it was
        defined by the given file at ``filepath``.

        :param fields: The fields to create the library definition from
        :param filepath: The path where the original fields were read (used
            to resolve relative paths)
        """
        type_ = fields.get_exactly_one('Type', InvalidLibraryError).value
        if type_ != 'Library':
            raise InvalidLibraryError(
                f'Library file declares incorrect Type "{type_}"')
        name = fields.get_exactly_one('Name', InvalidLibraryError).value
        path_ = fields.get_at_most_one('Path', InvalidLibraryError)
        path: Optional[Path]
        if path_:
            path = filepath.parent / path_.value
        else:
            path = None
        includes = [
            filepath.parent / f.value for f in fields.for_key('Include')
        ]
        defines = [f.value for f in fields.for_key('Define')]

        def split_req(req: str) -> Tuple[str, str]:
            seq = req.split('/')
            if not len(seq) == 2:
                raise InvalidLibraryError(
                    'Invalid usage name "{}" (espect "<Namespace>/<Library>")'.
                    format(req))
            return cast(Tuple[str, str], tuple(seq))

        uses = [split_req(f.value) for f in fields.for_key('Uses')]
        links = [split_req(f.value) for f in fields.for_key('Links')]
        return cls(name, path, includes, defines, uses, links, fields)
