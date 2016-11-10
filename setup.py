# coding: utf-8
from setuptools import setup, Extension, find_packages

__PACKAGE__ = 'kenshin_api'

setup(
    name=__PACKAGE__,
    version='0.1.0',
    url='https://github.com/douban/graphite-kenshin.git',
    author="zzl0",
    description=('A plugin for using graphite-api with kenshin-based '
                 'storage backend'),
    packages=find_packages(),
    zip_safe=False,
    ext_modules=[
        Extension(
            name='%s.%s' % (__PACKAGE__, name),
            sources=['%s/%s.pyx' % (__PACKAGE__, name)],
            extra_compile_args=['-O3', '-funroll-loops', '-Wall'],
        ) for name in ['fnv1a']
    ],
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
    setup_requires=['Cython'],
    install_requires=(
        'libmc',
    ),
    tests_require=['pytest'],
)
