# WSGI interface file for Apache's mod_wsgi

# If you are using a virtualenv, set this path
path_to_virtualenv = None

import sys
import os

if path_to_virtualenv is not None:
    activate_this = os.path.join(path_to_virtualenv, 'bin/activate_this.py')
    execfile(activate_this, dict(__file__=activate_this))

# iiab directory
package_dir = os.path.dirname(__file__)
parent_dir = os.path.split(package_dir)[0]

sys.path.append(parent_dir)

from iiab.webapp import create_app
from iiab.config import load_config
   
wsgi_config = os.path.join(package_dir, 'wsgi.ini') 
load_config([wsgi_config])

application = create_app()
