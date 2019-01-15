import sys
if sys.version_info < (3, 6, 0):
    raise ImportError('libman for Conan requires Python 3.6 or newer')

import conans

from lm_conan.generator import Generator

# Imports that are meant to be re-imported by clients
from lm_conan.cmake import CMakeConanFile, cmake_build
from lm_conan.export import package_exports, AlreadyPackaged, ExportCopier

# Supress "unused import" warnings
_ = (package_exports, AlreadyPackaged, ExportCopier, cmake_build)


# The actual class definition is on the base class `lm_conan.generator.Generator`
# This class just forces the generator to be exposed as `LibMan` to consumers
class LibMan(Generator):
    pass


class ConanFile(CMakeConanFile):
    name = 'libman'
    version = '0.2.0'
    build_requires = (
        'catch2/2.3.0@bincrafters/stable',
    )
    generators = 'cmake'
    exports = (
        'lm_conan/*',
    )
    exports_sources = (
        '*',
        '!build/*',
        '!.tox/*',
    )

    def build(self):
        cmake = conans.CMake(self)
        cmake.configure(args=[f'-C{self.source_folder}/cmake/ConanConfig.cmake'])
        cmake.build(target='libman-export')

    def package(self):
        self.copy('cmake/libman.cmake', keep_path=False)
        super().package()
