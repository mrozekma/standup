#!/usr/bin/env python3

import os
import signal
import sys
from threading import currentThread

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from Config import config
from HTTPHandler import HTTPHandler
from rorn.HTTPServer import HTTPServer

# from stasis.Singleton import set as setDB
# from stasis.DiskMap import DiskMap
# setDB(DiskMap('db', cache = True))

from Log import console

currentThread().name = 'main'

# When python is started in the background it ignores SIGINT instead of throwing a KeyboardInterrupt
def signal_die(signum, frame):
	signals = dict((getattr(signal, name), name) for name in dir(signal) if name.startswith('SIG') and '_' not in name)
	raise SystemExit("Caught %s; exiting" % signals.get(signum, "signal %d" % signum))
signal.signal(signal.SIGINT, signal.default_int_handler)
signal.signal(signal.SIGTERM, signal_die)

server = HTTPServer(('', config.localBindPort), HTTPHandler)
HTTPHandler.enableStaticHandler('static')
HTTPHandler.enableVue('components', 'views')
try:
	console('main', 'Listening for connections')
	server.serve_forever()
except KeyboardInterrupt:
	sys.__stdout__.write("\n\n")
	console('main', 'Exiting at user request')
except (Exception, SystemExit) as e:
	sys.__stdout__.write("\n\n")
	console('main', '%s', e)

console('main', 'Closing server sockets')
server.server_close()

console('main', 'Done')
