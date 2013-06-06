# Simple global configuration system
# Retrieve it with config()
import os

from ConfigParser import SafeConfigParser
from json import dumps, loads


global_config = None


class IiabConfig(SafeConfigParser):
    """Just some conveniences for IIAB configuration"""

    def all_items(self):
        """Return a dictionary of sections with a dictionary of name/value pairs"""
        j = {}
        for section in self.sections():
            js = {}
            for name, value in self.items(section):
                js[name] = self.get(section, name)
            j[section] = js
        return j

    def all_items_to_str(self):
        return dumps(self.all_items(), indent=4)

    def __str__(self):
        return self.all_items_to_str()

    def getjson(self, section, name):
        """Load a configuration value string and interpret
           it as a JSON structure"""
        return loads(self.get(section, name))


def load_config(config_files=[]):
    """First load iiab/defaults.ini, which is required.
    Then load optional files in the config_files array
    if they exist."""
    global global_config
    package_dir = os.path.dirname(__file__)
    master_config_file = os.path.join(package_dir, 'defaults.ini')
    config = IiabConfig()
    config.readfp(open(master_config_file, 'r'))
    config.read(config_files)
    global_config = config
    return global_config


def config():
    """Return the global ConfigParser object.
    If the config files have not yet been read, than this
    will load them"""
    global global_config
    if global_config is None:
        raise Exception("config() called before load_config()")
    return global_config
