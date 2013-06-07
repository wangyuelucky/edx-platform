"""Django interactions"""
import os
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
        os.system("pip install -q --no-index -r requirements/edx/local.txt")


@task
def fastlms():
    """Fast running of the lms server"""
    os.system(django_admin('lms', 'dev', 'runserver'))


def runserver(system, env, options):
    """ Run a django server for the given arguments """
    os.system(django_admin(system, env, 'runserver', options))


def run_system(system, args):
    """ Parses out the arguments coming from the command line and passes them along"""
    if len(args) > 0:
        environment = args[0]
    else:
        environment = 'dev'

    if len(args) > 1:
        options = args[1:]
    else:
        options = DEFAULT_OPTIONS[system]

    runserver(system, environment, options)


@task
@needs('pavements.prereqs.install_prereqs', 'predjango')
@consume_args
def lms(args):
    """
    Start the lms locally with the specified environment (defaults to dev).
    Other useful environments are devplus (for dev testing with a real local database)
    """
    run_system('lms', args)


@task
@needs('pavements.prereqs.install_prereqs', 'predjango')
@consume_args
def cms(args):
    """
    Start the cms locally with the specified environment (defaults to dev).
    Other useful environments are devplus (for dev testing with a real local database)
    """
    run_system('cms', args)


@task
@consume_args
def dj_admin(args):
    """Run django-admin <action> against the specified system and environment"""
    system = "lms"
    env = "dev"
    options = ""
    action = ""
    if len(args) < 1:
        raise Exception("Not enough arguments")
    if len(args) > 0:
        action = args[0]
    if len(args) > 1:
        system = args[1]
    if len(args) > 2:
        env = args[2]
    if len(args) > 3:
        env = args[3:]

    os.system(django_admin(system, env, action, options))


