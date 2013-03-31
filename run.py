#!/usr/bin/env python
# Internet-In-A-Box by Braddock Gaskill, Feb 2013

import sys
from optparse import OptionParser

sys.path.append('.')

from iiab.webapp import IiabWebApp
from iiab.config import load_config, config


# borrowed from flask.Flask.run to allow it to work with profiler wrapped app
def run(app, host=None, port=None, debug=None, **options):
    from werkzeug.serving import run_simple
    if host is None:
        host = '127.0.0.1'
    if port is None:
        port = 5000
    if debug is not None:
        app.debug = bool(debug)
    options.setdefault('use_reloader', app.debug)
    options.setdefault('use_debugger', app.debug)
    try:
        run_simple(host, port, app, **options)
    finally:
        # reset the first request information if the development server
        # resetted normally.  This makes it possible to restart the server
        # without reloader and that stuff from an interactive shell.
        app._got_first_request = False


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
    parser.add_option("--tornado", action="store_true", default=False,
                      help="Use the Tornado web server")
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

    enable_profiler = False
    webapp = IiabWebApp(options.debug, enable_profiler=True)

    if options.tornado:
        from tornado.wsgi import WSGIContainer
        from tornado.httpserver import HTTPServer
        from tornado.ioloop import IOLoop

        http_server = HTTPServer(WSGIContainer(webapp.app))
        http_server.listen(config().getint('WEBAPP', 'port'))
        IOLoop.instance().start()
    else:
        if not enable_profiler:
            webapp.app.run(debug=config().getboolean('DEFAULT', 'debug'),
                           port=config().getint('WEBAPP', 'port'), host='0.0.0.0')
        else:
            run(webapp.app, debug=config().getboolean('DEFAULT', 'debug'),
                port=config().getint('WEBAPP', 'port'), host='0.0.0.0')


if __name__ == "__main__":
    main(sys.argv)
