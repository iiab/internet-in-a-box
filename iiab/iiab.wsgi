# WSGI interface file for Apache's mod_wsgi
import sys
import os

# iiab directory
package_dir = os.path.dirname(__file__)
parent_dir = os.path.split(package_dir)[0]

os.chdir(parent_dir)  # FIXME: hack, may not always work
sys.path.append(parent_dir)

from iiab.webapp import create_app
from iiab.config import load_config
   
wsgi_config = os.path.join(package_dir, 'wsgi.ini') 
load_config(None, [wsgi_config])

application = create_app()
