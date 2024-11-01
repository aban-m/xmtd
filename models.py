import pathlib
import os

import sys
sys.path.insert(0, '../xmtlib')

from xmt.recipes.storage import FileStorage
try: from . import comm
except: import comm

from yaml import safe_load as load_yaml

import time
from datetime import datetime
from threading import Thread, Event


from croniter import croniter
import pytz
tz = pytz.FixedOffset(2)        # HACK!

now = lambda: tz.localize(datetime.now())

import logging
logger = logging.getLogger('cronjob')


class Profile:
    @classmethod
    def from_file(cls, path):
        spec, cwd = load_yaml(open(path)), str(pathlib.Path(path).parent.absolute())
        return cls(spec)
    
    def __init__(self, spec: dict):
        self.spec = spec
        self.parse_spec()

    def parse_spec(self):
        self.name = self.spec['name']
        self.writer = None
        self.reader = None
        
        self.interfaces = {}
        for interface, config in self.spec['io']['interfaces'].items():
            self.interfaces[interface] = comm.bootstrap(interface, config, self.name)
            
        self.interfaces[interface] = comm.bootstrap(interface, config, self.name)

        if not isinstance(self.spec['io']['write'], list):
            self.spec['io']['write'] = [self.spec['io']['write']]
        self.writers = [self.interfaces[interface] for interface in self.spec['io']['write']]
        assert all(interface.is_writer for interface in self.writers), 'Must be all writers.'
        
        self.reader = self.interfaces[self.spec['io']['read']]
        assert self.reader.is_reader, 'Must be a reader.'

        self.recipes = self.spec['recipes']

        for i, pack in enumerate(self.recipes):
            rname, rdec = list(pack.items())[0]
            if isinstance(rdec, str) or isinstance(rdec, list):
                rdec = {
                    'cron': rdec
                }
            if not 'with' in rdec: rdec['with'] = {}
            if not 'recon' in rdec: rdec['recon'] = {}
            if not isinstance(rdec['cron'], list): rdec['cron'] = [rdec['cron']]
            if not 'where' in rdec:
                rdec['where'] = self.spec['io']['write']
            else:
                if not isinstance(rdec['where'], list): rdec['where'] = [rdec['where']]
            self.recipes[i] = {rname: rdec}

    def write(self, where, text, override):
        for writer in where:
            self.interfaces[writer].write(text, override)
            
    def read(self, prompt, override):
        return self.reader.read(prompt, override)
    
        
class Cron:
    def __init__(self, name, cron_expr, func, *args, **kwargs):
        self.running = False
        self.cron_expr = cron_expr
        self.init_time = now()
        self.croniter = croniter(self.cron_expr, self.init_time)

        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs

        self.random = 'R' in cron_expr

    def pre_delta_hook(self):
        if self.random:
            self.croniter = croniter(self.cron_expr, now())

    def time_to_sleep(self, return_delta = True):
        self.pre_delta_hook()
        next_instant = self.croniter.get_next(datetime)
        if not return_delta: return next_instant
        
        delta = (next_instant-tz.localize(datetime.now())).total_seconds()
        self._last_delta = delta
        if delta < 0:
            return self.time_to_sleep() # will get accustomed.
        return delta

    def _loop(self):
        while self.running:
            delta = self.time_to_sleep()
            logger.debug(f'{self.name}: Must sleep for {int(delta)} seconds.')
            for _ in range(int(delta)+1):
                try: time.sleep(1)
                except KeyboardInterrupt: self.running = False; return
                if not self.running:
                    return
            if self.running:
                self.func(*self.args, **self.kwargs)
                logger.debug(f'{self.name}: Finished execution.')
            else:
                return

    def start(self):
        self.running = True
        Thread(target=self._loop).start()

    def stop(self):
        self.running = False

    
