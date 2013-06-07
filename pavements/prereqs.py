import os
from paver.easy import task, needs, consume_args, no_help

from pavements.config import config
from pavements.helpers import *
import distutils.sysconfig as dusc

PREREQ_INSTALL = not os.environ.get('NO_PREREQ_INSTALL')


@task
@needs('pavements.prereqs.install_node_prereqs',
       'pavements.prereqs.install_ruby_prereqs',
       'pavements.prereqs.install_python_prereqs')
def install_prereqs():
    """Install preprequisiites needed for the lms and cms"""
    pass


@task
@needs('pavements.ws.migrate')
def install_node_prereqs():
    """Install all ruby prerequisites for the lms and cms"""
    unchanged = 'Node requirements unchanged, nothing to install'
    if changed(['package.json']) and PREREQ_INSTALL:
        os.system('npm install')
    elif PREREQ_INSTALL:
        print unchanged


@task
@needs('pavements.ws.migrate')
def install_ruby_prereqs():
    """Install all python prerequisites for the lms and cms"""
    unchanged = 'Ruby requirements unchanged, nothing to install'
    if changed(['Gemfile']) and PREREQ_INSTALL:
        os.system('bundle install')
    elif PREREQ_INSTALL:
        print unchanged


@task
@needs('pavements.ws.migrate')
def install_python_prereqs():
    """Install all python prerequisites for the lms and cms"""
    site_packages_dir = dusc.get_python_lib()
    unchanged = 'Python requirements unchanged, nothing to install'
    if (changed(['requirements/**/*'], [site_packages_dir]) and
            PREREQ_INSTALL):
        os.environ['PIP_DOWNLOAD_CACHE'] = os.environ.get('PIP_DOWNLOAD_CACHE') or '.pip_download_cache'
        os.system('pip install --exists-action w -r requirements/edx/pre.txt')
        os.system('pip install --exists-action w -r requirements/edx/base.txt')
        os.system('pip install --exists-action w -r requirements/edx/post.txt')
        # requirements/private.txt is used to install our libs as
        # working dirs, or for personal-use tools.
        if os.path.isfile("requirements/private.txt"):
            os.system('pip install -r requirements/private.txt')
    elif PREREQ_INSTALL:
        print unchanged
