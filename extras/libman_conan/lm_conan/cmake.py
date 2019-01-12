import conans


def cmake_build(cf: conans.ConanFile, **kwargs):
    cmake = conans.CMake(cf, kwargs)
    cmake.configure()
    cmake.build(target='libman-export')


def cmake_install(cf: conans.ConanFile, **kwargs):
    pass


class CMakeConanFile(conans.ConanFile):
    def build(self):
        cmake_build(self)

    def install(self):
        cmake_install(self)
