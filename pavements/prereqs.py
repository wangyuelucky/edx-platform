"""Prerequisite installation tasks"""
import os
from paver.easy import task, needs

from pavements.config import config
from pavements.helpers import has_changed_files_dirs
import distutils.sysconfig as dusc

PREREQ_INSTALL = not os.environ.get('NO_PREREQ_INSTALL')


@task
def directory_prereqs():
    """
    Create required directories if they do not exist.

    Required directories are
    ../log
    ../data
    ../db
    """

    prereq_dirs = [config['LOG_DIR'], config['DATA_DIR'], config['DB_DIR']]

    for dir_path in prereq_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)


@task
@needs('install_node_prereqs',
       'install_ruby_prereqs',
       'install_python_prereqs')
def install_prereqs():
    """Install preprequisiites needed for the lms and cms"""
    pass


@task
@needs('pavements.workspace.migrate')
def install_node_prereqs():
    """Install all node prerequisites for the lms and cms"""
    unchanged = 'Node requirements unchanged, nothing to install'

    def _changed_file(changed):
        """ If the files have changed, install node prereqs.
            Otherwise, print out a message indicating that nothing has changed"""
        if changed:
            os.system('npm install')
        else:
            print unchanged

    if PREREQ_INSTALL:
        has_changed_files_dirs(_changed_file, ['package.json'])


@task
@needs('pavements.workspace.migrate')
def install_ruby_prereqs():
    """Install all python prerequisites for the lms and cms"""
    unchanged = 'Ruby requirements unchanged, nothing to install'

    def _changed_file(changed):
        """ If the files have changed, install ruby prereqs.
            Otherwise, print out a message indicating that nothing has changed"""
        if changed:
            os.system('bundle install')
        else:
            print unchanged

    if PREREQ_INSTALL:
        has_changed_files_dirs(_changed_file, ['Gemfile'])


@task
@needs('pavements.workspace.migrate')
def install_python_prereqs():
    """Install all python prerequisites for the lms and cms"""
    site_packages_dir = dusc.get_python_lib()
    unchanged = 'Python requirements unchanged, nothing to install'

    def _changed_file(changed):
        """ If the files have changed, install ruby prereqs.
            Otherwise, print out a message indicating that nothing has changed"""
        if changed:
            os.environ['PIP_DOWNLOAD_CACHE'] = os.environ.get('PIP_DOWNLOAD_CACHE') or '.pip_download_cache'
            os.system('pip install --exists-action w -r requirements/edx/pre.txt')
            os.system('pip install --exists-action w -r requirements/edx/base.txt')
            os.system('pip install --exists-action w -r requirements/edx/post.txt')
            # requirements/private.txt is used to install our libs as
            # working dirs, or for personal-use tools.
            if os.path.isfile("requirements/private.txt"):
                os.system('pip install -r requirements/private.txt')
        else:
            print unchanged

    if PREREQ_INSTALL:
        has_changed_files_dirs(_changed_file, ['requirements/**/*.txt'], [site_packages_dir])
