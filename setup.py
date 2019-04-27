# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Load the requirements from the text file.
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [x.strip() for x in f.readlines() if x.strip()]

__version__ = "1.0.0"

setup(
    name='bareasgi_static',
    version=__version__,
    description='SStatic file support for bareasgi',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/rob-blackbourn/bareasgi-static',
    author='Rob Blackbourn',
    author_email='rob.blackbourn@googlemail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries'
    ],
    license='Apache 2',
    keywords='ASGI framework bareasgi static files',
    package_dir={'': 'src'},
    packages=find_packages(where='src', exclude=['tests', 'examples']),
    setup_requires=['pytest-runner'],
    install_requires=requirements,
    tests_require=['pytest']
)
