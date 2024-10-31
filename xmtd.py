import runtime
import models
import logging
import time
import os.path
import argparse


parser = argparse.ArgumentParser(description='XMTD - XMT daemon.')
parser.add_argument('path', type=str, help='The path to the directory.')
parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity level (use -v, -vv, -vvv, etc.)')
parser.add_argument('--logfile', type=str, help='Log file destination (default: $cwd/xmtd.log)', default='xmtd.log')
parser.add_argument('--debug', action='store_true', help='Enable debug mode (equivalent to -vvvvv).')

args = parser.parse_args()
if args.debug: args.verbose = 5
loglevel = max(logging.INFO - (args.verbose * 10), 10)


logger_names = ['cronjob', 'telegram-io', 'xmtd']
if args.verbose >= 5: logger_names = logging.root.manager.loggerDict.keys()
for name in logger_names: logging.getLogger(name).setLevel('DEBUG')

formatter = logging.Formatter('%(asctime)s - %(levelname)s [%(name)s]: %(message)s', datefmt='%Y-%b-%d %H:%M:%S')

handler = logging.StreamHandler()
handler.setLevel(loglevel)
handler.setFormatter(formatter)

fhandler = logging.FileHandler(os.path.join(args.path, args.logfile), mode='a', encoding='utf-8')
fhandler.setLevel('DEBUG')          # always debug for the file handler
fhandler.setFormatter(formatter)

for name in logger_names:
    logger = logging.getLogger(name)
    for h in [handler, fhandler]: logger.addHandler(h)


r = runtime.Runtime(args.path)
r.boot()

runtime.logger.info('Booting sequence complete.')
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    runtime.logger.fatal('Received KeyboardInterrupt. Exiting...')
    r.stop()
    exit()
