import conans


libman = conans.python_requires('libman/0.2.0@vector-of-bool/test')


class ConanFile(libman.CMakeConanFile):
    generators = 'LibMan'
    libman_for = 'cmake'
    requires = (
        'spdlog/[*]@bincrafters/stable',
    )

    def test(self):
        pass
