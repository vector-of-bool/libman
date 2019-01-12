import sys
if sys.version_info[0] < 3:
    raise ImportError('libman for Conan requires Python 3 or newer')

import conans

from lm_conan.generator import Generator

# Imports that are meant to be re-imported by clients
from lm_conan.cmake import CMakeConanFile, cmake_build, cmake_install


# The actual class definitions are on the base class `lm_conan.generator.Generator`
# This class just forces the generator to be exposed as `LibMan` to consumers
class LibMan(Generator):
    pass


class ConanFile(conans.ConanFile):
    name = 'libman'
    version = '0.2.0'
    generators = 'txt'  # , 'LibMan'
    exports = 'lm_conan/*'
    exports_sources = '*', '../../cmake/libman.cmake'

    def package(self):
        super().package()
        self.copy('libman.cmake')
