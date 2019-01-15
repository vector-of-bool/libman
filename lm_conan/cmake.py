import conans
from pathlib import Path
import shutil
from typing import Set, Optional

from .export import package_exports, ExportCopier


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


class CMakeConanFile(ExportCopier, conans.ConanFile):
    def build(self):
        cmake_build(self)
