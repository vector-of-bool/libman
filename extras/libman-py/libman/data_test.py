# pylint: disable=C

from typing import Iterable, Tuple, Type, Optional, List
from pathlib import Path
from dataclasses import dataclass, field

import pytest

from . import data as mod

INDEX_PATH = Path('dummy/libman.lmi')
PKG_PATH = Path('dummy/libman.lmp')


def make_fieldseq(*pairs: Tuple[str, str]) -> mod.FieldSequence:
    """Helper for creating a field sequence"""
    return mod.FieldSequence(mod.Field(k, v) for k, v in pairs)


@dataclass(frozen=True)
class IndexTestCase:
    fields: Iterable[Tuple[str, str]]
    path: Path = Path('dummy/libman.lmi')
    expect_exception: Optional[Type[RuntimeError]] = None
    expect_packages: Iterable[Tuple[str, Path]] = field(
        default_factory=lambda: [])

    def create_index(self) -> mod.Index:
        return mod.Index.from_fields(make_fieldseq(*self.fields), self.path)


def test_index():
    cases: Iterable[IndexTestCase] = [
        IndexTestCase(
            # Missing 'Type'
            fields=[],
            expect_exception=mod.InvalidIndexError,
        ),
        IndexTestCase(fields=[('Type', 'Index')]),
        IndexTestCase(
            fields=[
                ('Type', 'Index'),
                ('Package', 'Meow'),  # <-- Missing path
            ],
            expect_exception=mod.InvalidIndexError,
        ),
        IndexTestCase(
            fields=[
                ('Type', 'Index'),
                ('Package', 'Meow; something/somewhere'),
                # Duplicate package name:
                ('Package', 'Meow; /absolute/path/somewhere'),
            ],
            expect_exception=mod.InvalidIndexError,
        ),
        IndexTestCase(
            fields=[
                ('Type', 'Index'),
                ('Package', 'Meow; something/somewhere'),
                ('Package', 'Meow2; /absolute/path/somewhere'),
            ],
            expect_packages=[
                ('Meow', Path('dummy/something/somewhere')),
                ('Meow2', Path('/absolute/path/somewhere')),
            ],
        ),
    ]
    for case in cases:
        if case.expect_exception:
            with pytest.raises(case.expect_exception):
                case.create_index()
        else:
            idx = case.create_index()
            assert len(idx) == len(case.expect_packages), \
                'Wrong number of packages parsed'
            for actual, expected in zip(idx, case.expect_packages):
                exp_name, exp_path = expected
                assert actual.name == exp_name, 'Package name parsed wrong'
                assert actual.path == exp_path, 'Package path parsed wrong'


@dataclass(frozen=True)
class PackageTestCase:
    fields: Iterable[Tuple[str, str]]
    path: Path = Path('/dummy/package.lmp')
    expect_exception: Optional[Type[RuntimeError]] = None
    expect_libraries: Iterable[Path] = field(default_factory=lambda: [])

    def create_package(self) -> mod.Package:
        return mod.Package.from_fields(make_fieldseq(*self.fields), self.path)


def test_packages():
    cases: List[PackageTestCase] = [
        PackageTestCase(
            # Empty. Missing "Type"
            fields=[],
            expect_exception=mod.InvalidPackageError,
        ),
        PackageTestCase(
            fields=[
                ('Type', 'Library'),  # <-- Wrong type
                ('Name', 'Meow'),
                ('Namespace', 'Boost'),
            ],
            expect_exception=mod.InvalidPackageError,
        ),
        PackageTestCase(
            fields=[
                ('Type', 'Package'),
                ('Name', 'Meow'),
                # Missing 'Namespace'
                ## ('Namespace', 'Cat'),
            ],
            expect_exception=mod.InvalidPackageError,
        ),
        PackageTestCase(
            fields=[
                ('Type', 'Package'),
                # Missing 'Name'
                ## ('Name', 'Meow'),
                ('Namespace', 'Cat'),
            ],
            expect_exception=mod.InvalidPackageError,
        ),
    ]
    for case in cases:
        if case.expect_exception:
            with pytest.raises(case.expect_exception):
                case.create_package()
        else:
            pkg = case.create_package()
            assert case.expect_libraries == pkg.libraries


@dataclass(frozen=True)
class LibraryTestCase:
    fields: Iterable[Tuple[str, str]]
    path: Path = Path('/dummy/library.lmi')
    expect_name: Optional[str] = None
    expect_path: Optional[Path] = None
    expect_exception: Optional[Type[RuntimeError]] = None
    expect_includes: Iterable[Path] = field(default_factory=lambda: [])
    expect_defines: Iterable[str] = field(default_factory=lambda: [])
    expect_uses: Iterable[Tuple[str, str]] = field(default_factory=lambda: [])
    expect_links: Iterable[Tuple[str, str]] = field(default_factory=lambda: [])

    def create_library(self) -> mod.Library:
        return mod.Library.from_fields(make_fieldseq(*self.fields), self.path)


def test_libraries():
    cases: Iterable[LibraryTestCase] = [
        LibraryTestCase(
            fields=[],
            expect_exception=mod.InvalidLibraryError,
        ),
        LibraryTestCase(
            # Invalid type
            fields=[('Type', 'Package')],
            expect_exception=mod.InvalidLibraryError,
        ),
        LibraryTestCase(
            # Missing 'Name'
            fields=[('Type', 'Library')],
            expect_exception=mod.InvalidLibraryError,
        ),
        LibraryTestCase(
            fields=[
                ('Type', 'Library'),
                ('Name', 'Foo2'),
            ],
            expect_name='Foo2',
        ),
        LibraryTestCase(
            fields=[
                ('Type', 'Library'),
                ('Name', 'Foo'),
                ('Include', 'some/path'),
                ('Include', 'some/other/path'),
                ('Uses', 'foo/bar'),
            ],
            expect_name='Foo',
            expect_includes=[
                Path('/dummy/some/path'),
                Path('/dummy/some/other/path'),
            ],
            expect_uses=[
                ('foo', 'bar'),
            ],
        ),
    ]
    for case in cases:
        if case.expect_exception:
            with pytest.raises(case.expect_exception):
                case.create_library()
        else:
            lib = case.create_library()
            assert lib.path == case.expect_path
            assert lib.includes == case.expect_includes
            assert lib.defines == case.expect_defines
            assert lib.uses == case.expect_uses
            assert lib.links == case.expect_links
