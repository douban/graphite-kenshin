# coding: utf-8

from setuptools import setup


setup(
    name='kenshin_api',
    version='0.1.0',
    url='https://github.com/douban/graphite-kenshin.git',
    author="zzl0",
    description=('A plugin for using graphite-api with kenshin-based '
                 'storage backend'),
    py_modules=('kenshin_api', 'kenshin_functions'),
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
    install_requires=(
        'libmc',
    ),
    test_suite='tests',
)
