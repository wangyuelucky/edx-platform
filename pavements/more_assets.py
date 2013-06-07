""" Asset compilation and watch. """
import os
import subprocess
from paver.easy import task, needs, pushd, consume_args

from pavements.config import config
from pavements.helpers import *


@task
def watch_sass():
    """ Compile and watch sass files. """
    # sys_cmd = "sass --debug-info --load-path ./common/static/sass --require ./common/static/sass/bourbon/lib/bourbon.rb --watch */static"
    static_dirs = ["lms/static", "common/static", "cms/static"]
    sys_cmd = "sass --debug-info --load-path ./common/static/sass --require ./common/static/sass/bourbon/lib/bourbon.rb --watch %s" % ' '.join(static_dirs)
    print sys_cmd
    # os.system(sys_cmd)
    # subprocess.Popen(sys_cmd.split(' '), shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    subprocess.Popen(sys_cmd.split(' '))
    print 'moving on from sass call...'
