# Simple global configuration system
# Retrieve it with config()
import os
import platform

from ConfigParser import SafeConfigParser
from json import dumps, loads

from utils import run_mount


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

    def get_json(self, section, name):
        """Load a configuration value string and interpret
           it as a JSON structure"""
        return loads(self.get(section, name))

    def verify_knowledge_dir(self, path=None):
        """Verify that path is a valid knowledge_dir directory"""
        if path is None:
            path = self.get('DEFAULT', 'knowledge_dir')
        return os.path.isdir(path)

    def get_knowledge_dir(self):
        """Find a knowledge dataset directory.  Return None if
        the configured knowledge_dir setting did not exist
        and a search for the knowledge dir either was not done
        or failed, depending on the search_for_knowledge_dir setting"""
        do_search = self.getboolean('DEFAULT', 'search_for_knowledge_dir')
        path = self.get('DEFAULT', 'knowledge_dir')
        if self.verify_knowledge_dir(path):
            return path
        if do_search:
            mount_points = run_mount()
            for mp in mount_points:
                if mp[0][0] == '/':
                    path = os.path.join(mp[1], 'knowledge')
                    if self.verify_knowledge_dir(path):
                        self.set('DEFAULT', 'knowledge_dir', path)
                        return path
            # Check current directory
            if self.verify_knowledge_dir('knowledge'):
                self.set('DEFAULT', 'knowledge_dir', 'knowledge')
                return 'knowledge'
        return None

    def get_path(self, section, name):
        """Used to get a path relative to the knowledge/ dir.
        This will first search for the knowledge/ dir on mounted volumes if
        search_for_knowledge_dir is true"""
        self.get_knowledge_dir()
        return self.get(section, name)

    def get_default(self, section, name, default):
        """Get a value if it exists, otherwise return default"""
        if not self.has_option(section, name):
            return default
        return self.get(section, name)


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
    # Set the arch variable to our cpu architecture
    config.set('DEFAULT', 'arch', platform.machine())
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
