# WSGI interface file for Apache's mod_wsgi
import sys
import os
os.chdir('/knowledge/internet-in-a-box')
sys.path.append('/knowledge/internet-in-a-box')
from iiab.webapp import IiabWebApp
from iiab.config import load_config
    
load_config('config.ini', [])

application = IiabWebApp().app
