import conans
from pathlib import Path
import shutil
from typing import Set, Optional


def cmake_build(cf: conans.ConanFile, **kwargs):
    """
    Build the libman-aware project in the provided ConanFile with CMake. Build
    the ``libman-export`` target.

    :param conans.ConanFile cf: The ConanFile defining the project.
    :param kwargs: Keyword arguments forwarded to the ``conans.CMake`` constructor.
    """
    cmake = conans.CMake(cf, kwargs)
    cmake.build_folder = 'cmake-build'
    cmake.configure()
    cmake.build(target='libman-export')


def cmake_package_exports(cf: conans.ConanFile, exported: Optional[Set[Path]] = None) -> Set[Path]:
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
    if not len(lm_exports):
        raise RuntimeError('Package did not create any .libman-export directories. Did you call export_package()?')

    exported_names = set(exp.name for exp in exported)
    for export in lm_exports:
        if export in exported:
            # This directory was already exported once. Don't export it again
            continue
        # Check that another export with the same name hasn't already been copied
        if export.name in exported_names:
            raise RuntimeError(f'More than one export directory with name "{export.stem}"!')
        # Calc the destination for the export and do the copy
        dest = Path(cf.package_folder) / export.name
        cf.output.info(f'Packaging libman export "{export.stem}" ({export})')
        shutil.copytree(export, dest)
        # Record what has been exported
        exported.add(export)
        exported_names.add(export.name)

    # Return the new set of exported directories
    return exported


class CMakeConanFile(conans.ConanFile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__exported: Set[Path] = set()

    def build(self):
        cmake_build(self)

    def package(self):
        self.__exported = cmake_package_exports(self, self.__exported)

    def package_info(self):
        self.user_info.libman_simple = True
