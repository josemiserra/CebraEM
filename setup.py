import glob
import os
import re
import sys
import warnings

import pkg_resources
from setuptools import find_packages, setup, Distribution, Command

from distutils.util import convert_path
from setuptools.command.install import install

import versioneer

classifiers = [
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    CLEAN_FILES = './build ./dist ./*.pyc ./*.tgz ./*.egg-info'.split(' ')

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        here = os.getcwd()

        for path_spec in self.CLEAN_FILES:
            # Make paths absolute and relative to this path
            abs_paths = glob.glob(os.path.normpath(os.path.join(here, path_spec)))
            for path in [str(p) for p in abs_paths]:
                if not path.startswith(here):
                    # Die if path in CLEAN_FILES is absolute + outside this directory
                    raise ValueError("%s is not a path inside %s" % (path, here))
                print('removing %s' % os.path.relpath(path))
                shutil.rmtree(path)


def get_commands():
        cmd = {} # versioneer.get_cmds()
        cmd.update({'clean':CleanCommand})
        return cmd


version_cebraem = {}
ver_path = convert_path('cebraem/_version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), version_cebraem)



#with open('install_requirements.txt') as f:
#    reqs = f.read().strip().split('\n')
#

setup(
    version= version_cebraem['__version__'],
    cmdclass= get_commands(),
    author='jhennies',
    author_email='hennies@embl.de',
    scripts=[
        'bin/init_project.py',
        'bin/run.py',
        'bin/init_gt.py',
        'bin/link_gt.py',
        'bin/log_gt.py',
        'bin/init_segmentation.py'
        'bin/install_torch.py',
        'bin/convert_to_bdv.py',
        'bin/normalize_instances.py'
    ],
    zip_safe=False,
    long_description=open('README.md',encoding="utf8").read(),
    classifiers=classifiers,
    python_requires='>=3.9'
)
