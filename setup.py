from setuptools import setup

from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='unsee-dl',
    version='1.0.1',
    description='unsee.cc downloader',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/andsala/unsee-dl',
    author='andsala',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Utilities'
    ],
    keywords='unsee download',
    project_urls={
        'Source': 'https://github.com/andsala/unsee-dl',
        'Issues': 'https://github.com/andsala/unsee-dl/issues',
    },
    py_modules=["unsee_dl"],
    install_requires=['selenium>=3.11"'],
    python_requires='>=3',
    entry_points={
        'console_scripts': [
            'unsee-dl = unsee_dl:main',
        ],
    }
)
