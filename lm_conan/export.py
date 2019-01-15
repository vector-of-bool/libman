"""
Module for handling .libman-export directories
"""

import conans
from pathlib import Path
import shutil

from typing import Optional, Set


class AlreadyPackaged(RuntimeError):
    pass


def package_exports(cf: conans.ConanFile, exported: Optional[Set[Path]] = None) -> Set[Path]:
    """
    Copy any libman export roots to the package directory for the Conan project.

    :param conans.ConanFile cf: The ConanFile that is being exported.
    :param Optional[Set[Path]] exported: A set of export roots that have
        already been exported

    :returns: The set of paths that have been exported, including those provided
        in the ``exported`` argument.

    .. note::
        If more than one export root directory has the same filename stem as
        another export root directory, the packaging will fail with an
        exception.
    """
    exported = set(exported or set())

    lm_exports = list(Path(cf.build_folder).glob('**/*.libman-export'))

    exported_names = set(exp.name for exp in exported)
    for export in lm_exports:
        if export in exported:
            # This directory was already exported once. Don't export it again
            continue
        # Check that another export with the same name hasn't already been copied
        cf.output.info(f'Packaging libman export "{export.stem}" ({export})')
        if export.name in exported_names:
            raise AlreadyPackaged(f'More than one export directory with name "{export.stem}"!')
        # Calc the destination for the export and do the copy
        dest = Path(cf.package_folder) / export.name
        shutil.copytree(export, dest)
        # Record what has been exported
        exported.add(export)
        exported_names.add(export.name)

    # Return the new set of exported directories
    return exported


class ExportCopier:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__already_exported = set()

    def package_exports(self):
        assert getattr(self, 'package_folder', None), 'No package_folder is defined'
        assert isinstance(self, conans.ConanFile), 'ExportCopier derived classes must also derive from ConanFile'
        self.__already_exported = package_exports(self, self.__already_exported)
        assert len(self.__already_exported) > 0, 'No directories have been exported'

    def package(self):
        self.package_exports()

    def package_info(self):
        self.user_info.libman_simple = True
