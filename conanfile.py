import conans

class ConanFile(conans.ConanFile):
    name = 'libman'
    version = '0.1.0'
    requires = (
        'catch2/2.3.0@bincrafters/stable',
        'spdlog/1.1.0@bincrafters/stable',
        'boost/1.68.0@conan/stable',
    )
    generators = 'cmake'
    exports_sources = '*'

    def build(self):
        for bt in ('Debug', 'Release'):
            cmake = conans.CMake(self, build_type=bt)
            cmake.configure()
            cmake.build()
