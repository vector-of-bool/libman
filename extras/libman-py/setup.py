"""
Setup for libman, the library manifest format library.
"""

from setuptools import setup, find_packages

setup(
    name='libman',
    version='0.1.0',
    packages=find_packages(),
    requires=['dataclasses'],
)
