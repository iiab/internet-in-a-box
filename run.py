#!/usr/bin/env python
# Internet-In-A-Box by Braddock Gaskill, Feb 2013

import sys
from optparse import OptionParser

sys.path.append('.')

from iiab.webapp import IiabWebApp
from iiab.config import config


def main(argv):
    parser = OptionParser()
    parser.add_option("--nodebug", dest="debug",
                      action="store_false", default=True,
                      help="Use to configure the app to not run in debug mode")
    parser.add_option("--port", dest="port", action="store", type="int",
                      default=25000, help="The network port the app will use")
    parser.add_option("--config", dest="config", default="",
                      help="Optional additional config file to read")
    parser.add_option("--knowledge", dest="knowledge", default="/knowledge",
                      help="Path to knowledge directory")
    (options, args) = parser.parse_args()

    config()['knowledge_dir'] = options.knowledge

    webapp = IiabWebApp(options.debug)
    webapp.app.run(debug=options.debug, port=options.port, host='0.0.0.0')


if __name__ == "__main__":
    main(sys.argv)
