import conans
from pathlib import Path
from itertools import chain
from typing import Dict, List, Optional

from conans.model import Generator


LIBMAN_CMAKE_EXT = r'''
set(LIBMAN_INDEX
    "${CMAKE_CURRENT_LIST_DIR}/conan.lmi"
    CACHE INTERNAL
    "Path to Conan-generated LibMan index"
    )
'''


def _libman_check():
    if libman is None:
        raise RuntimeError(
            '`libman-conan` requires the `libman` Python library to be installed'
        )


class LibManLibrary:
    def __init__(
            self,
            name: str,
            paths: List[Path],
            includes: List[Path],
            defines: List[str],
            uses: List[str],
            special_uses: List[str],
            infos: List[str],
            warnings: List[str],
    ):
        self.name = name
        self.paths = paths
        self.include_paths = includes
        self.defines = defines
        self.uses = uses
        self.special_uses = special_uses
        self.infos = infos
        self.warnings = warnings

    @classmethod
    def find_linkable(cls, lib: str, lib_paths: List[str]) -> Optional[Path]:
        for lib_path in lib_paths:
            lib_path = Path(lib_path)
            candidates = chain(
                lib_path.glob(f'lib{lib}.a'),
                lib_path.glob(f'lib{lib}.lib'),
                lib_path.glob(f'lib{lib}.so'),
                lib_path.glob(f'{lib}.dll'),
            )
            try:
                return next(iter(candidates))
            except StopIteration:
                pass
        # No linkable found
        return None

    @classmethod
    def generate_default(
            cls, name: str,
            cpp_info: conans.model.build_info.CppInfo) -> 'LibManLibrary':
        include_paths = [Path(p) for p in cpp_info.include_paths]
        defines = list(cpp_info.defines)
        paths: List[Path] = []
        specials: List[str] = []
        infos: List[str] = []
        warnings: List[str] = []
        uses = []  # We don't fill this out for default-generated libs
        for lib in cpp_info.libs:
            # Generate a path item for each library
            special_by_lib = {
                'pthread': 'Threading',
                'dl': 'DynamicLinking',
                'm': 'Math',
            }
            special = special_by_lib.get(lib)
            if special:
                infos.append(
                    f'Link to `{lib}` being interpreted as special requirement "{special}"'
                )
                specials.append(special)
            else:
                found = cls.find_linkable(lib, cpp_info.lib_paths)
                if found:
                    warnings.append(
                        f'Library has no libman metadata and was generated automatically: {found}'
                    )
                    paths.append(found)
                else:
                    warings.append(f'Unresolved library {name}')
        return LibManLibrary(
            name,
            paths,
            include_paths,
            defines,
            uses,
            specials,
            infos,
            warnings,
        )


class LibManPackage:
    def __init__(self, name: str, ns: str, requires: List[str],
                 libs: List[LibManLibrary], has_libman_data: bool) -> None:
        self.name = name
        self.namespace = ns
        self.requires = requires
        self.libs = libs
        self.has_libman_data = has_libman_data

    @staticmethod
    def create(name: str, cpp_info: conans.model.build_info.CppInfo,
               user_info: conans.model.user_info.UserInfo) -> 'LibManPackage':
        reqs = list(cpp_info.public_deps)
        ns = name
        lm_info = user_info.vars.get('libman')
        has_libman = lm_info is not None
        if has_libman:
            ns = lm_info.namespace
            libs = LibMan
        else:
            libs = [LibManLibrary.generate_default(name, cpp_info)]
        return LibManPackage(name, ns, reqs, libs, has_libman)

    def _generate_library_file(self, all_pkgs: Dict[str, 'LibManPackage'],
                               lib: LibManLibrary) -> Dict[str, str]:
        lines = [
            '# libman library file generate by Conan. DO NOT EDIT.',
            'Type: Library',
            f'Name: {lib.name}',
        ]
        for inc in lib.include_paths:
            lines.append(f'Include-Path: {inc}')
        for def_ in lib.defines:
            lines.append(f'Preprocessor-Define: {def_}')
        for path in lib.paths:
            lines.append(f'Path: {path}')
        for special in lib.special_uses:
            lines.append(f'Special-Uses: {special}')
        for uses in lib.uses:
            lines.append(f'Uses: {uses}')

        if not self.has_libman_data:
            # The package did not expose libman data, so we must generate some
            # important information ourselves manually
            for req in self.requires:
                other_pkg = all_pkgs[req]
                if not other_pkg.has_libman_data:
                    lines.append(f'Uses: {other_pkg.name}/{other_pkg.name}')
                else:
                    for other_lib in other_pkg.libs:
                        lines.append(
                            f'Uses: {other_pkg.namespace}/{other_lib.name}')

        lml_path = f'{self.name}-libs/{lib.name}.lml'
        return {f'lm/{lml_path}': '\n'.join(lines)}, lml_path

    def generate_files(self,
                       pkgs: Dict[str, 'LibManPackage']) -> Dict[str, str]:
        lines = [
            '# Libman package file generated by Conan. DO NOT EDIT',
            'Type: Package',
            f'Name: {self.name}',
            f'Namespace: {self.namespace}',
        ]
        for req in self.requires:
            lines.append(f'Requires: {req}')

        lmp_path = f'lm/{self.name}.lmp'
        ret = {}
        for lib in self.libs:
            more, lml_path = self._generate_library_file(pkgs, lib)
            ret.update(more)
            lines.append(f'Library: {lml_path}')
        ret[lmp_path] = '\n'.join(lines)
        return ret, lmp_path


class LibMan(Generator):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.output = self.conanfile.output

    @property
    def filename(self):
        pass

    def _generate_from_deps_info(
            self, build_infos: conans.model.build_info.DepsCppInfo,
            user_infos: conans.model.user_info.DepsUserInfo) -> Dict[str, str]:
        ret = {}
        index_lines = [
            'Type: Index',
        ]
        all_pkgs: Dict[str, LibManPackage] = {}
        for name, cpp_info in build_infos.dependencies:
            user_info = user_infos[name]
            all_pkgs[name] = LibManPackage.create(name, cpp_info, user_info)

        ret = {}
        for name, pkg in all_pkgs.items():
            more, lmp_path = pkg.generate_files(all_pkgs)
            ret.update(more)
            index_lines.append(f'Package: {name}; {lmp_path}')
            for lib in pkg.libs:
                for info in lib.infos:
                    self.output.info(f'{pkg.name}/{lib.name}: {info}')
                for warning in lib.warnings:
                    self.output.warn(f'{pkg.name}/{lib.name}: {warning}')

        ret['conan.lmi'] = '\n'.join(index_lines)
        lm_pkg_dir = self.deps_build_info['libman-generator'].rootpath
        libman_cmake = (Path(lm_pkg_dir) / 'libman.cmake').read_text()
        libman_cmake += LIBMAN_CMAKE_EXT
        ret['conan-libman.cmake'] = libman_cmake
        return ret

    @property
    def content(self):
        files = self._generate_from_deps_info(self.deps_build_info,
                                              self.deps_user_info)
        return files


class ConanFile(conans.ConanFile):
    name = 'libman-generator'
    version = '0.1.0'
    generators = 'txt'  # , 'LibMan'
    exports_sources = '*', '../../cmake/libman.cmake'

    def package(self):
        super().package()
        self.copy('libman.cmake')
