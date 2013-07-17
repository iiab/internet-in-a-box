# WSGI interface file for Apache's mod_wsgi

# If you are using a virtualenv, set this path
path_to_virtualenv = None

### NOTHING TO CONFIGURE BELOW THIS LINE ###

import sys
import os

if path_to_virtualenv is not None:
    activate_this = os.path.join(path_to_virtualenv, 'bin/activate_this.py')
    execfile(activate_this, dict(__file__=activate_this))

# Add iiab directory if we are running from the git sources
parent_dir = os.path.dirname(__file__)
sys.path.insert(1, parent_dir)

import iiab
from iiab.webapp import create_app
from iiab.config import load_config

package_dir = os.path.dirname(iiab.__file__)
   
config_files = [os.path.join(package_dir, 'wsgi.ini'),
                '/etc/iiab.conf',
                os.path.join(os.path.expanduser('~'), '.iiab.conf')]
load_config(config_files)

application = create_app()
