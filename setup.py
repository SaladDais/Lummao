#!/usr/bin/env python

from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='lummao',
    version='0.0.4',
    license='GPLv3',
    description='Toolkit for compiling and executing the Linden Scripting Language as Python',
    long_description=readme(),
    long_description_content_type="text/markdown",
    url='https://github.com/SaladDais/Lummao',
    author='Salad Dais',
    author_email='SaladDais@users.noreply.github.com',
    packages=['lummao'],
    data_files=[],
    install_requires=[],
    python_requires='>=3.8',
    zip_safe=False,
    tests_require=[
        "pytest",
        "pytest-cov"
    ],
    test_suite="tests"
)
