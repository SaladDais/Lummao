#!/usr/bin/env python
import os.path
import sys

from setuptools import setup, find_packages
from setuptools.extension import Extension
from wheel.bdist_wheel import bdist_wheel


class BDistWheelABI3(bdist_wheel):
    def get_tag(self):
        python, abi, plat = super().get_tag()

        if python.startswith("cp"):
            # on CPython, our wheels are abi3 and compatible back to 3.6
            return "cp38", "abi3", plat

        return python, abi, plat


def readme():
    with open('README.md') as f:
        return f.read()


if os.path.exists("build/packages/include"):
    library_dirs = ["build/packages/lib/release"]
    include_dirs = ["build/packages/include"]
else:
    print("Autobuild packages not found, relying on system Tailslide", file=sys.stderr)
    library_dirs = None
    include_dirs = None


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
    setup_requires=['setuptools_scm'],
    tests_require=[
        "pytest",
        "pytest-cov"
    ],
    test_suite="tests",
    cmdclass={"bdist_wheel": BDistWheelABI3},
    ext_modules=[
        Extension(
            "lummao._compiler",
            sources=["src/python_pass.cc", "src/compiler.cc"],
            define_macros=[("Py_LIMITED_API", "0x03080000")],
            libraries=["tailslide"],
            library_dirs=library_dirs,
            include_dirs=include_dirs,
            py_limited_api=True,
        )
    ],
    entry_points={
        'console_scripts': {
            'lummao = lummao.cli:cli_main',
        }
    },
)
