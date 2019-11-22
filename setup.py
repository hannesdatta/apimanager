from setuptools import setup

name = 'apimanager'
description = 'Manage API data retrieval for research via MongoDB'
version = '0.0.0'


def long_description():
    readme = open('README.md').read()
    changelog = open('CHANGELOG.md').read()

    # cut the part before the description to avoid repetition on PyPI
    readme = readme[readme.index(description) + len(description):]

    return '\n'.join((readme, changelog))


setup(
    name=name,
    version=version,
    description=description,
    long_description=long_description(),
    package_dir={'': 'src'},
    url='http://github.com/seantis/apimanager',
    author='Hannes Datta, Tilburg University',
    author_email='h.datta@tilburguniversity.edu',
    license='MIT',
    packages=['apimanager'],
    namespace_packages=name.split('.')[:-1],
    include_package_data=True,
    install_requires=[

    ],
    extras_require=dict(
        dev=[
            'scrambler',
        ],
        test=[
            'flake8',
            'pytest',
        ],
    ),
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
    ]
)
