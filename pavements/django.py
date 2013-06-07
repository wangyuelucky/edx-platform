"""Django interactions"""
import os
import subprocess
from paver.easy import task, needs, pushd, consume_args

from pavements.config import config
from pavements.helpers import *


DEFAULT_OPTIONS = {
    'lms': '8000',
    'cms': '8001',
}


@task
@needs('pavements.prereqs.install_python_prereqs')
def predjango():
    """ Clean up the pyc files and install local requirements"""
    os.system("find . -type f -name *.pyc -delete")
    with pushd(config['REPO_ROOT']):
        subprocess.call('pip install -q --no-index -r requirements/edx/local.txt')


@task
def fastlms():
    """Fast running of the lms server"""
    os.system(django_admin('lms', 'dev', 'runserver'))


def runserver(system, env, options):
    """ Run a django server for the given arguments """
    os.system(django_admin(system, env, 'runserver', options))


@task
@needs('pavements.prereqs.install_prereqs', 'predjango')
def lms(environment='dev', options=DEFAULT_OPTIONS['lms']):
    """
    Start the #{system} locally with the specified environment (defaults to dev).
    Other useful environments are devplus (for dev testing with a real local database)
    """
    runserver('lms', environment, options)
