# Simple global configuration system
# We just maintain a dictionary of settings
# Retrieve it with config()
import os


global_config = {}


def config():
    return global_config

class BaseConfig(object):
    ACCEPT_LANGUAGES = ['zh']
    BABEL_DEFAULT_LOCALE = 'en'

    DEBUG = False
    TESTING = False

    SECRET_KEY = os.urandom(24)

    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../gutenberg.db'

    GUTENBERG_INDEX_DIR = 'whoosh/gutenberg_index'
    #GUTENBERG_ROOT_DIR = '/knowledge/data/gutenberg/gutenberg/'
    GUTENBERG_ROOT_DIR = '/knowledge/data/gutenberg/gutenberg/'
    
    def __init__(self):
        # Seems like a very non-standard way to handle this...
        # Probably better to use object config with env overrides like std pattern.
        for k, v in config().items():
            setattr(self, k, v)

class DevelopmentConfig(BaseConfig):
    DEBUG = True

class ProductionConfig(BaseConfig):
    pass
