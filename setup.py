# coding: utf-8
import sys
from setuptools import setup, find_packages

__PACKAGE__ = 'kenshin_api'

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []
install_requires = ['libmc']
tests_require = ['pytest', 'pytest-cov']

setup(
    name=__PACKAGE__,
    version='0.1.1',
    url='https://github.com/douban/graphite-kenshin.git',
    author="zzl0",
    description=('A plugin for using graphite-api with kenshin-based '
                 'storage backend'),
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    classifiers=(
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Topic :: System :: Monitoring',
    ),
    setup_requires=pytest_runner,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'tests': tests_require}
)
