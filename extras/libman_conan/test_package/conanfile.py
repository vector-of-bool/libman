import conans


class ConanFile(conans.ConanFile):
    generators = 'LibMan'

    requires = (
        'spdlog/[*]@bincrafters/stable',
    )

    def build(self):
        cmake = conans.CMake(self)
        cmake.configure()
        cmake.build()
        cmake.build(target='libman-export')

    def test(self):
        pass