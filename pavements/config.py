import os

config = {}

config['REPO_ROOT'] = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
config['LOG_DIR']   = os.path.abspath(os.path.join(config['REPO_ROOT'], '..', 'log'))
config['DATA_DIR']  = os.path.abspath(os.path.join(config['REPO_ROOT'], '..', 'data'))
config['DB_DIR']    = os.path.abspath(os.path.join(config['REPO_ROOT'], '..', 'db'))
config['PREREQS_MD5_DIR'] = os.environ.get('PREREQ_CACHE_DIR', os.path.join(config['REPO_ROOT'], '.prereqs_cache'))
