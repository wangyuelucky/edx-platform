# --- Develop and public documentation ---
import os
from paver.easy import task, needs, consume_args, cmdopts, no_help, pushd
from subprocess import call

from pavements.config import config
from pavements.helpers import *

import webbrowser


@task
@cmdopts([
    ("public", "p", "build public docs"),
])
def builddocs(options):
    """ Invoke sphinx 'make build' to generate docs. """
    if 'public' in options.builddocs:
        path = "doc/public"
    else:
        path = "docs"

    with pushd(os.path.join(config['REPO_ROOT'], path)):
        call(['make', 'html'])


@task
@cmdopts([
    ("public", "p", "show public docs"),
])
def showdocs(options):
    """
    Show docs in browser.
    """
    if 'public' in options.showdocs:
        path = "doc/public"
    else:
        path = "docs"

    url = "file://" + os.path.join(config["REPO_ROOT"], path, "build/html/index.html")
    webbrowser.open(url)


@task
@needs(['builddocs', 'showdocs'])
@cmdopts([
    ("public", "p", "operate on public docs"),
], share_with=['buildocs', 'showdocs'])
def doc(options):
    """Build docs and show them in browser"""
