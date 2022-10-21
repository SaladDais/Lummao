#!/usr/bin/env python
import subprocess

from setuptools import setup, find_packages
from setuptools.extension import Extension
from setuptools.command.build_ext import build_ext
from wheel.bdist_wheel import bdist_wheel


class BDistWheelABI3(bdist_wheel):
    def get_tag(self):
        python, abi, plat = super().get_tag()

        if python.startswith("cp"):
            # on CPython, our wheels are abi3 and compatible back to 3.8
            return "cp38", "abi3", plat

        return python, abi, plat


class AutobuildBuildExt(build_ext):
    """Build an extension that requires autobuild dependencies"""
    def build_extension(self, ext):
        autobuild_deps = getattr(ext, 'autobuild_deps', [])
        if autobuild_deps:
            subprocess.check_call(["autobuild", "install", "-A64", *autobuild_deps])
        build_ext.build_extension(self, ext)


class AutobuildExtension(Extension):
    def __init__(self, name, /, *, autobuild_deps=None, **kwargs):
        self.autobuild_deps = autobuild_deps or []
        super().__init__(name, **kwargs)


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='lummao',
    license='GPLv3',
    description='Toolkit for compiling and executing the Linden Scripting Language as Python',
    long_description=readme(),
    long_description_content_type="text/markdown",
    url='https://github.com/SaladDais/Lummao',
    author='Salad Dais',
    author_email='SaladDais@users.noreply.github.com',
    packages=find_packages(include=['lummao', 'lummao.*']),
    data_files=[],
    install_requires=[],
    python_requires='>=3.8',
    zip_safe=False,
    use_scm_version=True,
    setup_requires=['setuptools_scm', 'autobuild<4'],
    tests_require=[
        "pytest",
        "pytest-cov"
    ],
    test_suite="tests",
    cmdclass={"bdist_wheel": BDistWheelABI3, "build_ext": AutobuildBuildExt},
    ext_modules=[
        AutobuildExtension(
            "lummao._compiler",
            sources=["src/python_pass.cc", "src/compiler.cc"],
            define_macros=[("Py_LIMITED_API", "0x03080000")],
            libraries=["tailslide"],
            library_dirs=["build/packages/lib/release"],
            include_dirs=["build/packages/include"],
            extra_compile_args=["-std=c++17"],
            py_limited_api=True,
            autobuild_deps=["tailslide"],
        )
    ],
    entry_points={
        'console_scripts': {
            'lummao = lummao.cli:cli_main',
        }
    },
)
