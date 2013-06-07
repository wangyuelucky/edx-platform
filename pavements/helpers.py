import os
import glob2
import hashlib
import re
import subprocess

from .config import config


def is_empty(dictionary):
    if dictionary:
        return False
    return True


def django_admin(system, env, command, *args):
    """ wrapper around django-admin """
    django_admin_cmd = os.environ.get('DJANGO_ADMIN_PATH') or select_executable(['django-admin.py', 'django-admin'])
    return "{django_admin} {command} --traceback --settings={system}.envs.{env} --pythonpath=. {args}".format(
        django_admin=django_admin_cmd, command=command, system=system, env=env, args=" ".join(args))


def select_executable(cmds):
    """ Finds a corresponding path for the given commands"""
    for cmd in cmds:
        try:
            paths = subprocess.check_output(['which', cmd]).split('\n')
            return paths[0]
        except (subprocess.CalledProcessError, IndexError):
            pass

    raise RuntimeError("could for find command in " + str(cmds))


def hash_files_dirs(files, dirs=[]):
    """
    Hash files and directories together into a single hash.
    Hash files by contents and directories by children filenames.

    files and dirs are fully qualified paths.
    """
    m = hashlib.md5()

    for file_path in files:
        # handle both single files and expansions (like requirements/**/*)
        for single_file in glob2.glob(file_path):
            print "adding file to hash: %s" % single_file
            with open(single_file, 'r') as f:
                body = f.read()
                m.update(body)

    for dir_path in dirs:
        print "adding dir to hash: %s" % dir_path
        children_names = os.listdir(dir_path)
        children_names_string = ', '.join(children_names)
        print "found children_names_string: %s" % children_names_string
        m.update(children_names_string)

    return m.hexdigest()


def has_changed_files_dirs(callback, files, dirs=[]):
    """
    if files in files or dirs differs from the stored hash, then run callback(true) and return true.
    else run callback(false) and return false

    callback is callable with one argument specifying whether the files/dirs have changed
    callback should do all modifications to files/dirs so that the new hash can be computed after
    """

    # cache_file_name = files[0].gsub(/\W+/, '-').sub(/-+$/, '')) + '.md5'
    cache_file_name = files[0]
    print cache_file_name
    cache_file_name = re.sub(r'\W+', '-', cache_file_name)
    cache_file_name = re.sub(r'-+$', '', cache_file_name)
    cache_file_name += '.md5'
    print cache_file_name

    cache_file = os.path.join(config['PREREQS_MD5_DIR'], cache_file_name)

    now_hash = hash_files_dirs(files, dirs)
    print cache_file

    if os.path.isfile(cache_file):
        with open(cache_file, 'r') as f:
            last_hash = f.read()
    else:
        last_hash = None

    # if the file doesn't exist, or the hash has changed, write the new hash and return true
    if last_hash == now_hash:
        callback(False)
        return False
    else:
        callback(True)
        with open(cache_file, 'w') as f:
            f.write(hash_files_dirs(files, dirs))
        return True
