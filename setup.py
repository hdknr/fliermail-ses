#! /usr/bin/env python

NAME = 'fliermail-ses'
PACKAGE = 'fliermailses'
DESCRIPTION = 'SES backend for fliermail'
PACKAGES = [PACKAGE, ]

SITE = 'github.com'
USER = "hdknr"
PROJECT = NAME
URL = 'https://{0}/{1}/{2}'.format(SITE, USER, PROJECT)
PACKAGE_DIR = ''


def install():
    from setuptools import setup
    setup(
        license='Simplfied BSD License',
        author='Hideki Nara of LaFoaglia,Inc.',
        author_email='gmail [at] hdknr.com',
        maintainer='LaFoglia,Inc.',
        maintainer_email='gmail [at] hdknr.com',
        platforms=['any'],
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Library',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Simplifed BSD License',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
        ],
        name=NAME,
        version=getattr(__import__(PACKAGE), 'get_version')(),
        url=URL,
        description=DESCRIPTION,
        download_url=URL,
        # package_dir={'': PACKAGE_DIR},
        packages=PACKAGES,
        include_package_data=True,
        zip_safe=False,
        long_description=read('README.md'),
        scripts=glob.glob('scripts/*.py'),
        install_requires=requires(),
    )

import sys
import os
import glob

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, PACKAGE_DIR))


def path(fname):
    return os.path.join(BASE_DIR, fname)


def read(fname):
    return open(path(fname)).read()


def lines(fname):
    return [line.strip()
            for line in open(path(fname)).readlines()]


def requires():
    return lines("requirements/pypi.txt")


if __name__ == '__main__':
    install()
