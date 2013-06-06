# WSGI interface file for Apache's mod_wsgi
import sys
import os

# iiab directory
package_dir = os.path.dirname(__file__)
parent_dir = os.path.split(package_dir)[0]

os.chdir(parent_dir)  # FIXME: hack, may not always work
sys.path.append(parent_dir)

from iiab.webapp import IiabWebApp
from iiab.config import load_config
    
load_config('iiab/config.ini', ['iiab/wsgi.ini'])

application = IiabWebApp().app
