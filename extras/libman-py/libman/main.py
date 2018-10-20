"""
Defines the entrypoint for the ``libman`` command-line tool
"""
import argparse
import sys
from pathlib import Path
from typing import List

from . import parse


def _query_index(args: argparse.Namespace) -> int:
    index_path = Path(args.index).resolve()
    index = parse.parse_index_file(index_path)
    if args.query == 'has-package':
        return 0 if args.package in index else 1
    if args.query == 'package-path':
        item = index.get(args.package)
        if not item:
            print('No such package:', args.package, file=sys.stderr)
            return 2
        print(item.path)
        return 0

    raise RuntimeError('No query type?')


def _add_query_index_parser(parser: argparse.ArgumentParser):
    parser.set_defaults(main_fn=_query_index)
    parser.add_argument(
        '--query',
        '-Q',
        required=True,
        help='The query type',
        choices=['has-package', 'package-path'],
    )
    parser.add_argument(
        '--index',
        '-I',
        required=True,
        help='Path to the index file',
    )
    parser.add_argument(
        '--package',
        '-p',
        required=True,
        help='Path to the index file',
    )


def _query_package(args: argparse.Namespace) -> int:
    pkg_path = Path(args.package).resolve()
    pkg = parse.parse_package_file(pkg_path)
    if args.query == 'namespace':
        print(pkg.namespace)
        return 0
    if args.query == 'name':
        print(pkg.name)
        return 0
    if args.query == 'requires':
        for req in pkg.requires:
            print(req)
        return 0
    if args.query == 'libraries':
        for lib in pkg.libraries:
            print(lib)
        return 0
    if args.query == 'key':
        if args.key is None:
            raise RuntimeError('No --key argument was specified')
        for field in pkg.fields:
            if field.key == args.key:
                print(field.value)
        return 0
    assert False, 'Unhandled query type: ' + args.query
    return 109


def _add_query_package_parser(parser: argparse.ArgumentParser):
    parser.set_defaults(main_fn=_query_package)
    parser.add_argument(
        '--query',
        '-Q',
        required=True,
        help='The query type',
        choices=['namespace', 'name', 'requires', 'libraries', 'key'],
    )
    parser.add_argument(
        '--package',
        '-p',
        required=True,
        help='Path to a package file',
    )
    parser.add_argument(
        '--key',
        help='Query a different package key (Used with --query=key)',
    )


def _query_library(args: argparse.Namespace) -> int:
    # pylint: disable=too-many-return-statements,too-many-branches
    lib_path = Path(args.library).resolve()
    lib = parse.parse_library_file(lib_path)
    if args.query == 'name':
        print(lib.name)
        return 0
    if args.query == 'path':
        print(lib.path)
        return 0
    if args.query == 'includes':
        for inc in lib.includes:
            print(inc)
        return 0
    if args.query == 'defines':
        for define in lib.defines:
            print(define)
        return 0
    if args.query == 'uses':
        for use in lib.uses:
            print(f'{use[0]}/{use[1]}')
        return 0
    if args.query == 'links':
        for use in lib.links:
            print(f'{use[0]}/{use[1]}')
        return 0
    if args.query == 'key':
        if args.key is None:
            raise RuntimeError('No --key argument was specified')
        for field in lib.fields:
            if field.key == args.key:
                print(field.value)
        return 0

    assert False, f'Unknown query type: {args.query}'
    return 14


def _add_library_package_parser(parser: argparse.ArgumentParser):
    parser.set_defaults(main_fn=_query_library)
    parser.add_argument(
        '--query',
        '-Q',
        required=True,
        help='The query type',
        choices=[
            'name',
            'path',
            'includes',
            'defines',
            'uses',
            'links',
            'key',
        ],
    )
    parser.add_argument(
        '--library',
        '-l',
        required=True,
        help='Path to a library file',
    )
    parser.add_argument(
        '--key',
        help='Query a package key (Used with --query=key)',
    )


def _add_query_parser(parser: argparse.ArgumentParser):
    sub = parser.add_subparsers(title='Query Command')
    _add_query_index_parser(
        sub.add_parser(
            'index',
            aliases=['i', 'idx'],
            help='Query an Index file',
        ))
    _add_query_package_parser(
        sub.add_parser(
            'package',
            aliases=['p', 'pkg'],
            help='Query a Package file',
        ))
    _add_library_package_parser(
        sub.add_parser(
            'library',
            aliases=['l', 'lib'],
            help='Query a Library file',
        ))


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create a command-line argument parser for the libman tool
    """
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(title='Command')
    _add_query_parser(
        sub.add_parser(
            'query',
            aliases=['q'],
            help='Query libman files',
        ))
    return parser


def main(argv: List[str]) -> int:
    """
    The main function for the libman command-line tool
    """
    parser = create_argument_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, 'main_fn'):
        parser.print_help()
        return 1
    return args.main_fn(args)


def _start():
    sys.exit(main(sys.argv[1:]))
