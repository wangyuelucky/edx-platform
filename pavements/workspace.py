"""Workspace migration"""
from paver.easy import task
from paver.path import path
from pavements.config import config
import os


MIGRATION_MARKER_DIR = os.path.join(config['REPO_ROOT'], '.ws_migrations_complete')
SKIP_MIGRATIONS = os.environ.get('SKIP_WS_MIGRATIONS') or False


@task
def migrate():
    """ Run migration scripts on the workspace"""
    if SKIP_MIGRATIONS:
        return
    print "running migrations"
    ws_dir = path('ws_migrations')
    # create the migration completion dir if it doesn't already exist
    if not os.path.exists(MIGRATION_MARKER_DIR):
        os.makedirs(MIGRATION_MARKER_DIR)

    def is_executable(file_path):
        ''' returns whether or not the given file is executable'''
        return file_path.access(os.X_OK)

    files = filter(is_executable, ws_dir.files())
    for file_path in files:
        completion_file = os.path.join(MIGRATION_MARKER_DIR, file_path.name)
        print "run migration for file %s" % completion_file
        if not os.path.exists(completion_file):
            os.system(file_path)
            with open(completion_file, 'w') as f_handler:
                f_handler.write('')
