# pylint: disable=C

from pathlib import Path

import pytest

from . import parse as mod


def test_empty():
    fields = list(mod.iter_string_fields(''))
    assert fields == []


def test_simple_line():
    field = mod.parse_line('foo: bar')
    assert field
    assert field.key == 'foo'
    assert field.value == 'bar'


def test_extra_whitespace():
    field = mod.parse_line('   foo:        bar    ')
    assert field
    assert field.key == 'foo'
    assert field.value == 'bar'


def test_empty_value():
    field = mod.parse_line('foo:   ')
    assert field
    assert field.key == 'foo'
    assert field.value == ''


def test_empty_value_at_eof():
    field = mod.parse_line('foo:')
    assert field
    assert field.key == 'foo'
    assert field.value == ''


def test_empty_value_at_nl():
    (field, ) = list(mod.iter_string_fields('foo:\n\n'))
    assert field.key == 'foo'
    assert field.value == ''


def test_ignore_comments():
    (field, ) = list(mod.iter_string_fields('# Comment line\nfoo: bar'))
    assert field.key == 'foo'
    assert field.value == 'bar'


def test_bad_line():
    with pytest.raises(ValueError):
        mod.parse_line('food')


def test_key_with_colon():
    field = mod.parse_line('foo:bar: baz')
    assert field
    assert field.key == 'foo:bar'
    assert field.value == 'baz'


def test_no_trailing_comment():
    field = mod.parse_line('foo: # bar')
    assert field
    assert field.key == 'foo'
    assert field.value == '# bar'


def test_key_with_whitespace():
    field = mod.parse_line('Foo Bar: Baz')
    assert field
    assert field.key == 'Foo Bar'
    assert field.value == 'Baz'


def test_parse_index():
    content = r'''
    Type: Index
    Package: foo ;      /bar/baz
    Package: Meow  ;cat/relative/path
    '''
    idx = mod.parse_index_string(content, Path('/dummy/something.lmi'))
    assert len(idx) == 2
    # Check that we have the foo package correctly
    entry = idx['foo']
    assert entry.name == 'foo'
    assert entry.path == Path('/bar/baz')
    # Check our that our "Meow" package relative path resolved
    entry = idx['Meow']
    assert entry.name == 'Meow'
    assert entry.path == Path('/dummy/cat/relative/path')


def test_parse_index_duplicate():
    content = r'''
    Type: Index
    Package: foo; bar
    Package: foo; baz
    '''
    # We have a duplicate package, so we will fail
    with pytest.raises(RuntimeError):
        mod.parse_index_string(content, Path('/dummy/foo.lmi'))
