"""
Generate MSBuild properties files from the libman index data
"""

import os
import re
from pathlib import Path
from typing import Dict, Optional, List
from xml.dom import minidom
from xml.etree import ElementTree as ET

from conans import ConanFile
from conans.client.output import ConanOutput


def _add_library(prop_group: ET.Element, autodefs: ET.Element, ns: str, lmp_path: Path,
                 lml_path: Path, data: Dict[str, str], out: ConanOutput) -> None:
    if not lml_path.is_absolute():
        lml_path = lmp_path.parent / lml_path

    if lml_path.is_absolute():
        lml_content = lml_path.read_text()
    else:
        lml_content = data[str(lml_path.as_posix())]

    NAME_LEAD = 'Name: '
    PATH_LEAD = 'Path: '
    INCLUDE_LEAD = 'Include-Path: '
    name: str = ''
    lib_path: str = ''
    includes: List[str] = []
    for line_ in lml_content.splitlines():
        line: str = line_.strip()
        if line.startswith(NAME_LEAD):
            name = line[len(NAME_LEAD):].strip()
        elif line.startswith(PATH_LEAD):
            lib_path = line[len(PATH_LEAD):]
        elif line.startswith(INCLUDE_LEAD):
            includes.append(line[len(INCLUDE_LEAD):] + '\\')
        elif line.startswith('Type: '):
            assert 'Library' in line
        elif line == '':
            pass
        else:
            out.warn(f'Unhandled lml line: {line}')

    if not name:
        raise RuntimeError(f'Missing name in lml: {lml_path}')

    def _resolve(p: str) -> str:
        if os.path.isabs(p):
            return p
        else:
            return str(lml_path.parent / p)

    # TODO: Transitive dependencies!

    condition = f'$([System.Text.RegularExpressions.Regex]::IsMatch($(LibmanUses), ".*(;|^)\s*{ns}/{name}\s*(;|$).*"))'

    resolved_includes = (_resolve(inc) for inc in includes)
    inc_prop = f'libman--{ns}__{name}--Include-Path'
    ET.SubElement(prop_group, inc_prop).text = ';'.join(resolved_includes)
    aid = 'AdditionalIncludeDirectories'
    ET.SubElement(
        ET.SubElement(autodefs, 'ClCompile', {'Condition': condition}),
        aid,
    ).text = f'$({inc_prop});%({aid})'

    if lib_path:
        link_prop = f'libman--{ns}__{name}--Path'
        ET.SubElement(prop_group, link_prop).text = _resolve(lib_path)
        adeps = 'AdditionalDependencies'
        ET.SubElement(
            ET.SubElement(autodefs, 'Link', {'Condition': condition}),
            adeps,
        ).text = f'$({link_prop});%({adeps})'


def _add_pkg(prop_group: ET.Element, autodefs: ET.Element, name: str, path: str,
             data: Dict[str, str], out: ConanOutput) -> None:
    if os.path.isabs(path):
        lmp_content = Path(path).read_text()
    else:
        lmp_content = data[path]

    NS_RE = re.compile(r'Namespace:\s+(?P<namespace>.*)$')
    namespace: str = ''
    LIB_RE = re.compile(r'Library:\s+(?P<path>.*)$')
    for line_ in lmp_content.splitlines():
        line: str = line_.strip()
        mat = NS_RE.match(line)
        if mat:
            namespace = mat.group('namespace')
            continue
        mat = LIB_RE.match(line)
        if mat:
            _add_library(prop_group, autodefs, namespace, Path(path),
                         Path(mat.group('path')), data, out)


def generate_msbuild_props(data: Dict[str, str], cf: ConanFile) -> str:
    out = cf.output
    root = ET.Element('Project', {'InitialTargets': 'LibmanValidate'})
    root.set('xmlns', 'http://schemas.microsoft.com/developer/msbuild/2003')
    out.info('Generating LibMan import properties for MSbuild')

    check_target = ET.SubElement(root, 'Target', {
        'Name': 'LibmanValidate',
        'Condition': "'$(LibmanDisableValidate)' == ''",
    })
    bt = str(cf.settings.build_type)
    ET.SubElement(
        check_target, 'Error', {
            'Text':
            f'The current build configuration `$(Configuration)` does not match '
            f'the configuration installed by Conan (`{bt}`)',
            'Condition': f"'$(Configuration)' != '{bt}'",
        })
    vs_platform = {
        'x86': 'Win32',
        'x86_64': 'x64',
    }.get(str(cf.settings.arch))
    if vs_platform is not None:
        ET.SubElement(
            check_target, 'Error', {
                'Text': f'The current build platform `$(Platform)` does not match '
                f'the platform installed by Conan (`{vs_platform}`)',
                'Condition': f"'$(Platform)' != '{vs_platform}'",
            })

    prop_group = ET.SubElement(root, 'PropertyGroup')
    ET.SubElement(prop_group, 'LibmanUses', {
        'Condition': "'$(LibmanUses)' == ''",
    })

    autodefs = ET.SubElement(root, 'ItemDefinitionGroup', {
        'Condition': "'$(LibmanDisableAutoUsage)' == ''",
    })

    index_content: str = data['INDEX.lmi']
    PACKAGE_RE = re.compile(r'Package:\s+(?P<name>[^;]+)\s*;\s*(?P<path>.+)$')
    for line_ in index_content.splitlines():
        line: str = line_.strip()
        mat = PACKAGE_RE.match(line)
        if mat is None:
            continue

        pkg_name = mat.groupdict()['name']
        lmp_path = mat.groupdict()['path']
        _add_pkg(prop_group, autodefs, pkg_name, lmp_path, data, out)

    dom = minidom.parseString(ET.tostring(root, encoding='UTF-8'))
    pretty = dom.toprettyxml(indent='  ', encoding='UTF-8')
    return pretty.decode()
