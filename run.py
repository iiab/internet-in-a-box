#!/usr/bin/env python
# Internet-In-A-Box by Braddock Gaskill, Feb 2013

import sys
from optparse import OptionParser

sys.path.append('.')

from iiab.webapp import IiabWebApp
from iiab.config import load_config, config


def main(argv):
    parser = OptionParser()
    parser.add_option("--nodebug", dest="debug",
                      action="store_false", default=True,
                      help="Use to configure the app to not run in debug mode")
    parser.add_option("--port", dest="port", action="store", type="int",
                      default=None, help="The network port the app will use")
    parser.add_option("--config", dest="config", default="local.ini",
                      help="Optional additional config file to read instead of local_config.ini")
    parser.add_option("--knowledge", dest="knowledge", default=None,
                      help="Path to knowledge directory")
    (options, args) = parser.parse_args()

    load_config('config.ini', [options.config])

    # Set command line parameters in our config global
    if options.knowledge is not None:
        config().set('DEFAULT', 'knowledge_dir', options.knowledge)
    if options.port is not None:
        config().set('WEBAPP', 'port', str(options.port))
    config().set('DEFAULT', 'debug', str(options.debug))

    #print "root_dir = "
    #config().get('IIAB', 'root_dir')
    print "CONFIGURATION"
    print config().all_items_to_str()

    webapp = IiabWebApp(options.debug)
    webapp.app.run(debug=config().getboolean('DEFAULT', 'debug'),
                   port=config().getint('WEBAPP', 'port'), host='0.0.0.0')


if __name__ == "__main__":
    main(sys.argv)
